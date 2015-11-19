#!/usr/bin/env python2

"""
mysql> SELECT pk, arguments FROM StandardTasksConfigs WHERE execute = 'archivematicaSetTransferType_v0.0';
+--------------------------------------+------------------------+
| pk                                   | arguments              |
+--------------------------------------+------------------------+
| 353f326a-c599-4e66-8e1c-6262316e3729 | "%SIPUUID%" "TRIM"     |
| 36ad6300-5a2c-491b-867b-c202541749e8 | "%SIPUUID%" "Standard" |
| 6c261f8f-17ce-4b58-86c2-ac3bfb0d2850 | "%SIPUUID%" "Dspace"   |
| 7b455fc5-b201-4233-ba1c-e05be059b279 | "%SIPUUID%" "Maildir"  |
+--------------------------------------+------------------------+
4 rows in set (0.00 sec)
"""

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
import sys

import django
django.setup()
# dashboard
from main.models import Transfer

# archivematicaCommon
from custom_handlers import get_script_logger

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.setTransferType")
    transferUUID = sys.argv[1]
    transferType = sys.argv[2]

    Transfer.objects.filter(uuid=transferUUID).update(type=transferType)
