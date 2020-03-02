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

Transfers have different characteristics such as whether a transfer can be
selected by directory, or by file, e.g. standard transfer vs. zipped bags.

This module should try and capture these characteristics where possible.
"""
from __future__ import absolute_import, unicode_literals

import collections

TRANSFER_STANDARD = "standard"
TRANSFER_ZIPFILE = "zipfile"
TRANSFER_UNZIPPED_BAG = "unzipped bag"
TRANSFER_ZIPPED_BAG = "zipped bag"
TRANSFER_DSPACE = "dspace"
TRANSFER_MAILDIR = "maildir"
TRANSFER_TRIM = "TRIM"
TRANSFER_DATAVERSE = "dataverse"

TRANSFER_DISk_IMAGE = "disk image"

WATCHED_STANDARD = "standardTransfer"
WATCHED_ZIPFILE = "zippedDirectory"
WATCHED_UNZIPPED_BAG = "baggitDirectory"
WATCHED_ZIPPED_BAG = "baggitZippedDirectory"
WATCHED_DSPACE = "Dspace"
WATCHED_MAILDIR = "maildir"
WATCHED_TRIM = "TRIM"
WATCHED_DATAVERSE = "dataverseTransfer"

# TRANSFER_DISK_IMAGE is treated differently by src/MCPServer/lib/server/packages.py.
TRANSFER_TYPES = (
    TRANSFER_STANDARD,
    TRANSFER_ZIPFILE,
    TRANSFER_UNZIPPED_BAG,
    TRANSFER_ZIPPED_BAG,
    TRANSFER_DSPACE,
    TRANSFER_MAILDIR,
    TRANSFER_TRIM,
    TRANSFER_DATAVERSE,
)

ARCHIVE_ZIP = ".zip"
ARCHIVE_TGZ = ".tgz"
ARCHIVE_TAR_GZ = ".tar.gz"

ARCHIVE_TYPES = (ARCHIVE_ZIP, ARCHIVE_TGZ, ARCHIVE_TAR_GZ)
ZIP_TYPE_TRANSFERS = (TRANSFER_ZIPFILE, TRANSFER_ZIPPED_BAG, TRANSFER_DSPACE)

# Manual approval jobs associated with a transfer.
APPROVE_STANDARD = "Approve standard transfer"
APPROVE_ZIPPED = "Approve zipped transfer"
APPROVE_DSPACE = "Approve DSpace transfer"
APPROVE_UNZIPPED_BAG = "Approve bagit transfer"
APPROVE_ZIPPED_BAG = "Approve zipped bagit transfer"

# Archivematica transfer profiles that describe a transfer's properties.
TransferProfile = collections.namedtuple(
    "TransferProfile", "transfer_type watched_directory api_caller"
)
ARCHIVEMATICA_TRANSFER_TYPES = {
    TRANSFER_STANDARD: TransferProfile(
        TRANSFER_STANDARD, WATCHED_STANDARD, TRANSFER_STANDARD
    ),
    TRANSFER_ZIPFILE: TransferProfile(
        TRANSFER_ZIPFILE, WATCHED_ZIPFILE, TRANSFER_ZIPFILE
    ),
    TRANSFER_UNZIPPED_BAG: TransferProfile(
        TRANSFER_UNZIPPED_BAG, WATCHED_UNZIPPED_BAG, TRANSFER_UNZIPPED_BAG
    ),
    TRANSFER_ZIPPED_BAG: TransferProfile(
        TRANSFER_ZIPPED_BAG, WATCHED_ZIPPED_BAG, TRANSFER_ZIPPED_BAG
    ),
    TRANSFER_DSPACE: TransferProfile(TRANSFER_DSPACE, WATCHED_DSPACE, TRANSFER_DSPACE),
    TRANSFER_MAILDIR: TransferProfile(
        TRANSFER_MAILDIR, WATCHED_MAILDIR, TRANSFER_MAILDIR
    ),
    TRANSFER_TRIM: TransferProfile(TRANSFER_TRIM, WATCHED_TRIM, TRANSFER_TRIM),
    TRANSFER_DATAVERSE: TransferProfile(
        TRANSFER_DATAVERSE, WATCHED_DATAVERSE, TRANSFER_DATAVERSE
    ),
}


def retrieve_watched_dirs():
    for type_ in ARCHIVEMATICA_TRANSFER_TYPES:
        yield ARCHIVEMATICA_TRANSFER_TYPES[
            type_
        ].transfer_type, ARCHIVEMATICA_TRANSFER_TYPES[type_].watched_directory


def retrieve_watched_directory(transfer_type, return_key_error=False):
    if transfer_type not in TRANSFER_TYPES:
        if not return_key_error:
            return ARCHIVEMATICA_TRANSFER_TYPES[TRANSFER_STANDARD].watched_directory
        raise KeyError("Returning KeyError for legacy compatibility")
    return ARCHIVEMATICA_TRANSFER_TYPES[transfer_type].watched_directory
