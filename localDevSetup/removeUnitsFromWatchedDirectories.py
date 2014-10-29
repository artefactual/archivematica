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
# @subpackage DevCleanup
# @author Joseph Perry <joseph@artefactual.com>
import os
import sys

sys.path.append("/usr/share/archivematica/dashboard")
os.environ["DJANGO_SETTINGS_MODULE"] = "settings.local"
from main.models import WatchedDirectory


def removeEverythingInDirectory(directory):
    if directory[-1] != "/":
        directory = "%s/" % (directory)
    execute = "sudo rm -rf \"%s\"*" % (directory)
    print "executing: ", execute
    os.system(execute)

def cleanWatchedDirectories():
    for path, in WatchedDirectory.objects.values_list('watched_directory_path'):
        try:
            directory = path.replace("%watchDirectoryPath%", "/var/archivematica/sharedDirectory/watchedDirectories/", 1)
            removeEverythingInDirectory(directory)
        except Exception as inst:
            print "debug except 2"
            print type(inst)     # the exception instance
            print inst.args      # arguments stored in .args

if __name__ == '__main__':
    import getpass
    user = getpass.getuser()
    print "user: ", user
    if user != "root":
        print "Please run as root (with sudo)"
        exit (1)
    cleanWatchedDirectories()
    alsoRemove = [
        "/var/archivematica/sharedDirectory/failed/",
        "/var/archivematica/sharedDirectory/currentlyProcessing/",
        "/var/archivematica/sharedDirectory/rejected/",
        "/var/archivematica/sharedDirectory/completed/transfers/",
    ]
    for directory in alsoRemove:
        removeEverythingInDirectory(directory)
