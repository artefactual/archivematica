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

target="$1"
date="$2"
SIPUUID="$3"
#uuidVersion="4"
#SIPUUID=`uuid -v ${uuidVersion}`

sudo chown -R archivematica:archivematica "${target}" 
chmod -R "750" "${target}"
if [ -d "${target}logs/" ]; then
	echo ${date} > "${target}logs/acquiredSIPDateTime.log"
fi
mv "${target}" "`dirname "${target}"`/`basename "${target}"`-${SIPUUID}"

exit $? 


