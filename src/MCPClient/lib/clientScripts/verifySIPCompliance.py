#!/usr/bin/env python2

import os
import sys

requiredDirectories = ["objects", \
                       "logs", \
                       "metadata",\
                       "metadata/submissionDocumentation"]
allowableFiles = ["processingMCP.xml"]

def checkDirectory(directory, ret=0):
    try:
        for directory, subDirectories, files in os.walk(directory):
            for file in files:
                filePath = os.path.join(directory, file)
    except Exception as inst:
        print >>sys.stderr, "Error navigating directory:", directory.__str__()
        print >>sys.stderr, type(inst)
        print >>sys.stderr, inst.args
        ret += 1
    return ret

def verifyDirectoriesExist(SIPDir, ret=0):
    for directory in requiredDirectories:
        if not os.path.isdir(os.path.join(SIPDir, directory)):
            print >>sys.stderr, "Required Directory Does Not Exist: " + directory
            ret += 1
    return ret

def verifyNothingElseAtTopLevel(SIPDir, ret=0):
    for entry in os.listdir(SIPDir):
        if os.path.isdir(os.path.join(SIPDir, entry)):
            if entry not in requiredDirectories:
                print >>sys.stderr, "Error, directory exists: " + entry
                ret += 1
        else:
            if entry not in allowableFiles:
                print >>sys.stderr, "Error, file exists: " + entry
                ret += 1
    return ret



if __name__ == '__main__':
    SIPDir = sys.argv[1]
    ret = verifyDirectoriesExist(SIPDir)
    ret = verifyNothingElseAtTopLevel(SIPDir, ret)
    ret = checkDirectory(SIPDir, ret)
    if ret != 0:
        import time
        time.sleep(10)
    quit(ret)
