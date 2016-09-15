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
import sys
import time

from linkTaskManager import LinkTaskManager
import archivematicaMCP
from linkTaskManagerChoice import choicesAvailableForUnits
from linkTaskManagerChoice import choicesAvailableForUnitsLock
from linkTaskManagerChoice import waitingOnTimer

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from dicts import ReplacementDict
sys.path.append("/usr/share/archivematica/dashboard")
from main.models import MicroServiceChoiceReplacementDic, UserProfile

LOGGER = logging.getLogger('archivematica.mcp.server')

class linkTaskManagerReplacementDicFromChoice(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerReplacementDicFromChoice, self).__init__(jobChainLink, pk, unit)

        self.choices = []
        dicts = MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=str(jobChainLink.pk))
        for i, dic in enumerate(dicts):
            self.choices.append((i, dic.description, dic.replacementdic))

        preConfiguredChain = self.checkForPreconfiguredXML()
        if preConfiguredChain != None:
            if preConfiguredChain != waitingOnTimer:
                self.jobChainLink.setExitMessage("Completed successfully")
                rd = ReplacementDict.fromstring(preConfiguredChain)
                self.update_passvar_replacement_dict(rd)
                self.jobChainLink.linkProcessingComplete(0, passVar=self.jobChainLink.passVar)
            else:
                LOGGER.info('Waiting on delay to resume processing on unit %s', unit)
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
                for preconfiguredChoice in root.findall(".//preconfiguredChoice"):
                    if preconfiguredChoice.find("appliesTo").text == self.jobChainLink.pk:
                        desiredChoice = preconfiguredChoice.find("goToChain").text
                        dic = MicroServiceChoiceReplacementDic.objects.get(id=desiredChoice, choiceavailableatlink=self.jobChainLink.pk)
                        ret = dic.replacementdic
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
                                LOGGER.info('Time to go: %s', timeToGo)
                                self.jobChainLink.setExitMessage("Waiting till: " + datetime.datetime.fromtimestamp((nowTime + timeToGo)).ctime())
                                rd = ReplacementDict.fromstring(ret)
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

                        except Exception:
                            LOGGER.info('Error parsing XML', exc_info=True)

            except Exception:
                LOGGER.warning('Error parsing xml at %s for pre-configured choice', xmlFilePath, exc_info=True)
        return ret

    def xmlify(self):
        """Returns an etree XML representation of the choices available."""
        ret = etree.Element("choicesAvailableForUnit")
        etree.SubElement(ret, "UUID").text = self.jobChainLink.UUID
        ret.append(self.unit.xmlify())
        choices = etree.SubElement(ret, "choices")
        for chainAvailable, description, rd in self.choices:
            choice = etree.SubElement(choices, "choice")
            etree.SubElement(choice, "chainAvailable").text = chainAvailable.__str__()
            etree.SubElement(choice, "description").text = description

        return ret

    def proceedWithChoice(self, index, user_id):
        if user_id:
            agent_id = UserProfile.objects.get(user_id=int(user_id)).agent_id
            agent_id = str(agent_id)
            self.unit.setVariable("activeAgent", agent_id, None)

        choicesAvailableForUnitsLock.acquire()
        del choicesAvailableForUnits[self.jobChainLink.UUID]
        choicesAvailableForUnitsLock.release()

        # get the one at index, and go with it.
        choiceIndex, description, replacementDic2 = self.choices[int(index)]
        rd = ReplacementDict.fromstring(replacementDic2)
        self.update_passvar_replacement_dict(rd)
        self.jobChainLink.linkProcessingComplete(0, passVar=self.jobChainLink.passVar)
