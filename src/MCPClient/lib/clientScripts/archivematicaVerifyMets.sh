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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$


set -e

exit 0

sipPath="$1"
metsFile="${sipPath}metadata/mets_structmap.xml"
schema="/usr/lib/archivematica/archivematicaCommon/externals/mets/mets.xsd"

#not used... doesn't put file in correct location either
if [ ! -f "${schema}" ]; then
	echo TODO
    echo getting mets.xsd
    wget http://www.loc.gov/standards/mets/mets.xsd /usr/lib/archivematica/archivematicaCommon/externals/mets/mets.xsd
fi

if [ -f "${metsFile}" ]; then
    xmllint --noout --schema "$schema" "${sipPath}metadata/mets_structmap.xml"
else
	echo No metadata/mets_structmap.xml file to verify.
fi
