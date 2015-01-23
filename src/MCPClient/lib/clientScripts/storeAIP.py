#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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
import logging
import os
import sys
from uuid import uuid4

# archivematicaCommon
import storageService as storage_service

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematica.log",
    level=logging.INFO)


def store_aip(aip_destination_uri, aip_path, sip_uuid, sip_name, sip_type):
    """ Stores an AIP with the storage service.

    aip_destination_uri = storage service destination URI, should be of purpose
        AIP Store (AS)
    aip_path = Full absolute path to the AIP's current location on the local
        filesystem
    sip_uuid = UUID of the SIP, which will become the UUID of the AIP
    sip_name = SIP name.  Not used directly, but part of the AIP name

    Example inputs:
    storeAIP.py
        "/api/v1/location/9c2b5bb7-abd6-477b-88e0-57107219dace/"
        "/var/archivematica/sharedDirectory/currentlyProcessing/ep6-0737708e-9b99-471a-b331-283e2244164f/ep6-0737708e-9b99-471a-b331-283e2244164f.7z"
        "0737708e-9b99-471a-b331-283e2244164f"
        "ep6"
    """

    # FIXME Assume current Location is the one set up by default until location
    # is passed in properly, or use Agent to make sure is correct CP
    current_location = storage_service.get_location(purpose="CP")[0]

    # Make aip_path relative to the Location
    shared_path = os.path.join(current_location['path'], '')  # Ensure ends with /
    relative_aip_path = aip_path.replace(shared_path, '')

    # Get the package type: AIC or AIP
    if sip_type == "SIP":
        package_type = "AIP"
    elif sip_type == 'AIC' or sip_type == 'DIP':
        package_type = sip_type

    # Uncompressed directory AIPs must be terminated in a /,
    # otherwise the storage service will place the directory
    # inside another directory of the same name.
    current_path = os.path.basename(aip_path)
    if os.path.isdir(aip_path) and not aip_path.endswith('/'):
        relative_aip_path = relative_aip_path + '/'

    # DIPs cannot share the AIP UUID, as the storage service depends on
    # having a unique UUID; assign a new one before uploading.
    # TODO allow mapping the AIP UUID to the DIP UUID for retrieval.
    if sip_type == 'DIP':
        uuid = str(uuid4())
    else:
        uuid = sip_uuid

    # If AIP is a directory, calculate size recursively
    if os.path.isdir(aip_path):
        size = 0
        for dirpath, _, filenames in os.walk(aip_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                size += os.path.getsize(file_path)
    else:
        size = os.path.getsize(aip_path)

    #Store the AIP
    (new_file, error_msg) = storage_service.create_file(
        uuid=uuid,
        origin_location=current_location['resource_uri'],
        origin_path=relative_aip_path,
        current_location=aip_destination_uri,
        current_path=current_path,
        package_type=package_type,
        size=size
    )

    if new_file is not None and new_file.get('status', '') != "FAIL":
        message = "Storage service created {}: {}".format(sip_type, new_file)
        logging.info(message)
        print message
        sys.exit(0)
    else:
        print >>sys.stderr, "{} creation failed.  See Storage Service logs for more details".format(sip_type)
        print >>sys.stderr, error_msg or "Package status: Failed"
        logging.warning("{} unabled to be created: {}.  See logs for more details.".format(sip_type, error_msg))
        sys.exit(1)


    # FIXME this should be moved to the storage service and areas that rely
    # on the thumbnails should be updated

    # #copy thumbnails to an AIP-specific directory for easy admin access
    # thumbnailSourceDir = os.path.join(bag, 'data', 'thumbnails')
    # thumbnailDestDir   = os.path.join(destination['path'], 'thumbnails', sip_uuid)

    # #create thumbnail dest dir
    # if not os.path.exists(thumbnailDestDir):
    #     os.makedirs(thumbnailDestDir)

    # #copy thumbnails to destination directory
    # thumbnails = os.listdir(thumbnailSourceDir)
    # for filename in thumbnails:
    #     shutil.copy(os.path.join(thumbnailSourceDir, filename), thumbnailDestDir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create AIP pointer file.')
    parser.add_argument('aip_destination_uri', type=str, help='%AIPsStore%')
    parser.add_argument('aip_filename', type=str, help='%AIPFilename%')
    parser.add_argument('sip_uuid', type=str, help='%SIPUUID%')
    parser.add_argument('sip_name', type=str, help='%SIPName%')
    parser.add_argument('sip_type', type=str, help='%SIPType%')
    args = parser.parse_args()
    sys.exit(store_aip(args.aip_destination_uri, args.aip_filename,
        args.sip_uuid, args.sip_name, args.sip_type))
