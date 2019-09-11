import argparse

from climatepixdb.core.database import ClimatePixDatabase
from climatepixdb.download import parse_since


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
    parser.add_argument('--invalid', '-i', action='store_true',
                        help='Delete only invalid collection entries not associated to any image. '
                             'NB: arguments "before", "after" and "invalid" are mutually exclusive.')
    parser.add_argument('--before', '-b', type=parse_since,
                        help='Delete images before this date. Format "AAAA-MM-DD". '
                             'NB: arguments "before", "after" and "invalid" are mutually exclusive.')
    parser.add_argument('--after', '-a', type=parse_since,
                        help='Delete images after this date. Format "AAAA-MM-DD". '
                             'NB: arguments "before", "after" and "invalid" are mutually exclusive.')
    parser.add_argument('--force', '-f', action='store_true',
                        help='If specified, force deletions without asking confirmation. '
                             'Used with --before or --after only.')
    # parser.add_argument('--verbose', '-v', action='store_true',
    #                     help='If specified, print downloading status.')
    args = parser.parse_args()
    dev = args.dev
    before = args.before
    after = args.after
    invalid = args.invalid
    nb_del_args = (before is not None) + (after is not None) + invalid
    if nb_del_args != 1:
        raise ValueError('You must specify exactly one flag between '
                         '--before, --after and --invalid.')

    print('Deleting ', end='')
    if invalid:
        print('invalid documents', end='')
        if dev:
            print(' from development collection', end='')
    else:
        if dev:
            print('development ', end='')
        print('images', 'before %s' % before if before else 'after %s' % after, end='')
    print('.')

    database = ClimatePixDatabase()
    if invalid:
        uploads = (database.get_dev_uploads() if dev else database.get_public_uploads())
        database.delete_invalid_documents(uploads)
    else:
        uploads = (database.get_dev_uploads(before=before, after=after)
                   if dev else database.get_public_uploads(before=before, after=after))
        database.delete_uploads(uploads=uploads, force=args.force, verbose=True)


if __name__ == '__main__':
    main()
