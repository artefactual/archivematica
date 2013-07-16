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
import ConfigParser
import logging
import os
import shutil
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import storageService as storage_service

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematica.log",
    level=logging.INFO)

def store_aip():
    """ Stores an AIP with the storage service.

    sys.argv[1] = storage service destination URI
      URI of the storage service Location.  Should be of purpose AIP Store (AS)
    sys.argv[2] = current location
      Full absolute path to the AIP's current location on the local filesystem
    sys.argv[3] = UUID
      UUID of the SIP, which will become the UUID of the AIP
    sys.argv[4] = SIP name
      User-chosen name for the AIP.  Not used directly, but part of the AIP name


    Example inputs:
    storeAIP.py
        "/api/v1/location/9c2b5bb7-abd6-477b-88e0-57107219dace/"
        "/var/archivematica/sharedDirectory/currentlyProcessing/ep6-0737708e-9b99-471a-b331-283e2244164f/ep6-0737708e-9b99-471a-b331-283e2244164f.7z"
        "0737708e-9b99-471a-b331-283e2244164f"
        "ep6"
    """

    aip_destination_uri = sys.argv[1]  # %AIPsStore%
    aip_path = sys.argv[2]  # SIPDirectory%%sip_name%-%sip_uuid%.7z
    sip_uuid = sys.argv[3]  # %sip_uuid%
    sip_name = sys.argv[4]  # %sip_name%

    # FIXME Assume current Location is the one set up by default until location
    # is passed in properly, or use Agent to make sure is correct CP
    current_location = storage_service.get_location(purpose="CP")[0]
    destination = storage_service.get_location_by_uri(aip_destination_uri)

    #Store the AIP
    new_file = storage_service.create_file(
        uuid=sip_uuid,
        origin_location=current_location['resource_uri'],
        origin_path=aip_path,  # FIXME should be relative
        current_location=aip_destination_uri,
        current_path=os.path.basename(aip_path),
        package_type="AIP",
        )
    if new_file:
        logging.info("Storage service created AIP: {}".format(new_file))
        exit (0)
    else:
        logging.warning("AIP unabled to be created from {}".format(current_location))
        exit (-1)


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
    store_aip()
