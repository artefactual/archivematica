#!/usr/bin/env python2

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

import datetime
import logging
import lxml.etree as etree
import os
import sys
import threading
import time

from linkTaskManager import LinkTaskManager
from executeOrRunSubProcess import executeOrRun
import jobChain
from utils import log_exceptions
import archivematicaMCP
global choicesAvailableForUnits
choicesAvailableForUnits = {}
choicesAvailableForUnitsLock = threading.Lock()

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from django_mysqlpool import auto_close_db
from archivematicaFunctions import unicodeToStr

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import MicroServiceChainChoice, UserProfile, Job

waitingOnTimer="waitingOnTimer"

LOGGER = logging.getLogger('archivematica.mcp.server')

class linkTaskManagerChoice(LinkTaskManager):
    """Used to get a selection, from a list of chains, to process"""
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerChoice, self).__init__(jobChainLink, pk, unit)
        self.choices = []
        self.delayTimerLock = threading.Lock()
        self.delayTimer = None

        choices = MicroServiceChainChoice.objects.filter(choiceavailableatlink_id=str(jobChainLink.pk))
        for choice in choices:
            self.choices.append((choice.chainavailable_id, choice.chainavailable.description))

        preConfiguredChain = self.checkForPreconfiguredXML()
        if preConfiguredChain != None:
            time.sleep(archivematicaMCP.config.getint('MCPServer', "waitOnAutoApprove"))
            self.jobChainLink.setExitMessage(Job.STATUS_COMPLETED_SUCCESSFULLY)
            jobChain.jobChain(self.unit, preConfiguredChain)

        else:
            choicesAvailableForUnitsLock.acquire()
            if self.delayTimer == None:
                self.jobChainLink.setExitMessage(Job.STATUS_AWAITING_DECISION)
            choicesAvailableForUnits[self.jobChainLink.UUID] = self
            choicesAvailableForUnitsLock.release()

    def checkForPreconfiguredXML(self):
        desiredChoice = None
        xmlFilePath = os.path.join( \
                                        self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1), \
                                        archivematicaMCP.config.get('MCPServer', "processingXMLFile") \
                                    )
        xmlFilePath = unicodeToStr(xmlFilePath)
        if os.path.isfile(xmlFilePath):
            # For a list of items with pks:
            # SELECT TasksConfigs.description, choiceAvailableAtLink, ' ' AS 'SPACE', MicroServiceChains.description, chainAvailable FROM MicroServiceChainChoice Join MicroServiceChains on MicroServiceChainChoice.chainAvailable = MicroServiceChains.pk Join MicroServiceChainLinks on MicroServiceChainLinks.pk = MicroServiceChainChoice.choiceAvailableAtLink Join TasksConfigs on TasksConfigs.pk = MicroServiceChainLinks.currentTask ORDER BY choiceAvailableAtLink desc;
            try:
                tree = etree.parse(xmlFilePath)
                root = tree.getroot()
                for preconfiguredChoice in root.findall(".//preconfiguredChoice"):
                    if preconfiguredChoice.find("appliesTo").text == self.jobChainLink.pk:
                        desiredChoice = preconfiguredChoice.find("goToChain").text
                        try:
                            #<delay unitAtime="yes">30</delay>
                            delayXML = preconfiguredChoice.find("delay")
                            if delayXML is not None:
                                unitAtimeXML = delayXML.get("unitCtime")
                            else:
                                unitAtimeXML = None
                            if unitAtimeXML is not None and unitAtimeXML.lower() != "no":
                                delaySeconds=int(delayXML.text)
                                unitTime = os.path.getmtime(self.unit.currentPath.replace("%sharedPath%", \
                                               archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1))
                                nowTime=time.time()
                                timeDifference = nowTime - unitTime
                                timeToGo = delaySeconds - timeDifference
                                LOGGER.info('Time to go: %s', timeToGo)
                                self.jobChainLink.setExitMessage("Waiting till: " + datetime.datetime.fromtimestamp((nowTime + timeToGo)).ctime())

                                t = threading.Timer(timeToGo, self.proceedWithChoice, args=[desiredChoice, None], kwargs={"delayTimerStart":True})
                                t.daemon = True
                                self.delayTimer = t
                                t.start()
                                return None

                        except Exception:
                            LOGGER.info('Error parsing XML', exc_info=True)
            except Exception:
                LOGGER.warning('Error parsing xml at %s for pre-configured choice', xmlFilePath, exc_info=True)
        LOGGER.info('Using preconfigured choice %s for %s', desiredChoice, self.jobChainLink.pk)
        return desiredChoice

    def xmlify(self):
        """Returns an etree XML representation of the choices available."""
        ret = etree.Element("choicesAvailableForUnit")
        etree.SubElement(ret, "UUID").text = self.jobChainLink.UUID
        ret.append(self.unit.xmlify())
        choices = etree.SubElement(ret, "choices")
        for chainAvailable, description in self.choices:
            choice = etree.SubElement(choices, "choice")
            etree.SubElement(choice, "chainAvailable").text = chainAvailable.__str__()
            etree.SubElement(choice, "description").text = description
        return ret

    @log_exceptions
    @auto_close_db
    def proceedWithChoice(self, chain, user_id, delayTimerStart=False):
        if user_id is not None:
            agent_id = UserProfile.objects.get(user_id=int(user_id)).agent_id
            agent_id = str(agent_id)
            self.unit.setVariable("activeAgent", agent_id, None)

        choicesAvailableForUnitsLock.acquire()
        del choicesAvailableForUnits[self.jobChainLink.UUID]
        self.delayTimerLock.acquire()
        if self.delayTimer != None and not delayTimerStart:
            self.delayTimer.cancel()
            self.delayTimer = None
        self.delayTimerLock.release()
        choicesAvailableForUnitsLock.release()
        self.jobChainLink.setExitMessage(Job.STATUS_COMPLETED_SUCCESSFULLY)
        LOGGER.info('Using user selected chain %s', chain)
        jobChain.jobChain(self.unit, chain)
