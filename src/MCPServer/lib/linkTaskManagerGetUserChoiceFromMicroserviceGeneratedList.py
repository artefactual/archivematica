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

from linkTaskManager import linkTaskManager
from taskStandard import taskStandard
import jobChain
import databaseInterface
import lxml.etree as etree
import os
import archivematicaMCP
from linkTaskManagerChoice import choicesAvailableForUnits
from linkTaskManagerChoice import choicesAvailableForUnitsLock
from linkTaskManagerChoice import waitingOnTimer
from linkTaskManagerGetMicroserviceGeneratedListInStdOut import choicesDic
from passClasses import replacementDic

class linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList:
    def __init__(self, jobChainLink, pk, unit):
        self.choices = []
        self.pk = pk
        self.jobChainLink = jobChainLink
        self.UUID = uuid.uuid4().__str__()
        self.unit = unit
        sql = sql = """SELECT execute FROM StandardTasksConfigs where pk = '%s'""" % (pk)
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        choiceIndex = 0
        while row != None:
            print row
            key = row[0]
            #self.choices.append((choiceIndex, description_, replacementDic_))
            row = c.fetchone()
            #choiceIndex += 1
        sqlLock.release()
        if isinstance(self.jobChainLink.passVar, list):
            found = False
            for item in self.jobChainLink.passVar:
                print >>sys.stderr
                print >>sys.stderr
                print >>sys.stderr
                print >>sys.stderr, isinstance(item, choicesDic), item
                if isinstance(item, choicesDic):
                    for description_, value in item.dic.iteritems():
                        replacementDic_ = {key: value}.__str__()
                        self.choices.append((choiceIndex, description_, replacementDic_))
                        choiceIndex += 1
                    found = True
                    break
            if not found:
                print >>sys.stderr, "self.jobChainLink.passVar", self.jobChainLink.passVar
                throw(exception2)
        else:
            throw(exception)

        print "choices", self.choices

        preConfiguredChain = self.checkForPreconfiguredXML()
        if preConfiguredChain != None:
            if preConfiguredChain != waitingOnTimer:
                #time.sleep(archivematicaMCP.config.getint('MCPServer', "waitOnAutoApprove"))
                #print "checking for xml file for processing rules. TODO"
                self.jobChainLink.setExitMessage("Completed successfully")
                #jobChain.jobChain(self.unit, preConfiguredChain)
                rd = replacementDic(eval(preConfiguredChain))
                if self.jobChainLink.passVar != None:
                    if isinstance(self.jobChainLink.passVar, list):
                        found = False
                        for passVar in self.jobChainLink.passVar:
                            if isinstance(self.jobChainLink.passVar, replacementDic):
                                new = {}
                                new.update(self.jobChainLink.passVar.dic)
                                new.update(rd.dic)
                                rd.dic = [new]
                                found = True
                                break
                        if not found:
                            self.jobChainLink.passVar.append(rd)
                            rd = self.jobChainLink.passVar 
                else:
                    rd = [rd]
                self.jobChainLink.linkProcessingComplete(0, rd)
            else:
                print "waiting on delay to resume processing on unit:", unit
        else:
            choicesAvailableForUnitsLock.acquire()
            self.jobChainLink.setExitMessage('Awaiting decision')
            choicesAvailableForUnits[self.jobChainLink.UUID] = self
            choicesAvailableForUnitsLock.release()

    def checkForPreconfiguredXML(self):
        ret = None
        xmlFilePath = os.path.join( \
                                        self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1) + "/", \
                                        archivematicaMCP.config.get('MCPServer', "processingXMLFile") \
                                    )

        if os.path.isfile(xmlFilePath):
            # For a list of items with pks:
            # SELECT TasksConfigs.description, choiceAvailableAtLink, ' ' AS 'SPACE', MicroServiceChains.description, chainAvailable FROM MicroServiceChainChoice Join MicroServiceChains on MicroServiceChainChoice.chainAvailable = MicroServiceChains.pk Join MicroServiceChainLinks on MicroServiceChainLinks.pk = MicroServiceChainChoice.choiceAvailableAtLink Join TasksConfigs on TasksConfigs.pk = MicroServiceChainLinks.currentTask ORDER BY choiceAvailableAtLink desc;
            try:
                tree = etree.parse(xmlFilePath)
                root = tree.getroot()
                for preconfiguredChoice in root.find("preconfiguredChoices"):
                    #if int(preconfiguredChoice.find("appliesTo").text) == self.jobChainLink.pk:
                    if preconfiguredChoice.find("appliesTo").text == self.jobChainLink.description:
                        desiredChoice = preconfiguredChoice.find("goToChain").text
                        sql = """SELECT MicroServiceChoiceReplacementDic.replacementDic FROM MicroServiceChoiceReplacementDic  WHERE MicroServiceChoiceReplacementDic.description = '%s' AND MicroServiceChoiceReplacementDic.choiceAvailableAtLink = '%s';""" % (desiredChoice, self.jobChainLink.pk.__str__())
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
                                rd = replacementDic(eval(ret))
                                if self.jobChainLink.passVar != None:
                                        if isinstance(self.jobChainLink.passVar, replacementDic):
                                            new = {}
                                            new.update(self.jobChainLink.passVar.dic)
                                            new.update(rd.dic)
                                            rd.dic = new
                                t = threading.Timer(timeToGo, self.jobChainLink.linkProcessingComplete, args=[0, rd], kwargs={})
                                t.daemon = True
                                t.start()

                                t2 = threading.Timer(timeToGo, self.jobChainLink.setExitMessage, args=["Completed successfully"], kwargs={})
                                t2.start()
                                return waitingOnTimer

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
        #print "xmlify"
        ret = etree.Element("choicesAvailableForUnit")
        etree.SubElement(ret, "UUID").text = self.jobChainLink.UUID
        ret.append(self.unit.xmlify())
        choices = etree.SubElement(ret, "choices")
        for chainAvailable, description, rd in self.choices:
            choice = etree.SubElement(choices, "choice")
            etree.SubElement(choice, "chainAvailable").text = chainAvailable.__str__()
            etree.SubElement(choice, "description").text = description
        #print etree.tostring(ret)
        return ret



    def proceedWithChoice(self, index, agent):
        if agent:
            self.unit.setVariable("activeAgent", agent, None)
        choicesAvailableForUnitsLock.acquire()
        del choicesAvailableForUnits[self.jobChainLink.UUID]
        choicesAvailableForUnitsLock.release()
        #while archivematicaMCP.transferDMovedFromCounter.value != 0:
        #    print "Waiting for all files to finish updating their location in the database"
        #    print transferD.movedFrom
        #    time.sleep(1)
        
        #get the one at index, and go with it.
        choiceIndex, description, replacementDic2 = self.choices[int(index)]
        rd = replacementDic(eval(replacementDic2))
        if self.jobChainLink.passVar != None:
            if isinstance(self.jobChainLink.passVar, list):
                found = False
                for passVar in self.jobChainLink.passVar:
                    if isinstance(self.jobChainLink.passVar, replacementDic):
                        new = {}
                        new.update(self.jobChainLink.passVar.dic)
                        new.update(rd.dic)
                        rd.dic = [new]
                        found = True
                        break
                if not found:
                    self.jobChainLink.passVar.append(rd)
                    rd = self.jobChainLink.passVar 
        else:
            rd = [rd]
        self.jobChainLink.linkProcessingComplete(0, rd)
        