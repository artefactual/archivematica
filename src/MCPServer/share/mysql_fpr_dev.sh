#!/bin/bash

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica. If not, see <http://www.gnu.org/licenses/>>.

origDir="`pwd`"
cd "`dirname $0`"

username="root"
databaseName="MCP"
set -e
echo -n "Enter the DATABASE root password (Hit enter if blank):"
read dbpassword

if [ ! -z "$dbpassword" ] ; then
  dbpassword="-p${dbpassword}"
else
  dbpassword=""
fi

pwd
# For a new dump,
# mysqldump -u root --complete-insert --no-create-info MCP fpr_idtool fpr_idcommand fpr_formatgroup fpr_fpcommand fpr_fptool fpr_format fpr_fprule fpr_idrule fpr_formatversion > mysql_fpr_1.0.sql
# mysqldump -u root --complete-insert --no-create-info MCP MicroServiceChoiceReplacementDic --where "replacementDic LIKE '%IDCommand%' AND replacementDic NOT LIKE '%None%'" >> mysql_fpr_1.0.sql

#fpr data is now included in main mysql dump.
#any new fpr changes should be added to a mysqL-fpr_dev_XXXX.sql file
#add a reference to that new file here in your branch
#mysql -u $username $dbpassword --execute="source ./delete_fpr_data.sql" $databaseName
#mysql -u $username $dbpassword --execute="source ./mysql_fpr_1.0.sql" $databaseName
#mysql -u $username $dbpassword --execute="source ./mysql_fpr_dev1.sql" $databaseName
# ./migration1.sh
# mysql -u $username $dbpassword --execute="source ./mysql_dev2.sql" $databaseName
# ./migration2.sh
# mysql -u $username $dbpassword --execute="source ./mysql_dev3.sql" $databaseName

cd "$origDir"
dbpassword=""
