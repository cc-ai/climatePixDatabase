from typing import Dict, List, Tuple

from climatepixdb.core.upload_failure import UploadFailure
from climatepixdb.core.upload_info import UploadInfo


class UploadList:
    __slots__ = ('uploads', 'failures', 'collections')

    def __init__(self):
        self.uploads = {}  # type: Dict[str, UploadInfo]
        self.failures = {}  # type: Dict[str, UploadFailure]
        self.collections = set()

    def add_upload(self, upload):
        # type: (UploadInfo) -> None
        self.uploads[upload.upload_id] = upload
        self.collections.add(upload.collection_id)

    def add_failure(self, failure):
        # type: (UploadFailure) -> None
        self.failures[failure.upload_id] = failure
        self.collections.add(failure.collection_id)

    def get_paths(self):
        # type: () -> List[Tuple[str, str]]
        paths = [(upload.collection_id, upload.upload_id)
                 for upload in self.uploads.values()]
        paths.extend((failure.collection_id, failure.upload_id)
                     for failure in self.failures.values())
        paths.sort()
        return paths
