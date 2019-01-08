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
import logging
from lxml import etree
import os

# This project,  alphabetical by import source
from linkTaskManager import LinkTaskManager
from linkTaskManagerChoice import choicesAvailableForUnits, choicesAvailableForUnitsLock

from dicts import ReplacementDict, ChoicesDict
from main.models import UserProfile, Job
from workflow import TranslationLabel

from django.conf import settings as django_settings
from django.utils.six import text_type

LOGGER = logging.getLogger('archivematica.mcp.server')


class linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList(LinkTaskManager):
    def __init__(self, jobChainLink, unit):
        super(linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList,
              self).__init__(jobChainLink, unit)

        self._populate_choices()

        preConfiguredIndex = self.checkForPreconfiguredXML()
        if preConfiguredIndex is not None:
            self.jobChainLink.setExitMessage(Job.STATUS_COMPLETED_SUCCESSFULLY)
            self.proceedWithChoice(index=preConfiguredIndex, user_id=None)
        else:
            choicesAvailableForUnitsLock.acquire()
            self.jobChainLink.setExitMessage(Job.STATUS_AWAITING_DECISION)
            choicesAvailableForUnits[self.jobChainLink.UUID] = self
            choicesAvailableForUnitsLock.release()

    def _populate_choices(self):
        self.choices = []
        if not isinstance(self.jobChainLink.passVar, list):
            errmsg = "passVar is {} instead of expected list".format(
                type(self.jobChainLink.passVar))
            LOGGER.error(errmsg)
            raise Exception(errmsg)
        key = self.jobChainLink.link.config["execute"]
        index = 0
        for item in self.jobChainLink.passVar:
            LOGGER.debug('%s is ChoicesDict: %s',
                         item, isinstance(item, ChoicesDict))
            if isinstance(item, ChoicesDict):
                # For display, convert the ChoicesDict passVar into a list
                # of tuples: (index, description, replacement dict string)
                for description, value in item.items():
                    description = TranslationLabel(description)
                    self.choices.append(
                        (index, description, str({key: value})))
                    index += 1
                break
        else:
            errmsg = "ChoicesDict not found in passVar: {}".format(
                self.jobChainLink.passVar)
            LOGGER.error(errmsg)
            raise Exception(errmsg)

    def checkForPreconfiguredXML(self):
        """ Check the processing XML file for a pre-selected choice.

        Returns an index for self.choices if found, None otherwise. """
        sharedPath = django_settings.SHARED_DIRECTORY
        xmlFilePath = os.path.join(
            self.unit.currentPath.replace("%sharedPath%", sharedPath, 1),
            django_settings.PROCESSING_XML_FILE
        )
        try:
            tree = etree.parse(xmlFilePath)
            root = tree.getroot()
        except (etree.LxmlError, IOError):
            LOGGER.warning('Error parsing xml at %s for pre-configured choice', xmlFilePath, exc_info=True)
            return None
        for choice in root.findall(".//preconfiguredChoice"):
            # Find the choice whose text matches this link's description
            if choice.find("appliesTo").text == self.jobChainLink.pk:
                # Search self.choices for desired choice, return index of
                # matching choice
                desiredChoice = choice.find("goToChain").text
                for choice in self.choices:
                    index, description, replace_dict = choice
                    if desiredChoice == description or desiredChoice in replace_dict:
                        return index
        return None

    def xmlify(self):
        """Returns an etree XML representation of the choices available."""
        ret = etree.Element("choicesAvailableForUnit")
        etree.SubElement(ret, "UUID").text = self.jobChainLink.UUID
        ret.append(self.unit.xmlify())
        choices = etree.SubElement(ret, "choices")
        for index, description, __ in self.choices:
            choice = etree.SubElement(choices, "choice")
            etree.SubElement(choice, "chainAvailable").text = text_type(index)
            etree.SubElement(choice, "description").text = text_type(description)
        return ret

    def proceedWithChoice(self, index, user_id):
        if user_id:
            agent_id = UserProfile.objects.get(user_id=int(user_id)).agent_id
            agent_id = str(agent_id)
            self.unit.setVariable("activeAgent", agent_id, None)

        choicesAvailableForUnitsLock.acquire()
        try:
            del choicesAvailableForUnits[self.jobChainLink.UUID]
        except KeyError:
            pass
        choicesAvailableForUnitsLock.release()

        # get the one at index, and go with it.
        __, __, replace_dict = self.choices[int(index)]
        rd = ReplacementDict.fromstring(replace_dict)
        self.update_passvar_replacement_dict(rd)
        self.jobChainLink.linkProcessingComplete(0, passVar=self.jobChainLink.passVar)
