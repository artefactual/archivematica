#!/bin/bash

databaseName=$1
dbpassword=$2  # should be "" or "-p<password>", like in localDevSetup/recreateDB.sh
currentDir="`dirname $0`"

# To regenerate table creation SQL in mysql_dev2_fpr_table_create.sql:
# python2 manage.py sql fpr --settings='settings.local' > ~/archivematica/src/MCPServer/share/mysql_dev2_fpr_table_create.sql
# sed -i 's/CREATE TABLE `/CREATE TABLE IF NOT EXISTS `/g' ~/archivematica/src/MCPServer/share/mysql_dev2_fpr_table_create.sql
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev1.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev2_fpr_table_create.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev3.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev4_atk_dip_upload.sql;"
