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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>

import os
import sys
import mailbox
exitCodes = {None: 0, 'maildir': 179}

def isMaildir(path):
    maildir = path + "objects/Maildir/"
    if not os.path.isdir(maildir):
        return False
    if not os.path.isdir(os.path.join(path, "objects", "attachments")):
        return False
    try:
        for maildirsub2 in os.listdir(maildir):
            maildirsub = os.path.join(maildir, maildirsub2)
            md = mailbox.Maildir(maildirsub, None)
    except:
        return False
    return True


if __name__ == '__main__':
    path = sys.argv[1]
    if isMaildir(path):
        exit(exitCodes['maildir'])
        
    exit(exitCodes[None])