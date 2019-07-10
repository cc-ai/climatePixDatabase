from climate_pix_database import ClimatePixDatabase, images_by_category


def example_download_1_image():
    """ Usage example.
        ** NB **: To be able to connect to Firebase, a credentials file called `credentials.json` should be placed
        in the folder where script is executed. Please ask to project owner to get a copy of credentials file.
    """
    cpdb = ClimatePixDatabase()
    public_uploads = cpdb.get_public_uploads()
    print(len(public_uploads), 'public upload(s).')
    image_info_example = public_uploads[0].images[0]
    cpdb.download_image(image_info_example, image_info_example.firebase_path)
    print('An image was downloaded to', image_info_example.firebase_path)


def example_download_all_images():
    cpdb = ClimatePixDatabase()

    public_uploads = cpdb.get_public_uploads()
    print('Uploads:')
    for upload in public_uploads:
        print('\t%s\t%s' % (upload.upload_id, upload.timestamp))

    categories = images_by_category(public_uploads)
    print('Number of images per categories in uploads:')
    for category, images in categories.items():
        print('\t%s\t%d' % (category, len(images)))

    sorted_uploads = sorted(public_uploads, key=lambda u: (u.timestamp, u.upload_id))
    print('Uploaded sorted by timestamp:')
    for upload in sorted_uploads:
        print('\t%s\t%s' % (upload.upload_id, upload.timestamp))

    after = sorted_uploads[1].timestamp
    recent_uploads = cpdb.get_public_uploads(after=after)
    print('Recent uploads after', after)
    for upload in recent_uploads:
        print('\t%s\t%s' % (upload.upload_id, upload.timestamp))

    print('Downloading images from recent uploads.')
    nb_downloaded = cpdb.download_all_images(recent_uploads, 'public', verbose=True)
    print('Downloaded', nb_downloaded, '/', sum(len(u.images) for u in recent_uploads), 'images from recent uploads.')


def main():
    example_download_all_images()


if __name__ == '__main__':
    main()
