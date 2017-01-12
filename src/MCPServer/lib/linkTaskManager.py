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

import logging
import uuid
import os

from django.utils import timezone

from archivematicaFunctions import strToUnicode
from dicts import ReplacementDict
from main.models import Task

LOGGER = logging.getLogger('archivematica.mcp.server')


class LinkTaskManager(object):
    """ Common manager for MicroServiceChainLinks of different task types. """
    def __init__(self, jobChainLink):
        self.jobChainLink = jobChainLink
        self.UUID = str(uuid.uuid4())

        # Shortcuts
        self.link = self.jobChainLink.link
        self.unit = self.jobChainLink.unit
        self.unit_choices = self.jobChainLink.unit_choices
        self.workflow = self.jobChainLink.jobChain.workflow

    def update_passvar_replacement_dict(self, replace_dict):
        """ Update the ReplacementDict in the passVar, creating one if needed. """
        if self.jobChainLink.passVar is not None:
            if isinstance(self.jobChainLink.passVar, list):
                # Search the list for a ReplacementDict, and update it if it
                # exists, otherwise append to list
                for passVar in self.jobChainLink.passVar:
                    if isinstance(passVar, ReplacementDict):
                        passVar.update(replace_dict)
                        break
                else:
                    self.jobChainLink.passVar.append(replace_dict)
            elif isinstance(self.jobChainLink.passVar, ReplacementDict):
                # passVar is a ReplacementDict that needs to be updated
                self.jobChainLink.passVar.update(replace_dict)
            else:
                # Create list with existing passVar and replace_dict
                self.jobChainLink.passVar = [replace_dict, self.jobChainLink.passVar]
        else:
            # PassVar is empty, create new list
            self.jobChainLink.passVar = [replace_dict]

    def log_task(self, command_replacement_dict, task_uuid, arguments):
        """
        Creates a new entry in the Tasks table using the supplied data.

        :param MCPServer.linkTaskManager task_manager: A linkTaskManager subclass instance.
        :param ReplacementDict command_replacement_dict: A ReplacementDict or dict instance. %fileUUID% and %relativeLocation% variables will be looked up from this dict.
        :param str task_uuid: The UUID to be used for this Task in the database.
        :param str arguments: The arguments to be passed to the command when it is executed, as a string. Can contain replacement variables; see ReplacementDict for supported values.
        """
        Task.objects.create(
            taskuuid=task_uuid,
            job_id=self.jobChainLink.UUID,
            fileuuid=command_replacement_dict.get('%fileUUID%', ''),
            filename=os.path.basename(os.path.abspath(command_replacement_dict['%relativeLocation%'])),
            execution=self.get_config().execute,
            arguments=arguments,
            createdtime=timezone.now()
        )

    def log_completed_task(self, uuid, results):
        """
        Logs the results of the completed task to the database.
        Updates the entry in the Tasks table with data in the provided task.
        Saves the following fields: exitCode, stdOut, stdError

        :param uuid: the task UUID
        :param results: the output of the task (see taskStandard for more details)
        """
        LOGGER.info('Logging output of task %s to the database', uuid)

        # ``strToUnicode`` here prevents the MCP server from crashing when, e.g.,
        # stderr contains Latin-1-encoded chars such as \xa9, i.e., the copyright
        # symbol, cf. #9967.
        Task.objects.filter(taskuuid=uuid).update(
            endtime=timezone.now(),
            exitcode=str(results['exitCode']),
            stdout=strToUnicode(results['stdOut'], obstinate=True),
            stderror=strToUnicode(results['stdError'], obstinate=True),
        )
