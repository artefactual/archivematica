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

set -e
BAG="$1"
DATE="$2"
DIRNAME="`dirname "$BAG"`"
tmpUUID="`uuid`"
mv "${BAG}data" "${DIRNAME}/${tmpUUID}"
mkdir -p "${DIRNAME}/${tmpUUID}/metadata/bagit"
mv "${BAG}"* "${DIRNAME}/${tmpUUID}/metadata/bagit/."
rm -r "${BAG}"
mv "${DIRNAME}/${tmpUUID}" "${BAG}" 
if [ ! -d "${BAG}objects" ]; then
    mkdir "${DIRNAME}/${tmpUUID}"
    mkdir "${DIRNAME}/${tmpUUID}/objects"
    mv "${BAG}"* "${DIRNAME}/${tmpUUID}/."
	rm -r "${BAG}"
	mv "${DIRNAME}/${tmpUUID}" "${BAG}"
fi
if [ ! -d "${BAG}logs" ]; then
    mkdir "${BAG}logs"
fi
if [ ! -d "${BAG}logs/fileMeta" ]; then
    mkdir "${BAG}logs/fileMeta"
fi

if [ ! -d "${BAG}metadata" ]; then
    mkdir "${BAG}metadata"
fi
if [ ! -d "${BAG}metadata/submissionDocumentation" ]; then
    mkdir "${BAG}metadata/submissionDocumentation"
fi
if [ ! -e "${BAG}logs/acquiredSIPDateTime.log" ]; then
	echo ${DATE} > "${BAG}logs/acquiredSIPDateTime.log"
fi
