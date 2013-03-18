#!/bin/bash

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$


#-- configuration
databaseUser="root"
databasePassword=""

#-- script
DATE="`date +"%Y.%m.%d-%H.%M.%S"`"

if [[ $databasePassword != "" ]]; then
        dbPwd="-p${databasePassword}"
    else
        dbPwd=""
fi

mysql MCP -H -u ${databaseUser} ${dbPwd} -e "SELECT * FROM PDI_by_unit;" > ${DATE}_${HOSTNAME}_PDI_by_unit.html
mysql MCP -H -u ${databaseUser} ${dbPwd} -e "SELECT * FROM processingDurationInformation;" > ${DATE}_${HOSTNAME}_processingDurationInformation.html
mysql MCP -H -u ${databaseUser} ${dbPwd} -e "SELECT * FROM jobDurationsView" > ${DATE}_${HOSTNAME}_jobDurationsView.html
mysql MCP -H -u ${databaseUser} ${dbPwd} -e "status" > ${DATE}_${HOSTNAME}_mysql_status.log
mysqldump -u ${databaseUser} ${dbPwd} MCP > ${DATE}_${HOSTNAME}_MCP_DUMP.sql
netstat -s > ${DATE}_${HOSTNAME}_netstat_summary.log


