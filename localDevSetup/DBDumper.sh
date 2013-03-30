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

# @package Archivematica
# @author Joseph Perry <joseph@artefactual.com>>
# @version svn: $Id$

origDir="`pwd`"
cd "`dirname $0`"
databaseName="MCP"
set -e
echo -n "Enter the DATABASE root password (Hit enter if blank):"
read dbpassword

if [ ! -z "$dbpassword" ] ; then
  dbpassword="-p${dbpassword}"
else
  dbpassword=""
fi

#remove FPR links for local processing
../src/FPRClient/lib/removeLinks.py

mysqldump="mysqldump -u root ${dbpassword} ${databaseName}"
dumpTables="--skip-triggers --skip-comments -d"
dumpData="--skip-triggers --skip-comments --no-create-info --extended-insert=FALSE --complete-insert=TRUE --order-by-primary"
# Quick load dump for testing
#dumpData="--skip-triggers --skip-comments --no-create-info --extended-insert=TRUE"
MCPDumpSQLLocation="../src/MCPServer/share/mysql"
InitialFPRData="../src/FPRClient/share/mysql"

#echo 'START TRANSACTION;' > $MCPDumpSQLLocation
echo 'SET foreign_key_checks = 0;' > $MCPDumpSQLLocation
#MCP
#--todo: remove transcoder links

#-- MCP dump tables --
$mysqldump Accesses Agents MetadataAppliesToTypes Dublincore RightsStatement RightsStatementCopyright RightsStatementCopyrightNote RightsStatementCopyrightDocumentationIdentifier RightsStatementLicense RightsStatementLicenseDocumentationIdentifier RightsStatementLicenseNote ArchivematicaRightsStatement RightsStatementStatuteInformation RightsStatementStatuteInformationNote RightsStatementStatuteDocumentationIdentifier RightsStatementOtherRightsInformation RightsStatementOtherRightsDocumentationIdentifier RightsStatementOtherRightsNote RightsStatementRightsGranted RightsStatementRightsGrantedRestriction RightsStatementRightsGrantedNote RightsStatementLinkingAgentIdentifier Tasks Notifications Sounds TaskTypes TasksConfigs MicroServiceChainLinks Transfers SIPs Files FilesFits FilesIDs Events Derivations MicroServiceChainLinksExitCodes Jobs MicroServiceChains MicroServiceChainChoice MicroServiceChoiceReplacementDic WatchedDirectoriesExpectedTypes WatchedDirectories StandardTasksConfigs TasksConfigsAssignMagicLink TasksConfigsStartLinkForEachFile UnitVariables TasksConfigsSetUnitVariable TasksConfigsUnitVariableLinkPull  $dumpTables >> $MCPDumpSQLLocation

#-- MCP dump data --
$mysqldump Accesses Agents MetadataAppliesToTypes Sounds TaskTypes TasksConfigs MicroServiceChainLinks MicroServiceChainLinksExitCodes MicroServiceChains MicroServiceChainChoice MicroServiceChoiceReplacementDic WatchedDirectoriesExpectedTypes WatchedDirectories StandardTasksConfigs TasksConfigsAssignMagicLink TasksConfigsStartLinkForEachFile  TasksConfigsSetUnitVariable TasksConfigsUnitVariableLinkPull $dumpData >> $MCPDumpSQLLocation





#Transcoder
#Reset counters for commit
mysql -u root ${dbpassword} ${databaseName} --execute "UPDATE CommandRelationships SET countAttempts=0, countOK=0, countNotOK=0;"
$mysqldump CommandTypes CommandClassifications CommandsSupportedBy Commands FileIDTypes FileIDs CommandRelationships  Groups FileIDGroupMembers SubGroups DefaultCommandsForClassifications FileIDsBySingleID FilesIdentifiedIDs $dumpTables >> $MCPDumpSQLLocation


#ElasticsearchIndexBackup
$mysqldump ElasticsearchIndexBackup  $dumpTables >> $MCPDumpSQLLocation



#Dashboard
#-- Dashboard dump tables --
$mysqldump auth_message auth_user auth_user_groups auth_user_user_permissions auth_group auth_group_permissions auth_permission django_content_type django_session SourceDirectories DashboardSettings StorageDirectories tastypie_apiaccess tastypie_apikey $dumpTables >> $MCPDumpSQLLocation
$mysqldump auth_message auth_user_groups auth_user_user_permissions auth_group auth_group_permissions auth_permission django_content_type $dumpData >> $MCPDumpSQLLocation

#initial FPR dump
$mysqldump Commands  CommandClassifications  CommandRelationships  CommandTypes  CommandsSupportedBy  DefaultCommandsForClassifications  FileIDs  FileIDGroupMembers  FileIDTypes  FileIDsBySingleID  Groups  SubGroups $dumpData >> $InitialFPRData

echo 'SET foreign_key_checks = 1;' >> $MCPDumpSQLLocation
#echo 'COMMIT;' >> $MCPDumpSQLLocation

sed -i -e 's/ AUTO_INCREMENT=[0-9]\+//' $MCPDumpSQLLocation

#re-add FPR links for local processing
../src/FPRClient/lib/addLinks.py

#VIEWS
#-- MCP-views --
##$mysqldump filesPreservationAccessFormatStatus jobDurationsView lastJobsInfo lastJobsTasks processingDurationInformation processingDurationInformation2 processingDurationInformationByClient taskDurationsView transfersAndSIPs $dumpTables >> $MCPDumpSQLLocation

#-- Transcoder-views --
##$mysqldump filesPreservationAccessFormatStatus  >> $MCPDumpSQLLocation

#-- Dashboard dump Dashboard-views --
##$mysqldump developmentAide_choicesDisplayed $dumpTables >> $MCPDumpSQLLocation

#--todo: add transcoder links

cd "$origDir"

