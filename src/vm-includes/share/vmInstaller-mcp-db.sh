#!/bin/bash

databaseName="MCP"
username="demo"
password="demo"
dpPassword="$1"
sudo mysqladmin create "$databaseName" $dpPassword
#sudo mysql $databaseName
sudo mysql $dpPassword --execute="source /usr/share/archivematica/mysql" "$databaseName"
sudo mysql $dpPassword --execute="CREATE USER '${username}'@'localhost' IDENTIFIED BY '${password}'"
sudo mysql $dpPassword --execute="GRANT SELECT, UPDATE, INSERT ON ${databaseName}.* TO '${username}'@'localhost'" 
