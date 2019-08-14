import os
import sys
from typing import List, Optional, Dict

import firebase_admin
import ujson as json
from firebase_admin import firestore, storage as firebase_storage, credentials
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from google.cloud.firestore_v1.collection import CollectionReference
from google.api_core.exceptions import NotFound

class UploadError(Exception):
    """ Specific upload exception raised if a upload document from database is invalid. """


class CredentialsError(Exception):
    def __init__(self, file_name):
        super(CredentialsError, self).__init__(
"""
-----------------------------------------------
MISSING CREDENTIALS FILE TO CONNECT TO DATABASE
-----------------------------------------------
Credentials file %s not found in working directory.
If you have this file, either place it here or execute your script where the file is stored.
Otherwise, please contact CCAI project members to get a copy of this file.
Thanks!
""" % file_name
        )


class ImageInfo:
    """ Image info class representing a image info stored in Firebase database. Properties:
        - category: image category
        - location: image location
        - url: public web URL to access image file, usable in browser.
        - firebase_path: image path in Firebase storage. To be used to retrieve image file from storage.
        - local_path: local file path where image is downloaded. Initialized with None, you are free
            to set it manually to remember where you downloaded the image.
            If you use download memthods from class ClimatePixDatabase (`download_image() or download_all_images()`),
            this field will be automatically filled.
    """
    __slots__ = ('category', 'location', 'firebase_path', 'local_path', 'url')

    DEFAULT_CATEGORY = 'Flood'

    def __init__(self, dictionary):
        self.category = dictionary['category'] or ImageInfo.DEFAULT_CATEGORY
        self.location = dictionary['location']
        self.firebase_path = dictionary['path']
        self.url = dictionary['url']
        self.local_path = None


class UploadInfo:
    """ Upload info class representing an upload info stored in Firebase database. Properties:
        - upload_id: ID of upload info in Firebase database.
        - images: list of ImageInfo objects representing info abouts images uploaded on this upload.
        - timestamp_nanoseconds: server timestamp in nanoseconds where this upload was done.
    """
    __slots__ = ('collection_id', 'upload_id', 'images', 'timestamp')

    def __init__(self, collection_id, upload_id, dictionary):
        # type: (str, str, dict) -> None
        for field in ('timestamp', 'images'):
            if field not in dictionary:
                raise UploadError('Upload dictionary missing field %s' % field)
        timestamp = dictionary['timestamp']
        images = dictionary['images']
        if not isinstance(timestamp, DatetimeWithNanoseconds):
            raise UploadError('Invalid upload dictionary timestamp format.')
        if not isinstance(images, list):
            raise UploadError('Invalid upload dictionary images format.')
        self.collection_id = collection_id
        self.upload_id = upload_id
        self.images = [ImageInfo(image_dictionary) for image_dictionary in images]
        self.timestamp = timestamp

    @property
    def timestamp_nanoseconds(self):
        # Convert timestamp field (DateWithNanoseconds object) to nanoseconds as integer.
        timestamp = self.timestamp.timestamp_pb()
        return timestamp.seconds * 1000000000 + timestamp.nanos


def images_by_category(uploads):
    # type: (List[UploadInfo]) -> Dict[str, List[ImageInfo]]
    """ Classify images of given list of uploads per image category.
        :param uploads: list of UploadInfo objects.
        :return: a dictionary matching each category found to a list of images (ImageInfo objects).
    """
    categories = {}
    for upload in uploads:
        for image_info in upload.images:
            categories.setdefault(image_info.category, []).append(image_info)
    return categories


class ClimatePixDatabase:
    """ Class to be used to connect to Firebase, get uploads info and download uploaded images.
        Credentials JSON file must be placed on the folder when script is executed. File name must be:
        "credentials.json"
    """
    __slots__ = ('__database', '__storage', '__dev_collection', '__public_collection')

    def __init__(self):
        credentials_file_name = "credentials.json"
        if not os.path.isfile(credentials_file_name):
            raise CredentialsError(credentials_file_name)

        cred = credentials.Certificate(credentials_file_name)
        options = {"storageBucket": "floodreport-d0dfb.appspot.com", }
        firebase_admin.initialize_app(cred, options=options)
        self.__database = firestore.client()
        self.__storage = firebase_storage.bucket()
        self.__dev_collection = self.__database.collection('dev')
        self.__public_collection = self.__database.collection('public')

    @staticmethod
    def __get_uploads(collection, before=None, after=None):
        # type: (CollectionReference, Optional[DatetimeWithNanoseconds], Optional[DatetimeWithNanoseconds]) -> List[UploadInfo]
        """ Retrieve uploads from given collection. If after is specified, it should be a
            DateWithNanoseconds object used to return only uploads occurred after this date.
            :param collection: a Firebase collection object (e.g. ClimatePixDatabase.__dev_collection
                and ClimatePixDatabase.__public_collection attributes)
            :param before: (optional) a DateWithNanoseconds object representing a timestamp.
                If provided, only uploads strictly older than this timestamp will be returned.
            :param after: (optional) a DateWithNanoseconds object representing a timestamp
                (e.g. ImageInfo.timestamp field). If provided, only uploads
                strictly more recent than this timestamp will be returned.
                NB: after or before should be provided, or none of them, but not both of them.
            :return: a list of UploadInfo objects.
        """
        uploads = []
        if before is None and after is None:
            stream = collection.stream()
        else:
            if before is not None and after is not None:
                raise AssertionError('after and before cannot be provided both.')
            if after is not None:
                comparison = '>'
                timestamp = after
            else:
                comparison = '<'
                timestamp = before
            stream = collection.where('timestamp', comparison, timestamp).stream()
        for doc in stream:
            try:
                uploads.append(UploadInfo(collection.id, doc.id, doc.to_dict()))
            except UploadError:
                print('[Collection %s] Invalid upload dictionary' % collection.id, doc.id, file=sys.stderr)
        return uploads

    def get_dev_uploads(self, before=None, after=None):
        # type: (Optional[DatetimeWithNanoseconds], Optional[DatetimeWithNanoseconds]) -> List[UploadInfo]
        """ Retrieve uploads info from `dev` database folder.
            If before XOR after is provided, it should be a timestamp as DateWithNanoseconds object
            (e.g. ImageInfo.timestamp field), and only uploads strictly more recent (if after)
            or older (if before) will be returned.
        """
        return self.__get_uploads(self.__dev_collection, before=before, after=after)

    def get_public_uploads(self, before=None, after=None):
        # type: (Optional[DatetimeWithNanoseconds], Optional[DatetimeWithNanoseconds]) -> List[UploadInfo]
        """ Retrieve uploads info from `public` database folder.
            If before XOR after is provided, it should be a timestamp as DateWithNanoseconds object
            (e.g. ImageInfo.timestamp field), and only uploads strictly more recent (f after)
            or older (if before)  will be returned.
        """
        return self.__get_uploads(self.__public_collection, before=before, after=after)

    def download_image(self, image_info, filename):
        # type: (ImageInfo, str) -> bool
        """ Download image file associated to given image info into given file name.
            If image is successfully downloaded, image_info.local_path will be updated with filename.
            :param image_info: ImageInfo object
            :param filename: output file path
            :return True if image was successfully downloaded, False otherwise.
        """
        is_downloaded = False
        blob = self.__storage.get_blob(image_info.firebase_path)
        if blob is not None:
            dir_name = os.path.dirname(filename)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            blob.download_to_filename(filename)
            if os.path.exists(filename):
                image_info.local_path = filename
                is_downloaded = True
        return is_downloaded

    def download_all_images(self, uploads, output_folder, categorize=False, verbose=False, save_metadata=True):
        # type: (List[UploadInfo], str, bool, bool, bool) -> int
        """ Download all images from given list of uploads to given output folder.
            If an image is successfully downloaded, field ImageInfo.local_path
            of corresponding ImageInfo object will be updated with local image path.
            :param uploads: a list of UploadInfo objects.
            :param output_folder: string representing output folder. Will be created if not exists.
            :param categorize: if True, group images by category into output folder. Each category will be
                a sub-folder with category as name, containing associated images files.
            :param verbose: if True, print some info about images not found and images downloaded.
            :param save_metadata: if True, save metadata associated to images into a JSON file.
                - If `categorize` is False, save metadata into `<output_folder>/metadata.json`. JSON object will be a
                  dictionary mapping each image file path to a dictionary of metadata (category, location and timestamp).
                - If `categorize` is True, save metadata for each category into `<output_folder>/<category>/metadata.json`.
                  JSON object will be a dictionary mapping each image file path to a dictionary of metadata
                  (location and timestamp).
            :return: number of images downloaded.
        """
        nb_downloaded = 0
        metadata = {}
        for upload in uploads:
            for image_info in upload.images:
                blob = self.__storage.get_blob(image_info.firebase_path)
                if blob:
                    output_pieces = [output_folder]
                    if categorize:
                        output_pieces.append(image_info.category)
                    output_pieces.append(image_info.firebase_path.replace('/', '_'))
                    output_path = os.path.join(*output_pieces)
                    os.makedirs(os.path.join(*output_pieces[:-1]), exist_ok=True)
                    blob.download_to_filename(output_path)
                    if os.path.isfile(output_path):
                        nb_downloaded += 1
                        image_info.local_path = output_path
                        if save_metadata:
                            if categorize:
                                metadata.setdefault(image_info.category, {})[output_path] = {
                                    'location': image_info.location,
                                    'timestamp': str(upload.timestamp)
                                }
                            else:
                                metadata[output_path] = {
                                    'category': image_info.category,
                                    'location': image_info.location,
                                    'timestamp': str(upload.timestamp)
                                }
                        if verbose:
                            print('DOWNLOADED', image_info.firebase_path, '=>', output_path)
                elif verbose:
                    print('NOT FOUND', image_info.firebase_path)
        if save_metadata:
            if categorize:
                for category, data in metadata.items():
                    json_path = os.path.join(output_folder, category, 'metadata.json')
                    with open(json_path, 'w') as file:
                        json.dump(data, file, indent=1)
                    if verbose:
                        print('METADATA SAVED', json_path)
            else:
                json_path = os.path.join(output_folder, 'metadata.json')
                with open(json_path, 'w') as file:
                    json.dump(metadata, file, indent=1)
                if verbose:
                    print('METADATA SAVED', json_path)
        return nb_downloaded

    def delete_all_images(self, uploads, force=False, verbose=False):
        # type: (List[UploadInfo], bool, bool) -> None
        """ Delete all images from given list of uploads on server.
            :param uploads: a list of UploadInfo objects.
            :param force: if True, delete images without asking for confirmation.
            :param verbose: if True, print some info about deleted images.
        """
        nb_deleted = 0
        for upload in uploads:
            col = self.__database.collection(upload.collection_id)
            doc = col.document(upload.upload_id)
            path = '%s/%s' % (upload.collection_id, upload.upload_id)
            if not force:
                to_delete = None
                while to_delete is None:
                    raw_reply = input(
                        'Delete this upload? (Yes/yes/y or No/no/n) [%s]:' % path).strip().lower()
                    if raw_reply in ('y', 'yes'):
                        to_delete = True
                    elif raw_reply in ('n', 'no'):
                        to_delete = False
                    else:
                        print('Bad reply ...')
                if not to_delete:
                    continue
            for image_info in upload.images:
                try:
                    self.__storage.delete_blob(image_info.firebase_path)
                    nb_deleted += 1
                    if verbose:
                        print('[IMAGE DELETED]', image_info.firebase_path)
                except NotFound:
                    if verbose:
                        print('[IMAGE NOT FOUND]', image_info.firebase_path)
            doc.delete()
            if verbose:
                print('[DOC DELETED]', doc.id)
