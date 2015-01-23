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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
import shutil
import os
import sys

# dashboard
from main.models import File, SIP

# archivematicaCommon
import archivematicaFunctions
import databaseFunctions

if __name__ == '__main__':
    objectsDirectory = sys.argv[1]
    transferName = sys.argv[2]
    transferUUID = sys.argv[3]
    processingDirectory = sys.argv[4]
    autoProcessSIPDirectory = sys.argv[5]
    sharedPath = sys.argv[6]
    sipName = transferName

    tmpSIPDir = os.path.join(processingDirectory, sipName) + "/"
    destSIPDir =  os.path.join(autoProcessSIPDirectory, sipName) + "/"
    archivematicaFunctions.create_structured_directory(tmpSIPDir, manual_normalization=False)

    #create row in SIPs table if one doesn't already exist
    lookup_path = destSIPDir.replace(sharedPath, '%sharedPath%')
    try:
        sipUUID = SIP.objects.get(currentpath=lookup_path).uuid
    except SIP.DoesNotExist:
        sipUUID = databaseFunctions.createSIP(lookup_path)

    #move the objects to the SIPDir
    for item in os.listdir(objectsDirectory):
        src_path = os.path.join(objectsDirectory, item)
        dst_path = os.path.join(tmpSIPDir, "objects", item)
        # If dst_path already exists and is a directory, shutil.move
        # will move src_path into it rather than overwriting it;
        # to avoid incorrectly-nested paths, move src_path's contents
        # into it instead.
        if os.path.exists(dst_path) and os.path.isdir(src_path):
            for subitem in os.listdir(src_path):
                shutil.move(os.path.join(src_path, subitem), dst_path)
        else:
            shutil.move(src_path, dst_path)

    #get the database list of files in the objects directory
    #for each file, confirm it's in the SIP objects directory, and update the current location/ owning SIP'
    files = File.objects.filter(transfer_id=transferUUID,
                                currentlocation__startswith='%transferDirectory%objects',
                                removedtime__isnull=True)
    for f in files:
        currentPath = databaseFunctions.deUnicode(f.currentlocation)
        currentSIPFilePath = currentPath.replace("%transferDirectory%", tmpSIPDir)
        if os.path.isfile(currentSIPFilePath):
            f.currentlocation = currentPath.replace("%transferDirectory%", "%SIPDirectory%")
            f.sip_id = sipUUID
            f.save()
        else:
            print >>sys.stderr, "file not found: ", currentSIPFilePath

    archivematicaFunctions.create_directories(archivematicaFunctions.MANUAL_NORMALIZATION_DIRECTORIES, basepath=tmpSIPDir)

    # Copy the JSON metadata file, if present;
    # this contains a serialized copy of DC metadata entered in the dashboard UI
    src = os.path.normpath(os.path.join(objectsDirectory, "..", "metadata", "dc.json"))
    dst = os.path.join(tmpSIPDir, "metadata", "dc.json")
    # This file only exists if any metadata was created during the transfer
    if os.path.exists(src):
        shutil.copy(src, dst)
    
    #copy processingMCP.xml file
    src = os.path.join(os.path.dirname(objectsDirectory[:-1]), "processingMCP.xml") 
    dst = os.path.join(tmpSIPDir, "processingMCP.xml")
    shutil.copy(src, dst)
    
    #moveSIPTo autoProcessSIPDirectory
    shutil.move(tmpSIPDir, destSIPDir)
