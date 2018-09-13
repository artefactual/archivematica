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

from utils import choice_unifier
from linkTaskManager import LinkTaskManager
from linkTaskManagerChoice import choicesAvailableForUnits, choicesAvailableForUnitsLock, waitingOnTimer

from dicts import ReplacementDict
from main.models import DashboardSetting, Job, MicroServiceChainLink, MicroServiceChoiceReplacementDic, StandardTaskConfig, UserProfile
from django.conf import settings as django_settings

LOGGER = logging.getLogger('archivematica.mcp.server')


class linkTaskManagerReplacementDicFromChoice(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerReplacementDicFromChoice, self).__init__(jobChainLink, pk, unit)

        self.choices = []
        dicts = MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=str(jobChainLink.pk))
        for i, dic in enumerate(dicts):
            self.choices.append((i, dic.description, dic.replacementdic))

        # There are MicroServiceChoiceReplacementDic links with no
        # replacements (``self.choices`` has zero elements at this point). This
        # is true for the following chain links:
        #
        #   - ``Choose Config for Archivists Toolkit DIP Upload``
        #   - ``Choose config for AtoM DIP upload``
        #   - ``Choose Config for ArchivesSpace DIP Upload``
        #
        # The only purpose of these links is to  load settings from the
        # Dashboard configuration store (``DashboardSetting``), e.g.
        # connection details or credentials that are needed to perform the
        # upload of the DIP to the remote system.
        #
        # Once the settings are loaded, we proceed with the next chain link
        # automatically instead of prompting the user with a single choice
        # which was considered inconvenient and confusing. In the future, it
        # should be possible to prompt the user only if we want to have the
        # user decide between multiple configurations, e.g. more than one
        # AtoM instance is available and the user wants to decide which one is
        # going to be used.
        rdict = self._get_dashboard_setting_choice()
        if rdict and not self.choices:
            LOGGER.debug('Found Dashboard settings for this task, proceed.')
            self.update_passvar_replacement_dict(rdict)
            self.jobChainLink.linkProcessingComplete(
                0, passVar=self.jobChainLink.passVar)
            return

        preConfiguredChain = self.checkForPreconfiguredXML()
        if preConfiguredChain is not None:
            if preConfiguredChain != waitingOnTimer:
                self.jobChainLink.setExitMessage(Job.STATUS_COMPLETED_SUCCESSFULLY)
                rd = ReplacementDict.fromstring(preConfiguredChain)
                self.update_passvar_replacement_dict(rd)
                self.jobChainLink.linkProcessingComplete(0, passVar=self.jobChainLink.passVar)
            else:
                LOGGER.info('Waiting on delay to resume processing on unit %s', unit)
        else:
            choicesAvailableForUnitsLock.acquire()
            self.jobChainLink.setExitMessage(Job.STATUS_AWAITING_DECISION)
            choicesAvailableForUnits[self.jobChainLink.UUID] = self
            choicesAvailableForUnitsLock.release()

    def _format_items(self, items):
        """Wrap replacement items with the ``%`` wildcard character."""
        return {'%{}%'.format(key): value
                for key, value in items.items()}

    def _get_dashboard_setting_choice(self):
        """Load settings associated to this task into a ``ReplacementDict``.

        The model used (``DashboardSetting``) is a shared model.
        """
        try:
            mscl = MicroServiceChainLink.objects.get(id=self.jobChainLink.pk)
            task_id = mscl.defaultnextchainlink.currenttask.tasktypepkreference
            stc = StandardTaskConfig.objects.get(id=task_id)
        except (MicroServiceChainLink.DoesNotExist,
                StandardTaskConfig.DoesNotExist,
                AttributeError):
            return
        args = DashboardSetting.objects.get_dict(stc.execute)
        if not args:
            return
        return ReplacementDict(self._format_items(args))

    def checkForPreconfiguredXML(self):
        ret = None
        xmlFilePath = os.path.join(
            self.unit.currentPath.replace(
                "%sharedPath%",
                django_settings.SHARED_DIRECTORY, 1) + "/",
            django_settings.PROCESSING_XML_FILE
        )

        if os.path.isfile(xmlFilePath):
            # For a list of items with pks:
            # SELECT TasksConfigs.description, choiceAvailableAtLink, ' ' AS 'SPACE', MicroServiceChains.description, chainAvailable FROM MicroServiceChainChoice Join MicroServiceChains on MicroServiceChainChoice.chainAvailable = MicroServiceChains.pk Join MicroServiceChainLinks on MicroServiceChainLinks.pk = MicroServiceChainChoice.choiceAvailableAtLink Join TasksConfigs on TasksConfigs.pk = MicroServiceChainLinks.currentTask ORDER BY choiceAvailableAtLink desc;
            try:
                this_choice_point = choice_unifier.get(
                    self.jobChainLink.pk, self.jobChainLink.pk)
                tree = etree.parse(xmlFilePath)
                root = tree.getroot()
                for preconfiguredChoice in root.findall(".//preconfiguredChoice"):
                    if preconfiguredChoice.find("appliesTo").text == this_choice_point:
                        desiredChoice = preconfiguredChoice.find("goToChain").text
                        desiredChoice = choice_unifier.get(
                            desiredChoice, desiredChoice)
                        dic = MicroServiceChoiceReplacementDic.objects.get(
                            id=desiredChoice,
                            choiceavailableatlink=this_choice_point)
                        ret = dic.replacementdic
                        try:
                            # <delay unitAtime="yes">30</delay>
                            delayXML = preconfiguredChoice.find("delay")
                            unitAtimeXML = None
                            if delayXML:
                                unitAtimeXML = delayXML.get("unitCtime")
                            if unitAtimeXML is not None and unitAtimeXML.lower() != "no":
                                delaySeconds = int(delayXML.text)
                                unitTime = os.path.getmtime(
                                    self.unit.currentPath.replace(
                                        "%sharedPath%",
                                        django_settings.SHARED_DIRECTORY,
                                        1))
                                nowTime = time.time()
                                timeDifference = nowTime - unitTime
                                timeToGo = delaySeconds - timeDifference
                                LOGGER.info('Time to go: %s', timeToGo)
                                self.jobChainLink.setExitMessage("Waiting till: " + datetime.datetime.fromtimestamp((nowTime + timeToGo)).ctime())
                                rd = ReplacementDict.fromstring(ret)
                                if self.jobChainLink.passVar is not None:
                                    if isinstance(self.jobChainLink.passVar, ReplacementDict):
                                        new = {}
                                        new.update(self.jobChainLink.passVar.dic)
                                        new.update(rd.dic)
                                        rd.dic = new
                                t = threading.Timer(timeToGo, self.jobChainLink.linkProcessingComplete, args=[0, rd], kwargs={})
                                t.daemon = True
                                t.start()

                                t2 = threading.Timer(timeToGo, self.jobChainLink.setExitMessage, args=[Job.STATUS_COMPLETED_SUCCESSFULLY], kwargs={})
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
