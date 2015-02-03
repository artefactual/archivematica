#!/bin/bash

databaseName=$1
dbpassword=$2  # should be "" or "-p<password>", like in localDevSetup/recreateDB.sh
currentDir="`dirname $0`"

# Add post 1.3.1 development to the following files
echo 'Running mysql_dev1'
#mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_XXXX_your_script.sql;"

# ...
