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
# @subpackage SIPCreationTools
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

#source /etc/archivematica/SIPCreationTools/md5Settings

outputDirectory="./../metadata"
outputFile="${outputDirectory}/checksum.md5"
set -e
cd "$1"
cd objects
if [ -d "${outputDirectory}" ]; then
	md5deep -rl "." > "${outputFile}" 	
else
  	echo $outputDirectory does not exist\ 1>&2
  	echo this script needs to be run from the objects directory 1>&2
  	exit 1 
fi


