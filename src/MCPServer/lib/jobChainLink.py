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
from importlib import import_module
import uuid

from django_mysqlpool import auto_close_db
from django.utils import timezone

from main.models import Job
from utils import get_decimal_date, log_exceptions

LOGGER = logging.getLogger('archivematica.mcp.server')


class jobChainLink:
    def __init__(self, jobChain, link_id, unit, passVar=None):
        self.UUID = uuid.uuid4().__str__()
        self.jobChain = jobChain
        self.unit_choices = jobChain.unit_choices
        self.unit = unit
        self.passVar = passVar

        self.link = self.jobChain.workflow.links.get(link_id)
        if self.link is None:
            LOGGER.exception('jobChainLink error: link %s not found', link_id)
            return

        LOGGER.debug('Creating jobChainLink for link %s', self.link.id)
        LOGGER.info('Running %s (unit %s)', self.link.description['en'], self.unit.UUID)

        self.unit.reload()
        self.log_job()
        self.start_manager()

    def log_job(self):
        """
        Logs a job's properties into the Jobs table in the database.
        """
        unit_uuid = self.unit.UUID
        if self.unit.owningUnit is not None:
            unit_uuid = self.unit.owningUnit.UUID

        # Microseconds are always 6 digits
        # The number returned may have a leading 0 which needs to be preserved
        created_date = timezone.now()
        decimal_date = get_decimal_date('.' + str(created_date.microsecond).zfill(6))

        Job.objects.create(
            jobuuid=self.UUID,
            directory=self.unit.currentPath,
            sipuuid=unit_uuid,
            currentstep=Job.STATUS_EXECUTING_COMMANDS,
            unittype=self.unit.__class__.__name__,
            createdtime=created_date,
            createdtimedec=decimal_date,
            microservicechainlink=self.link.id,

            # For backward-compatibility, using English values here
            jobtype=self.link.description['en'],
            microservicegroup=str(self.link.group['en'])
        )

    def start_manager(self):
        manager_name = self.link.config.manager
        try:
            # The link configuration has a property called "manager" with the
            # name of the manager class that corresponds to that link. We could
            # change that property into an enum later.
            mod = import_module(manager_name)
            cls = getattr(mod, manager_name)
        except (ImportError, AttributeError):
            LOGGER.error('Unknown manager %s', manager_name)
            return

        if manager_name == 'linkTaskManagerFiles':
            self.unit.reloadFileList()

        # Instantiate the manager!
        cls(self)

    def get_exit_code_config(self, exit_code):
        """
        Looks up the Link.LinkExitCode matching the given exit code.
        """
        try:
            exit_code = int(exit_code)
        except ValueError:
            return
        # It is possible that there is a single entry in exitCodes for the exit
        # code zero and linkId being an empty string representing the end of a
        # chain. We make sure that None is returned in that case.
        for item in self.link.exitCodes:
            if item.code == exit_code:
                return item

    def get_next_chain_link(self, exit_code):
        """
        Look up the next chain link based on the exit code. If there is no
        behaviour described for the exit_code specified, the default chain link
        will be used instead.
        """
        ec_config = self.get_exit_code_config(exit_code)  # LinkExitCode
        if ec_config is not None:
            return ec_config.linkId
        return self.link.fallbackLinkId

    @log_exceptions
    @auto_close_db
    def setExitMessage(self, status_code):
        """
        Updates Job database record. Defaults to Job.STATUS_UNKNOWN if the
        code given is not an integer.
        """
        try:
            status_code = int(status_code)
        except ValueError:
            return
        if status_code == 0:
            return
        Job.objects.filter(jobuuid=self.UUID).update(currentstep=status_code)

    def updateExitMessage(self, exit_code):
        """
        Updates the job status after the exit code.
        """
        job_status = self.link.fallbackJobStatus
        ec_config = self.get_exit_code_config(exit_code)
        LOGGER.debug('Updating job status: exit_code=%s, ec_config = %s', exit_code, ec_config)
        if ec_config is not None:
            job_status = ec_config.jobStatus
        self.setExitMessage(job_status)

    @log_exceptions
    @auto_close_db
    def linkProcessingComplete(self, exit_code, passVar=None):
        self.updateExitMessage(exit_code)
        self.jobChain.next_link(self.get_next_chain_link(exit_code), passVar=passVar)
