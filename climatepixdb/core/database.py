import os
from datetime import datetime
from typing import Optional

import firebase_admin
import ujson as json
from firebase_admin import firestore, storage as firebase_storage, credentials
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from google.api_core.exceptions import NotFound, AlreadyExists
from google.cloud.firestore_v1.collection import CollectionReference

from climatepixdb.core.errors import UploadError, CredentialsError
from climatepixdb.core.image_info import ImageInfo
from climatepixdb.core.sending_utils import Sending, UploadToSend
from climatepixdb.core.upload_failure import UploadFailure
from climatepixdb.core.upload_info import UploadInfo
from climatepixdb.core.upload_list import UploadList


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
        options = {"storageBucket": "climatepixweb-244121.appspot.com", }
        firebase_admin.initialize_app(cred, options=options)
        self.__database = firestore.client()
        self.__storage = firebase_storage.bucket()
        self.__dev_collection = self.__database.collection('dev')
        self.__public_collection = self.__database.collection('public')

    def test(self):
        print(self.__storage.name)
        for blob in self.__storage.list_blobs(prefix='dev/'):
            print(blob.name)

    @staticmethod
    def __get_uploads(collection, before=None, after=None):
        # type: (CollectionReference, Optional[DatetimeWithNanoseconds], Optional[DatetimeWithNanoseconds]) -> UploadList
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
        upload_list = UploadList()
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
            doc_dict = doc.to_dict()
            try:
                upload_list.add_upload(UploadInfo(collection.id, doc.id, doc_dict))
            except UploadError as exc:
                upload_list.add_failure(UploadFailure(collection.id, doc.id, exc, doc_dict))
        return upload_list

    def get_dev_uploads(self, before=None, after=None):
        # type: (Optional[DatetimeWithNanoseconds], Optional[DatetimeWithNanoseconds]) -> UploadList
        """ Retrieve uploads info from `dev` database folder.
            If before XOR after is provided, it should be a timestamp as DateWithNanoseconds object
            (e.g. ImageInfo.timestamp field), and only uploads strictly more recent (if after)
            or older (if before) will be returned.
        """
        return self.__get_uploads(self.__dev_collection, before=before, after=after)

    def get_public_uploads(self, before=None, after=None):
        # type: (Optional[DatetimeWithNanoseconds], Optional[DatetimeWithNanoseconds]) -> UploadList
        """ Retrieve uploads info from `public` database folder.
            If before XOR after is provided, it should be a timestamp as DateWithNanoseconds object
            (e.g. ImageInfo.timestamp field), and only uploads strictly more recent (f after)
            or older (if before)  will be returned.
        """
        return self.__get_uploads(self.__public_collection, before=before, after=after)

    def download_all_images(self,
                            uploads,
                            output_folder,
                            categorize=False,
                            verbose=False,
                            save_metadata=True):
        # type: (UploadList, str, bool, bool, bool) -> int
        """ Download all images from given list of uploads to given output folder.
            If an image is successfully downloaded, field ImageInfo.local_path
            of corresponding ImageInfo object will be updated with local image path.
            :param uploads: a UploadList object.
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
        metadata = {}
        downloaded_images = set()
        images_without_metadata = set()
        upload_indices = set()
        for collection_id in uploads.collections:
            for blob in self.__storage.list_blobs(prefix='%s/' % collection_id):
                _, upload_id, image_name = blob.name.split('/')
                upload_indices.add(upload_id)
                image_info = None
                if upload_id in uploads.uploads and blob.name in uploads.uploads[upload_id].images:
                    upload_info = uploads.uploads[upload_id]
                    image_info = upload_info.images[blob.name]
                    category = image_info.category
                    location = image_info.location
                    timestamp = str(upload_info.timestamp)
                else:
                    images_without_metadata.add(blob.name)
                    category = ImageInfo.UNKNOWN_CATEGORY
                    location = ""
                    if upload_id in uploads.failures:
                        timestamp = uploads.failures[upload_id].timestamp
                    else:
                        timestamp = ImageInfo.UNKNOWN_CATEGORY

                output_pieces = [output_folder]
                if categorize:
                    output_pieces.append(category)
                output_pieces.append(blob.name.replace('/', '_'))
                output_path = os.path.join(*output_pieces)
                os.makedirs(os.path.join(*output_pieces[:-1]), exist_ok=True)
                blob.download_to_filename(output_path)
                if os.path.isfile(output_path):
                    downloaded_images.add(blob.name)
                    if image_info:
                        image_info.local_path = output_path
                    if save_metadata:
                        if categorize:
                            metadata.setdefault(category, {})[output_path] = {
                                'location': location,
                                'timestamp': timestamp
                            }
                        else:
                            metadata[output_path] = {
                                'category': category,
                                'location': location,
                                'timestamp': timestamp
                            }
                    if verbose:
                        print('DOWNLOADED', blob.name, '=>', output_path)

        remaining_images = set()
        invalid_uploads = []
        for upload in uploads.uploads.values():
            if upload.upload_id not in upload_indices:
                invalid_uploads.append(upload)
            else:
                for firebase_path in upload.images:
                    if firebase_path not in downloaded_images:
                        remaining_images.add(firebase_path)
        for failure in uploads.failures.values():
            if failure.upload_id not in upload_indices:
                invalid_uploads.append(failure)
        if verbose:
            for firebase_path in sorted(remaining_images):
                print('NOT FOUND', firebase_path)
            if downloaded_images:
                print('NB DOWNLOADED', len(downloaded_images))
            if images_without_metadata:
                print('NB WITHOUT METADATA', len(images_without_metadata))
            for upload_status in sorted(invalid_uploads, key=lambda u: u.upload_id):
                print('INVALID UPLOAD', upload_status.upload_id, '(no images associated)')

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
        return len(downloaded_images)

    def delete_invalid_documents(self, uploads):
        # type: (UploadList) -> None
        upload_indices = {}
        for collection_id in uploads.collections:
            for blob in self.__storage.list_blobs(prefix='%s/' % collection_id):
                upload_indices.setdefault(collection_id, set()).add(blob.name.split('/')[1])
        invalid_uploads = []
        for upload in uploads.uploads.values():
            if upload.upload_id not in upload_indices[upload.collection_id]:
                invalid_uploads.append((upload.collection_id, upload.upload_id))
        for failure in uploads.failures.values():
            if failure.upload_id not in upload_indices[failure.collection_id]:
                invalid_uploads.append((failure.collection_id, failure.upload_id))
        for collection_id, upload_id in sorted(invalid_uploads):
            col = self.__database.collection(collection_id)
            doc = col.document(upload_id)
            doc.delete()
            print('DELETED INVALID UPLOAD ENTRY',
                  '%s/%s' % (collection_id, upload_id),
                  '(no images associated)')

    def delete_uploads(self, uploads, force=False, verbose=False):
        # type: (UploadList, bool, bool) -> None
        """ Delete all images from given list of uploads on server.
            :param uploads: a UploadLIst object.
            :param force: if True, delete images without asking for confirmation.
            :param verbose: if True, print some info about deleted images.
        """
        images = {}
        for collection_id in uploads.collections:
            for blob in self.__storage.list_blobs(prefix='%s/' % collection_id):
                upload_id = blob.name.split('/')[1]
                images.setdefault(collection_id, {}).setdefault(upload_id, set()).add(blob.name)
        for collection_id, upload_id in uploads.get_paths():
            col = self.__database.collection(collection_id)
            doc = col.document(upload_id)
            path = '%s/%s' % (collection_id, upload_id)
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
            if collection_id in images and upload_id in images[collection_id]:
                for firebase_path in sorted(images[collection_id][upload_id]):
                    try:
                        self.__storage.delete_blob(firebase_path)
                        if verbose:
                            print('[IMAGE DELETED]', firebase_path)
                    except NotFound:
                        if verbose:
                            print('[IMAGE NOT FOUND]', firebase_path)
            doc.delete()
            if verbose:
                print('[DOC DELETED]', doc.id)

    def upload(self, metadata_file_name):
        # type: (str) -> None
        metadata_file_name = os.path.abspath(metadata_file_name)
        metadata_directory = os.path.dirname(metadata_file_name)
        with open(metadata_file_name, 'r') as file:
            metadata = json.load(file)
        if not isinstance(metadata, dict):
            raise RuntimeError('Metadata is not a dictionary in file %s' % metadata_file_name)
        structured_to_send = {}
        uploads_to_send = {}
        nb_no_category = 0
        nb_sendings = 0
        for image_path, image_metadata in sorted(metadata.items()):
            image_basename = os.path.basename(image_path)
            sending = Sending()
            sending.category = image_metadata.get('category', None)
            sending.location = image_metadata['location']
            sending.timestamp = image_metadata['timestamp']
            sending.firebase_path = image_basename.replace('_', '/')
            sending.collection_id, sending.upload_id, image_name = sending.firebase_path.split('/')
            sending.image_id = int(os.path.splitext(image_name)[0])
            sending.local_path = os.path.join(metadata_directory, image_basename)
            assert sending.timestamp, 'Got an invalid timestamp'
            nb_no_category += sending.category is None
            nb_sendings += 1
            structured_to_send.setdefault(
                sending.collection_id, {}).setdefault(sending.upload_id, []).append(sending)

        # Check categories.
        if nb_no_category == nb_sendings:
            inferred_category = os.path.basename(metadata_directory)
            print('Getting category from metadata containing folder', inferred_category)
            for upload_id_to_sendings in structured_to_send.values():
                for sendings in upload_id_to_sendings.values():
                    for sending in sendings:
                        sending.category = inferred_category
        elif nb_no_category != 0:
            raise RuntimeError('Invalid metadata: all images should either have a category or '
                               'no category specified (to be retrieved from metadata folder name).')

        # Check timestamps.
        for collection_id, uploads in structured_to_send.items():
            for upload_id, images in uploads.items():
                timestamps = {sending.timestamp for sending in images}
                if len(timestamps) != 1:
                    raise RuntimeError('No same timestamp for all images in %s' % upload_id)
                timestamp = images[0].timestamp
                # Update timestamp to current date if timestamp is unknown
                if timestamp == ImageInfo.UNKNOWN_CATEGORY:
                    timestamp = datetime.now().isoformat()
                uploads_to_send.setdefault(collection_id, []).append(UploadToSend(
                    upload_id, timestamp, images))

        for collection_id, uploads in uploads_to_send.items():
            col = self.__database.collection(collection_id)
            for upload in sorted(uploads, key=lambda u: u.upload_id):
                doc = col.document(upload.upload_id)
                doc_just_created = False
                try:
                    doc.create({
                        'timestamp': datetime.fromisoformat(upload.timestamp),
                        'images': None
                    })
                    doc_just_created = True
                    for sending in upload.images:  # type: Sending
                        blob = self.__storage.blob(sending.firebase_path)
                        if blob.exists():
                            raise AlreadyExists(
                                'An image already exists: %s' % sending.firebase_path)
                    for sending in sorted(upload.images, key=lambda s: s.image_id):  # type: Sending
                        blob = self.__storage.blob(sending.firebase_path)
                        blob.upload_from_filename(sending.local_path)
                        sending.url = blob.public_url
                        print('UPLOADED', sending.firebase_path)
                    doc.update({
                        'images': [sending.to_upload() for sending in sorted(
                            upload.images, key=lambda s: s.image_id)]
                    })
                    print('CREATED UPLOAD', upload.upload_id)
                except AlreadyExists as exc:
                    print('CANNOT SEND UPLOAD', upload.upload_id, exc)
                    if doc_just_created:
                        doc.delete()
