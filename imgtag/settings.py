"""Stores all global application settings."""

import configparser
import logging
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..'))

CONFIG_FILENAME = 'config.ini'
CONFIG_FILEPATH = os.path.join(PROJECT_ROOT, CONFIG_FILENAME)

config = configparser.ConfigParser()
config.read(CONFIG_FILEPATH)

# Database
DB_FILEPATH = os.path.join(PROJECT_ROOT, config['database']['filename'])

# Filesystem
ROOT_DIR = config['filesystem']['root_dir']
IMAGE_EXTS = config['filesystem']['image_extensions'].split(',')

# Logging
LOG_LEVEL = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}[config['logging']['level']]
