"""Provides all logging-related functions."""

import logging

from .settings import LOG_LEVEL


def get_logger(name) -> logging.Logger:
    """Returns a configured named logger."""
    logger = logging.getLogger(name)

    logger.setLevel(LOG_LEVEL)

    logger.addHandler(logging.NullHandler())

    formatter = logging.Formatter('%(levelname)s | %(module)s | %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
