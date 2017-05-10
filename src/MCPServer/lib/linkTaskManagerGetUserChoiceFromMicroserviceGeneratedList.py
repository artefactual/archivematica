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

# Stdlib, alphabetical by import source
import logging
from lxml import etree
import os

# This project,  alphabetical by import source
from linkTaskManager import LinkTaskManager
import archivematicaMCP

from dicts import ReplacementDict, ChoicesDict

from main.models import UserProfile, Job

LOGGER = logging.getLogger('archivematica.mcp.server')


class linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList(LinkTaskManager):
    def __init__(self, jobChainLink):
        super(linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList, self).__init__(jobChainLink)

        self.populate_choices()

        preConfiguredIndex = self.checkForPreconfiguredXML()
        with self.unit_choices:
            if preConfiguredIndex is not None:
                self.jobChainLink.setExitMessage(Job.STATUS_COMPLETED_SUCCESSFULLY)
                self.proceed_with_choice(index=preConfiguredIndex, user_id=None)
            else:
                self.jobChainLink.setExitMessage(Job.STATUS_AWAITING_DECISION)
                self.unit_choices[self.jobChainLink.UUID] = self

    def get_config(self):
        return self.link.config.standard

    def populate_choices(self):
        config = self.get_config()
        self.choices = []
        choiceIndex = 0
        if isinstance(self.jobChainLink.passVar, list):
            for item in self.jobChainLink.passVar:
                LOGGER.debug('%s is ChoicesDict: %s', item, isinstance(item, ChoicesDict))
                if isinstance(item, ChoicesDict):
                    # For display, convert the ChoicesDict passVar into a list
                    # of tuples: (index, description, replacement dict string)
                    for description, value in item.items():
                        replacementDic_ = str({config.execute: value})
                        self.choices.append((choiceIndex, {'en': description}, replacementDic_))
                        choiceIndex += 1
                    break
            else:
                LOGGER.error("ChoicesDict not found in passVar: %s", self.jobChainLink.passVar)
                raise Exception("ChoicesDict not found in passVar: {}".format(self.jobChainLink.passVar))
        else:
            LOGGER.error("passVar is %s instead of expected list", type(self.jobChainLink.passVar))
            raise Exception("passVar is {} instead of expected list".format(type(self.jobChainLink.passVar)))

        LOGGER.info('Choices: %s', self.choices)

    def checkForPreconfiguredXML(self):
        """ Check the processing XML file for a pre-selected choice.

        Returns an index for self.choices if found, None otherwise. """
        sharedPath = archivematicaMCP.config.get('MCPServer', "sharedDirectory")
        xmlFilePath = os.path.join(
            self.unit.currentPath.replace("%sharedPath%", sharedPath, 1),
            archivematicaMCP.config.get('MCPServer', "processingXMLFile")
        )
        try:
            tree = etree.parse(xmlFilePath)
            root = tree.getroot()
        except (etree.LxmlError, IOError):
            LOGGER.warning('Error parsing xml at %s for pre-configured choice', xmlFilePath, exc_info=True)
            return None
        for choice in root.findall(".//preconfiguredChoice"):
            # Find the choice whose text matches this link's description
            if choice.find("appliesTo").text == self.link.id:
                # Search self.choices for desired choice, return index of
                # matching choice
                desiredChoice = choice.find("goToChain").text
                for choice in self.choices:
                    index, description, replace_dict = choice
                    if desiredChoice == description or desiredChoice in replace_dict:
                        return index
        return None

    def proceed_with_choice(self, index, user_id):
        if user_id:
            agent_id = UserProfile.objects.get(user_id=int(user_id)).agent_id
            agent_id = str(agent_id)
            self.unit.setVariable("activeAgent", agent_id, None)

        del self.unit_choices[self.jobChainLink.UUID]

        # get the one at index, and go with it.
        _, _, replace_dict = self.choices[int(index)]
        rd = ReplacementDict.fromstring(replace_dict)
        self.update_passvar_replacement_dict(rd)
        self.jobChainLink.linkProcessingComplete(0, passVar=self.jobChainLink.passVar)
