import argparse
from climatepixdb.download import parse_since
from climatepixdb.database import ClimatePixDatabase

def main():
    parser = argparse.ArgumentParser(
        prog='Helper script to delete images on ClimatePix database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
This script cant be used to remotely delete images in ClimatePix database
(type --help to display documentation).

A credentials file named "credentials.json" must be present in the working directory
to help the script connect to database.

If you don't have this file, please contact a CCAI project member.

If you have this file, either place it where you want to run the script,
or run the script where the file is stored."""
    )
    parser.add_argument('--dev', '-d',
                        action='store_true',
                        help='If specified, delete images from development collection. '
                             'By default, download images from public collection.')
    parser.add_argument('--before', '-b', type=parse_since,
                        help='Delete images before this date. Format "AAAA-MM-DD". '
                             'NB: You must provide either before of after, but not both.')
    parser.add_argument('--after', '-a', type=parse_since,
                        help='Delete images after this date. Format "AAAA-MM-DD". '
                             'NB: You must provide either before of after, but not both.')
    parser.add_argument('--force', '-f', action='store_true',
                        help='If specified, force deletions without asking confirmation.')
    # parser.add_argument('--verbose', '-v', action='store_true',
    #                     help='If specified, print downloading status.')
    args = parser.parse_args()
    before = args.before
    after = args.after
    dev = args.dev
    if before is None and after is None:
        raise ValueError('You must specify either --before of --after.')
    if before is not None and after is not  None:
        raise ValueError('You must specify --before of --after, not both.')
    print('Deleting %simages %s %s' % (
        'development ' if dev else '',
        'before' if before is not None else 'after',
        before if before is not None else after
    ))
    database = ClimatePixDatabase()
    uploads = (database.get_dev_uploads(before=before, after=after)
               if dev else database.get_public_uploads(before=before, after=after))
    database.delete_all_images(uploads=uploads, force=args.force, verbose=True)


if __name__ == '__main__':
    main()
