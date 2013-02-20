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
# @author Mike Cantelon <mike@artefactual.com>

import subprocess

def check_for_string_presence_in_file(string, file):
    fileContents = open(file, 'r').read()
    return string in fileContents

atomProjectConfigFile = '/var/www/ica-atom/config/ProjectConfiguration.class.php'
if not check_for_string_presence_in_file('qtSwordPlugin', atomProjectConfigFile):
    print "The qtSwordPlugin plugin hasn't been enabled in " \
      + atomProjectConfigFile + '.'
    exit(1)

processData = subprocess.check_output(['ps', 'aux'])
if not 'gearman:worker' in processData:
    print "The sword service doesn't seem to be running."
    exit(1)

print 'No issues detected in your AtoM/SWORD configuration!'
