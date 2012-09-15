#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

import mailbox
import sys
import os
import uuid
import traceback
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from externals.extractMaildirAttachments import parse
from fileOperations import addFileToTransfer
from fileOperations import updateSizeAndChecksum
import databaseInterface

def writeFile(filePath, fileContents):   
    try:
        os.makedirs(os.path.dirname(filePath))
    except:
        pass
    print filePath
    FILE = open(filePath,"w")
    FILE.writelines(fileContents)    
    FILE.close()

def addFile(filePath, transferPath, transferUUID, date, eventDetail = "", fileUUID = uuid.uuid4().__str__()): 
    taskUUID = uuid.uuid4().__str__()
    filePathRelativeToSIP = filePath.replace(transferPath, "%transferDirectory%", 1)
    addFileToTransfer(filePathRelativeToSIP, fileUUID, transferUUID, taskUUID, date, sourceType="unpacking", eventDetail=eventDetail)
    updateSizeAndChecksum(fileUUID, filePath, date, uuid.uuid4.__str__())

def getFileUUIDofSourceFile(transferUUID, sourceFilePath):
    ret = ""
    sql = """SELECT fileUUID FROM Files WHERE removedTime = 0 AND transferUUID = '%s' AND currentLocation LIKE '%s%%';""" % (transferUUID, sourceFilePath.replace('%', '\%'))
    rows = databaseInterface.queryAllSQL(sql)
    if len(rows):
        ret = rows[0][0]
    return ret

def setSourceFileToBeExcludedFromDIP(sourceFileUUID):
    sql = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES ('%s', (SELECT pk FROM FileIDs WHERE description = 'A maildir email file')); """ % (sourceFileUUID)
    databaseInterface.runSQL(sql)
    
def addKeyFileToNormalizeMaildirOffOf(relativePathToRepresent, mirrorDir, transferPath, transferUUID, date, eventDetail = "", fileUUID=uuid.uuid4().__str__()):
    basename = os.path.basename(mirrorDir)
    dirname = os.path.dirname(mirrorDir)
    outFile = os.path.join(dirname, basename + ".archivematicaMaildir")
    content = """#This file is used in the archivematica system to represent a maildir dirctory, for normalization and permission purposes.
[archivematicaMaildir]
path = %s
    """ % (relativePathToRepresent)
    f = open(outFile, 'w')
    f.write(content)
    f.close()
    addFile(outFile, transferPath, transferUUID, date, eventDetail=eventDetail, fileUUID=fileUUID)
    return
   
if __name__ == '__main__':
    #http://www.doughellmann.com/PyMOTW/mailbox/
    while False: #used to stall the mcp and stop the client for testing this module
        import time
        time.sleep(10)
    global errorCounter
    errorCounter = 0
    transferDir = sys.argv[1]
    transferUUID =  sys.argv[2]
    date =  sys.argv[3]
    maildir = transferDir + "objects/Maildir/" 
    outXML = transferDir + "logs/attachmentExtraction.xml"
    mirrorDir = os.path.join(transferDir, "objects/attachments")
    try:
        os.makedirs(mirrorDir)
    except:
        pass
    import lxml.etree as etree
    #print "Extracting attachments from: " + maildir
    root = etree.Element("ArchivematicaMaildirAttachmentExtractionRecord")
    root.set("directory", maildir) 
    for maildirsub2 in os.listdir(maildir):
        maildirsub = os.path.join(maildir, maildirsub2)
        #print "Extracting attachments from: " + maildirsub
        md = mailbox.Maildir(maildirsub, None)
        directory = etree.SubElement(root, "subDir")
        directory.set("dir", maildirsub2)
        try:
            for item in md.iterkeys():
                try:
                    subDir = md.get_message(item).get_subdir()
                    sourceFilePath2 = os.path.join(maildir, maildirsub2, subDir, item)
                    sourceFilePath = sourceFilePath2.replace(transferDir, "%transferDirectory%", 1)
                    fil = md.get_file(item)
                    out = parse(fil)
                    sourceFileUUID = getFileUUIDofSourceFile(transferUUID, sourceFilePath)
                    setSourceFileToBeExcludedFromDIP(sourceFileUUID)
                    if len(out['attachments']):
                        msg = etree.SubElement(directory, "msg")
                        etree.SubElement(msg, "Message-ID").text = out['msgobj']['Message-ID'][1:-1]
                        etree.SubElement(msg, "Extracted-from").text = item
                        etree.SubElement(msg, "Subject").text = out["subject"] 
                        etree.SubElement(msg, "Date").text = out['msgobj']['date']
                        etree.SubElement(msg, "To").text = out["to"]
                        etree.SubElement(msg, "From").text = out["from"]
                        for i in range(len(out['attachments'])):
                            try:
                                attachment = out['attachments'][i]
                                if attachment.name == None:
                                    continue
                                attachedFileUUID = uuid.uuid4().__str__()
                                #attachment = StringIO(file_data) TODO LOG TO FILE
                                attch = etree.SubElement(msg, "attachment")
                                #attachment.name = attachment.name[1:-1]
                                etree.SubElement(attch, "name").text = attachment.name
                                etree.SubElement(attch, "content_type").text = attachment.content_type
                                etree.SubElement(attch, "size").text = str(attachment.size)
                                #print attachment.create_date
                                # Dates don't appear to be working. Disabling for the moment - Todo
                                #etree.SubElement(attch, "create_date").text = attachment.create_date
                                #etree.SubElement(attch, "mod_date").text = attachment.mod_date
                                #etree.SubElement(attch, "read_date").text = attachment.read_date
                                
                                filePath = os.path.join(transferDir, "objects/attachments", maildirsub2, subDir, "%s_%s" % (attachedFileUUID, attachment.name))
                                writeFile(filePath, attachment)
                                eventDetail="Unpacked from: {%s}%s" % (sourceFileUUID, sourceFilePath) 
                                addFile(filePath, transferDir, transferUUID, date, eventDetail=eventDetail, fileUUID=attachedFileUUID)
                            except Exception as inst:
                                print >>sys.stderr, sourceFilePath
                                traceback.print_exc(file=sys.stderr)
                                print >>sys.stderr, type(inst)     # the exception instance
                                print >>sys.stderr, inst.args
                                print >>sys.stderr, etree.tostring(msg) 
                                print >>sys.stderr
                                errorCounter += 1
                except Exception as inst:
                    print >>sys.stderr, sourceFilePath
                    traceback.print_exc(file=sys.stderr)
                    print >>sys.stderr, type(inst)     # the exception instance
                    print >>sys.stderr, inst.args
                    print >>sys.stderr
                    errorCounter += 1
        except Exception as inst:
            print >>sys.stderr, "INVALID MAILDIR FORMAT"
            print >>sys.stderr, type(inst)
            print >>sys.stderr, inst.args
            exit(-10)
        mirrorDir = os.path.join(transferDir, "objects/attachments", maildirsub2)
        try:
            os.makedirs(mirrorDir)
        except:
            pass
        eventDetail = "added for normalization purposes"
        fileUUID=uuid.uuid4().__str__()
        addKeyFileToNormalizeMaildirOffOf(os.path.join(maildir, maildirsub2).replace(transferDir, "%transferDirectory%", 1), mirrorDir, transferDir, transferUUID, date, eventDetail=eventDetail, fileUUID=fileUUID)
    tree = etree.ElementTree(root)
    tree.write(outXML, pretty_print=True, xml_declaration=True)
    exit(errorCounter)

                    
