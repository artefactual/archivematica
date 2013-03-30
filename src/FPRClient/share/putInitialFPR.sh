#!/bin/bash

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica. If not, see <http://www.gnu.org/licenses/>>.

# @package Archivematica
# @author Joseph Perry <joseph@artefactual.com>>
# @version svn: $Id$

origDir="`pwd`"
cd "`dirname $0`"
username="root"
databaseName="MCP"
set -e
echo -n "Enter the DATABASE root password (Hit enter if blank):"
read dbpassword

if [ ! -z "$dbpassword" ] ; then
  dbpassword="-p${dbpassword}"
else
  dbpassword=""
fi


mysql -u $username $dbpassword --execute="source ./removeFPRData.sql" $databaseName
mysql -u $username $dbpassword --execute="source ./mysql" $databaseName
mysql -u $username $dbpassword --execute="INSERT INTO UnitVariables SET pk='351e1464-7ab8-4cf1-a4cf-db8cef5c3090', variableValue='2013-03-29T13:10:12', unitType='FPR', unitUUID = 'Client', variable = 'maxLastUpdate';" $databaseName

/usr/lib/archivematica/FPRClient/addLinks.py

cd "$origDir"
dbpassword=""

