class Sending:
    __slots__ = ('category', 'location', 'firebase_path', 'url', 'local_path',
                 'timestamp', 'collection_id', 'upload_id', 'image_id')

    def __init__(self):
        self.category = None
        self.location = None
        self.firebase_path = None
        self.url = None
        self.local_path = None

        self.timestamp = None
        self.collection_id = None
        self.upload_id = None
        self.image_id = None

    def to_upload(self):
        return {
            'category': self.category,
            'location': self.location,
            'path': self.firebase_path,
            'url': self.url,
        }

    def __repr__(self):
        return str(self)

    def __str__(self):
        return ('('
                'CATEGORY %s, '
                'LOCATION %s, '
                'TIMESTAMP %s, '
                'COLLECTION %s, '
                'UPLOAD ID %s, '
                'ID %s, '
                'PATH %s'
                ')' % (
                    self.category,
                    self.location,
                    self.timestamp,
                    self.collection_id,
                    self.upload_id,
                    self.firebase_path,
                    self.local_path
                ))


class UploadToSend:
    __slots__ = ('upload_id', 'timestamp', 'images')

    def __init__(self, upload_id, timestamp, images):
        self.upload_id = upload_id
        self.timestamp = timestamp
        self.images = images
