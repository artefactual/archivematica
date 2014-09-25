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

set +e
origDir="`pwd`/"
cd ../
svnDir="`pwd`/"

lib="/usr/lib/archivematica"
sudo mkdir $lib
etc="/etc/archivematica"
sudo mkdir $etc
share="/usr/share/archivematica"
sudo mkdir $share

sudo ln -s "${svnDir}src/MCPServer/etc" "${etc}/MCPServer"
sudo ln -s "${svnDir}src/MCPClient/etc" "${etc}/MCPClient"
sudo ln -s "${svnDir}src/archivematicaCommon/etc" "${etc}/archivematicaCommon"

sudo ln -s "${svnDir}src/MCPServer/lib/" "${lib}/MCPServer"
sudo ln -s "${svnDir}src/MCPClient/lib/" "${lib}/MCPClient"
sudo ln -s "${svnDir}src/archivematicaCommon/lib/" "${lib}/archivematicaCommon"
sudo ln -s "${svnDir}src/dashboard/src/" "${share}/dashboard"

if [ ! -e  /etc/init/archivematica-mcp-server.conf ] ; then
	sudo ln "${svnDir}src/MCPServer/init/archivematica-mcp-server.conf" "/etc/init/"
fi
if [ ! -e  /etc/init/archivematica-mcp-client.conf ] ; then
	sudo ln "${svnDir}src/MCPClient/init/archivematica-mcp-client.conf" "/etc/init/"
fi
if [ -e  /etc/init/openoffice-service.conf ] ; then
    sudo stop openoffice-service
	sudo rm "/etc/init/openoffice-service.conf"
fi

sudo ln "${svnDir}localDevSetup/apache/apache.default" "/etc/apache2/sites-enabled/000-default.conf" -f
sudo ln "${svnDir}localDevSetup/apache/apache.default" "/etc/apache2/sites-available/000-default.conf" -f
sudo ln -sf "${svnDir}localDevSetup/apache/httpd.conf" "/etc/apache2/httpd.conf"

sudo mkdir /var/archivematica/
sudo ln -s "${svnDir}src/MCPServer/share/sharedDirectoryStructure" "/var/archivematica/sharedDirectory"
sudo chown -R archivematica:archivematica "/var/archivematica/sharedDirectory"
sudo chmod -R g+s "/var/archivematica/sharedDirectory"

cd "$origDir" 
"${svnDir}src/MCPServer/share/postinstSharedWithDev" || echo "Problem with MCPServer/share/postinstSharedWithDev!"

echo restarting apache
sudo apache2ctl restart


