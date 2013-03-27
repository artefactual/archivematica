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

import databaseInterface
import datetime
import threading
import uuid
import sys
import time
#select * from MicroServiceChainChoice JOIN MicroServiceChains on chainAvailable = MicroServiceChains.pk;
#| pk | choiceAvailableAtLink | chainAvailable | pk | startingLink | description

from linkTaskManager import linkTaskManager
from taskStandard import taskStandard
from executeOrRunSubProcess import executeOrRun
import jobChain
import databaseInterface
import lxml.etree as etree
import os
import archivematicaMCP
global choicesAvailableForUnits
choicesAvailableForUnits = {}
choicesAvailableForUnitsLock = threading.Lock()
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from archivematicaFunctions import unicodeToStr

waitingOnTimer="waitingOnTimer"

class linkTaskManagerChoice:
    def __init__(self, jobChainLink, pk, unit):
        self.choices = []
        self.pk = pk
        self.jobChainLink = jobChainLink
        self.UUID = uuid.uuid4().__str__()
        self.unit = unit
        self.delayTimerLock = threading.Lock()
        self.delayTimer = None
        sql = """SELECT chainAvailable, description FROM MicroServiceChainChoice JOIN MicroServiceChains on chainAvailable = MicroServiceChains.pk WHERE choiceAvailableAtLink = '%s' ORDER BY MicroServiceChainChoice.pk;""" % (jobChainLink.pk.__str__())
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            print row
            chainAvailable = row[0]
            description = row[1]
            self.choices.append((chainAvailable, description,))
            row = c.fetchone()
        sqlLock.release()

        preConfiguredChain = self.checkForPreconfiguredXML()
        if preConfiguredChain != None:
            time.sleep(archivematicaMCP.config.getint('MCPServer', "waitOnAutoApprove"))
            self.jobChainLink.setExitMessage("Completed successfully")
            jobChain.jobChain(self.unit, preConfiguredChain)

        else:
            choicesAvailableForUnitsLock.acquire()
            if self.delayTimer == None:
                self.jobChainLink.setExitMessage('Awaiting decision')
            choicesAvailableForUnits[self.jobChainLink.UUID] = self
            choicesAvailableForUnitsLock.release()

    def checkForPreconfiguredXML(self):
        ret = None
        xmlFilePath = os.path.join( \
                                        self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1), \
                                        archivematicaMCP.config.get('MCPServer', "processingXMLFile") \
                                    )
        xmlFilePath = unicodeToStr(xmlFilePath)
        if os.path.isfile(xmlFilePath):
            # For a list of items with pks:
            # SELECT TasksConfigs.description, choiceAvailableAtLink, ' ' AS 'SPACE', MicroServiceChains.description, chainAvailable FROM MicroServiceChainChoice Join MicroServiceChains on MicroServiceChainChoice.chainAvailable = MicroServiceChains.pk Join MicroServiceChainLinks on MicroServiceChainLinks.pk = MicroServiceChainChoice.choiceAvailableAtLink Join TasksConfigs on TasksConfigs.pk = MicroServiceChainLinks.currentTask ORDER BY choiceAvailableAtLink desc;
            try:
                command = "sudo chmod 774 \"" + xmlFilePath + "\""
                if isinstance(command, unicode):
                    command = command.encode("utf-8")
                exitCode, stdOut, stdError = executeOrRun("command", command, "", printing=False)
                tree = etree.parse(xmlFilePath)
                root = tree.getroot()
                for preconfiguredChoice in root.find("preconfiguredChoices"):
                    #if int(preconfiguredChoice.find("appliesTo").text) == self.jobChainLink.pk:
                    if preconfiguredChoice.find("appliesTo").text == self.jobChainLink.description:
                        desiredChoice = preconfiguredChoice.find("goToChain").text
                        sql = """SELECT MicroServiceChains.pk FROM MicroServiceChainChoice Join MicroServiceChains on MicroServiceChainChoice.chainAvailable = MicroServiceChains.pk WHERE MicroServiceChains.description = '%s' AND MicroServiceChainChoice.choiceAvailableAtLink = '%s';""" % (desiredChoice, self.jobChainLink.pk.__str__())
                        c, sqlLock = databaseInterface.querySQL(sql)
                        row = c.fetchone()
                        while row != None:
                            ret = row[0]
                            row = c.fetchone()
                        sqlLock.release()
                        try:
                            #<delay unitAtime="yes">30</delay>
                            delayXML = preconfiguredChoice.find("delay")
                            unitAtimeXML = delayXML.get("unitCtime")
                            if unitAtimeXML != None and unitAtimeXML.lower() != "no":
                                delaySeconds=int(delayXML.text)
                                unitTime = os.path.getmtime(self.unit.currentPath.replace("%sharedPath%", \
                                               archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1))
                                nowTime=time.time()
                                timeDifference = nowTime - unitTime
                                timeToGo = delaySeconds - timeDifference
                                print "time to go:", timeToGo
                                #print "that will be: ", (nowTime + timeToGo)
                                self.jobChainLink.setExitMessage("Waiting till: " + datetime.datetime.fromtimestamp((nowTime + timeToGo)).ctime())

                                t = threading.Timer(timeToGo, self.proceedWithChoice, args=[ret, None], kwargs={"delayTimerStart":True})
                                t.daemon = True
                                self.delayTimer = t
                                t.start()
                                return None

                        except Exception as inst:
                            print >>sys.stderr, "Error parsing xml:"
                            print >>sys.stderr, type(inst)
                            print >>sys.stderr, inst.args

            except Exception as inst:
                print >>sys.stderr, "Error parsing xml:"
                print >>sys.stderr, type(inst)
                print >>sys.stderr, inst.args
        return ret

    def xmlify(self):
        ret = etree.Element("choicesAvailableForUnit")
        etree.SubElement(ret, "UUID").text = self.jobChainLink.UUID
        ret.append(self.unit.xmlify())
        choices = etree.SubElement(ret, "choices")
        for chainAvailable, description in self.choices:
            choice = etree.SubElement(choices, "choice")
            etree.SubElement(choice, "chainAvailable").text = chainAvailable.__str__()
            etree.SubElement(choice, "description").text = description
        return ret



    def proceedWithChoice(self, chain, agent, delayTimerStart=False):
        if agent:
            self.unit.setVariable("activeAgent", agent, None)
        choicesAvailableForUnitsLock.acquire()
        del choicesAvailableForUnits[self.jobChainLink.UUID]
        self.delayTimerLock.acquire()
        if self.delayTimer != None and not delayTimerStart:
            self.delayTimer.cancel()
            self.delayTimer = None
        self.delayTimerLock.release()
        choicesAvailableForUnitsLock.release()
        self.jobChainLink.setExitMessage("Completed successfully")
        jobChain.jobChain(self.unit, chain)
