#!/usr/bin/env python2

import sys
import os
from optparse import OptionParser

def verifyFileUUID(fileUUID, filePath, sipDirectory):
    if fileUUID == "None":
        relativeFilePath = filePath.replace(sipDirectory, "%SIPDirectory%", 1)
        print >>sys.stderr, relativeFilePath
        os.remove(filePath)
        quit(0)


if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-f",  "--inputFile",          action="store", dest="inputFile", default="")
    parser.add_option("-o",  "--sipDirectory",  action="store", dest="sipDirectory", default="")
    parser.add_option("-i",  "--fileUUID",           action="store", dest="fileUUID", default="")

    (opts, args) = parser.parse_args()

    verifyFileUUID(opts.fileUUID, opts.inputFile, opts.sipDirectory)
