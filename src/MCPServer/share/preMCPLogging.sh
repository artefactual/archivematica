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
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

databaseName="MCP"
username="archivematica"
password="demo"

stty -echo
echo -n "Enter the DATABASE root password (Hit enter if blank):"
read dbpassword
stty echo

if [ ! -z "$dbpassword" ] ; then
    dbpassword="-p${dbpassword}"
else
    dbpassword=""
fi
mysql -hlocalhost -uroot "${dbpassword}" --execute="DROP DATABASE IF EXISTS ${databaseName}"
mysql -hlocalhost -uroot "${dbpassword}" --execute="CREATE DATABASE ${databaseName} CHARACTER SET utf8 COLLATE utf8_unicode_ci"
mysql -hlocalhost -uroot "${dbpassword}" --execute="source ./mysql" "$databaseName"
mysql -hlocalhost -uroot "${dbpassword}" --execute="source ./mysql2Views" "$databaseName"
mysql -hlocalhost -uroot "${dbpassword}" --execute="DROP USER '${username}'@'localhost'"
mysql -hlocalhost -uroot "${dbpassword}" --execute="CREATE USER '${username}'@'localhost' IDENTIFIED BY '${password}'"
mysql -hlocalhost -uroot "${dbpassword}" --execute="GRANT SELECT, UPDATE, INSERT, DELETE ON ${databaseName}.* TO '${username}'@'localhost'"
dbpassword=""
