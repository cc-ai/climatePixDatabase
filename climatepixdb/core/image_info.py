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
    UNKNOWN_CATEGORY = '__unknown__'

    def __init__(self, dictionary):
        self.category = dictionary['category'] or ImageInfo.DEFAULT_CATEGORY
        self.location = dictionary['location']
        self.firebase_path = dictionary['path']
        self.url = dictionary['url']
        self.local_path = None
