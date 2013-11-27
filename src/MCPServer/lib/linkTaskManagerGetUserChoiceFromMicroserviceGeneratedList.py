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
import logging
from lxml import etree
import os
import sys

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
                    # For display, convert the ChoicesDict passVar into a list
                    # of tuples: (index, description, replacement dict string)
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

        print "LTM GetUserChoiceFromMicroserviceGeneratedList choices", self.choices

        preConfiguredIndex = self.checkForPreconfiguredXML()
        if preConfiguredIndex is not None:
            self.jobChainLink.setExitMessage("Completed successfully")
            self.proceedWithChoice(index=preConfiguredIndex, agent=None)
        else:
            choicesAvailableForUnitsLock.acquire()
            self.jobChainLink.setExitMessage('Awaiting decision')
            choicesAvailableForUnits[self.jobChainLink.UUID] = self
            choicesAvailableForUnitsLock.release()

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
        except (etree.LxmlError, IOError) as e:
            print >>sys.stderr, "Error parsing xml for pre-configured choice", e
            return None
        for choice in root.find("preconfiguredChoices"):
            # Find the choice whose text matches this link's description
            if choice.find("appliesTo").text == self.jobChainLink.description:
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
        try:
            del choicesAvailableForUnits[self.jobChainLink.UUID]
        except KeyError:
            pass
        choicesAvailableForUnitsLock.release()
        
        #get the one at index, and go with it.
        _, _, replace_dict = self.choices[int(index)]
        rd = ReplacementDict.fromstring(replace_dict)
        self.update_passvar_replacement_dict(rd)
        self.jobChainLink.linkProcessingComplete(0, passVar=self.jobChainLink.passVar)
