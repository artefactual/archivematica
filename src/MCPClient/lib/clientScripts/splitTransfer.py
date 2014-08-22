#!/usr/bin/python -OO

# This file is part of a new Archivematica Workflow
# It creates a new folder for each AIP that should get created
# and moves the corresponding folders into the created ones
#
# @author Patrick Brantner

import os
import sys
import shutil

def getAipUid(folder):
    return "SIP-" + folder
		
if __name__ == '__main__':
    rootDir = sys.argv[1]
    destination = sys.argv[2]
    for dirname in os.listdir(rootDir):
        src = os.path.join(rootDir,dirname)
        if (os.path.isdir(src)):
            uid = getAipUid(dirname)
            des = os.path.join(rootDir,uid)
            if not os.path.exists(os.path.join(rootDir,uid)):
                os.makedirs(os.path.join(rootDir,uid))
            shutil.move(src,des)
            print "Moved " + dirname + " into SIP " + uid
    for dirname in os.listdir(rootDir):
        src = os.path.join(rootDir,dirname)
        if (os.path.isdir(src)):
            shutil.move(src,destination)
            print "Starting transfer of " + dirname