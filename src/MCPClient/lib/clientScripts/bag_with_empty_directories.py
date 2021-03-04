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

import argparse
import multiprocessing
import os
import shutil

import django
import scandir

django.setup()
from django.conf import settings as mcpclient_settings

# archivematicaCommon
from archivematicaFunctions import get_setting

from bagit import make_bag


def get_sip_directories(job, sip_dir):
    """ Get a list of directories in the SIP, to be created after bagged. """
    directory_list = []
    for directory, subdirs, _ in scandir.walk(sip_dir):
        for subdir in subdirs:
            path = os.path.join(directory, subdir).replace(sip_dir + "/", "", 1)
            directory_list.append(path)
    job.pyprint("directory list:")
    for sip_dir in directory_list:
        job.pyprint("\t", sip_dir)
    return directory_list


def create_directories(base_dir, dir_list):
    """Create all the SIP's directories in the bag's data/ folder.

    Some directories should have been created in the data/ folder by the bagit
    command, but create any empty (or unspecified) directories."""
    for directory in dir_list:
        directory = os.path.join(base_dir, directory)
        try:
            os.makedirs(directory)
        except os.error:
            pass


_PAYLOAD_ENTRIES = ("logs/", "objects/", "README.html", "thumbnails/", "metadata/")


def bag_with_empty_directories(job, destination, sip_directory, sip_uuid, algorithm):
    """Create BagIt and include any empty directories from the SIP."""
    # Get list of directories in SIP
    dir_list = get_sip_directories(job, sip_directory)
    payload_entries = _PAYLOAD_ENTRIES + ("METS.%s.xml" % sip_uuid,)
    os.mkdir(destination)
    for item in payload_entries:
        item = os.path.join(sip_directory, item)
        # Omit payload items that don't exist
        if not os.path.exists(item):
            continue
        if os.path.isfile(item):
            shutil.copy(item, destination)
        else:
            dst = os.path.join(destination, os.path.basename(os.path.dirname(item)))
            shutil.copytree(item, dst)
    make_bag(
        destination,
        processes=multiprocessing.cpu_count(),
        bag_info={"External-Identifier": sip_uuid},
        checksums=[algorithm],
    )
    create_directories(os.path.join(destination, "data"), dir_list)


def call(jobs):
    # Parse arguments
    parser = argparse.ArgumentParser(description="Convert folder into a bag.")
    parser.add_argument("destination")
    parser.add_argument("sip_directory")
    parser.add_argument("sip_uuid")

    algorithm = get_setting(
        "checksum_type", mcpclient_settings.DEFAULT_CHECKSUM_ALGORITHM
    )

    for job in jobs:
        with job.JobContext():
            args = parser.parse_args(job.args[1:])
            bag_with_empty_directories(
                job, args.destination, args.sip_directory, args.sip_uuid, algorithm
            )
