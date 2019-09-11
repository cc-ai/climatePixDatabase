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
