#!/bin/bash

databaseName="MCP"
currentDir="$(dirname $0)"
username="archivematica"
password="demo"

echo "Removing existing units"
sudo ./removeUnitsFromWatchedDirectories.py
sudo rm -rf /var/archivematica/sharedDirectory/tmp/tmp*
sudo rm -rf /var/archivematica/sharedDirectory/www/thumbnails/*

# Delete pyc's & pyo's
find ../src -name '*.py[o|c]' -delete

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
mysql -u root "${dbpassword}" --execute="GRANT SELECT, UPDATE, INSERT, DELETE, CREATE, ALTER, INDEX ON ${databaseName}.* TO '${username}'@'localhost';"

echo "Creating and populating MCP tables"
# Set up initial DB state
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/../src/MCPServer/share/mysql;"
# Run Django's syncdb
../src/dashboard/src/manage.py syncdb --noinput --settings='settings.local'
# Run SQL dev scripts
../src/MCPServer/share/mysql_dev.sh ${databaseName} ${dbpassword}
# mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/../src/MCPServer/share/mysql_dev1;"

echo "Creating MCP Views"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/../src/MCPServer/share/mysql2Views;"

dbpassword=""

#set +o verbose #echo off
printGreen="${databaseName} database created successfully."
echo -e "\e[6;32m${printGreen}\e[0m"
