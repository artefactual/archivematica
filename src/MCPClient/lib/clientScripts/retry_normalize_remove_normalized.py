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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>

import os
import sys
import shutil
import traceback
from optparse import OptionParser

import django

django.setup()
# dashboard
from django.db import transaction
from django.utils import timezone
from main.models import Derivation, Event, File


def removeDIP(job, SIPDirectory, SIPUUID):
    try:
        DIP = os.path.join(SIPDirectory, "DIP")
        if os.path.isdir(DIP):
            shutil.rmtree(DIP)
    except (os.error, shutil.Error):
        job.pyprint("Error deleting DIP", file=sys.stderr)
        job.print_output(traceback.format_exc())


def removeThumbnails(job, SIPDirectory, SIPUUID):
    try:
        thumbnails = os.path.join(SIPDirectory, "thumbnails")
        if os.path.isdir(thumbnails):
            shutil.rmtree(thumbnails)
    except (os.error, shutil.Error):
        job.pyprint("Error deleting thumbnails", file=sys.stderr)
        job.print_output(traceback.format_exc())


def removePreservationFiles(job, SIPDirectory, SIPUUID):
    # Remove Archivematica-created preservation files
    try:
        files = File.objects.filter(
            sip_id=SIPUUID, removedtime__isnull=True, filegrpuse="preservation"
        )
        for file_ in files:
            try:
                file_.removedtime = timezone.now()
                file_.save()
                os.remove(
                    file_.currentlocation.replace("%SIPDirectory%", SIPDirectory, 1)
                )
            except Exception:
                job.pyprint("Error removing preservation files", file=sys.stderr)
                job.print_output(traceback.format_exc())
    except Exception:
        job.pyprint("Error running SQL", file=sys.stderr)
        job.print_output(traceback.format_exc())

    # Remove manually normalized derivation links
    # TODO? Update this to delete for all derivations where the event is deleted
    try:
        Derivation.objects.filter(
            derived_file__filegrpuse="manualNormalization", derived_file__sip_id=SIPUUID
        ).delete()
    except Exception:
        job.pyprint(
            "Error deleting manual normalization links from database", file=sys.stderr
        )
        job.print_output(traceback.format_exc())

    # Remove normalization events
    try:
        Event.objects.filter(
            file_uuid__sip_id=SIPUUID, event_type="normalization"
        ).delete()
    except Exception:
        job.pyprint(
            "Error deleting normalization events from database.", file=sys.stderr
        )
        job.print_output(traceback.format_exc())


def call(jobs):
    parser = OptionParser()
    # mysql> UPDATE StandardTasksConfigs SET arguments = '--SIPDirectory "%SIPDirectory%" --SIPUUID "%SIPUUID%" --preservation --thumbnails' WHERE PK = '352fc88d-4228-4bc8-9c15-508683dabc58';
    # mysql> UPDATE StandardTasksConfigs SET arguments = '--SIPDirectory "%SIPDirectory%" --SIPUUID "%SIPUUID%" --preservation --thumbnails --access' WHERE PK = 'c15de53e-a5b2-41a1-9eee-1a7b4dd5447a';

    # '--SIPDirectory "%SIPDirectory%" --accessDirectory "objects/access/" --objectsDirectory "objects" --DIPDirectory "DIP" -c'
    parser.add_option(
        "-s", "--SIPDirectory", action="store", dest="SIPDirectory", default=""
    )
    parser.add_option("-u", "--SIPUUID", action="store", dest="SIPUUID", default="")
    parser.add_option(
        "-p", "--preservation", action="store_true", dest="preservation", default=False
    )
    parser.add_option(
        "-t", "--thumbnails", action="store_true", dest="thumbnails", default=False
    )
    parser.add_option(
        "-a", "--access", action="store_true", dest="access", default=False
    )

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                (opts, args) = parser.parse_args(job.args[1:])

                SIPDirectory = opts.SIPDirectory
                SIPUUID = opts.SIPUUID

                if opts.preservation:
                    removePreservationFiles(job, SIPDirectory, SIPUUID)
                if opts.thumbnails:
                    removeThumbnails(job, SIPDirectory, SIPUUID)
                if opts.access:
                    removeDIP(job, SIPDirectory, SIPUUID)
