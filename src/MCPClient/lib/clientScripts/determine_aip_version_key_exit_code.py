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

import namespaces as ns
import os
import sys
from lxml import etree

VERSION_MAP = {
    # Only change exit code if AIP format changes. If unknown, default to latest
    # version. Currently, all AIPs are the same format so no special cases
    # required.
    # Example:
    # 'Archivematica-1.2': 100,
}


def get_version_from_mets(mets):
    for agent in mets.iter(ns.metsBNS + "agentIdentifier"):
        if agent.findtext(ns.metsBNS + "agentIdentifierType") != "preservation system":
            continue
        return agent.findtext(ns.metsBNS + "agentIdentifierValue")
    return None


def call(jobs):
    for job in jobs:
        with job.JobContext():
            sip_uuid = job.args[1]
            unit_path = job.args[2]

            mets_path = os.path.join(unit_path, "data", "METS.%s.xml" % (sip_uuid))
            if not os.path.isfile(mets_path):
                job.pyprint("Mets file not found: ", mets_path, file=sys.stderr)
                job.set_status(0)
                continue

            parser = etree.XMLParser(remove_blank_text=True)
            root = etree.parse(mets_path, parser)

            version = get_version_from_mets(root)
            job.pyprint("Version found in METSt:", version)

            job.set_status(VERSION_MAP.get(version, 0))
