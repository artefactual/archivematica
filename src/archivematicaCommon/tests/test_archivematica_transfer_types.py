# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import pytest

import archivematica_transfer_types as amtypes

EXPECTED_DIRS = [
    ("standard", "standardTransfer"),
    ("zipped package", "zippedPackage"),
    ("unzipped bag", "baggitDirectory"),
    ("zipped bag", "baggitZippedDirectory"),
    ("dspace", "Dspace"),
    ("maildir", "maildir"),
    ("TRIM", "TRIM"),
    ("dataverse", "dataverseTransfer"),
]


def test_retrieve_watched_dirs():
    dirs = amtypes.retrieve_watched_dirs()
    assert len(list(dirs)) == len(EXPECTED_DIRS)
    for dir_ in dirs:
        assert (
            dir_ in EXPECTED_DIRS
        ), "Unexpected watched directory in transfer watched directories: {}".format(
            dir_
        )


def test_watched_directory():
    for transfer_type, watched_directory_name in EXPECTED_DIRS:
        assert (
            amtypes.retrieve_watched_directory(transfer_type) == watched_directory_name
        )
    amtypes.retrieve_watched_directory(
        "unknown transfer type"
    ) == amtypes.WATCHED_DIRECTORY_STANDARD
    with pytest.raises(KeyError):
        amtypes.retrieve_watched_directory("unknown transfer type with exception", True)
