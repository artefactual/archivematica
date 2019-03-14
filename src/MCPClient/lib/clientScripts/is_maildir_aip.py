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
import mailbox

EXIT_CODES = {None: 0, "maildir": 179}


def isMaildir(path):
    maildir = path + "objects/Maildir/"
    if not os.path.isdir(maildir):
        return False
    if not os.path.isdir(os.path.join(path, "objects", "attachments")):
        return False
    try:
        for maildirsub2 in os.listdir(maildir):
            maildirsub = os.path.join(maildir, maildirsub2)
            mailbox.Maildir(maildirsub, None)
    except:
        return False
    return True


def call(jobs):
    for job in jobs:
        with job.JobContext():
            path = job.args[1]
            if isMaildir(path):
                job.set_status(EXIT_CODES["maildir"])
            else:
                job.set_status(EXIT_CODES[None])
