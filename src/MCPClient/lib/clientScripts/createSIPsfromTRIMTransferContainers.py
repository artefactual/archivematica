#!/usr/bin/env python2

import uuid
import shutil
import os
import sys

import django
django.setup()
# dashboard
from main.models import File

# archivematicaCommon
import archivematicaFunctions
from custom_handlers import get_script_logger
import databaseFunctions

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.createSIPfromTRIMTransferContainers")

    objectsDirectory = sys.argv[1]
    transferName = sys.argv[2]
    transferUUID = sys.argv[3]
    processingDirectory = sys.argv[4]
    autoProcessSIPDirectory = sys.argv[5]
    sharedPath = sys.argv[6]
    transfer_objects_directory = '%transferDirectory%objects'

    for container in os.listdir(objectsDirectory):
        sipUUID = uuid.uuid4().__str__()
        containerPath = os.path.join(objectsDirectory, container)
        if not os.path.isdir(containerPath):
            print >>sys.stderr, "file (not container) found: ", container
            continue
            
        sipName = "%s-%s" % (transferName, container) 
        
        tmpSIPDir = os.path.join(processingDirectory, sipName) + "/"
        destSIPDir =  os.path.join(autoProcessSIPDirectory, sipName) + "/"
        archivematicaFunctions.create_structured_directory(tmpSIPDir, manual_normalization=True)
        databaseFunctions.createSIP(destSIPDir.replace(sharedPath, '%sharedPath%'), sipUUID)
    
        # move the objects to the SIPDir
        for item in os.listdir(containerPath):
            shutil.move(os.path.join(containerPath, item), os.path.join(tmpSIPDir, "objects", item))
    
        # get the database list of files in the objects directory
        # for each file, confirm it's in the SIP objects directory, and update the current location/ owning SIP'
        directory = os.path.join(transfer_objects_directory, container)
        files = File.objects.filter(removedtime__isnull=True,
                                    currentlocation__startswith=directory,
                                    transfer_id=transferUUID)
        for f in files:
            currentPath = databaseFunctions.deUnicode(f.currentlocation).replace(directory, transfer_objects_directory)
            currentSIPFilePath = currentPath.replace("%transferDirectory%", tmpSIPDir)
            if os.path.isfile(currentSIPFilePath):
                f.currentlocation = currentPath.replace("%transferDirectory%", "%SIPDirectory%")
                f.sip_id = sipUUID
                f.save()
            else:
                print >>sys.stderr, "file not found: ", currentSIPFilePath

        # moveSIPTo autoProcessSIPDirectory
        shutil.move(tmpSIPDir, destSIPDir)
