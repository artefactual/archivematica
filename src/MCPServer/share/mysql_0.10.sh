#!/bin/bash

databaseName=$1
dbpassword=$2  # should be "" or "-p<password>", like in localDevSetup/recreateDB.sh
currentDir="`dirname $0`"

# To regenerate table creation SQL in mysql_0.10_dev2_fpr_table_create.sql:
# python2 manage.py sql fpr --settings='settings.local' > ~/archivematica/src/MCPServer/share/mysql_0.10_dev2_fpr_table_create.sql
# sed -i 's/CREATE TABLE `/CREATE TABLE IF NOT EXISTS `/g' ~/archivematica/src/MCPServer/share/mysql_0.10_dev2_fpr_table_create.sql
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_0.10_dev1.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_0.10_dev2_fpr_table_create.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_0.10_dev3.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_0.10_dev4_atk_dip_upload.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_0.10_dev5.sql;"
