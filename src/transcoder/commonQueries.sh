SIPUUID="$1"
#cd "$2"
mysql MCP --execute="SELECT Tasks.fileUUID, Tasks.fileName FROM Tasks JOIN Jobs on Tasks.jobUUID = Jobs.jobUUID WHERE Tasks.exec LIKE \"transcoderNormalizeAccess_v0.0\" AND exitCode = 0 AND Tasks.stdOut like \"%Already in access format%\" AND Jobs.SIPUUID =\"${SIPUUID}\";" > "Already in access format.txt"

mysql MCP --execute="SELECT Tasks.fileUUID, Tasks.fileName FROM Tasks JOIN Jobs on Tasks.jobUUID = Jobs.jobUUID WHERE Tasks.exec LIKE \"transcoderNormalizePreservation_v0.0\" AND exitCode = 0 AND Tasks.stdOut like \"%Already in preservation format%\" AND Jobs.SIPUUID =\"${SIPUUID}\";" > "Already in preservation format.txt"

mysql MCP --execute="SELECT Tasks.fileUUID, Tasks.fileName FROM Tasks JOIN Jobs on Tasks.jobUUID = Jobs.jobUUID WHERE Tasks.exec LIKE \"transcoderNormalizeAccess_v0.0\" AND exitCode = 0 AND Tasks.stdOut like \"%Unable to verify access readiness%\" AND Jobs.SIPUUID =\"${SIPUUID}\";" > "Files not normalized to access format and not in access format.txt"

mysql MCP --execute="SELECT Tasks.fileUUID, Tasks.fileName FROM Tasks JOIN Jobs on Tasks.jobUUID = Jobs.jobUUID WHERE Tasks.exec LIKE \"transcoderNormalizePreservation_v0.0\" AND exitCode = 0 AND Tasks.stdOut like \"%Unable to verify archival readiness.%\" AND Jobs.SIPUUID =\"${SIPUUID}\";" > "Files not normalized to preservation format and not in preservation format.txt"


mysql MCP --execute="SELECT Groups.description, FIBE.Extension, CC.classification, CT.TYPE, CR.countAttempts, CR.countOK, CR.countNotOK, CR.countAttempts - CR.countOK + CR.countNotOK AS countIncomplete, Commands.PK AS CommandPK, Commands.description FROM FileIDsByExtension AS FIBE RIGHT OUTER JOIN FileIDs ON FIBE.FileIDs = FileIDs.pk LEFT OUTER JOIN FileIDGroupMembers AS FIGM ON FIGM.fileID = FileIDs.pk LEFT OUTER JOIN Groups on Groups.pk = FIGM.groupID JOIN CommandRelationships AS CR ON FileIDs.pk = CR.FileID JOIN Commands ON CR.command = Commands.pk JOIN CommandClassifications AS CC on CR.commandClassification = CC.pk JOIN CommandTypes AS CT ON Commands.commandType = CT.pk ORDER BY Groups.description, FIBE.Extension, CC.classification" > "Normalization Paths.txt"

mysql MCP --execute="SELECT Groups.description, FIBE.Extension, CC.classification, CT.TYPE, CR.countAttempts, CR.countOK, CR.countNotOK, CR.countAttempts - CR.countOK + CR.countNotOK AS countIncomplete, Commands.PK AS CommandPK, Commands.description, Commands.command FROM FileIDsByExtension AS FIBE RIGHT OUTER JOIN FileIDs ON FIBE.FileIDs = FileIDs.pk LEFT OUTER JOIN FileIDGroupMembers AS FIGM ON FIGM.fileID = FileIDs.pk LEFT OUTER JOIN Groups on Groups.pk = FIGM.groupID JOIN CommandRelationships AS CR ON FileIDs.pk = CR.FileID JOIN Commands ON CR.command = Commands.pk JOIN CommandClassifications AS CC on CR.commandClassification = CC.pk JOIN CommandTypes AS CT ON Commands.commandType = CT.pk ORDER BY Groups.description, FIBE.Extension, CC.classification" > "Normalization Paths With Commands.txt"





