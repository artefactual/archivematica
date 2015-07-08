#!/bin/bash

databaseName=$1
dbpassword=$2  # should be "" or "-p<password>", like in localDevSetup/recreateDB.sh
currentDir="`dirname $0`"

# Add post 1.0 development to the following files
echo 'Running mysql_dev1'
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7464_processing_directory.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7478_processing_directory.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7603_metadata_identification.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7606_atk_whitespace.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_6488_aip_reingest.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7137_models.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7424_identifiers_in_es.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7714_transfer_mets.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7690_recursive_extraction.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7239_contentdm.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_8825_checksum_failure.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_8019_dspace_at_fixes.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7922_index_aips.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_8287_siegfried.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7321_dip_processing_xml.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_8415_checksum.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_8423_extract_logging.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_4757_sounds.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_8252_fpr_update.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_7595_archivesspace_upload.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_6488_aip_reingest2.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_hierarchical_dip_upload.sql;"
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_8609_automate_matching_gui.sql;"
# ...
# optional delete unused MCSL's
mysql -u root "${dbpassword}" --execute="USE ${databaseName}; SOURCE $currentDir/mysql_dev_delete_links.sql;"

touch $currentDir/mysql_dev.complete
