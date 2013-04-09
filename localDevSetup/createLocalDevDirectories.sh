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
sudo ln -s "${svnDir}src/SIPCreationTools/etc/" "${etc}/SIPCreationTools"
sudo ln -s "${svnDir}src/transcoder/etc" "${etc}/transcoder"
sudo ln -s "${svnDir}src/FPRClient/etc" "${etc}/FPRClient"



sudo ln -s "${svnDir}src/MCPServer/lib/" "${lib}/MCPServer"
sudo ln -s "${svnDir}src/MCPClient/lib/" "${lib}/MCPClient"
sudo ln -s "${svnDir}src/archivematicaCommon/lib/" "${lib}/archivematicaCommon"
sudo ln -s "${svnDir}src/SIPCreationTools/lib/" "${lib}/SIPCreationTools"
sudo ln -s "${svnDir}src/upload-qubit/lib/" "${lib}/upload-qubit"
sudo ln -s "${svnDir}src/transcoder/lib/" "${lib}/transcoder"
sudo ln -s "${svnDir}src/FPRClient/lib/" "${lib}/FPRClient"
sudo ln -s "${svnDir}src/sanitizeNames/lib/" "/usr/lib/sanitizeNames"
sudo ln -s "${svnDir}src/dashboard/src/" "${share}/dashboard"
sudo ln "${svnDir}src/SIPCreationTools/bin/archivematicaCreateMD5" "/usr/bin/"
sudo ln "${svnDir}src/SIPCreationTools/bin/archivematicaRestructureForCompliance" "/usr/bin/"

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
if [ ! -e  /etc/init/qubit-sword.conf ] ; then
        sudo ln "${svnDir}qubit-git/init/qubit-sword.conf" "/etc/init/"
fi

sudo ln "${svnDir}src/upload-qubit/upload-qubit" "/usr/bin/" 
sudo ln "${svnDir}src/transcoder/bin/transcoder" "/usr/bin/"
sudo ln "${svnDir}src/sanitizeNames/bin/sanitizeNames" "/usr/bin/"
sudo ln "${svnDir}src/FPRClient/bin/FPRClient" "/usr/bin/"

sudo ln "${svnDir}src/vm-includes/share/apache.default" "/etc/apache2/sites-enabled/000-default" -f
sudo ln "${svnDir}src/vm-includes/share/apache.default" "/etc/apache2/sites-available/default" -f
sudo ln -sf "${svnDir}src/vm-includes/share/httpd.conf" "/etc/apache2/httpd.conf"

sudo ln -sf "${svnDir}qubit-git" /var/www/ica-atom
sudo chown -R www-data:www-data "${svnDir}qubit-git"

if [ ! -e /usr/share/fits/xml/fits.xmlbackup ]; then
sudo cp /usr/share/fits/xml/fits.xml /usr/share/fits/xml/fits.xmlbackup
fi
sudo ln -f "${svnDir}externals/fits/archivematicaConfigs/fits.xml" /usr/share/fits/xml/
sudo chmod 644 /usr/share/fits/xml/fits.xml

sudo mkdir /var/archivematica/
sudo ln -s "${svnDir}src/MCPServer/share/sharedDirectoryStructure" "/var/archivematica/sharedDirectory"
sudo chown -R archivematica:archivematica "/var/archivematica/sharedDirectory"
sudo chmod -R g+s "/var/archivematica/sharedDirectory"

${svnDir}src/MCPServer/share/postinstSharedWithDev

echo restarting apache
sudo apache2ctl restart


