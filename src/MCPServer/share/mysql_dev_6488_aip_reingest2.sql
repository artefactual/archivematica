
-- Update for mandatory/optional fields
ALTER TABLE RightsStatementCopyright
    MODIFY copyrightStatusDeterminationDate longtext NULL,
    MODIFY copyrightApplicableStartDate longtext NULL,
    MODIFY copyrightApplicableEndDate longtext NULL
    ;
ALTER TABLE RightsStatementCopyrightDocumentationIdentifier MODIFY copyrightDocumentationIdentifierRole longtext NULL;
ALTER TABLE RightsStatementLicense
    MODIFY licenseApplicableStartDate longtext NULL,
    MODIFY licenseApplicableEndDate longtext NULL
    ;
ALTER TABLE RightsStatementLicenseDocumentationIdentifier MODIFY licenseDocumentationIdentifierRole longtext NULL;
ALTER TABLE RightsStatementStatuteInformation
    MODIFY statuteInformationDeterminationDate longtext NULL,
    MODIFY statuteApplicableStartDate longtext NULL,
    MODIFY statuteApplicableEndDate longtext NULL
    ;
ALTER TABLE RightsStatementStatuteDocumentationIdentifier MODIFY statuteDocumentationIdentifierRole longtext NULL;
ALTER TABLE RightsStatementOtherRightsInformation
    MODIFY otherRightsApplicableStartDate longtext NULL,
    MODIFY otherRightsApplicableEndDate longtext NULL
    ;
ALTER TABLE RightsStatementOtherRightsDocumentationIdentifier MODIFY otherRightsDocumentationIdentifierRole longtext NULL;
ALTER TABLE RightsStatementRightsGranted
    MODIFY startDate longtext COLLATE utf8_unicode_ci NULL,
    MODIFY endDate longtext COLLATE utf8_unicode_ci NULL
    ;

-- Only one exit code for determine version
DELETE FROM MicroServiceChainLinksExitCodes WHERE pk='7f2d5239-b464-4837-8e01-0fc43e31395d';
UPDATE MicroServiceChainLinksExitCodes SET exitCode=0 WHERE pk='6e06fd5e-3892-4e79-b64f-069876bd95a1';

-- Update DIPfromAIP to Reingest
UPDATE MicroServiceChainLinks SET microserviceGroup='Reingest AIP' WHERE pk IN ('9520386f-bb6d-4fb9-a6b6-5845ef39375f', '77c722ea-5a8f-48c0-ae82-c66a3fa8ca77', 'c103b2fb-9a6b-4b68-8112-b70597a6cd14', '60b0e812-ebbe-487e-810f-56b1b6fdd819', '31fc3f66-34e9-478f-8d1b-c29cd0012360', 'e4e19c32-16cc-4a7f-a64d-a1f180bdb164', '83d5e887-6f7c-48b0-bd81-e3f00a9da772');
-- Update Watched Directory
UPDATE WatchedDirectories SET watchedDirectoryPath = '%watchDirectoryPath%system/reingestAIP/' WHERE watchedDirectoryPath='%watchDirectoryPath%system/createDIPFromAIP/';
-- Rename DIPfromAIP
UPDATE TasksConfigs SET description = 'Approve AIP reingest' WHERE pk='c450501a-251f-4de7-acde-91c47cf62e36';
UPDATE MicroServiceChains SET description='Approve AIP reingest' WHERE startingLink='77c722ea-5a8f-48c0-ae82-c66a3fa8ca77';
UPDATE MicroServiceChains SET description='AIP reingest approval chain' WHERE startingLink='9520386f-bb6d-4fb9-a6b6-5845ef39375f';

-- Add processingMCP
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('ff516d0b-2bba-414c-88d4-f3575ebf050a', 'Reingest AIP', 'Failed', 'f89b9e0f-8789-4292-b5d0-4a330c0205e1', '7d728c39-395f-4892-8193-92f086c0546f');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('545f54cc-475c-4980-9dff-8f7e65ebaeba', 'ff516d0b-2bba-414c-88d4-f3575ebf050a', 0, '60b0e812-ebbe-487e-810f-56b1b6fdd819', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='ff516d0b-2bba-414c-88d4-f3575ebf050a' WHERE microServiceChainLink='c103b2fb-9a6b-4b68-8112-b70597a6cd14';
-- Redirect to typical normalization node
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='5d6a103c-9a5d-4010-83a8-6f4c61eb1478' WHERE microServiceChainLink IN ('83d5e887-6f7c-48b0-bd81-e3f00a9da772', 'e4e19c32-16cc-4a7f-a64d-a1f180bdb164') AND exitCode=0;

-- Reject SIP should be the SIP chain, not transfer
UPDATE MicroServiceChainChoice SET chainAvailable='a6ed697e-6189-4b4e-9f80-29209abc7937' WHERE choiceAvailableAtLink='9520386f-bb6d-4fb9-a6b6-5845ef39375f' AND chainAvailable='1b04ec43-055c-43b7-9543-bd03c6a778ba';

-- Add parse METS to DB MSCL
SET @repopulateSTC = '12fcbb37-499b-4e1c-8164-3beb1657b6dd' COLLATE utf8_unicode_ci;
SET @repopulateTC = '507c13db-63c9-476b-9a16-0c3a05aff1cb' COLLATE utf8_unicode_ci;
SET @repopulateMSCL = '33533fbb-1607-434f-a82b-cf938c05f60b' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES (@repopulateSTC, 0, 'parseMETStoDB_v1.0', '%SIPUUID% %SIPDirectory%');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@repopulateTC, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @repopulateSTC, 'Populate database with reingested AIP data');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@repopulateMSCL, 'Reingest AIP', 'Failed', @repopulateTC, '7d728c39-395f-4892-8193-92f086c0546f');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('7ec3b34f-7505-4459-a139-9d7f5738984c', @repopulateMSCL, 0, 'e4e19c32-16cc-4a7f-a64d-a1f180bdb164', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@repopulateMSCL WHERE microServiceChainLink='31fc3f66-34e9-478f-8d1b-c29cd0012360';

-- Update metadata
ALTER TABLE Dublincore ADD status varchar(8) DEFAULT 'ORIGINAL' COLLATE utf8_unicode_ci NOT NULL;
ALTER TABLE RightsStatement ADD status varchar(8) DEFAULT 'ORIGINAL' COLLATE utf8_unicode_ci NOT NULL;

-- Add SIP type to createMETS2
UPDATE StandardTasksConfigs SET arguments = '--amdSec --baseDirectoryPath "%SIPDirectory%" --baseDirectoryPathString "SIPDirectory" --fileGroupIdentifier "%SIPUUID%" --fileGroupType "sip_id" --xmlFile "%SIPDirectory%METS.%SIPUUID%.xml" --sipType "%SIPType%"' WHERE pk='0aec05d4-7222-4c28-89f4-043d20a812cc';

-- METS failure should result in a failed SIP
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@MoveSIPToFailedLink WHERE pk='ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0';
-- /METS failure
