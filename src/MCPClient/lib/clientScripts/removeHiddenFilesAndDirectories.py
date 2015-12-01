#!/usr/bin/env python2

import sys
import os
import shutil


def removeHiddenFilesFromDirectory(dir):
    for item in os.listdir(dir):
        fullPath = os.path.join(dir, item)
        if os.path.isdir(fullPath):
            if item.startswith("."):
                print "Removing directory: ", fullPath
                shutil.rmtree(fullPath)
            else:
                removeHiddenFilesFromDirectory(fullPath)
        elif os.path.isfile(fullPath):
            if item.startswith(".") or item.endswith("~"):
                print "Removing file: ", fullPath 
                os.remove(fullPath)
               
        else:
            print >>sys.stderr, "Not file or directory: ", fullPath
                
            

if __name__ == '__main__':
    transferDirectory = sys.argv[1]
    removeHiddenFilesFromDirectory(transferDirectory)
            


    
    
