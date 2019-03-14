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
import string
import uuid

from utils import log_exceptions

from databaseFunctions import auto_close_db, getUTCDate

from main.models import Job


LOGGER = logging.getLogger("archivematica.mcp.server")


class jobChainLink:
    def __init__(self, jobChain, link, workflow, unit, passVar=None):
        if link is None:
            return None

        self.UUID = uuid.uuid4().__str__()
        self.jobChain = jobChain
        self.workflow = workflow
        self.unit = unit
        self.passVar = passVar
        self.pk = link.id
        self.link = link
        self.workflow = workflow
        self.created_at = getUTCDate()
        self.group = link.get_label("group", "en")
        self.description = link.get_label("description", "en")

        LOGGER.info("Running %s (unit %s)", self.description, self.unit.UUID)
        self.unit.reload()

        self._create_job()
        self._run_task_manager()

    def _run_task_manager(self):
        """Execute the task manager corresponding to this link."""
        try:
            manager = self.link.manager
        except Exception as err:
            LOGGER.exception("Unsupported task type: %s", err)
            return
        manager(self, self.unit)

    def _create_job(self):
        """Persist job in the database."""
        try:
            if self.unit.owningUnit is not None:
                unit_id = self.unit.owningUnit.UUID
        except AttributeError:
            unit_id = self.unit.UUID
        return Job.objects.create(
            jobuuid=self.UUID,
            jobtype=self.description,
            directory=self.unit.currentPath,
            sipuuid=unit_id,
            currentstep=Job.STATUS_EXECUTING_COMMANDS,
            unittype=self.unit.__class__.__name__,
            microservicegroup=self.group,
            createdtime=self.created_at,
            createdtimedec=self._created_at_dec,
            microservicechainlink=self.pk,
        )

    @property
    def _created_at_dec(self):
        # Microseconds are always 6 digits.
        # The number returned may have a leading 0 which needs to be preserved.
        date = "." + str(self.created_at.microsecond).zfill(6)
        valid = "." + string.digits
        ret = ""
        for c in date:
            if c in valid:
                ret += c
        return str("{:10.10f}".format(float(ret)))

    @log_exceptions
    @auto_close_db
    def setExitMessage(self, status_code):
        """
        Set the value of Job.currentstep, comming either from any
        MicroServiceChainLinkExitCode.exitmessage or different code paths where
        a value is manually assigned based on different circunstances.

        Should this be a method of the Job model?

        Note: linkTaskManager{Choice,ReplacementDicFromChoice}.py call this
        method passing an unknown status, e.g. "Waiting till ${time}" which
        we are going to map as UNKNOWN for now.
        """
        try:
            status_code = int(status_code)
        except ValueError:
            status_code = 0
        Job.objects.filter(jobuuid=self.UUID).update(currentstep=status_code)

    @log_exceptions
    @auto_close_db
    def linkProcessingComplete(self, exitCode, passVar=None, next_link=None):
        """Link completion callback.

        It continues the workflow running the next chain link which is looked
        up in the workflow data unless determined by `next_link_id`. Before
        starting, the status of the job associated to this link is updated.
        """
        self.setExitMessage(self.link.get_status_id(exitCode))
        if next_link is None:
            try:
                next_link = self.link.get_next_link(exitCode)
            except KeyError:
                return
        self.jobChain.nextChainLink(next_link, passVar=passVar)
