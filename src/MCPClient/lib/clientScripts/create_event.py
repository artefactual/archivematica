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
from optparse import OptionParser
import uuid

# databaseFunctions requires Django to be set up
import django

django.setup()
# archivematicaCommon
from databaseFunctions import insertIntoEvents
from django.db import transaction


def call(jobs):
    parser = OptionParser()
    parser.add_option("-i", "--fileUUID", action="store", dest="fileUUID", default="")
    parser.add_option("-t", "--eventType", action="store", dest="eventType", default="")
    parser.add_option(
        "-d", "--eventDateTime", action="store", dest="eventDateTime", default=""
    )
    parser.add_option(
        "-e", "--eventDetail", action="store", dest="eventDetail", default=""
    )
    parser.add_option(
        "-o", "--eventOutcome", action="store", dest="eventOutcome", default=""
    )
    parser.add_option(
        "-n",
        "--eventOutcomeDetailNote",
        action="store",
        dest="eventOutcomeDetailNote",
        default="",
    )
    parser.add_option(
        "-u",
        "--eventIdentifierUUID",
        action="store",
        dest="eventIdentifierUUID",
        default="",
    )

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                (opts, args) = parser.parse_args(job.args[1:])

                # The "Create removal from backlog PREMIS events" is one of the
                # micro-services that uses this createEvent client script. It used to
                # ignore everything not in an objects/ subdirectory. However, this becomes
                # problematic when you create a SIP from a subdirectory of something in
                # backlog; in that case there may be no objects/ root directory, in which
                # case "removal from backlog" events will, contrary to desire, not be
                # created. Therefore, we make sure that there is a file UUID value prior to
                # creating an event.
                if opts.fileUUID and opts.fileUUID != "None":
                    insertIntoEvents(
                        fileUUID=opts.fileUUID,
                        eventIdentifierUUID=str(uuid.uuid4()),
                        eventType=opts.eventType,
                        eventDateTime=opts.eventDateTime,
                        eventDetail=opts.eventDetail,
                        eventOutcome=opts.eventOutcome,
                        eventOutcomeDetailNote=opts.eventOutcomeDetailNote,
                    )
