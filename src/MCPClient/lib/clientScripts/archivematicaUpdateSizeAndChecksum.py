#!/usr/bin/env python2

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import os
import re
import sys
import uuid

# fileOperations requires Django to be set up
import django
django.setup()

from main.models import File, FileFormatVersion

from custom_handlers import get_script_logger
from databaseFunctions import insertIntoDerivations
from fileOperations import updateSizeAndChecksum

import metsrw

import parse_mets_to_db

logger = get_script_logger('archivematica.mcp.client.updateSizeAndChecksum')


def find_mets_file(unit_path):
    """
    Return the location of the original METS in a Archivematica AIP transfer.
    """
    p = re.compile(r'^METS\..*\.xml$', re.IGNORECASE)
    src = os.path.join(unit_path, 'metadata')
    for item in os.listdir(src):
        m = p.match(item)
        if m:
            return os.path.join(src, m.group())


def get_file_info_from_mets(shared_path, file_):
    """Get file size, checksum & type, and derivation for this file from METS.

    Given an instance of a File, return a dict with keys: file_size,
    checksum and checksum_type, as they are described in the original METS
    document of the transfer. The dict will be empty or missing keys on error.
    """
    transfer = file_.transfer
    transfer_location = transfer.currentlocation.replace(
        '%sharedPath%', shared_path, 1)
    mets_file = find_mets_file(transfer_location)
    if not mets_file:
        logger.info('Archivematica AIP: METS file not found in %s.',
                    transfer_location)
        return {}
    logger.info('Archivematica AIP: reading METS file %s.', mets_file)
    mets = metsrw.METSDocument.fromfile(mets_file)
    fsentry = mets.get_file(file_uuid=file_.uuid)
    if not fsentry:
        logger.error('Archivematica AIP: FSEntry with UUID %s not found', file_.uuid)
        return {}

    # Get the UUID of a preservation derivative, if one exists
    try:
        premis_object = fsentry.get_premis_objects()[0]
    except IndexError:
        logger.error('Archivematica AIP: PREMIS:OBJECT could not be found')
        return {}
    premis_object = fsentry.get_premis_objects()[0]
    related_object_uuid = None
    for relationship in premis_object.relationship:
        if relationship.sub_type != 'is source of':
            continue
        event = fsentry.get_premis_event(
            relationship.related_event_identifier_value)
        if (not event) or (event.type != 'normalization'):
            continue
        rel_obj_uuid = relationship.related_object_identifier_value
        related_object_fsentry = mets.get_file(file_uuid=rel_obj_uuid)
        if getattr(related_object_fsentry, 'use', None) != 'preservation':
            continue
        related_object_uuid = rel_obj_uuid
        break

    premis_object_doc = [
        ss.contents.document for ss in fsentry.amdsecs[0].subsections
        if ss.contents.mdtype == metsrw.FSEntry.PREMIS_OBJECT][0]

    ret = {
        'file_size': premis_object.size,
        'checksum': premis_object.message_digest,
        'checksum_type': premis_object.message_digest_algorithm,
        'derivation': related_object_uuid,
        'format_version': parse_mets_to_db.parse_format_version(
            premis_object_doc),
    }
    logger.info('Archivematica AIP: %s', ret)
    return ret


def main(shared_path, file_uuid, file_path, date, event_uuid):
    try:
        file_ = File.objects.get(uuid=file_uuid)
    except File.DoesNotExist:
        logger.exception('File with UUID %s cannot be found.', file_uuid)
        return 1

    # See if it's a Transfer and in particular a Archivematica AIP transfer.
    # If so, try to extract the size, checksum and checksum function from the
    # original METS document.
    kw = {}
    if (file_.transfer and
            (not file_.sip) and
            file_.transfer.type == 'Archivematica AIP'):
        info = get_file_info_from_mets(shared_path, file_)
        kw.update(fileSize=info['file_size'],
                  checksum=info['checksum'],
                  checksumType=info['checksum_type'],
                  add_event=False)
        if info.get('derivation'):
            insertIntoDerivations(
                sourceFileUUID=file_uuid,
                derivedFileUUID=info['derivation'],
            )
        if info.get('format_version'):
            FileFormatVersion.objects.create(
                file_uuid_id=file_uuid,
                format_version=info['format_version']
            )

    updateSizeAndChecksum(file_uuid, file_path, date, event_uuid, **kw)

    return 0


if __name__ == '__main__':
    logger.info('Invoked as %s.', ' '.join(sys.argv))

    parser = argparse.ArgumentParser()
    parser.add_argument('sharedPath')
    parser.add_argument('-i', '--fileUUID', type=lambda x: str(uuid.UUID(x)), dest='file_uuid')
    parser.add_argument('-p', '--filePath', action='store', dest='file_path', default='')
    parser.add_argument('-d', '--date', action='store', dest='date', default='')
    parser.add_argument('-u', '--eventIdentifierUUID', type=lambda x: str(uuid.UUID(x)), dest='event_uuid')
    args = parser.parse_args()

    sys.exit(main(
        args.sharedPath,
        args.file_uuid,
        args.file_path,
        args.date,
        args.event_uuid))
