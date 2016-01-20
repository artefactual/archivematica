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

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>

from __future__ import print_function
import os
import re
import sys
import shutil

import django
django.setup()
from main.models import Transfer

from verifyBAG import verify_bag

# archivematicaCommon
import archivematicaFunctions
from archivematicaFunctions import REQUIRED_DIRECTORIES, OPTIONAL_FILES
from custom_handlers import get_script_logger

logger = get_script_logger('archivematica.mcp.client.restructureForCompliance')


def _move_file(src, dst, exit_on_error=True):
    logger.info('Moving %s to %s', src, dst)
    try:
        shutil.move(src, dst)
    except IOError:
        print('Could not move', src)
        if exit_on_error:
            raise


def restructure_transfer(unit_path):
    # Create required directories
    archivematicaFunctions.create_structured_directory(unit_path, printing=True)

    # Move everything else to the objects directory
    for item in os.listdir(unit_path):
        src = os.path.join(unit_path, item)
        dst = os.path.join(unit_path, "objects", '.')
        if os.path.isdir(src) and item not in REQUIRED_DIRECTORIES:
            _move_file(src, dst)
        elif os.path.isfile(src) and item not in OPTIONAL_FILES:
            _move_file(src, dst)


def restructure_transfer_aip(unit_path):
    """
    Restructure a transfer that comes from re-ingesting an Archivematica AIP.
    """
    old_bag = os.path.join(unit_path, 'old_bag', '')
    os.makedirs(old_bag)

    # Move everything to old_bag
    for item in os.listdir(unit_path):
        if item == 'old_bag':
            continue
        src = os.path.join(unit_path, item)
        _move_file(src, old_bag)

    # Create required directories
    # - "/logs" and "/logs/fileMeta"
    # - "/metadata" and "/metadata/submissionDocumentation"
    # - "/objects"
    archivematicaFunctions.create_structured_directory(unit_path, printing=True)

    # Move /old_bag/data/METS.<UUID>.xml => /metadata/METS.<UUID>.xml
    p = re.compile(r'^METS\..*\.xml$', re.IGNORECASE)
    src = os.path.join(old_bag, 'data')
    for item in os.listdir(src):
        m = p.match(item)
        if m:
            break # Stop trying after the first match
    src = os.path.join(src, m.group())
    dst = os.path.join(unit_path, 'metadata')
    _move_file(src, dst)

    # Move /old_bag/data/objects/submissionDocumentation/* => /metadata/submissionDocumentation/
    src = os.path.join(old_bag, 'data', 'objects', 'submissionDocumentation')
    dst = os.path.join(unit_path, 'metadata', 'submissionDocumentation')
    for item in os.listdir(src):
        item_path = os.path.join(src, item)
        _move_file(item_path, dst)
    shutil.rmtree(src)

    # Move /old_bag/data/objects/* => /objects/
    src = os.path.join(old_bag, 'data', 'objects')
    dst = os.path.join(unit_path, 'objects')
    for item in os.listdir(src):
        item_path = os.path.join(src, item)
        _move_file(item_path, dst)

    # Get rid of old_bag
    shutil.rmtree(old_bag)

if __name__ == '__main__':
    sip_path = sys.argv[1]
    sip_uuid = sys.argv[2]

    transfer = Transfer.objects.get(uuid=sip_uuid)
    logger.info('Transfer.type=%s', transfer.type)

    if transfer.type == 'Archivematica AIP':
        logger.info('Archivematica AIP detected, verifying bag...')
        exit_code = verify_bag(sip_path)
        if exit_code > 0:
            logger.info('Archivematica AIP: bag verification failed!')
            sys.exit(exit_code)
        logger.info('Restructuring transfer (Archivematica AIP re-ingest)...')
        restructure_transfer_aip(sip_path)
    else:
        logger.info('Restructuring transfer...')
        restructure_transfer(sip_path)
