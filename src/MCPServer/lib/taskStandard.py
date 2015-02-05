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
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>

import uuid
import time
import gearman
import cPickle
import datetime
import archivematicaMCP
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from fileOperations import writeToFile


# ~Class Task~
#Tasks are what are assigned to clients.
#They have a zero-many(tasks) TO one(job) relationship
#This relationship is formed by storing a pointer to it's owning job in its job variable.
#They use a "replacement dictionary" to define variables for this task.
#Variables used for the task are defined in the Job's configuration/module (The xml file)
class taskStandard():
    """A task to hand to gearman"""

    def __init__(self, linkTaskManager, execute, arguments, standardOutputFile, standardErrorFile, outputLock=None, UUID=None):
        if UUID == None:
            UUID = uuid.uuid4().__str__()
        self.UUID = UUID
        self.linkTaskManager = linkTaskManager
        self.execute = execute.encode( "utf-8" )
        self.arguments = arguments
        self.standardOutputFile = standardOutputFile
        self.standardErrorFile = standardErrorFile
        self.outputLock = outputLock


    def performTask(self):
        from archivematicaMCP import limitGearmanConnectionsSemaphore
        limitGearmanConnectionsSemaphore.acquire()
        gm_client = gearman.GearmanClient([archivematicaMCP.config.get('MCPServer', "MCPArchivematicaServer")])
        data = {"createdDate" : datetime.datetime.now().__str__()}
        data["arguments"] = self.arguments
        print '"'+self.execute+'"', data
        completed_job_request = None
        failMaxSleep = 60
        failSleepInitial = 1
        failSleep = failSleepInitial
        failSleepIncrementor = 2
        while completed_job_request == None:
            try:
                completed_job_request = gm_client.submit_job(self.execute.lower(), cPickle.dumps(data), self.UUID)
            except gearman.errors.ServerUnavailable as inst:
                completed_job_request = None
                time.sleep(failSleep)
                if failSleep == failSleepInitial:
                    print >>sys.stderr, inst.args
                    print >>sys.stderr, "Retrying issueing gearman command."
                if failSleep < failMaxSleep:
                    failSleep += failSleepIncrementor
        limitGearmanConnectionsSemaphore.release()
        self.check_request_status(completed_job_request)
        gm_client.shutdown()
        print "DEBUG: FINISHED PERFORMING TASK: ", self.UUID

    def check_request_status(self, job_request):
        if job_request.complete:
            self.results = cPickle.loads(job_request.result)
            print "Task %s finished!  Result: %s - %s" % (job_request.job.unique, job_request.state, self.results)
            self.writeOutputs()
            self.linkTaskManager.taskCompletedCallBackFunction(self)

        elif job_request.timed_out:
            print >>sys.stderr, "Task %s timed out!" % job_request.unique
            self.results['exitCode'] = -1
            self.results["stdError"] = "Task %s timed out!" % job_request.unique
            self.linkTaskManager.taskCompletedCallBackFunction(self)

        elif job_request.state == gearman.client.JOB_UNKNOWN:
            print >>sys.stderr, "Task %s connection failed!" % job_request.unique
            self.results["stdError"] = "Task %s connection failed!" % job_request.unique
            self.results['exitCode'] = -1
            self.linkTaskManager.taskCompletedCallBackFunction(self)

        else:
            print >>sys.stderr, "Task %s failed!" % job_request.unique
            self.results["stdError"] = "Task %s failed!" % job_request.unique
            self.results['exitCode'] = -1
            self.linkTaskManager.taskCompletedCallBackFunction(self)





    #This function is used to verify that where
    #the MCP is writing to is an allowable location
    #@fileName - full path of file it wants to validate.
    def writeOutputsValidateOutputFile(self, fileName):
        ret = fileName
        if ret:
            if "%sharedPath%" in ret and "../" not in ret:
                ret = ret.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1)
            else:
                ret = "<^Not allowed to write to file^> " + ret
        return ret

    #Used to write the output of the commands to the specified files
    def writeOutputs(self):
        """Used to write the output of the commands to the specified files"""


        if self.outputLock != None:
            self.outputLock.acquire()

        standardOut = self.writeOutputsValidateOutputFile(self.standardOutputFile)
        standardError = self.writeOutputsValidateOutputFile(self.standardErrorFile)

        #output , filename
        a = writeToFile(self.results["stdOut"], standardOut)
        b = writeToFile(self.results["stdError"], standardError)

        if self.outputLock != None:
            self.outputLock.release()

        if a:
            self.stdError = "Failed to write to file{" + standardOut.encode('utf-8') + "}\r\n" + self.results["stdOut"]
        if b:
            self.stdError = "Failed to write to file{" + standardError.encode('utf-8') + "}\r\n" + self.results["stdError"]
        if  self.results['exitCode']:
            return self.results['exitCode']
        return a + b
