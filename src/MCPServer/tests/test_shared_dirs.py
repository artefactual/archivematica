# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import server.shared_dirs as shared_dirs


def test_generate_transfer_watched_dirs():
    EXPECTED_DIRS = [
        "watchedDirectories/activeTransfers/baggitDirectory",
        "watchedDirectories/activeTransfers/baggitZippedDirectory",
        "watchedDirectories/activeTransfers/dataverseTransfer",
        "watchedDirectories/activeTransfers/Dspace",
        "watchedDirectories/activeTransfers/maildir",
        "watchedDirectories/activeTransfers/standardTransfer",
        "watchedDirectories/activeTransfers/TRIM",
        "watchedDirectories/activeTransfers/zippedPackage",
    ]
    transfer_watched_dirs = shared_dirs.generate_transfer_watched_dirs()
    assert len(transfer_watched_dirs) == 8
    for dir_ in transfer_watched_dirs:
        assert (
            dir_ in EXPECTED_DIRS
        ), "Unexpected directory in transfer watched directories: {}".format(dir_)
