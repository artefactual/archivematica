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
# @version svn: $Id$

databaseName="MCP"
currentDir="$(dirname $0)"
username="archivematica"
password="demo"

echo "Removing existing units"
sudo ./removeUnitsFromWatchedDirectories.py
sudo rm -rf /var/archivematica/sharedDirectory/tmp/tmp*

set -e
echo -n "Enter the DATABASE root password (Hit enter if blank):"
read dbpassword

if [ ! -z "$dbpassword" ] ; then
    dbpassword="-p${dbpassword}"
else
    dbpassword=""
fi
#set -o verbose #echo on
pwd
currentDir="`dirname $0`"
set +e
echo "Removing the old database"
mysql -u root "${dbpassword}" --execute="DROP DATABASE IF EXISTS ${databaseName}"
echo "Removing ${username} user"
mysql -u root "${dbpassword}" --execute="DROP USER '${username}'@'localhost';"
set -e

echo "Creating MCP database"
mysql -u root "${dbpassword}" --execute="CREATE DATABASE ${databaseName} CHARACTER SET utf8 COLLATE utf8_unicode_ci;"
echo "Creating ${username} user"
mysql -u root "${dbpassword}" --execute="CREATE USER '${username}'@'localhost' IDENTIFIED BY '${password}';"
mysql -u root "${dbpassword}" --execute="GRANT SELECT, UPDATE, INSERT, DELETE ON ${databaseName}.* TO '${username}'@'localhost';"

echo "Creating and populating MCP tables"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/../src/MCPServer/share/mysql_1.0.sql;"
../src/MCPServer/share/mysql_dev.sh ${databaseName} ${dbpassword}
# mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/../src/MCPServer/share/mysql_dev1;"

echo "Creating MCP Views"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/../src/MCPServer/share/mysql2Views;"

dbpassword=""

#set +o verbose #echo off
printGreen="${databaseName} database created successfully."
echo -e "\e[6;32m${printGreen}\e[0m"

#do initial FPR setup:
echo "Insert FPR data dump"
"${currentDir}/../src/MCPServer/share/mysql_fpr_dev.sh"
