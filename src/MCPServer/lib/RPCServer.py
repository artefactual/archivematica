#!/usr/bin/env python2

import archivematicaMCP
import sys
from linkTaskManagerChoice import choicesAvailableForUnits
import logging
import lxml.etree as etree
import gearman
import cPickle
import time
import traceback
from socket import gethostname
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from custom_handlers import GroupWriteRotatingFileHandler
import databaseInterface

def rpcError(code="", details=""):
    ret = etree.Element("Error")
    etree.SubElement(ret, "code").text = code.__str__()
    etree.SubElement(ret, "details").text = details.__str__()
    return ret
    
def verifyDatabaseIsNotLocked():
    timeBeforeReturningErrorLockedDB = 4
    timeToSleep = 0.1
    numberOfRuns = 0 #count of number of runs in loop
    while not databaseInterface.sqlLock.acquire(False):
        time.sleep(timeToSleep)
        numberOfRuns += 1
        if numberOfRuns * timeToSleep > timeBeforeReturningErrorLockedDB:
            return rpcError(code="DatabaseLock", details="Couldn't acquire database lock")           
    databaseInterface.sqlLock.release()
    return None

def getJobsAwaitingApproval():
    ret = etree.Element("choicesAvailableForUnits")
    dbStatus = verifyDatabaseIsNotLocked()
    if dbStatus:
        #print etree.tostring(dbStatus)
        return etree.tostring(dbStatus)
    for UUID, choice in choicesAvailableForUnits.items():
        ret.append(choice.xmlify())
    return etree.tostring(ret, pretty_print=True)


def approveJob(jobUUID, chain, agent):
    print "approving: ", jobUUID, chain, agent
    if jobUUID in choicesAvailableForUnits:
        choicesAvailableForUnits[jobUUID].proceedWithChoice(chain, agent)
    return "approving: ", jobUUID, chain

def gearmanApproveJob(gearman_worker, gearman_job):
    try:
        #execute = gearman_job.task
        data = cPickle.loads(gearman_job.data)
        jobUUID = data["jobUUID"]
        chain = data["chain"]
        agent = str(data["uid"])
        ret = cPickle.dumps(approveJob(jobUUID, chain, agent))
        if not ret:
            ret = ""
        return ""
    #catch OS errors
    except Exception as inst:
        print >>sys.stderr, "DEBUG EXCEPTION! gearmanApproveJob"
        traceback.print_exc(file=sys.stdout)
        print >>sys.stderr, type(inst)     # the exception instance
        print >>sys.stderr, inst.args
        return ""

def gearmanGetJobsAwaitingApproval(gearman_worker, gearman_job):
    try:
        #print "DEBUG - getting list of jobs"
        #execute = gearman_job.task
        ret = cPickle.dumps(getJobsAwaitingApproval())
        #print ret
        if not ret:
            ret = ""
        return ret
    #catch OS errors
    except Exception as inst:
        print >>sys.stderr, "DEBUG EXCEPTION! gearmanGetJobsAwaitingApproval"
        traceback.print_exc(file=sys.stdout)
        print >>sys.stderr, type(inst)     # the exception instance
        print >>sys.stderr, inst.args
        return ""


def startRPCServer():
    logger = logging.getLogger("archivematica")
    logger.addHandler(GroupWriteRotatingFileHandler("/var/log/archivematica/MCPServer/MCPServer.log", maxBytes=4194304))

    gm_worker = gearman.GearmanWorker([archivematicaMCP.config.get('MCPServer', 'GearmanServerWorker')])
    hostID = gethostname() + "_MCPServer"
    gm_worker.set_client_id(hostID)
    gm_worker.register_task("approveJob", gearmanApproveJob)
    gm_worker.register_task("getJobsAwaitingApproval", gearmanGetJobsAwaitingApproval)
    failMaxSleep = 30
    failSleep = 1
    failSleepIncrementor = 2
    while True:
        try:
            gm_worker.work()
        except gearman.errors.ServerUnavailable as inst:
            #print >>sys.stderr, inst.args
            #print >>sys.stderr, "Retrying in %d seconds." % (failSleep)
            time.sleep(failSleep)
            if failSleep < failMaxSleep:
                failSleep += failSleepIncrementor
