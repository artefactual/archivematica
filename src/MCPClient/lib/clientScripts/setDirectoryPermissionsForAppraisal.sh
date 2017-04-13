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

exit 0

target="$1"
if [ -e "${target}" ]; then
	sudo chown -R archivematica:archivematica "${target}"  
	echo `basename "${target}"` owned by "archivematica:archivematica" now 
	sudo chmod -R 660 "${target}"
	sudo chmod 640 "${target}"
	sudo find "${target}" -type d -execdir chmod 770 '{}' +
	if [ -d "${target}objects" ]; then	
		sudo chmod -R 660 "${target}objects"
        sudo find "${target}objects" -type d -execdir chmod 770 '{}' +
	fi
	if [ -d "${target}metadata" ]; then	
		sudo chmod -R 660 "${target}metadata"
        sudo find "${target}metadata" -type d -execdir chmod 770 '{}' +
	fi
else
  	echo $target does not exist\ 1>&2
  	exit 1 
fi

