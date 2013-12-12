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
import ConfigParser

def removeEverythingInDirectory(directory):
    if directory[-1] != "/":
        directory = "%s/" % (directory)
    execute = "sudo rm -rf \"%s\"*" % (directory)
    print "executing: ", execute
    os.system(execute)

if __name__ == '__main__':
    import getpass
    user = getpass.getuser()
    print "user: ", user
    if user != "root":
        print "Please run as root (with sudo)"
        exit (1)

    # Get sharedDirectory from config file
    config = ConfigParser.SafeConfigParser()
    config.read("/etc/archivematica/MCPServer/serverConfig.conf")
    sharedDirectory = config.get('MCPServer', "sharedDirectory")
    if not sharedDirectory:
        sharedDirectory = '/var/archivematica/sharedDirectory/'
    removeEverythingInDirectory(sharedDirectory)
