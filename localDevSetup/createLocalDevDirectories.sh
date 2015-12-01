#!/bin/bash

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
log="/var/log/archivematica"
sudo mkdir -p $log
sudo chown -R archivematica:archivematica $log
sudo chmod g+ws $log

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


