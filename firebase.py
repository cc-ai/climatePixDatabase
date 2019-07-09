import os
import sys
from typing import List

import firebase_admin
from firebase_admin import firestore, storage as firebase_storage, credentials


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
    __slots__ = ('upload_id', 'images', 'timestamp_nanoseconds')

    def __init__(self, upload_id, dictionary):
        if ('timestamp' not in dictionary
                or not hasattr(dictionary['timestamp'], 'timestamp_pb')
                or not callable(dictionary['timestamp'].timestamp_pb)):
            raise UploadError('Upload dictionary does not have a valid timestamp field.')
        if 'images' not in dictionary or not dictionary['images'] or not isinstance(dictionary['images'], list):
            raise UploadError('Upload dictionary does not have a valid images field.')
        timestamp = dictionary['timestamp'].timestamp_pb()
        self.upload_id = upload_id
        self.images = [ImageInfo(image_dictionary) for image_dictionary in dictionary['images']]
        self.timestamp_nanoseconds = timestamp.seconds * 1000000000 + timestamp.nanos


class Firebase:
    """ Firebase class to be used to connect to Firebase, get uploads info and download uploaded images.
        Credentials JSON file must be placed on the folder when script is executed. File name must be:
        "credentials.json"
    """
    __slots__ = ('__database', '__storage', '__dev_collection', '__public_collection')

    def __init__(self):
        cred = credentials.Certificate("credentials.json")
        options = {
            "storageBucket": "floodreport-d0dfb.appspot.com",
        }
        firebase_admin.initialize_app(cred, options=options)
        self.__database = firestore.client()
        self.__storage = firebase_storage.bucket()
        self.__dev_collection = self.__database.collection('dev')
        self.__public_collection = self.__database.collection('public')

    def __get_uploads(self, collection):
        uploads = []
        for doc in collection.stream():
            try:
                uploads.append(UploadInfo(doc.id, doc.to_dict()))
            except UploadError:
                print('[%s] Invalid upload dictionary' % collection.id, doc.id, file=sys.stderr)
        return uploads

    def get_dev_uploads(self):
        # type: () -> List[UploadInfo]
        """ Retrieve uploads info from `dev` database folder. """
        return self.__get_uploads(self.__dev_collection)

    def get_public_uploads(self):
        # type: () -> List[UploadInfo]
        """ Retrieve uploads info from `public` database folder. """
        return self.__get_uploads(self.__public_collection)

    def download(self, image_info, filename):
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


def main():
    """ Usage example.
        ** NB **: To be able to connect to Firebase, a credentials file called `credentials.json` should be placed
        in the folder where script is executed. Please ask to project owner to get a copy of credentials file.
    """
    firebase = Firebase()
    public_uploads = firebase.get_public_uploads()
    print(len(public_uploads), 'public upload(s).')
    image_info_example = public_uploads[0].images[0]
    firebase.download(image_info_example, image_info_example.path)
    print('An image was downloaded to', image_info_example.path)


if __name__ == '__main__':
    main()
