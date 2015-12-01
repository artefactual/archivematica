#!/usr/bin/env python2

import os
import sys
import shutil

# archivematicaCommon
import archivematicaFunctions
from archivematicaFunctions import REQUIRED_DIRECTORIES, OPTIONAL_FILES
from custom_handlers import get_script_logger


def restructureDirectory(unitPath):
    unitPath = str(unitPath)
    # Create required directories
    archivematicaFunctions.create_directories(
        REQUIRED_DIRECTORIES, unitPath, printing=True)
    # Move everything else to the objects directory
    for item in os.listdir(unitPath):
        dst = os.path.join(unitPath, "objects", '.')
        itemPath =  os.path.join(unitPath, item)
        if os.path.isdir(itemPath) and item not in REQUIRED_DIRECTORIES:
            shutil.move(itemPath, dst)
            print "moving directory to objects: ", item
        elif os.path.isfile(itemPath) and item not in OPTIONAL_FILES:
            shutil.move(itemPath, dst)
            print "moving file to objects: ", item

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.restructureForCompliance")

    target = sys.argv[1]
    restructureDirectory(target)
    
