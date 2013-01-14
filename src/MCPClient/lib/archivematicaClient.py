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
# @subpackage archivematicaClient
# @author Joseph Perry <joseph@artefactual.com>

#~DOC~
#
# --- This is the MCP Client---
#It connects to the MCP server, and informs the server of the tasks it can perform.
#The server can send a command (matching one of the tasks) for the client to perform.
#The client will perform that task, and return the exit code and output to the server.
#
#For archivematica 0.9 release. Added integration with the transcoder.
#The server will send the transcoder association pk, and file uuid to run.
#The client is responsible for running the correct command on the file. 

import sys
import os
import shlex
import subprocess
import time
import threading
import string
import ConfigParser
from socket import gethostname
import transcoderNormalizer 
import gearman
import threading
import cPickle
import traceback
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
import databaseInterface
from databaseFunctions import logTaskAssignedSQL
printOutputLock = threading.Lock()

databaseInterface.printSQL = True

config = ConfigParser.SafeConfigParser({'MCPArchivematicaServerInterface': ""})
config.read("/etc/archivematica/MCPClient/clientConfig.conf")

replacementDic = {
    "%sharedPath%":config.get('MCPClient', "sharedDirectoryMounted"), \
    "%clientScriptsDirectory%":config.get('MCPClient', "clientScriptsDirectory")
}
supportedModules = {}

def loadSupportedModulesSupport(key, value):
    for key2, value2 in replacementDic.iteritems():
        value = value.replace(key2, value2)
    if not os.path.isfile(value):
        print >>sys.stderr, "Warning - Module can't find file, or relies on system path:{%s}%s" % (key.__str__(), value.__str__())
    supportedModules[key] = value + " "

def loadSupportedModules(file):
    supportedModulesConfig = ConfigParser.RawConfigParser()
    supportedModulesConfig.read(file)
    for key, value in supportedModulesConfig.items('supportedCommands'):
        loadSupportedModulesSupport(key, value)

    loadSupportedCommandsSpecial = config.get('MCPClient', "LoadSupportedCommandsSpecial")
    if loadSupportedCommandsSpecial.lower() == "yes" or \
    loadSupportedCommandsSpecial.lower() == "true":
        for key, value in supportedModulesConfig.items('supportedCommandsSpecial'):
            loadSupportedModulesSupport(key, value)


def executeCommand(gearman_worker, gearman_job):
    try:
        execute = gearman_job.task
        print "executing:", execute, "{", gearman_job.unique, "}"
        data = cPickle.loads(gearman_job.data)
        utcDate = databaseInterface.getUTCDate()
        arguments = data["arguments"]#.encode("utf-8")
        if isinstance(arguments, unicode):
            arguments = arguments.encode("utf-8")
        #if isinstance(arguments, str):
        #    arguments = unicode(arguments)

        sInput = ""
        clientID = gearman_worker.worker_client_id

        #if True:
        #    print clientID, execute, data
        logTaskAssignedSQL(gearman_job.unique.__str__(), clientID, utcDate)

        if execute not in supportedModules:
            output = ["Error!", "Error! - Tried to run and unsupported command." ]
            exitCode = -1
            return cPickle.dumps({"exitCode" : exitCode, "stdOut": output[0], "stdError": output[1]})
        command = supportedModules[execute]


        replacementDic["%date%"] = utcDate
        replacementDic["%jobCreatedDate%"] = data["createdDate"]
        #Replace replacement strings
        for key in replacementDic.iterkeys():
            command = command.replace ( key, replacementDic[key] )
            arguments = arguments.replace ( key, replacementDic[key] )

        key = "%taskUUID%"
        value = gearman_job.unique.__str__()
        arguments = arguments.replace(key, value)

        #execute command

        command += " " + arguments
        printOutputLock.acquire()
        print "<processingCommand>{" + gearman_job.unique + "}" + command.__str__() + "</processingCommand>"
        printOutputLock.release()
        exitCode, stdOut, stdError = executeOrRun("command", command, sInput, printing=False)
        return cPickle.dumps({"exitCode" : exitCode, "stdOut": stdOut, "stdError": stdError})
    #catch OS errors
    except OSError, ose:
        traceback.print_exc(file=sys.stdout)
        printOutputLock.acquire()
        print >>sys.stderr, "Execution failed:", ose
        printOutputLock.release()
        output = ["Archivematica Client Error!", ose.__str__() ]
        exitCode = 1
        return cPickle.dumps({"exitCode" : exitCode, "stdOut": output[0], "stdError": output[1]})
    except:
        traceback.print_exc(file=sys.stdout)
        printOutputLock.acquire()
        print sys.exc_info().__str__()
        print "Unexpected error:", sys.exc_info()[0]
        printOutputLock.release()
        output = ["", sys.exc_info().__str__()]
        return cPickle.dumps({"exitCode" : -1, "stdOut": output[0], "stdError": output[1]})


def startThread(threadNumber):
    gm_worker = gearman.GearmanWorker([config.get('MCPClient', "MCPArchivematicaServer")])
    hostID = gethostname() + "_" + threadNumber.__str__()
    gm_worker.set_client_id(hostID)
    for key in supportedModules.iterkeys():
        printOutputLock.acquire()
        print "registering:", '"' + key + '"'
        printOutputLock.release()
        gm_worker.register_task(key, executeCommand)
    
    #load transoder jobs
    sql = """SELECT CommandRelationships.pk 
                FROM CommandRelationships 
                JOIN Commands ON CommandRelationships.command = Commands.pk
                JOIN CommandsSupportedBy ON Commands.supportedBy = CommandsSupportedBy.pk 
                WHERE CommandsSupportedBy.description = 'supported by default archivematica client';"""
    rows = databaseInterface.queryAllSQL(sql)
    if rows:
        for row in rows:
            CommandRelationshipsPK = row[0]
            key = "transcoder_cr%s" % (CommandRelationshipsPK.__str__())
            printOutputLock.acquire()
            print "registering:", '"' + key + '"'
            printOutputLock.release()
            gm_worker.register_task(key, transcoderNormalizer.executeCommandReleationship)
    gm_worker.work()


def flushOutputs():
    while True:
        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(5)

def startThreads(t=1):
    if True:
        t2 = threading.Thread(target=flushOutputs)
        t2.daemon = True
        t2.start()
    if t == 0:
        from externals.detectCores import detectCPUs
        t = detectCPUs()
    for i in range(t):
        t = threading.Thread(target=startThread, args=(i+1, ))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    loadSupportedModules(config.get('MCPClient', "archivematicaClientModules"))
    startThreads(config.getint('MCPClient', "numberOfTasks"))
    tl = threading.Lock()
    tl.acquire()
    tl.acquire()
