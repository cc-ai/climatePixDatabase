from typing import Optional

from google.api_core.datetime_helpers import DatetimeWithNanoseconds

from climatepixdb.core.image_info import ImageInfo


class UploadFailure:
    __slots__ = ('collection_id', 'upload_id', 'exception', 'timestamp')

    def __init__(self, collection_id, upload_id, exception, initial_data=None):
        # type: (str, str, Exception, Optional[dict]) -> None
        self.collection_id = collection_id  # type: str
        self.upload_id = upload_id  # type: str
        self.exception = exception  # type: Exception
        self.timestamp = ImageInfo.UNKNOWN_CATEGORY
        if (initial_data
                and 'timestamp' in initial_data
                and isinstance(initial_data['timestamp'], DatetimeWithNanoseconds)):
            self.timestamp = str(initial_data['timestamp'])
