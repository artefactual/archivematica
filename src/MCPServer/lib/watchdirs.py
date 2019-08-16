from __future__ import unicode_literals

import logging
import os
import scandir

from django.conf import settings
from inotify_simple import INotify, flags


logger = logging.getLogger("archivematica.mcp.server.watchdirs")


def watch_directories(watched_dirs, shutdown_event, callback):
    """Accepts a list of workflow WatchedDir objects.
    """
    base_dir = os.path.abspath(settings.WATCH_DIRECTORY)
    inotify = INotify()
    watch_flags = flags.CREATE | flags.MOVED_TO
    watches = {}  # descriptor: (path, WatchedDir)

    for watched_dir in watched_dirs:
        path = os.path.join(base_dir, watched_dir.path.lstrip("/"))
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
        events = inotify.read(timeout=1000)
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
