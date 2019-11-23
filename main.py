#!/usr/bin/env python

import os
import sys

from PySide2.QtWidgets import QApplication

from imgtag import MainWindow, settings
from imgtag.data import File, FileTag, Tag, db
from imgtag.logger import get_logger
from imgtag.settings import DB_FILEPATH

VER_MAJ_REQ, VER_MIN_REQ = 3, 7

logger = get_logger(__name__)


def init():
    check_version()

    # Create database if not present
    if not os.path.exists(DB_FILEPATH):
        db.connect()
        db.create_tables([File, Tag, FileTag])
        logger.debug('Created all tables')


def check_version():
    major, minor, _, _, _ = sys.version_info
    logger.info('Running Python {}.{}'.format(major, minor))
    if major < VER_MAJ_REQ or minor < VER_MIN_REQ:
        logger.warning('Required: Python {}.{}+'.format(VER_MAJ_REQ, VER_MIN_REQ))
        sys.exit()


if __name__ == '__main__':
    init()

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()

    sys.exit(app.exec_())
