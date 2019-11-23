"""Provides miscellaneous utility functions."""

import os

from .settings import IMAGE_EXTS


def is_image_file(filepath: str) -> bool:
    """Checks if the given file has one of the configured image extensions."""
    return os.path.splitext(filepath)[-1].lower().replace('.', '') in IMAGE_EXTS
