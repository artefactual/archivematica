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
import threading
import time

from linkTaskManager import LinkTaskManager
from executeOrRunSubProcess import executeOrRun
import jobChain
from utils import log_exceptions
import archivematicaMCP

from django_mysqlpool import auto_close_db
from archivematicaFunctions import unicodeToStr

from main.models import UserProfile, Job

waitingOnTimer = "waitingOnTimer"

LOGGER = logging.getLogger('archivematica.mcp.server')


class linkTaskManagerChoice(LinkTaskManager):
    """Used to get a selection, from a list of chains, to process"""
    def __init__(self, jobChainLink):
        super(linkTaskManagerChoice, self).__init__(jobChainLink)

        self.populate_choices()

        self.delayTimerLock = threading.Lock()
        self.delayTimer = None

        preConfiguredChain = self.checkForPreconfiguredXML()
        if preConfiguredChain is not None:
            time.sleep(archivematicaMCP.config.getint('MCPServer', "waitOnAutoApprove"))
            self.jobChainLink.setExitMessage(Job.STATUS_COMPLETED_SUCCESSFULLY)
            jobChain.jobChain(self.unit, preConfiguredChain, self.workflow, self.unit_choices)

        else:
            with self.unit_choices:
                if self.delayTimer is None:
                    self.jobChainLink.setExitMessage(Job.STATUS_AWAITING_DECISION)
                self.unit_choices[self.jobChainLink.UUID] = self

    def get_config(self):
        return self.link.config.userChoice

    def populate_choices(self):
        self.choices = []
        config = self.get_config()
        for chain_id in config.chainIds:
            chain = self.workflow.chains[chain_id]
            if chain is None:
                continue
            self.choices.append((chain_id, chain.description))

    def checkForPreconfiguredXML(self):
        desiredChoice = None
        xmlFilePath = os.path.join(
            self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1),
            archivematicaMCP.config.get('MCPServer', "processingXMLFile")
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
                for preconfiguredChoice in root.findall(".//preconfiguredChoice"):
                    if preconfiguredChoice.find("appliesTo").text == self.link.id:
                        desiredChoice = preconfiguredChoice.find("goToChain").text
                        try:
                            # <delay unitAtime="yes">30</delay>
                            delayXML = preconfiguredChoice.find("delay")
                            if delayXML is not None:
                                unitAtimeXML = delayXML.get("unitCtime")
                            else:
                                unitAtimeXML = None
                            if unitAtimeXML is not None and unitAtimeXML.lower() != "no":
                                delaySeconds = int(delayXML.text)
                                unitTime = os.path.getmtime(self.unit.currentPath.replace('%sharedPath%', archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1))
                                nowTime = time.time()
                                timeDifference = nowTime - unitTime
                                timeToGo = delaySeconds - timeDifference
                                LOGGER.info('Time to go: %s', timeToGo)
                                self.jobChainLink.setExitMessage("Waiting till: " + datetime.datetime.fromtimestamp((nowTime + timeToGo)).ctime())

                                t = threading.Timer(timeToGo, self.safe_proceed_with_choice, args=[desiredChoice, None], kwargs={"delayTimerStart": True})
                                t.daemon = True
                                self.delayTimer = t
                                t.start()
                                return None

                        except Exception:
                            LOGGER.info('Error parsing XML', exc_info=True)
            except Exception:
                LOGGER.warning('Error parsing xml at %s for pre-configured choice', xmlFilePath, exc_info=True)
        LOGGER.info('Using preconfigured choice %s for %s', desiredChoice, self.link.id)
        return desiredChoice

    def safe_proceed_with_choice(self, *args, **kwargs):
        """
        Wrapper of proceed_with_choice with a lock on unit_choices.
        """
        with self.unit_choices:
            return self.proceed_with_choice(*args, **kwargs)

    @log_exceptions
    @auto_close_db
    def proceed_with_choice(self, chain, user_id, delayTimerStart=False):
        if user_id is not None:
            agent_id = UserProfile.objects.get(user_id=int(user_id)).agent_id
            agent_id = str(agent_id)
            self.unit.setVariable("activeAgent", agent_id, None)

        del self.unit_choices[self.jobChainLink.UUID]
        with self.delayTimerLock:
            if self.delayTimer is not None and not delayTimerStart:
                self.delayTimer.cancel()
                self.delayTimer = None

        self.jobChainLink.setExitMessage(Job.STATUS_COMPLETED_SUCCESSFULLY)
        LOGGER.info('Using user selected chain %s', chain)
        jobChain.jobChain(self.unit, chain, self.workflow, self.unit_choices)
