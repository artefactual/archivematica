#!/usr/bin/env python2
# -*- coding: utf8
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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
import os
import unicodedata
import uuid

import django
import six

django.setup()
from django.db import transaction

# dashboard
from main.models import Event, File, Directory, Transfer, SIP

# archivematicaCommon
from custom_handlers import get_script_logger
import change_names

logger = get_script_logger("archivematica.mcp.client.changeObjectNames")


class NameChanger(object):
    """
    Class to track batch filename changes of files and directories, both in the
    filesystem and in the database.
    """

    BATCH_SIZE = 2000
    EVENT_DETAIL = (
        'prohibited characters removed: program="change_names"; version="'
        + change_names.VERSION
        + '"'
    )
    EVENT_OUTCOME_DETAIL = u'Original name="{}"; new name="{}"'

    def __init__(
        self, job, objects_directory, sip_uuid, date, group_type, group_sql, sip_path
    ):
        if group_type not in ("%SIPDirectory%", "%transferDirectory%"):
            raise ValueError("Unexpected group type: {}".format(group_type))

        if isinstance(objects_directory, six.binary_type):
            objects_directory = objects_directory.decode("utf-8")

        if isinstance(sip_path, six.binary_type):
            sip_path = sip_path.decode("utf-8")

        if group_sql == "transfer_id":
            self.transfer = Transfer.objects.get(uuid=sip_uuid)
            self.sip = None
        elif group_sql == "sip_id":
            self.transfer = None
            self.sip = SIP.objects.get(uuid=sip_uuid)
        else:
            raise ValueError("Unexpected group sql: {}".format(group_sql))

        self.job = job
        self.objects_directory = objects_directory
        self.date = date
        self.group_type = group_type
        self.sip_path = sip_path

        self.files_index = {}  # old_path: new_path
        self.dirs_index = {}  # old_path: new_path

    @property
    def directory_queryset(self):
        """
        Base queryset for Directory objects related to the SIP/Transfer.
        """
        if self.transfer is not None and self.transfer.diruuids:
            return Directory.objects.filter(transfer=self.transfer)
        elif self.sip is not None and self.sip.diruuids:
            return Directory.objects.filter(sip=self.sip)

        return None

    @property
    def file_queryset(self):
        """
        Base queryset for File objects related to the SIP/Transfer.
        """
        file_qs = File.objects.filter(removedtime__isnull=True)
        if self.sip is not None:
            return file_qs.filter(sip=self.sip)
        else:
            return file_qs.filter(transfer=self.transfer)

    def normalize_path_for_db(self, path):
        """
        Returns a unicode normalized, relative paths (e.g.
        %transferDirectory%objects/example.txt)
        """
        return unicodedata.normalize("NFC", path).replace(
            self.sip_path, self.group_type, 1
        )

    def apply_file_updates(self):
        """
        Run a single batch of File updates.
        """
        if self.sip:
            event_agents = self.sip.agents
        else:
            event_agents = self.transfer.agents

        events = []

        # We pass through _all_ objects here, as they may not be normalized in
        # the db :(
        for file_obj in self.file_queryset.iterator():
            old_location = unicodedata.normalize("NFC", file_obj.currentlocation)
            try:
                changed_location = self.files_index[old_location]
            except KeyError:
                continue

            file_obj.currentlocation = changed_location
            file_obj.save()

            change_event = Event(
                event_id=uuid.uuid4(),
                file_uuid=file_obj,
                event_type="filename change",
                event_datetime=self.date,
                event_detail=self.EVENT_DETAIL,
                event_outcome_detail=self.EVENT_OUTCOME_DETAIL.format(
                    old_location, changed_location
                ),
            )
            events.append(change_event)

        Event.objects.bulk_create(events)

        # Adding m2m fields with bulk create is awkward, we have to loop through again.
        for event in Event.objects.filter(
            file_uuid__in=[event.file_uuid for event in events]
        ):
            event.agents.add(*event_agents)

        if len(self.files_index) > 0:
            logger.debug(
                "Filename change applied to batch of %s files", len(self.files_index)
            )

            self.files_index = {}
        else:
            logger.debug("No filename change required.")

    def apply_dir_updates(self):
        """
        Run a single batch of Directory updates.
        """
        if self.directory_queryset is None:
            logger.debug("No directory name change required.")
            return

        # We pass through _all_ objects here, as they may not be normalized in
        # the db :(
        for dir_obj in self.directory_queryset.iterator():
            old_location = unicodedata.normalize("NFC", dir_obj.currentlocation)
            try:
                changed_location = self.dirs_index[old_location]
            except KeyError:
                continue

            dir_obj.currentlocation = changed_location
            dir_obj.save()

            # TODO: Dir name changes don't generate events?
            # Is seems like they should.

        if len(self.dirs_index) > 0:
            logger.debug(
                "Name change applied to batch of %s directories", len(self.dirs_index)
            )
            self.dirs_index = {}
        else:
            logger.debug("No directory name change required.")

    def add_file_to_batch(self, old_path, new_path):
        """
        Index a path change for later updating in the database.

        If our index is over a certain size, then trigger application of the
        batched changes.
        """
        old_path = self.normalize_path_for_db(old_path)
        new_path = self.normalize_path_for_db(new_path)

        self.files_index[old_path] = new_path

        if len(self.files_index) >= self.BATCH_SIZE:
            self.apply_file_updates()

    def add_dir_to_batch(self, old_path, new_path):
        """
        Index a path change for later updating in the database.

        If our index is over a certain size, then trigger application of the
        batched changes.
        """
        old_path = self.normalize_path_for_db(old_path)
        new_path = self.normalize_path_for_db(new_path)

        # Add trailing slashes if necessary
        old_path = os.path.join(old_path, "")
        new_path = os.path.join(new_path, "")

        self.dirs_index[old_path] = new_path

        if len(self.dirs_index) >= self.BATCH_SIZE:
            self.apply_dir_updates()

    def change_objects(self):
        """
        Iterate over the filesystem, changing names as we go. Updates made on disk
        are batched and then applied to the database in chunks of BATCH_SIZE.
        """
        for old_path, new_path, is_dir, was_changed in change_names.change_tree(
            self.objects_directory, self.objects_directory
        ):
            # We need to use job.pyprint here to log to stdout, otherwise the filename
            # cleanup log file is not generated.
            if not was_changed:
                self.job.pyprint("No filename changes for", old_path)
                continue

            if is_dir:
                self.add_dir_to_batch(old_path, new_path)
            else:
                self.add_file_to_batch(old_path, new_path)
            self.job.pyprint("Changed name:", old_path, " -> ", new_path)

        # Catch the remainder afer all batches
        self.apply_file_updates()
        self.apply_dir_updates()


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                # job.args[4] (taskUUID) is unused.
                objects_directory = job.args[1]  # directory to run changes on.
                sip_uuid = job.args[2]  # %sip_uuid%
                date = job.args[3]  # %date%
                group_type = job.args[5]  # SIPDirectory or transferDirectory
                group_type = "%%%s%%" % (
                    group_type
                )  # %SIPDirectory% or %transferDirectory%
                group_sql = job.args[6]  # transfer_id or sip_id
                sip_path = job.args[7]  # %SIPDirectory%

                name_changer = NameChanger(
                    job,
                    objects_directory,
                    sip_uuid,
                    date,
                    group_type,
                    group_sql,
                    sip_path,
                )
                name_changer.change_objects()
                job.set_status(0)
