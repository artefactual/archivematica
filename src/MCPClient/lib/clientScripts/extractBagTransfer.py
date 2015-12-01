#!/usr/bin/env python2

import shutil
import os
import sys

import django
django.setup()
# dashboard
from main.models import Transfer

# archivematicaCommon
from custom_handlers import get_script_logger
from executeOrRunSubProcess import executeOrRun

def extract(target, destinationDirectory):
    filename, file_extension = os.path.splitext(target)

    if file_extension != '.tgz' and file_extension != '.gz':
        print 'Unzipping...'

        command = """/usr/bin/7z x -bd -o"%s" "%s" """ % (destinationDirectory, target)
        exitC, stdOut, stdErr = executeOrRun("command", command, printing=False)
        if exitC != 0:
            print stdOut
            print >>sys.stderr, "Failed extraction: ", command, "\r\n", stdErr
            exit(exitC)
    else:
        print 'Untarring...'

        parent_dir = os.path.abspath(os.path.join(destinationDirectory, os.pardir))
        file_extension = ''
        command = ("tar zxvf " + target + ' --directory="%s"') % (parent_dir)
        exitC, stdOut, stdErr = executeOrRun("command", command, printing=False)
        if exitC != 0:
            print stdOut
            print >>sys.stderr, "Failed to untar: ", command, "\r\n", stdErr
            exit(exitC)


if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.extractBagTransfer")

    target = sys.argv[1]
    transferUUID =  sys.argv[2]
    processingDirectory = sys.argv[3]
    sharedPath = sys.argv[4]
    
    basename = os.path.basename(target)
    basename = basename[:basename.rfind(".")]
    
    destinationDirectory = os.path.join(processingDirectory, basename)

    # trim off '.tar' if present (os.path.basename doesn't deal well with '.tar.gz')
    try:
        tar_extension_position = destinationDirectory.rindex('.tar')
        destinationDirectory = destinationDirectory[:tar_extension_position]
    except ValueError:
        pass

    zipLocation = os.path.join(processingDirectory, os.path.basename(target))
    
    #move to processing directory
    shutil.move(target, zipLocation)
    
    #extract
    extract(zipLocation, destinationDirectory)
    
    #checkForTopLevelBag
    listdir = os.listdir(destinationDirectory)
    if len(listdir) == 1:
        internalBagName = listdir[0]
        #print "ignoring BagIt internal name: ", internalBagName  
        temp = destinationDirectory + "-tmp"
        shutil.move(destinationDirectory, temp)
        #destinationDirectory = os.path.join(processingDirectory, internalBagName)
        shutil.move(os.path.join(temp, internalBagName), destinationDirectory)
        os.rmdir(temp)
    
    #update transfer
    destinationDirectoryDB = destinationDirectory.replace(sharedPath, "%sharedPath%", 1)
    t = Transfer.objects.filter(uuid=transferUUID).update(currentlocation=destinationDirectoryDB)
    
    #remove bag
    os.remove(zipLocation)
