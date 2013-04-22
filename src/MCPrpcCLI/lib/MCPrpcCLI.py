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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage MCPrpcCLI
# @author Joseph Perry <joseph@artefactual.com>

import gearman
import cPickle
import lxml.etree as etree
import traceback
import os
import time
import sys

class Settings:
    MCP_SERVER = ('localhost', 4730)

settings = Settings()

class MCPClient:

    def __init__(self, host=settings.MCP_SERVER[0], port=settings.MCP_SERVER[1]):
        self.server = "%s:%d" % (host, port)

    def list(self):
        gm_client = gearman.GearmanClient([self.server])
        completed_job_request = gm_client.submit_job("getJobsAwaitingApproval", "", None)
        #self.check_request_status(completed_job_request)
        return cPickle.loads(completed_job_request.result)

    def execute(self, uuid, choice):
        gm_client = gearman.GearmanClient([self.server])
        data = {}
        data["jobUUID"] = uuid
        data["chain"] = choice
        data["uid"] = "1"
        completed_job_request = gm_client.submit_job("approveJob", cPickle.dumps(data), None)
        #self.check_request_status(completed_job_request)
        return

mcpClient = MCPClient()

def getTagged(root, tag): #bad, I use this elsewhere, should be imported
    ret = []
    for element in root:
        if element.tag == tag:
            ret.append(element)
            return ret #only return the first encounter
    return ret

def updateJobsAwaitingApproval(jobsAwaitingApproval):
    del jobsAwaitingApproval
    ret = mcpClient.list()
    jobsAwaitingApproval = etree.XML(ret)
    return jobsAwaitingApproval

def printJobsAwaitingApproval(jobsAwaitingApproval):
    i = 0
    #print len(jobsAwaitingApproval)
    for job in jobsAwaitingApproval:
        print i
        i += 1
        print etree.tostring(job, pretty_print=True)

def approveJob(jobsAwaitingApproval, choice, choice2):
    try:
        index = int(choice)
        if index >= len(jobsAwaitingApproval):
            print "index out of range"
            return
        sipUUID = getTagged(getTagged(getTagged(jobsAwaitingApproval[index], "unit")[0], \
                                   "unitXML")[0], \
                                   "UUID")[0].text
        uuid = getTagged(jobsAwaitingApproval[index], "UUID")[0].text

        chain = getTagged(getTagged(jobsAwaitingApproval[index], "choices")[0][int(choice2)], \
                                   "chainAvailable")[0].text
        print "Approving: " + uuid, chain, sipUUID
        mcpClient.execute(uuid, chain)
        del jobsAwaitingApproval[index]
    except ValueError:
        print "Value error"
        traceback.print_exc(file=sys.stdout)
        return


if __name__ == '__main__':
    os.system("clear")
    jobsAwaitingApproval = etree.Element("jobsAwaitingApproval")
    jobsAwaitingApproval = updateJobsAwaitingApproval(jobsAwaitingApproval)
    #print etree.tostring(jobsAwaitingApproval)
    choice = "No-op"
    while choice != "q":
        while not (len(jobsAwaitingApproval)):
            print "Fetching..."
            time.sleep(2)
            jobsAwaitingApproval = updateJobsAwaitingApproval(jobsAwaitingApproval)
        printJobsAwaitingApproval(jobsAwaitingApproval)
        print "q to quit"
        print "u to update List"
        print "number to approve Job"
        choice = raw_input('Please enter a value:')
        print "choice: " + choice
        if choice == "u":
            jobsAwaitingApproval = updateJobsAwaitingApproval(jobsAwaitingApproval)
        else:
            if choice == "q":
                break
            choice2 = "No-op"
            while choice2 != "q":
                #try:
                printJobsAwaitingApproval(jobsAwaitingApproval[int(choice)][2])
                choice2 = raw_input('Please enter a value:')
                print "choice2: " + choice2
                approveJob(jobsAwaitingApproval, choice, choice2)
                choice2 = "q"
                #except:
                #print "invalid choice"
                #choice2 = "q"
        os.system("clear")
