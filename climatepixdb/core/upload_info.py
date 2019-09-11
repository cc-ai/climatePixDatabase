from typing import Dict

from google.api_core.datetime_helpers import DatetimeWithNanoseconds

from climatepixdb.core.errors import UploadError
from climatepixdb.core.image_info import ImageInfo


class UploadInfo:
    """ Upload info class representing an upload info stored in Firebase database. Properties:
        - upload_id: ID of upload info in Firebase database.
        - images: list of ImageInfo objects representing info abouts images uploaded on this upload.
        - timestamp_nanoseconds: server timestamp in nanoseconds where this upload was done.
    """
    __slots__ = ('collection_id', 'upload_id', 'images', 'timestamp')
    images: Dict[str, ImageInfo]

    def __init__(self, collection_id, upload_id, dictionary):
        # type: (str, str, dict) -> None
        for field in ('timestamp', 'images'):
            if field not in dictionary:
                raise UploadError('Upload dictionary missing field %s' % field)
        timestamp = dictionary['timestamp']
        images = dictionary['images']
        if not isinstance(timestamp, DatetimeWithNanoseconds):
            raise UploadError('Invalid timestamp format.')
        if not isinstance(images, list):
            raise UploadError(
                'Invalid images format (expected a list, got %s).' % type(images).__name__)
        self.collection_id = collection_id
        self.upload_id = upload_id
        self.images = {}
        for image_dictionary in images:
            image_info = ImageInfo(image_dictionary)
            self.images[image_info.firebase_path] = image_info
        self.timestamp = timestamp

    @property
    def timestamp_nanoseconds(self):
        # Convert timestamp field (DateWithNanoseconds object) to nanoseconds as integer.
        timestamp = self.timestamp.timestamp_pb()
        return timestamp.seconds * 1000000000 + timestamp.nanos
