"""Defines all data-layer models and query logic."""

import logging
import os
from typing import List, Tuple

import peewee as pw
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

from .logger import get_logger
from .settings import DB_FILEPATH, LOG_LEVEL, ROOT_DIR

logger = get_logger(__name__)

# peewee logging
logger_pw = get_logger('peewee')
logger_pw.addHandler(logging.StreamHandler())
logger_pw.setLevel(LOG_LEVEL)

db = pw.SqliteDatabase(DB_FILEPATH)

# beaker caching via decorator API
cache = CacheManager(**parse_cache_config_options({
    # 'cache.type': 'file',
    'cache.type': 'memory',
    'cache.data_dir': '.beaker_cache/data',
    'cache.lock_dir': '.beaker_cache/lock',
}))

# -- Models


class BaseModel(pw.Model):
    class Meta:
        database = db


class File(BaseModel):
    name = pw.CharField(unique=True)
    # Cached path for faster loads
    path = pw.CharField(null=True)


class Tag(BaseModel):
    name = pw.CharField(unique=True)


class FileTag(BaseModel):
    fil = pw.ForeignKeyField(File)
    tag = pw.ForeignKeyField(Tag)


# -- File


@cache.cache('get_file_path', duration=3600)
def get_file_path(filename: str) -> str:
    fil, _created = File.get_or_create(name=filename)
    if fil.path and os.path.exists(fil.path):
        return fil.path
    path = _resolve_filepath(ROOT_DIR, filename)
    if path:
        set_file_path(filename, path)
        return path
    raise ValueError(f'Unable to resolve path for {filename}')


def set_file_path(filename: str, path: str):
    cache.invalidate(get_file_path, 'get_file_path', filename)

    fil, _created = File.get_or_create(name=filename)
    fil.path = path
    return fil.save()


def get_file_paths(root_path: str, filenames: List[str]) -> List[str]:
    """Returns the full paths for the given filenames.

    If the path is not cached in the database or is invalid, manually resolves the path and updates
    the database.
    """
    paths = []
    for filename, filepath in ((filename, get_file_path(filename)) for filename in filenames):
        # NOTE: Need to check if path is valid in case we get an outdated cached path
        if not filepath or not os.path.exists(filepath):
            filepath = _resolve_filepath(root_path, filename)
            if filepath:
                set_file_path(filename, filepath)
                logger.debug(f'Saved filepath for {filename}')
        paths.append(filepath)
    return paths


def _resolve_filepath(root_path: str, filename: str) -> str:
    """Returns the path of the _first_ matching filename.

    If the file is not found, returns an empty string.
    """
    # TODO: Is there a more efficient way of doing this? Maybe with glob?
    for dirpath, _, filenames in os.walk(root_path):
        for fname in filenames:
            if fname == filename:
                filepath = os.path.join(dirpath, fname)
                logger.debug(f'Found {filename} at {filepath}')
                return filepath
    logger.info(f'Filename {filename} not found - removing from database')
    delete_file(filename)
    return ''


def delete_file(filename: str) -> int:
    """Deletes the given file, along with all tag associations, and returns the number of rows
    deleted.
    """
    cache.invalidate(get_file_tags, 'get_file_tags', filename)

    return File.delete().where(File.name == filename).execute()


# -- Tag


def get_all_tags() -> List[Tuple[str, int]]:
    query = (Tag.select(Tag.name,
                        pw.fn.COUNT(FileTag.id).alias('file_count')).join(
                            FileTag,
                            pw.JOIN.LEFT_OUTER).group_by(Tag.name).order_by(Tag.name.asc()))
    return [(tag.name, tag.file_count) for tag in query]


# -- FileTag


@cache.cache('get_file_tags', duration=3600)
def get_file_tags(filename: str) -> List[Tuple[str, int]]:
    tags = (Tag.select(Tag.name).join(FileTag).join(File).where(File.name == filename).order_by(
        Tag.name.asc()))
    logger.info(f'Got {len(tags)} tag(s) for {filename}')
    # TODO: Try to avoid separate DB hit per tag to count files
    return [(tag.name, count_files_with_tag(tag.name)) for tag in tags]


def get_files_with_tag(tagname: str) -> List[str]:
    tag = Tag.get_or_none(name=tagname)
    if not tag:
        return []
    return sorted(
        [fil.name for fil in File.select(File.name).join(FileTag).where(FileTag.tag == tag)])


def get_files_with_tags(tagnames: List[str], excluded_tagnames: List[str]=[]) -> List[str]:
    results = set(get_files_with_tag(tagnames[0]))
    for tagname in tagnames[1:]:
        filenames = set(get_files_with_tag(tagname))
        results = results.intersection(filenames)
    # Filter out files with at least one excluded tag
    for tagname in excluded_tagnames:
        filenames = set(get_files_with_tag(tagname))
        results = results.difference(filenames)
    return sorted(list(results))


def add_file_tag(filename: str, tagname: str):
    cache.invalidate(get_file_tags, 'get_file_tags', filename)
    cache.invalidate(count_files_with_tag, 'count_files_with_tag', tagname)

    fil, _ = File.get_or_create(name=filename)
    tag, _ = Tag.get_or_create(name=tagname)
    _, filetag_created = FileTag.get_or_create(fil=fil, tag=tag)
    if filetag_created:
        logger.info(f'Added tag {tagname} to {filename}')
    else:
        logger.info(f'{filename} already has tag {tagname}; nothing to do')


def remove_file_tag(filename: str, tagname: str) -> int:
    # NOTE: We don't bother invalidating cached tag counts for other images
    #       since it doesn't seem to justify the extra computational work
    cache.invalidate(get_file_tags, 'get_file_tags', filename)
    cache.invalidate(count_files_with_tag, 'count_files_with_tag', tagname)

    fil = File.get_or_none(name=filename)
    tag = Tag.get_or_none(name=tagname)
    n_rows = FileTag.delete().where((FileTag.fil == fil) & (FileTag.tag == tag)).execute()
    logger.info(f'Removed tag {tagname} from {filename} ({n_rows} row(s) modified)')
    return n_rows


# -- Misc


@cache.cache('count_files_with_tag', duration=3600)
def count_files_with_tag(tagname: str) -> int:
    tag = Tag.get_or_none(name=tagname)
    return FileTag.select().where(FileTag.tag == tag).count() if tag else 0
