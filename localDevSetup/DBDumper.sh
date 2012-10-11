#!/bin/bash

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>>
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

databaseName="MCP"
set -e
echo -n "Enter the DATABASE root password (Hit enter if blank):"
read dbpassword

if [ ! -z "$dbpassword" ] ; then
  dbpassword="-p${dbpassword}"
else
  dbpassword=""
fi




mysqldump="mysqldump -u root ${dbpassword} ${databaseName}"
dumpTables="--skip-triggers --skip-comments -d"
dumpData="--skip-triggers --skip-comments --no-create-info"
MCPDumpSQLLocation="../src/MCPServer/share/mysql2"

#echo 'START TRANSACTION;' > $MCPDumpSQLLocation
echo 'SET foreign_key_checks = 0;' > $MCPDumpSQLLocation
#MCP
#-- MCP dump tables --
$mysqldump Accesses Agents MetadataAppliesToTypes Dublincore RightsStatement RightsStatementCopyright RightsStatementCopyrightNote RightsStatementCopyrightDocumentationIdentifier RightsStatementLicense RightsStatementLicenseDocumentationIdentifier RightsStatementLicenseNote ArchivematicaRightsStatement RightsStatementStatuteInformation RightsStatementStatuteInformationNote RightsStatementStatuteDocumentationIdentifier RightsStatementOtherRightsInformation RightsStatementOtherRightsDocumentationIdentifier RightsStatementOtherRightsNote RightsStatementRightsGranted RightsStatementRightsGrantedRestriction RightsStatementRightsGrantedNote RightsStatementLinkingAgentIdentifier Tasks AIPs Notifications Sounds TaskTypes TasksConfigs MicroServiceChainLinks Transfers SIPs Files FilesFits FilesIDs Events Derivations MicroServiceChainLinksExitCodes Jobs MicroServiceChains MicroServiceChainChoice MicroServiceChoiceReplacementDic WatchedDirectoriesExpectedTypes WatchedDirectories StandardTasksConfigs SourceDirectories TasksConfigsAssignMagicLink TasksConfigsStartLinkForEachFile  $dumpTables >> $MCPDumpSQLLocation

#-- MCP dump data --
$mysqldump Accesses Agents MetadataAppliesToTypes Sounds TaskTypes TasksConfigs MicroServiceChainLinks MicroServiceChainLinksExitCodes MicroServiceChains MicroServiceChainChoice MicroServiceChoiceReplacementDic WatchedDirectoriesExpectedTypes WatchedDirectories StandardTasksConfigs SourceDirectories TasksConfigsAssignMagicLink TasksConfigsStartLinkForEachFile $dumpData >> $MCPDumpSQLLocation





#Transcoder
$mysqldump CommandTypes CommandClassifications CommandsSupportedBy Commands FileIDTypes FileIDs CommandRelationships FileIDsByExtension FileIDsByFitsFileUtilityFormat FileIDsByPronom Groups FileIDGroupMembers SubGroups DefaultCommandsForClassifications FilesIdentifiedIDs  $dumpTables >> $MCPDumpSQLLocation
$mysqldump CommandTypes CommandClassifications CommandsSupportedBy Commands FileIDTypes FileIDs CommandRelationships FileIDsByExtension FileIDsByFitsFileUtilityFormat FileIDsByPronom Groups FileIDGroupMembers SubGroups DefaultCommandsForClassifications $dumpData >> $MCPDumpSQLLocation #Source of FPR DATA


#ElasticsearchIndexBackup
$mysqldump ElasticsearchIndexBackup >> $MCPDumpSQLLocation



#Dashboard
#-- Dashboard dump tables --
$mysqldump auth_message auth_user auth_user_groups auth_user_user_permissions auth_group auth_group_permissions auth_permission django_content_type django_session $dumpTables >> $MCPDumpSQLLocation
$mysqldump auth_message auth_user_groups auth_user_user_permissions auth_group auth_group_permissions auth_permission django_content_type django_session  $dumpData >> $MCPDumpSQLLocation



echo 'SET foreign_key_checks = 1;' >> $MCPDumpSQLLocation
#echo 'COMMIT;' >> $MCPDumpSQLLocation


#VIEWS
#-- MCP-views --
##$mysqldump filesPreservationAccessFormatStatus jobDurationsView lastJobsInfo lastJobsTasks processingDurationInformation processingDurationInformation2 processingDurationInformationByClient taskDurationsView transfersAndSIPs $dumpTables >> $MCPDumpSQLLocation

#-- Transcoder-views --
##$mysqldump filesPreservationAccessFormatStatus  >> $MCPDumpSQLLocation

#-- Dashboard dump Dashboard-views --
##$mysqldump developmentAide_choicesDisplayed $dumpTables >> $MCPDumpSQLLocation

