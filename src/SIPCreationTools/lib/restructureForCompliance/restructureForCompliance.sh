#!/bin/bash
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
# @subpackage SIPCreationTools
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

target=$1

if [ -d "$target" ]; then
	mkdir "${target}/objects"
	mv $(find "$target" -mindepth 1 -maxdepth 1 ! -name "objects") "${target}objects/"
	mkdir -p "${target}/logs/fileMeta"
	mkdir -p "${target}/metadata/submissionDocumentation"
elif [ -f "$target" -a ! -d "$(dirname $target)/$(basename ${target%.*})" ]; then
	mkdir -p "$(dirname $target)/$(basename ${target%.*})/objects"
	mv "$target" "$(dirname $target)/$(basename ${target%.*})/objects/"
	mkdir -p "$(dirname $target)/$(basename ${target%.*})/logs/fileMeta"
	mkdir -p "$(dirname $target)/$(basename ${target%.*})/metadata/submissionDocumentation"
else
	echo Error: Needs SIP directory or file as argument 1>&2
	exit 1
fi 



