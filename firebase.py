import os
import sys
from typing import List, Optional

import firebase_admin
from firebase_admin import firestore, storage as firebase_storage, credentials
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from google.cloud.firestore_v1.collection import CollectionReference


class UploadError(Exception):
    """ Specific upload exception raised if a upload document from database is invalid. """


class ImageInfo:
    """ Image info class representing a image info stored in Firebase database. Properties:
        - category: image category
        - location: image location
        - path: image path in Firebase storage. To be used to retrieve image file from storage.
        - url: public web URL to access image file, usable in browser.
    """
    __slots__ = ('category', 'location', 'path', 'url')

    def __init__(self, dictionary):
        self.category = dictionary['category']
        self.location = dictionary['location']
        self.path = dictionary['path']
        self.url = dictionary['url']


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


class Firebase:
    """ Firebase class to be used to connect to Firebase, get uploads info and download uploaded images.
        Credentials JSON file must be placed on the folder when script is executed. File name must be:
        "credentials.json"
    """
    __slots__ = ('__database', '__storage', '__dev_collection', '__public_collection')

    def __init__(self):
        cred = credentials.Certificate("credentials.json")
        options = {"storageBucket": "floodreport-d0dfb.appspot.com", }
        firebase_admin.initialize_app(cred, options=options)
        self.__database = firestore.client()
        self.__storage = firebase_storage.bucket()
        self.__dev_collection = self.__database.collection('dev')
        self.__public_collection = self.__database.collection('public')

    @staticmethod
    def __get_uploads(collection, after=None):
        # type: (CollectionReference, Optional[DatetimeWithNanoseconds]) -> List[UploadInfo]
        """ Retrieve uploads from given collection. If after is specified, it should be a
            DateWithNanoseconds object used to return only uploads occurred after this date.
            :param collection: a Firebase collection object (e.g. firebase.__dev_collection
                and firebase.__public_collection attributes)
            :param after: (optional) a DateWithNanoseconds object representing a timestamp
                (e.g. ImageInfo.timestamp field). If provided, only uploads
                strictly more recent than this timestamp will be returned.
            :return: a list of UploadInfo objects.
        """
        uploads = []
        if after is None:
            stream = collection.stream()
        else:
            stream = collection.where('timestamp', '>', after).stream()
        for doc in stream:
            try:
                uploads.append(UploadInfo(collection.id, doc.id, doc.to_dict()))
            except UploadError:
                print('[Collection %s] Invalid upload dictionary' % collection.id, doc.id, file=sys.stderr)
        return uploads

    def get_dev_uploads(self, after=None):
        # type: (Optional[DatetimeWithNanoseconds]) -> List[UploadInfo]
        """ Retrieve uploads info from `dev` database folder.
            If after is provided, it should be a timestamp as DateWithNanoseconds object
            (e.g. ImageInfo.timestamp field), and only uploads strictly more recent
            than this date will be returned.
        """
        return self.__get_uploads(self.__dev_collection, after=after)

    def get_public_uploads(self, after=None):
        # type: (Optional[DatetimeWithNanoseconds]) -> List[UploadInfo]
        """ Retrieve uploads info from `public` database folder.
            If after is provided, it should be a timestamp as DateWithNanoseconds object
            (e.g. ImageInfo.timestamp field), and only uploads strictly more recent
            than this date will be returned.
        """
        return self.__get_uploads(self.__public_collection, after=after)

    def download_image(self, image_info, filename):
        # type: (ImageInfo, str) -> None
        """ Download image file associated to given image info into given file name.
            :param image_info: ImageInfo object
            :param filename: output file path
        """
        blob = self.__storage.get_blob(image_info.path)
        dir_name = os.path.dirname(filename)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        blob.download_to_filename(filename)

    def download_all_images(self, uploads, output_folder, verbose=False):
        # type: (List[UploadInfo], str, bool) -> int
        """ Download all images from given list of uploads to given output folder.
            :param uploads: a list of UploadInfo objects.
            :param output_folder: string representing output folder. Will be created if not exists.
            :param verbose: if True, print some info about images not found and images downloaded.
            :return: number of images downloaded.
        """
        nb_downloaded = 0
        os.makedirs(output_folder, exist_ok=True)
        for upload in uploads:
            for image_info in upload.images:
                blob = self.__storage.get_blob(image_info.path)
                if blob:
                    output_basename = image_info.path.replace('/', '_')
                    output_path = os.path.join(output_folder, output_basename)
                    blob.download_to_filename(output_path)
                    if os.path.isfile(output_path):
                        nb_downloaded += 1
                        if verbose:
                            print('DOWNLOADED', image_info.path, '=>', output_path)
                elif verbose:
                    print('NOT FOUND', image_info.path)
        return nb_downloaded


def example_download_1_image():
    """ Usage example.
        ** NB **: To be able to connect to Firebase, a credentials file called `credentials.json` should be placed
        in the folder where script is executed. Please ask to project owner to get a copy of credentials file.
    """
    firebase = Firebase()
    public_uploads = firebase.get_public_uploads()
    print(len(public_uploads), 'public upload(s).')
    image_info_example = public_uploads[0].images[0]
    firebase.download_image(image_info_example, image_info_example.path)
    print('An image was downloaded to', image_info_example.path)


def example_download_all_images():
    firebase = Firebase()
    public_uploads = firebase.get_public_uploads()
    sorted_uploads = sorted(public_uploads, key=lambda u: (u.timestamp, u.upload_id))
    print('Uploads:')
    for upload in public_uploads:
        print('\t%s\t%s' % (upload.upload_id, upload.timestamp))
    print('Uploaded sorted by timestamp:')
    for upload in sorted_uploads:
        print('\t%s\t%s' % (upload.upload_id, upload.timestamp))
    after = sorted_uploads[1].timestamp
    recent_uploads = firebase.get_public_uploads(after=after)
    print('Recent uploads after', after)
    for upload in recent_uploads:
        print('\t%s\t%s' % (upload.upload_id, upload.timestamp))
    print('Downloading images from recent uploads.')
    nb_downloaded = firebase.download_all_images(recent_uploads, 'public', verbose=True)
    print('Downloaded', nb_downloaded, '/', sum(len(u.images) for u in recent_uploads), 'images from recent uploads.')


def main():
    example_download_all_images()


if __name__ == '__main__':
    main()
