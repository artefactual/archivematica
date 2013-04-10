#!/usr/bin/python -OO
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
# @subpackage archivematicaClient
# @author Joseph Perry <joseph@artefactual.com>
import cPickle
import traceback
import archivematicaClient
import transcoder
import uuid
import os
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
import databaseInterface
from fileOperations import addFileToSIP
from fileOperations import updateSizeAndChecksum
from databaseFunctions import insertIntoEvents
from databaseFunctions import insertIntoDerivations


def executeCommandReleationship(gearman_worker, gearman_job):
    """some text"""
    try:
        execute = gearman_job.task
        print "executing:", execute, "{", gearman_job.unique, "}"
        data = cPickle.loads(gearman_job.data)
        utcDate = databaseInterface.getUTCDate()
        opts = data["arguments"]#.encode("utf-8")
        #if isinstance(arguments, unicode):
        #    arguments = arguments.encode("utf-8")
        #if isinstance(arguments, str):
        #    arguments = unicode(arguments)
        
        sInput = ""
        clientID = gearman_worker.worker_client_id

        opts["date"] = utcDate
        opts["accessDirectory"] = os.path.join(opts['sipPath'], "DIP/objects") + "/"
        opts["thumbnailDirectory"] = os.path.join(opts['sipPath'], "thumbnails")  + "/"
        print opts
        for key, value in archivematicaClient.replacementDic.iteritems():
            for key2 in opts:
                opts[key2] = opts[key2].replace(key, value)
        replacementDic = getReplacementDic(opts)
        #if True:
        opts["prependStdOut"] =    """Operating on file: {%s}%s \r\nUsing  %s  command classifications""" % (opts["fileUUID"], replacementDic["%fileName%"], opts["commandClassification"])
        opts["prependStdError"] = "\r\nSTDError:"
        #    print clientID, execute, data
        archivematicaClient.logTaskAssignedSQL(gearman_job.unique.__str__(), clientID, utcDate)
        cl = transcoder.CommandLinker(opts["CommandRelationship"], replacementDic, opts, onceNormalized)
        cl.execute()
        
        co = cl.commandObject
        exitCode = co.exitCode
        stdOut = "%s \r\n%s" % (opts["prependStdOut"], co.stdOut)
        if not co.stdError or co.stdError.isspace():
            stdError = ""
        else:
            stdError = "%s \r\n%s" % (opts["prependStdError"], co.stdError)
        
        #TODO add date to ops


        #Replace replacement strings
        #archivematicaClient.printOutputLock.acquire()
        #print >>sys.stderr, "<processingCommand>{" + gearman_job.unique + "}" + command.__str__() + "</processingCommand>"
        #archivematicaClient.printOutputLock.release()
        #exitCode, stdOut, stdError = executeOrRun("command", command, sInput, printing=False)
        return cPickle.dumps({"exitCode" : exitCode, "stdOut": stdOut, "stdError": stdError})
    #catch OS errors
    except OSError, ose:
        archivematicaClient.printOutputLock.acquire()
        traceback.print_exc(file=sys.stdout)
        print >>sys.stderr, "Execution failed:", ose
        archivematicaClient.printOutputLock.release()
        output = ["Config Error!", ose.__str__() ]
        exitCode = 1
        return cPickle.dumps({"exitCode" : exitCode, "stdOut": output[0], "stdError": output[1]})
    except:
        archivematicaClient.printOutputLock.acquire()
        traceback.print_exc(file=sys.stdout)
        print sys.exc_info().__str__()
        print "Unexpected error:", sys.exc_info()[0]
        archivematicaClient.printOutputLock.release()
        output = ["", sys.exc_info().__str__()]
        return cPickle.dumps({"exitCode" : -1, "stdOut": output[0], "stdError": output[1]})


def getReplacementDic(opts): 
    ret = {}
    prefix = ""
    postfix = ""
    outputDirectory = ""
    #get file name and extension
    s = opts["inputFile"]
    #get indexes for python string array
    #index of next char after last /
    x1 = s.rfind('/')+1
    #index of last .
    x2 = s.rfind('.')
    #index of next char after last .
    x2mod = x2+1
    #length of s
    sLen = len(s)

    if x2 < x1:
        x2mod = 0


    fileDirectory = os.path.dirname(s) + "/"
    if x2mod != 0:
        fileExtension = s[x2mod:sLen]
        fileTitle = s[x1:x2]
        fileFullName = fileDirectory + fileTitle + "." + fileExtension
    else:
        #print "No file extension!"
        fileExtension = ""
        fileTitle = s[x1:sLen]
        fileFullName = fileDirectory + fileTitle
    fileExtensionWithDot = "." + fileExtension
    if fileExtension == "":
        fileExtensionWithDot = ""

    sql = """SELECT CommandClassifications.classification FROM CommandRelationships JOIN CommandClassifications ON CommandRelationships.commandClassification = CommandClassifications.pk WHERE CommandRelationships.pk = '%s';""" % (opts["CommandRelationship"])
    rows = databaseInterface.queryAllSQL(sql)
    if rows:
        for row in rows:
            opts["commandClassification"] = row[0]
            if row[0] == "preservation":
                postfix = "-" + opts["taskUUID"]
                outputFileUUID = opts["taskUUID"]
                outputDirectory = fileDirectory
            elif row[0] == "access":
                prefix = opts["fileUUID"] + "-"
                outputDirectory = opts["accessDirectory"]
            elif row[0] == "thumbnail":
                outputDirectory = opts["thumbnailDirectory"]
                postfix = opts["fileUUID"]
            else:
                print >>sys.stderr, "Unsupported command classification.", opts["CommandRelationship"], row[0]
                return ret
    else:
        print >>sys.stderr, "Unsupported None command classification.", opts["CommandRelationship"]

    
    
    
    ret["%inputFile%"]= fileFullName
    ret["%outputDirectory%"] = outputDirectory
    ret["%fileExtension%"] = fileExtension
    ret["%fileExtensionWithDot%"] = fileExtensionWithDot
    ret["%fileFullName%"] = fileFullName
    ret["%preservationFileDirectory%"] = fileDirectory
    ret["%fileDirectory%"] = fileDirectory
    ret["%fileTitle%"] = fileTitle
    ret["%fileName%"] =  fileTitle
    ret["%prefix%"] = prefix
    ret["%postfix%"] = postfix
    ret["%outputFileUUID%"] = opts["taskUUID"]
    return ret


def onceNormalized(command, opts, replacementDic):
    transcodedFiles = []
    if not command.outputLocation:
        command.outputLocation = ""
    if os.path.isfile(command.outputLocation):
        transcodedFiles.append(command.outputLocation)
    elif os.path.isdir(command.outputLocation):
        for w in os.walk(command.outputLocation):
            path, directories, files = w
            for p in files:
                p = os.path.join(path, p)
                if os.path.isfile(p):
                    transcodedFiles.append(p)
    elif command.outputLocation:
        print >>sys.stderr, command
        print >>sys.stderr, "Error - output file does not exist [" + command.outputLocation + "]"
        command.exitCode = -2

    derivationEventUUID = uuid.uuid4().__str__()
    eventDetail = "ArchivematicaFPRCommandID=\"%s\"" % (command.pk)
    if command.eventDetailCommand != None:
        eventDetail = '%s; %s' % (eventDetail, command.eventDetailCommand.stdOut)
    for ef in transcodedFiles:
        if opts["commandClassifications"] == "preservation":
            #Add the new file to the sip
            filePathRelativeToSIP = ef.replace(opts["sipPath"], "%SIPDirectory%", 1)
            # addFileToSIP(filePathRelativeToSIP, fileUUID, sipUUID, taskUUID, date, sourceType="ingestion"):
            addFileToSIP(filePathRelativeToSIP, replacementDic["%outputFileUUID%"], opts["sipUUID"], uuid.uuid4().__str__(), opts["date"], sourceType="creation", use="preservation")
            #Calculate new file checksum
            #Add event information to current file
            insertIntoEvents(fileUUID=opts["fileUUID"], \
               eventIdentifierUUID=derivationEventUUID, \
               eventType="normalization", \
               eventDateTime=opts["date"], \
               eventDetail=eventDetail, \
               eventOutcome="", \
               eventOutcomeDetailNote=filePathRelativeToSIP)

            updateSizeAndChecksum(replacementDic["%outputFileUUID%"], ef, opts["date"], uuid.uuid4().__str__())

            #Add linking information between files
            insertIntoDerivations(sourceFileUUID=opts["fileUUID"], derivedFileUUID=replacementDic["%outputFileUUID%"], relatedEventUUID=derivationEventUUID)

            sql = "INSERT INTO FilesIDs (fileUUID, formatName, formatVersion, formatRegistryName, formatRegistryKey) VALUES ('%s', '%s', NULL, NULL, NULL);" % (replacementDic["%outputFileUUID%"], command.outputFormat)
            databaseInterface.runSQL(sql)
            
            replacementDic["%outputFileUUID%"] = uuid.uuid4().__str__()
            replacementDic["%postfix%"] = "-" + replacementDic["%outputFileUUID%"]




