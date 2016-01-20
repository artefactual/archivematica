#!/usr/bin/env python2
# -*- coding: utf-8 -*-

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

from __future__ import print_function

import argparse
import os
import re
import sys
import uuid

import django
django.setup()
# dashboard
from main.models import File, Transfer
# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import addFileToTransfer
from fileOperations import addFileToSIP

import metsrw


logger = get_script_logger('archivematica.mcp.client.assignFileUUID')


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


def get_file_uuid_from_mets(sip_directory, file_path_relative_to_sip):
    """
    Look up the UUID of the file in the METS document using metsrw.
    """
    mets_file = find_mets_file(sip_directory)
    if not mets_file:
        logger.info('Archivematica AIP: METS file not found.')
        return
    logger.info('Archivematica AIP: reading METS file %s.', mets_file)
    mets = metsrw.METSDocument.fromfile(mets_file)

    file_path_relative_to_sip = file_path_relative_to_sip.replace('%transferDirectory%', '', 1)
    file_path_relative_to_sip = file_path_relative_to_sip.replace('%SIPDirectory%', '', 1)

    # Warning! This is not the fastest way to achieve this. But we will focus
    # on optimizations later.
    # TODO: is it ok to assume that the file structure is flat?
    entry = mets.get_file(path=file_path_relative_to_sip)
    if entry:
        logger.info('Archivematica AIP: file UUID of has been found in the METS document (%s).', entry.path)
        return entry.file_uuid
    logger.info('Archivematica AIP: file UUID has not been found in the METS document: %s', file_path_relative_to_sip)


def main(file_uuid=None, file_path='', date='', event_uuid=None, sip_directory='', sip_uuid=None, transfer_uuid=None, use='original', update_use=True):
    if file_uuid == "None":
        file_uuid = None
    if file_uuid:
        logger.error('File already has UUID: %s', file_uuid)
        if update_use:
            File.objects.filter(uuid=file_uuid).update(filegrpuse=use)
        return 0

    # Stop if both or neither of them are used
    if all([sip_uuid, transfer_uuid]) or not any([sip_uuid, transfer_uuid]):
        logger.error('SIP exclusive-or Transfer UUID must be defined')
        return 2

    # Transfer
    if transfer_uuid:
        file_path_relative_to_sip = file_path.replace(sip_directory, '%transferDirectory%', 1)
        transfer = Transfer.objects.get(uuid=transfer_uuid)
        if transfer.type == 'Archivematica AIP':
            file_uuid = get_file_uuid_from_mets(sip_directory, file_path_relative_to_sip)
        if not file_uuid:
            file_uuid = str(uuid.uuid4())
            logger.info('Generated UUID for this file: %s.', file_uuid)
        addFileToTransfer(file_path_relative_to_sip, file_uuid, transfer_uuid, event_uuid, date, use=use)
        return 0

    # Ingest
    if sip_uuid:
        file_uuid = str(uuid.uuid4())
        file_path_relative_to_sip = file_path.replace(sip_directory,"%SIPDirectory%", 1)
        addFileToSIP(file_path_relative_to_sip, file_uuid, sip_uuid, event_uuid, date, use=use)
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--fileUUID', type=str, dest='file_uuid')
    parser.add_argument('-p', '--filePath', action='store', dest='file_path', default='')
    parser.add_argument('-d', '--date', action='store', dest='date', default='')
    parser.add_argument('-u', '--eventIdentifierUUID', type=lambda x: str(uuid.UUID(x)), dest='event_uuid')
    parser.add_argument('-s', '--sipDirectory', action='store', dest='sip_directory', default='')
    parser.add_argument('-S', '--sipUUID', type=lambda x: str(uuid.UUID(x)), dest='sip_uuid')
    parser.add_argument('-T', '--transferUUID', type=lambda x: str(uuid.UUID(x)), dest='transfer_uuid')
    parser.add_argument('-e', '--use', action='store', dest="use", default='original')
    parser.add_argument('--disable-update-filegrpuse', action='store_false', dest='update_use', default=True)
    args = parser.parse_args()

    sys.exit(main(**vars(args)))
