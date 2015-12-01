#!/bin/bash

databaseName=$1
dbpassword=$2  # should be "" or "-p<password>", like in localDevSetup/recreateDB.sh
currentDir="`dirname $0`"

# Add post release development to the following files
echo 'Running mysql_dev_pre_django'
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_pre_django_8634_events_agents.sql;"
