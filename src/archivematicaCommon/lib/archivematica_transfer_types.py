# -*- coding: utf-8 -*-

"""
Archivematica transfer types.

Module collects together information related to the validation and initiation
of Archivematica transfers.

Where feasible this module can be imported to be used in different classes
calling it in Python. Places where this isn't feasible are as follows:

 - Listing of transfer types plus file-type transfer control:
     * src/dashboard/frontend/app/browse/browse.controller.js

 - Enable the transfer type to be selected in the browser drop-down:
     * src/dashboard/frontend/app/front_page/transfer_browser.html

 - Disable the visibility for a transfer name in the browser:
     * src/dashboard/frontend/app/header/header.controller.js

 - A dummy name is generated for a transfer in the UI:
     * src/dashboard/frontend/app/services/transfer_browser_transfer.service.js

 - References to watched directories also exist in Workflow.json and MCP
   server's shared_dirs.py
     * src/MCPServer/lib/assets/workflow.json

Transfers have different characteristics such as whether a transfer can be
selected by directory, or by file, e.g. standard transfer vs. zipped bags.

This module should try and capture these characteristics where possible.
"""
from __future__ import absolute_import, unicode_literals

import collections

TRANSFER_TYPE_STANDARD = "standard"
TRANSFER_TYPE_ZIPPED_PACKAGE = "zipped package"
TRANSFER_TYPE_UNZIPPED_BAG = "unzipped bag"
TRANSFER_TYPE_ZIPPED_BAG = "zipped bag"
TRANSFER_TYPE_DSPACE = "dspace"
TRANSFER_TYPE_MAILDIR = "maildir"
TRANSFER_TYPE_TRIM = "TRIM"
TRANSFER_TYPE_DATAVERSE = "dataverse"

TRANSFER_TYPE_DISK_IMAGE = "disk image"

WATCHED_DIRECTORY_STANDARD = "standardTransfer"
WATCHED_DIRECTORY_ZIPPED_PACKAGE = "zippedPackage"
WATCHED_DIRECTORY_UNZIPPED_BAG = "baggitDirectory"
WATCHED_DIRECTORY_ZIPPED_BAG = "baggitZippedDirectory"
WATCHED_DIRECTORY_DSPACE = "Dspace"
WATCHED_DIRECTORY_MAILDIR = "maildir"
WATCHED_DIRECTORY_TRIM = "TRIM"
WATCHED_DIRECTORY_DATAVERSE = "dataverseTransfer"

ARCHIVE_ZIP = ".zip"
ARCHIVE_TGZ = ".tgz"
ARCHIVE_TAR_GZ = ".tar.gz"

ARCHIVE_TYPES = (ARCHIVE_ZIP, ARCHIVE_TGZ, ARCHIVE_TAR_GZ)
ZIP_TYPE_TRANSFERS = (
    TRANSFER_TYPE_ZIPPED_PACKAGE,
    TRANSFER_TYPE_ZIPPED_BAG,
    TRANSFER_TYPE_DSPACE,
)

# Manual approval jobs associated with a transfer.
APPROVE_STANDARD = "Approve standard transfer"
APPROVE_ZIPPED = "Approve zipped transfer"
APPROVE_DSPACE = "Approve DSpace transfer"
APPROVE_UNZIPPED_BAG = "Approve bagit transfer"
APPROVE_ZIPPED_BAG = "Approve zipped bagit transfer"

APPROVE_TRANSFER_JOB_NAMES = (
    APPROVE_STANDARD,
    APPROVE_ZIPPED,
    APPROVE_DSPACE,
    APPROVE_UNZIPPED_BAG,
    APPROVE_ZIPPED_BAG,
)

# Archivematica transfer profiles that describe a transfer's properties.
TransferProfile = collections.namedtuple(
    "TransferProfile", "transfer_type watched_directory"
)
ARCHIVEMATICA_TRANSFER_TYPES = {
    TRANSFER_TYPE_STANDARD: TransferProfile(
        TRANSFER_TYPE_STANDARD, WATCHED_DIRECTORY_STANDARD
    ),
    TRANSFER_TYPE_ZIPPED_PACKAGE: TransferProfile(
        TRANSFER_TYPE_ZIPPED_PACKAGE, WATCHED_DIRECTORY_ZIPPED_PACKAGE
    ),
    TRANSFER_TYPE_UNZIPPED_BAG: TransferProfile(
        TRANSFER_TYPE_UNZIPPED_BAG, WATCHED_DIRECTORY_UNZIPPED_BAG
    ),
    TRANSFER_TYPE_ZIPPED_BAG: TransferProfile(
        TRANSFER_TYPE_ZIPPED_BAG, WATCHED_DIRECTORY_ZIPPED_BAG
    ),
    TRANSFER_TYPE_DSPACE: TransferProfile(
        TRANSFER_TYPE_DSPACE, WATCHED_DIRECTORY_DSPACE
    ),
    TRANSFER_TYPE_MAILDIR: TransferProfile(
        TRANSFER_TYPE_MAILDIR, WATCHED_DIRECTORY_MAILDIR
    ),
    TRANSFER_TYPE_TRIM: TransferProfile(TRANSFER_TYPE_TRIM, WATCHED_DIRECTORY_TRIM),
    TRANSFER_TYPE_DATAVERSE: TransferProfile(
        TRANSFER_TYPE_DATAVERSE, WATCHED_DIRECTORY_DATAVERSE
    ),
}


def retrieve_watched_dirs():
    """Return a generator of tuples of Archivematica Transfer Types, which
    contains the transfer type, and suffix that will form part of the
    transfer's watched directory.
    """
    for type_ in ARCHIVEMATICA_TRANSFER_TYPES:
        yield ARCHIVEMATICA_TRANSFER_TYPES[
            type_
        ].transfer_type, ARCHIVEMATICA_TRANSFER_TYPES[type_].watched_directory


def retrieve_watched_directory(transfer_type, return_key_error=False):
    if transfer_type not in ARCHIVEMATICA_TRANSFER_TYPES.keys():
        if not return_key_error:
            return ARCHIVEMATICA_TRANSFER_TYPES[
                TRANSFER_TYPE_STANDARD
            ].watched_directory
        raise KeyError("Returning KeyError for legacy compatibility")
    return ARCHIVEMATICA_TRANSFER_TYPES[transfer_type].watched_directory
