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

# Set up Django settings
path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

path = "/usr/lib/archivematica/archivematicaCommon"
if path not in sys.path:
    sys.path.append(path)
import storageService as storage_service

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematica.log",
    level=logging.INFO)


def store_aip(aip_destination_uri, aip_path, sip_uuid, sip_name):
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

    #Store the AIP
    (new_file, error_msg) = storage_service.create_file(
        uuid=sip_uuid,
        origin_location=current_location['resource_uri'],
        origin_path=aip_path,  # FIXME should be relative
        current_location=aip_destination_uri,
        current_path=os.path.basename(aip_path),
        package_type="AIP",
        size=os.path.getsize(aip_path)
    )
    if new_file is not None:
        message = "Storage service created AIP: {}".format(new_file)
        logging.info(message)
        print message
        sys.exit(0)
    else:
        print >>sys.stderr, "AIP creation failed."
        print >>sys.stderr, error_msg
        logging.warning("AIP unabled to be created: {}.  See logs for more details.".format(error_msg))
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
    args = parser.parse_args()
    sys.exit(store_aip(args.aip_destination_uri, args.aip_filename,
        args.sip_uuid, args.sip_name))
