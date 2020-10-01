#!/usr/bin/env python
"""Helper script for working directly with the database."""

import shutil
import sys
from argparse import ArgumentParser

from imgtag.data import DB_FILEPATH, File, FileTag, Tag, db, get_all_tags
from imgtag.logger import get_logger

logger = get_logger(__name__)

# TODO: We may just want to merge this into the main script


def main():
    parser = ArgumentParser(description='Tag and query images')
    parser.add_argument('--reset', help='Reset the database', action='store_true')
    parser.add_argument('--cleanup', help='Cleanup the database', action='store_true')
    parser.add_argument('--list-tags', help='List all tags', action='store_true')

    args = parser.parse_args()

    if args.reset:
        reset_db()
        sys.exit()

    if args.cleanup:
        cleanup_db()
        sys.exit()

    if args.list_tags:
        print(f'{"Tag".ljust(20)} # Files')
        for name, count in get_all_tags():
            print(f'{name.ljust(20)} {count}')
        sys.exit()

    parser.print_usage()


def reset_db():
    print('DANGER! Resetting database')
    yn = input('Are you sure? [y/n] ')
    if yn != 'y':
        print('Aborting')
        sys.exit()

    db_filepath_backup = f'{DB_FILEPATH}.back'
    shutil.copy(DB_FILEPATH, db_filepath_backup)
    logger.info(f'Backed up database to {db_filepath_backup}')

    db.connect()
    db.drop_tables([FileTag, File, Tag])
    logger.debug('Dropped all tables')
    db.create_tables([File, Tag, FileTag])
    logger.debug('Created all tables')


def cleanup_db():
    # TODO: remove orphaned tags
    # TODO: remove orphaned files (probably really slow)
    # TODO: other stuff
    return


if __name__ == '__main__':
    main()
