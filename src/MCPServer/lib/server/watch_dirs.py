# -*- coding: utf-8 -*-
"""
Watched directory handling.

Watched directories are configured in the workflow and start a specific chain
whenever a file or directory is placed in them. They are something we probably
want to remove in future; however, currently they are used extensively in all
workflows, as many chains start the next chain by moving a transfer or SIP t
the appropriate watched directory.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import os
import scandir
import sys
import time
import warnings

from django.conf import settings
from inotify_simple import INotify, flags


IS_LINUX = sys.platform.startswith("linux")
WATCHED_BASE_DIR = os.path.abspath(settings.WATCH_DIRECTORY)

logger = logging.getLogger("archivematica.mcp.server.watchdirs")


def watch_directories_poll(
    watched_dirs, shutdown_event, callback, interval=settings.WATCH_DIRECTORY_INTERVAL
):
    """
    Watch the directories given via poll. This is a very inefficient way to handle
    watches, but it is compatible with all operating systems and filesystems.

    Accepts an iterable of workflow WatchedDir objects, a shutdown event, and a
    callback to be called when content appears in the watched dir.
    """
    # paths that have already appeared in watch directories
    known_paths = set()

    while not shutdown_event.is_set():
        current_paths = set()

        for watched_dir in watched_dirs:
            path = os.path.join(WATCHED_BASE_DIR, watched_dir.path.lstrip("/"))
            for item in scandir.scandir(path):
                if watched_dir.only_dirs and not item.is_dir():
                    continue
                elif item.path in known_paths:
                    # Re-add to current entries, so we keep tracking it
                    current_paths.add(item.path)
                    continue

                current_paths.add(item.path)
                callback(item.path, watched_dir)

        # Update what we know about from the last pass, so that it doesn't grow
        # endlessly
        known_paths = current_paths

        time.sleep(interval)


def watch_directories_inotify(
    watched_dirs, shutdown_event, callback, interval=settings.WATCH_DIRECTORY_INTERVAL
):
    """
    Watch the directories given via inotify. This is a very efficient way to handle
    watches, however it requires linux, and may not work with NFS mounts.

    Accepts an iterable of workflow WatchedDir objects, a shutdown event, and a
    callback to be called when content appears in the watched dir.
    """
    if not IS_LINUX:
        warnings.warn(
            "inotify may not work as a watched directory method on non-linux systems.",
            RuntimeWarning,
        )

    inotify = INotify()
    watch_flags = flags.CREATE | flags.MOVED_TO
    watches = {}  # descriptor: (path, WatchedDir)

    for watched_dir in watched_dirs:
        path = os.path.join(WATCHED_BASE_DIR, watched_dir.path.lstrip("/"))
        if not os.path.isdir(path):
            raise OSError('The path "{}" is not a directory.'.format(path))

        descriptor = inotify.add_watch(path, watch_flags)
        watches[descriptor] = (path, watched_dir)

        # If the directory already has something in it, trigger callbacks
        for item in scandir.scandir(path):
            if watched_dir.only_dirs and not item.is_dir():
                continue
            logger.debug(
                "Found existing data in watched dir %s: %s", watched_dir.path, item.name
            )

            callback(item.path, watched_dir)

    while not shutdown_event.is_set():
        # timeout is in milliseconds
        events = inotify.read(timeout=interval * 1000)
        for event in events:
            path, watched_dir = watches[event.wd]
            logger.debug(
                "Watched dir %s detected activity: %s", watched_dir.path, event.name
            )

            # bitwise check the mask for dirs, if dirs_only is set
            if watched_dir.only_dirs and (flags.ISDIR & event.mask == 0):
                continue

            callback(os.path.join(path, event.name), watched_dir)

    for watch_descriptor in watches.keys():
        inotify.rm_watch(watch_descriptor)

    inotify.close()


def watch_directories(*args, **kwargs):
    method = settings.WATCH_DIRECTORY_METHOD or "poll"

    logger.debug("Starting directory watch (using %s).", method)

    if method == "inotify":
        watch_directories_inotify(*args, **kwargs)
    elif method == "poll":
        watch_directories_poll(*args, **kwargs)
    else:
        raise RuntimeError("Unexpected watch method {}".format(method))
