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
import archivematicaMCP
from linkTaskManagerChoice import waitingOnTimer

from dicts import ReplacementDict

from main.models import DashboardSetting, Job, UserProfile

LOGGER = logging.getLogger('archivematica.mcp.server')


class linkTaskManagerReplacementDicFromChoice(LinkTaskManager):
    def __init__(self, jobChainLink):
        super(linkTaskManagerReplacementDicFromChoice, self).__init__(jobChainLink)

        self.populate_choices()

        preConfiguredChain = self.checkForPreconfiguredXML()
        if preConfiguredChain is None:
            with self.unit_choices:
                self.jobChainLink.setExitMessage(Job.STATUS_AWAITING_DECISION)
                self.unit_choices[self.jobChainLink.UUID] = self
            return
        if preConfiguredChain == waitingOnTimer:
            LOGGER.info('Waiting on delay to resume processing on unit %s', self.unit)
            return

        self.jobChainLink.setExitMessage(Job.STATUS_COMPLETED_SUCCESSFULLY)

        self.update_passvar_replacement_dict(self.convert_replacement_dict(preConfiguredChain))
        self.jobChainLink.linkProcessingComplete(exit_code=0, passVar=self.jobChainLink.passVar)

    def get_config(self):
        return self.link.config.userChoiceDict

    def populate_choices(self):
        self.choices = []

        config = self.get_config()
        for index, item in enumerate(config.replacements):
            self.choices.append((index, item.description, item.items))

        # Look up DashboardSettings to extend self.choices
        fallback_link = self.workflow.links[self.link.fallbackLinkId]
        if fallback_link is None:
            return
        module = fallback_link.config.standard.execute  # e.g. "upload-qubit_v0.0"
        args = DashboardSetting.objects.get_dict(module)
        if args:
            args = {'%{}%'.format(key): value for key, value in args.items()}
            self.choices.append((len(self.choices), module, str(args)))

    def get_replacement_dic(self, dict_id):
        config = self.get_config()
        for item in config.replacements:
            if item.id == dict_id:
                return item.items

    def checkForPreconfiguredXML(self):
        xml_path = os.path.join(
            self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1) + "/",
            archivematicaMCP.config.get('MCPServer', "processingXMLFile"))

        if not os.path.isfile(xml_path):
            return

        ret = None
        try:
            tree = etree.parse(xml_path)
            root = tree.getroot()
            for preconfiguredChoice in root.findall(".//preconfiguredChoice"):
                if preconfiguredChoice.find("appliesTo").text != self.link.id:
                    continue
                ret = self.get_replacement_dic(preconfiguredChoice.find("goToChain").text)

                # TODO: clean this up
                delayXML = preconfiguredChoice.find("delay")  # e.g <delay unitAtime="yes">30</delay>
                unitAtimeXML = delayXML.get("unitCtime")
                if unitAtimeXML is not None and unitAtimeXML.lower() != "no":
                    delaySeconds = int(delayXML.text)
                    unitTime = os.path.getmtime(self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1))
                    nowTime = time.time()
                    timeDifference = nowTime - unitTime
                    timeToGo = delaySeconds - timeDifference
                    LOGGER.info('Time to go: %s', timeToGo)

                    # TODO: this is just going to cause the job status to be
                    # marked as unknown. Do we need a new status? Is this
                    # trying to signal something else? e.g. Dashboard UI maybe?
                    self.jobChainLink.setExitMessage("Waiting till: " + datetime.datetime.fromtimestamp((nowTime + timeToGo)).ctime())

                    rd = self.convert_replacement_dict(ret)
                    if self.jobChainLink.passVar is not None:
                        if not isinstance(self.jobChainLink.passVar, ReplacementDict):
                            continue
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
            LOGGER.warning('Error parsing xml at %s for pre-configured choice', xml_path, exc_info=True)
        return ret

    def proceed_with_choice(self, index, user_id):
        if user_id:
            agent_id = UserProfile.objects.get(user_id=int(user_id)).agent_id
            agent_id = str(agent_id)
            self.unit.setVariable("activeAgent", agent_id, None)

        del self.unit_choices[self.jobChainLink.UUID]

        choiceIndex, description, rd = self.choices[int(index)]

        self.update_passvar_replacement_dict(self.convert_replacement_dict(rd))
        self.jobChainLink.linkProcessingComplete(0, passVar=self.jobChainLink.passVar)

    def convert_replacement_dict(self, proto_rd):
        """
        Convert the google.protobuf.internal.containers.ScalarMap replacement
        dictionary to a ReplacementDict.
        """
        rd = dict(proto_rd)
        for key, value in rd.copy().items():
            del rd[key]
            rd['%' + key + '%'] = value
        return ReplacementDict(rd)
