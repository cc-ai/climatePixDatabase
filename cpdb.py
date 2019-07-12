import argparse
from datetime import datetime
from typing import Optional

from climate_pix_database import ClimatePixDatabase


def parse_since(value):
    # type: (str) -> Optional[datetime]
    value = value.strip()
    if value.lower() == 'all':
        return None
    year, month, day = value.split('-')
    return datetime(year=int(year), month=int(month), day=int(day))


def main():
    parser = argparse.ArgumentParser(
        prog='Download images uploaded into ClimatePix Firebase database.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output:
- If images are not grouped by category, then they are directly downloaded into output folder,
  and a JSON file named "metadata.json" is added with metadata for each image.
  JSON object is a dictionary with following format:
  <image_filename.extension> : {"category": <category>, "location": <location>, "timestamp": <download timestamp>}
- If images are grouped by category, then output folder will contain one sub-folder per category found. Sub-folder
  name will be category name. Sub-folder will contain associated images files and a JSON file named "metadata.json"
  that map each image file name to all metadata except category.
  JSON object is a dictionary with following format:
  <image_filename.extension>: {"location": <location>, "timestamp": <download timestamp>}
        """
    )
    parser.add_argument('--output', '-o',
                        type=str, default='.',
                        help='Output directory where downloaded images will be stored. '
                             'Default is current working directory.')
    parser.add_argument('--since', '-t',
                        type=parse_since, required=True,
                        help='Date to retrieve images uploaded only since that day. '
                             'Either a date in format "AAAA-MM-DD", or "all" to download all uploaded images.')
    parser.add_argument('--dev', '-d',
                        action='store_true',
                        help='If specified, download images from development collection. '
                             'By default, download images from public collection.')
    parser.add_argument('--categorize', '-c',
                        action='store_true',
                        help='If specified, group images by category sub-folders into output folder. '
                             'Sub-folders names will be categories names. '
                             'By default, download all images directly into output folder.')
    parser.add_argument('--verbose', '-v', action='store_true', help='If specified, print downloading status.')

    args = parser.parse_args()

    download_info = (
            ('development ' if args.dev else '') + 'images' + (' grouped by category' if args.categorize else ''))

    print('Downloading',
          ('all %s' % download_info
           if args.since is None
           else '%s since %s' % (download_info, args.since)),
          'into folder', args.output)

    database = ClimatePixDatabase()
    uploads = database.get_dev_uploads(after=args.since) if args.dev else database.get_public_uploads(after=args.since)
    database.download_all_images(uploads, args.output, verbose=args.verbose, categorize=args.categorize)


if __name__ == '__main__':
    main()
