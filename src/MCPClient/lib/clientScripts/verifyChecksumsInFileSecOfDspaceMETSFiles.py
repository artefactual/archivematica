#!/usr/bin/env python2

import hashlib
import os
import sys
import lxml.etree as etree

from externals.checksummingTools import get_file_checksum

def verifyMetsFileSecChecksums(metsFile, date, taskUUID, relativeDirectory="./"):
    print metsFile
    exitCode = 0
    tree = etree.parse(metsFile)
    root = tree.getroot()
    for item in root.findall("{http://www.loc.gov/METS/}fileSec/{http://www.loc.gov/METS/}fileGrp/{http://www.loc.gov/METS/}file"):
        checksum = item.get("CHECKSUM")
        checksumType = item.get('CHECKSUMTYPE', '').lower()

        for item2 in item:
            if item2.tag == "{http://www.loc.gov/METS/}FLocat":
                fileLocation = item2.get("{http://www.w3.org/1999/xlink}href")

        fileFullPath = os.path.join(relativeDirectory, fileLocation)

        if checksumType and checksumType in hashlib.algorithms:
            checksum2 = get_file_checksum(fileFullPath, checksumType)
            eventDetail = 'program="python"; module="hashlib.{}()"'.format(checksumType)
        else:
            print >>sys.stderr, "Unsupported checksum type: %s" % (checksumType.__str__())
            exit(300)

        if checksum != checksum2:
            eventOutcome = "Fail"
            print "%s - %s - %s" % ((checksum == checksum2).__str__(), checksum.__str__(), checksum2.__str__())
            print >>sys.stderr, eventOutcome, fileFullPath
            exitCode = exitCode + 22
        else:
            eventOutcome = "Pass"
            print eventOutcome, fileLocation

    return exitCode


if __name__ == '__main__':
    metsFile = sys.argv[1]
    date = sys.argv[2]
    taskUUID = sys.argv[3]

    ret = verifyMetsFileSecChecksums(metsFile, date, taskUUID, relativeDirectory=os.path.dirname(metsFile) + "/")
    quit(ret)
