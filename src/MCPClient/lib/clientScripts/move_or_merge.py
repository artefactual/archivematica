#!/usr/bin/env python2
# -*- encoding: utf-8

import errno
import filecmp
import os
import shutil

import scandir

from custom_handlers import get_script_logger

logger = get_script_logger("archivematica.mcp.client.move_or_merge")


def mkdir_p(path):
    """Create a directory if it doesn't already exist."""
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == errno.EEXIST:
            pass
        else:
            raise


def _move_file(src, dst):
    """
    Move an individual file from ``src`` to ``dst``.
    """
    # Ensure the destination directory exists
    mkdir_p(os.path.dirname(dst))

    # If the file already exists at the destination, check if it's the same.
    # If so, we can clean up the original file and we're done.  If not, we're
    # at risk of losing data, so error out.
    if os.path.isfile(dst):
        if filecmp.cmp(src, dst, shallow=False):
            os.unlink(src)
        else:
            raise RuntimeError(
                "Tried to move src=%s to dst=%s, but dst exists and is different"
                % (src, dst)
            )
    else:
        shutil.move(src, dst)


def move_or_merge(src, dst):
    """
    Move a file/directory to a new location, or merge two directories.

    If ``dst`` doesn't exist, it's a simple move: ``src`` is moved to the same
    path as ``dst``.

    If ``dst`` does exist and is a directory, the two directories are merged by
    moving the contents of ``src`` into ``dst``.
    """
    logger.info("Testing for the existence of src: %s", src)
    logger.info("Moving or merging to dst: %s", dst)
    if os.path.isfile(src):
        logger.debug("src: %s is a file", src)
        _move_file(src, dst)
    elif os.path.isdir(src):
        # This loop walks the tree looking for files.  For every file in ``src``,
        # it finds the path relative to the top of ``src``, then moves it
        # to the corresponding path in ``dst``. If the top-level ``dst``
        # directory doesn't already exist, we guarantee its creation even if
        # ``src`` lower-levels are empty.
        logger.debug("src: %s is a directory", src)
        if not os.path.exists(dst):
            logger.info("Creating top-level dst folder: %s, moving src as-a-whole", dst)
            shutil.move(src, dst)
        else:
            logger.info("dst: %s exists, copying src files one-by-one", dst)
            for root, _, filenames in scandir.walk(src):
                rel_root = os.path.relpath(root, start=src)
                for f in filenames:
                    _move_file(
                        src=os.path.join(src, rel_root, f),
                        dst=os.path.join(dst, rel_root, f),
                    )
            shutil.rmtree(src)


def main(src, dst):
    """
    Moves a file/directory to a new location, or moves two directories.

    If dst doesn't exist, acts like mv: src is moved to the same path as dst.
    If dst does exist and is a directory, the two directories are merged by
    moving src's contents into dst.
    """
    move_or_merge(src, dst)
    return 0


def call(jobs):
    for job in jobs:
        with job.JobContext(logger=logger):
            src = job.args[1]
            dst = job.args[2]
            try:
                job.set_status(main(src, dst))
            except Exception as e:
                job.print_error(repr(e))
                job.set_status(1)
