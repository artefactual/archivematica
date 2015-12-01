#!/bin/bash

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
