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

import os
from lxml import etree

import namespaces

import django
from django.db import transaction

django.setup()
# dashboard
from main.models import File


def identify_dspace_files(
    job, mets_file, transfer_dir, transfer_uuid, relative_dir="./"
):
    job.print_output(mets_file)
    nsmap = {"m": namespaces.metsNS, "x": namespaces.xlinkNS}
    tree = etree.parse(mets_file)
    root = tree.getroot()
    for item in root.findall("m:fileSec/m:fileGrp", namespaces=nsmap):
        use = item.get("USE")
        if use in ("TEXT", "LICENSE"):
            try:
                filename = item.find("m:file/m:FLocat", namespaces=nsmap).get(
                    namespaces.xlinkBNS + "href"
                )
            except AttributeError:  # Element not found
                continue
            if filename is None:  # Filename not an attribute
                continue
            job.write_output("File: %s Use: %s\n" % (filename, use))
            full_path = os.path.join(relative_dir, filename)
            db_location = full_path.replace(transfer_dir, "%transferDirectory%")
            if use == "TEXT":
                db_use = "text/ocr"
            elif use == "LICENSE":
                db_use = "license"
            else:
                job.write_error("Unexpected usage %s\n" % (use))
                continue

            File.objects.filter(
                currentlocation=db_location, transfer_id=transfer_uuid
            ).update(filegrpuse=db_use)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                mets_file = job.args[1]
                transfer_dir = job.args[2]
                transfer_uuid = job.args[3]

                identify_dspace_files(
                    job,
                    mets_file,
                    transfer_dir,
                    transfer_uuid,
                    relative_dir=os.path.dirname(mets_file) + "/",
                )
