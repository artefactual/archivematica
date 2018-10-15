#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
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

"""Where third party PID values are provided to Archivematica in the
``identifiers.json`` file update the ``Identifiers`` model to also include the
values supplied in that file.
"""
from os import path

import archivematicaFunctions
from dicts import ReplacementDict
from custom_handlers import get_script_logger

from main.models import Directory, File, SIP

logger = get_script_logger('archivematica.mcp.client.bind_third_party_pids')

IDENTIFIERS_JSON = "identifiers.json"


class ThirdPartyPIDsException(Exception):
    """If I am raised, return 1."""
    exit_code = 1


def parse_identifiers_json(job, sip_uuid, identifiers_loc, shared_path):
    try:
        sip_loc = SIP.objects.get(uuid=sip_uuid).currentpath\
            .replace("%sharedPath%", shared_path)
    except SIP.DoesNotExist:
        ThirdPartyPIDsException("Cannot find SIP %s", sip_uuid)
    identifiers_loc = \
        identifiers_loc.currentlocation.replace(
            "%SIPDirectory%", sip_loc)
    if path.exists(identifiers_loc):
        job.pyprint("Let's do some work with the JSON here")
