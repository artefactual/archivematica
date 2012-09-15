#!/bin/bash

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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
# @version svn: $Id$
#source /etc/archivematica/archivematicaConfig.conf
set -e
DIRNAME="`dirname "$1"`"
sudo chown -R archivematica:archivematica "$1"
sudo chmod 777 -R "$1"
exitCode=0
#for a in `ls "${1}"*.zip`; do
find "${1}" -name "*.zip" -printf "%f:%h\n" | while IFS=":" read a PATH
do
	extractedDirectory="${DIRNAME}"
	echo Extracting to: "$extractedDirectory" 1>&2
	#/bin/mkdir "$extractedDirectory"
	/usr/bin/7z x -bd -o"${extractedDirectory}" "${1}${a}"
	exitCode=$(($exitCode + $? ))
	/usr/bin/sudo /bin/chown -R archivematica:archivematica "${extractedDirectory}"
	/usr/bin/sudo /bin/chmod -R 770 "${extractedDirectory}"
	/usr/bin/sudo /bin/chmod 777 "${1}${a}"
	/bin/rm "${1}${a}" 
done
/bin/rm "${1}" -r 
exit $exitCode

