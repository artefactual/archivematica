#!/usr/bin/python -OO

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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage MCPrpcCLI
# @author Joseph Perry <joseph@artefactual.com>

import gearman
admin = gearman.admin_client.GearmanAdminClient(host_list=["127.0.0.1"])
#print admin.get_status()
#print admin.get_workers()

for client in admin.get_workers():
    if client["client_id"] != "-": #exclude server task connections
        print client["client_id"], client["ip"]

for stat in admin.get_status():
    if stat["running"] != 0 or stat["queued"] != 0:
        print stat
