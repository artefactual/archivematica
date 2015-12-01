#!/usr/bin/env python2

import os
import sys
import shutil



requiredDirectories = ["logs", "logs/fileMeta", "metadata", "metadata/submissionDocumentation", "objects", "objects/Maildir"]
optionalFiles = "processingMCP.xml"

def restructureMaildirDirectory(unitPath):
    for dir in requiredDirectories:
        dirPath = os.path.join(unitPath, dir)
        if not os.path.isdir(dirPath):
            os.mkdir(dirPath)
            print "creating: ", dir
    for item in os.listdir(unitPath):
        dst = os.path.join(unitPath, "objects", "Maildir") + "/."
        itemPath =  os.path.join(unitPath, item)
        if os.path.isdir(itemPath) and item not in requiredDirectories:
            shutil.move(itemPath, dst)
            print "moving directory to objects/Maildir: ", item
        elif os.path.isfile(itemPath) and item not in optionalFiles:
            shutil.move(itemPath, dst)
            print "moving file to objects/Maildir: ", item

if __name__ == '__main__':
    target = sys.argv[1]
    restructureMaildirDirectory(target)
    
