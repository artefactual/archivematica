-- These date fields used to use 0 as a "no date" value,
-- but Django is not able to represent that value.
-- Make them nullable and represent all non-dates as NULL instead.
ALTER TABLE Files
	MODIFY COLUMN removedTime timestamp NULL DEFAULT NULL;
UPDATE Files SET removedTime=NULL WHERE removedTime=0;

ALTER TABLE Tasks
	MODIFY COLUMN startTime timestamp NULL DEFAULT NULL,
	MODIFY COLUMN endTime timestamp NULL DEFAULT NULL;
UPDATE Tasks SET startTime=NULL WHERE startTime=0;
UPDATE Tasks SET endTime=NULL WHERE endTime=0;

-- Update fileGroupType keys to Django's version instead of the column name
UPDATE StandardTasksConfigs
	SET arguments='--sipUUID "%SIPUUID%" --basePath "%SIPDirectory%" --xmlFile "%SIPDirectory%"metadata/submissionDocumentation/METS.xml --basePathString "transferDirectory" --fileGroupIdentifier "transfer_id"'
	WHERE execute='createMETS_v0.0';
UPDATE StandardTasksConfigs
	SET arguments='--amdSec --baseDirectoryPath "%SIPDirectory%" --baseDirectoryPathString "SIPDirectory" --fileGroupIdentifier "%SIPUUID%" --fileGroupType "sip_id" --xmlFile "%SIPDirectory%METS.%SIPUUID%.xml"'
	WHERE pk='0aec05d4-7222-4c28-89f4-043d20a812cc';
UPDATE StandardTasksConfigs
	SET arguments='--baseDirectoryPath "%SIPDirectory%" --baseDirectoryPathString "SIPDirectory" --fileGroupIdentifier "%SIPUUID%" --fileGroupType "sip_id" --xmlFile "%SIPDirectory%METS.%SIPUUID%.xml"'
	WHERE pk='1f3f4e3b-2f5a-47a2-8d1c-27a6f1b94b95';
UPDATE StandardTasksConfigs
	set arguments='"%SIPDirectory%objects/metadata/" "%SIPUUID%" "%date%" "%taskUUID%" "SIPDirectory" "sip_id" "%SIPDirectory%"'
	WHERE pk='58b192eb-0507-4a83-ae5a-f5e260634c2a';
UPDATE StandardTasksConfigs
	set arguments='"%SIPDirectory%objects/submissionDocumentation/" "%SIPUUID%" "%date%" "%taskUUID%" "SIPDirectory" "sip_id" "%SIPDirectory%"'
	WHERE pk='ad65bf76-3491-4c3d-afb0-acc94ff28bee';
UPDATE StandardTasksConfigs
	SET arguments='"%SIPObjectsDirectory%" "%SIPUUID%" "%date%" "%taskUUID%" "transferDirectory" "transfer_id" "%SIPDirectory%"'
	WHERE pk IN ('f368a36d-2b27-4f08-b662-2828a96d189a', '80759ad1-c79a-4c3b-b255-735c28a50f9e');
UPDATE StandardTasksConfigs
	SET arguments='"%SIPObjectsDirectory%attachments/" "%SIPUUID%" "%date%" "%taskUUID%" "transferDirectory" "transfer_id" "%SIPDirectory%"'
	WHERE pk='89b4d447-1cfc-4bbf-beaa-fb6477b00f70';
