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

# Stdlib, alphabetical by import source
import ast
import datetime
import logging
from lxml import etree
import os
import sys
import time
import threading

# This project,  alphabetical by import source
from linkTaskManager import LinkTaskManager
import archivematicaMCP
from linkTaskManagerChoice import choicesAvailableForUnits
from linkTaskManagerChoice import choicesAvailableForUnitsLock
from linkTaskManagerChoice import waitingOnTimer
from passClasses import ReplacementDict, ChoicesDict
import databaseInterface

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematica.log",
    level=logging.INFO)

class linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList, self).__init__(jobChainLink, pk, unit)
        self.choices = []
        sql = sql = """SELECT execute FROM StandardTasksConfigs where pk = '%s'""" % (pk)
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        choiceIndex = 0
        while row != None:
            print row
            key = row[0]
            row = c.fetchone()
        sqlLock.release()
        if isinstance(self.jobChainLink.passVar, list):
            for item in self.jobChainLink.passVar:
                print item, "is ChoicesDict: ", isinstance(item, ChoicesDict)
                if isinstance(item, ChoicesDict):
                    for description, value in item.iteritems():
                        replacementDic_ = str({key: value})
                        self.choices.append((choiceIndex, description, replacementDic_))
                        choiceIndex += 1
                    break
            else:
                print >>sys.stderr, "self.jobChainLink.passVar", self.jobChainLink.passVar
                logging.error("ChoicesDict not found in passVar: {}".format(self.jobChainLink.passVar))
                raise Exception("ChoicesDict not found in passVar: {}".format(self.jobChainLink.passVar))
        else:
            logging.error("passVar is {} instead of expected list".format(
                type(self.jobChainLink.passVar)))
            raise Exception("passVar is {} instead of expected list".format(
                type(self.jobChainLink.passVar)))

        print "choices", self.choices

        preConfiguredChain = self.checkForPreconfiguredXML()
        if preConfiguredChain != None:
            if preConfiguredChain != waitingOnTimer:
                self.jobChainLink.setExitMessage("Completed successfully")
                rd = ReplacementDict(eval(preConfiguredChain))
                self.update_passvar_replacement_dict(rd)
                self.jobChainLink.linkProcessingComplete(0, passVar=self.jobChainLink.passVar)
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
                                rd = ReplacementDict(eval(ret))
                                if self.jobChainLink.passVar != None:
                                        if isinstance(self.jobChainLink.passVar, ReplacementDict):
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
                            print >>sys.stderr, "Error parsing xml for pre-configured choice"
            except Exception as inst:
                print >>sys.stderr, "Error parsing xml for pre-configured choice", inst
        return ret

    def xmlify(self):
        """Returns an etree XML representation of the choices available."""
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
        
        #get the one at index, and go with it.
        choiceIndex, description, replacementDic2 = self.choices[int(index)]
        rd = ReplacementDict(ast.literal_eval(replacementDic2))
        self.update_passvar_replacement_dict(rd)
        self.jobChainLink.linkProcessingComplete(0, passVar=self.jobChainLink.passVar)
