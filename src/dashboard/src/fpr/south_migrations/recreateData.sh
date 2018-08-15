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
# @author Joseph Perry <joseph@artefactual.com>

database="$FPR_DB_NAME"
origDir="`pwd`"
currentDir="$(dirname $0)"
username="$FPR_DB_USER"
dbpassword="$FPR_DB_PASSWORD"
dbhost="$FPR_DB_HOST"

if [ ! -z "$dbpassword" ] ; then
    dbpassword="-p${dbpassword}"
else
    dbpassword=""
fi

cd "$currentDir"
set +e
echo "Removing existing entries"
mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM Command;" $database
mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM CommandClassification;" $database
mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM CommandRelationship;" $database
mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM CommandType;" $database
#mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM CommandsSupportedBy;" $database
#mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM DefaultCommandsForClassification;" $database
mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM FileID;" $database
#mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM FileIDGroupMember;" $database
mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM FileIDType;" $database
mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM FileIDsBySingleID;" $database
#mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM $database.Group;" $database
#mysql $dbhost -u $username "${dbpassword}" --execute="DELETE FROM SubGroup;" $database
set -e
mysql $dbhost -u $username "${dbpassword}" --execute="source ./rawdump.sql" $database

cd "$origDir"
dbpassword=""

