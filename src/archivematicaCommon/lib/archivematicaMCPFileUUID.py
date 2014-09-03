#!/usr/bin/python -OO
#
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
# @subpackage archivematicaCommon
# @author Joseph Perry <joseph@artefactual.com>

#~DOC~
#
#This file is all in support of one goal:
#to get the UUID of a file efficiently.
#Primarily it looks for them in the 'sipUUIDfile' : /logs/fileUUIDs.log
#Failing that, it checks each of the fileMeta xml files to match the filename on the 'currentFileName' field.
#In order to do this efficiently and not block the processing of other SIPs, it dynamically creates a lock for each SIP, based on the UUID.
#


import os
import lxml.etree as etree
import sys
import threading
import string

lockDicsLock = threading.Lock()
sipUUIDFileLocksCount = {}
sipUUIDFileLocks = {}

def releaseSIPUUIDFileLock(sipUUIDfile):
    lockDicsLock.acquire()
    sipUUIDFileLocksCount[sipUUIDfile] -= 1
    if sipUUIDFileLocksCount[sipUUIDfile] == 0:
        #remove the locks from the system to prevent memory leak.
        #print "actually removing lock: " + sipUUIDfile
        del sipUUIDFileLocksCount[sipUUIDfile]
        del sipUUIDFileLocks[sipUUIDfile]
    lockDicsLock.release()

def acquireSIPUUIDFileLock(sipUUIDfile):
    lockDicsLock.acquire()
    if sipUUIDfile in sipUUIDFileLocksCount:
        sipUUIDFileLocksCount[sipUUIDfile] += 1
    else:
        sipUUIDFileLocksCount[sipUUIDfile] = 1
        sipUUIDFileLocks[sipUUIDfile] = threading.Lock()
    lockDicsLock.release()
    if sipUUIDfile in sipUUIDFileLocks:
        sipUUIDFileLocks[sipUUIDfile].acquire()
    else:
        print "Software logic error. This should not happen."

def loadFileUUIDsDic(sipUUIDfile):
    UUIDsDic = {}
    if os.path.isfile(sipUUIDfile):
        FileUUIDs_fh = open(sipUUIDfile, "r")
        line = FileUUIDs_fh.readline()
        while line:
            theFileLine = line.split(" -> ",1)
            if len(theFileLine) > 1 :
                fileUUID = theFileLine[0]
                fileName = theFileLine[1]
                fileName = string.replace(fileName, "\n", "", 1)
                UUIDsDic[fileName] = fileUUID
            line = FileUUIDs_fh.readline()
    else:
        UUIDsDic = {}
    return UUIDsDic

def getTagged(root, tag):
    ret = []
    for element in root:
        if element.tag == tag:
            ret.append(element)
            return ret #only return the first encounter
    return ret

def findUUIDFromFileUUIDxml(sipUUIDfile, filename, fileUUIDxmlFilesDirectory, updateSIPUUIDfile=True):
    ret = "No UUID for file: " + filename
    #for every file in the fileUUIDxmlFilesDirectory:
    configFiles = []
    try:
        for dirs, subDirs, files in os.walk(fileUUIDxmlFilesDirectory):
            configFiles = files
            break

        #print "config file - dir: ", fileUUIDxmlFilesDirectory
        for configFile in configFiles:
            if configFile.endswith(".xml"):
                try:
                    #print "config file - opening: " + configFile
                    tree = etree.parse(fileUUIDxmlFilesDirectory + configFile )
                    root = tree.getroot()
                    xmlFileName = getTagged(root, "currentFileName")[0]
                    uuid = getTagged(root, "fileUUID")[0]
                    if xmlFileName.text == filename:
                        ret = uuid.text
                        try:
                            if updateSIPUUIDfile:
                                acquireSIPUUIDFileLock(sipUUIDfile)
                                f = open(sipUUIDfile, 'a')
                                f.write(uuid.text + " -> " + filename + "\n")
                                f.close()
                        except OSError as ose:
                            print >>sys.stderr, "output Error", ose
                            return -2
                        except IOError as (errno, strerror):
                            print "I/O error({0}): {1}".format(errno, strerror)
                        except:
                            print "debug except 1"
                        #print "releasing Lock"
                        if updateSIPUUIDfile:
                            releaseSIPUUIDFileLock(sipUUIDfile)
                        return ret
                except Exception as inst:
                    print "debug except 2"
                    print type(inst)     # the exception instance
                    print inst.args      # arguments stored in .args
                    print inst           # __str__ allows args to printed directly
                    continue
    except:
        print "debug except 3"
        ret = ret
    return ret


def getUUIDOfFile(sipUUIDfile, basepath, fullFileName, fileUUIDxmlFilesDirectory, relativeString="objects/"):
    UUIDsDic = loadFileUUIDsDic(sipUUIDfile)
    if basepath not in fullFileName:
        return "No UUID for file: " + os.path.basename(fullFileName)
    filename = string.replace( fullFileName, basepath, relativeString, 1 )
    if UUIDsDic and filename in UUIDsDic:
        return UUIDsDic[filename]
    else :
        return findUUIDFromFileUUIDxml(sipUUIDfile, filename, fileUUIDxmlFilesDirectory)


if __name__ == '__main__':
    function =  sys.argv[1]

    if function == "Logline" :
        basepath = sys.argv[2]
        fullFileName = sys.argv[3]
        filename = string.replace( fullFileName, basepath, "objects", 1 )
        print filename

    elif function == "getFileUUID":
        sipUUIDfile = sys.argv[2]
        basepath = sys.argv[3]
        fullFileName = sys.argv[4]
        fileUUIDxmlFilesDirectory = sys.argv[5]
        print getUUIDOfFile( sipUUIDfile, basepath, fullFileName, fileUUIDxmlFilesDirectory)
