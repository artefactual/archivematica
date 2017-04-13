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
import shutil
import sys

import django
django.setup()
# dashboard
from main.models import SIP

# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import rename

def updateDB(dst, sip_uuid):
    SIP.objects.filter(uuid=sip_uuid).update(currentpath=dst)

def moveSIP(src, dst, sipUUID, sharedDirectoryPath):
    # Prepare paths
    if src.endswith("/"):
        src = src[:-1]

    dest = dst.replace(sharedDirectoryPath, "%sharedPath%", 1)
    if dest.endswith("/"):
        dest = os.path.join(dest, os.path.basename(src))
    if dest.endswith("/."):
        dest = os.path.join(dest[:-1], os.path.basename(src))
    updateDB(dest + "/", sipUUID)

    # If destination already exists, delete it with warning
    dest_path = os.path.join(dst, os.path.basename(src))
    if os.path.exists(dest_path):
        print(dest_path, 'exists, deleting', file=sys.stderr)
        shutil.rmtree(dest_path)

    rename(src, dst)

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.moveSIP")

    src = sys.argv[1]
    dst = sys.argv[2]
    sipUUID = sys.argv[3]
    sharedDirectoryPath = sys.argv[4]
    moveSIP(src, dst, sipUUID, sharedDirectoryPath)
