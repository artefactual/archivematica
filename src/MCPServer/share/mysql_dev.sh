#!/bin/bash

databaseName=$1
dbpassword=$2  # should be "" or "-p<password>", like in localDevSetup/recreateDB.sh
currentDir="`dirname $0`"

# Add post 1.4.0 development to the following files
echo 'Running mysql_dev1'
#mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_XXXX_your_new_update.sql;"
# ...
# optional delete unused MCSL's
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_delete_links.sql;"

touch $currentDir/mysql_dev.complete
