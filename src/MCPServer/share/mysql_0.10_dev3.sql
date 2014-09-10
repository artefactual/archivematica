-- Common
SET @MoveTransferToFailedLink = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd';
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';

-- /Common

CREATE TABLE IF NOT EXISTS south_migrationhistory (
  id int(11) NOT NULL AUTO_INCREMENT,
  app_name varchar(255) NOT NULL,
  migration varchar(255) NOT NULL,
  applied datetime NOT NULL,
  PRIMARY KEY (id)
) ;
-- /FPR admin additions

-- Issue 5575 FPR integration with Storage Service

-- Add choice of which format ID tool to use before identify and extract metadata

-- Updated FilesIdentifiedIDs constraint
ALTER TABLE `FilesIdentifiedIDs` DROP FOREIGN KEY `FilesIdentifiedIDs_ibfk_2`;
ALTER TABLE `FilesIdentifiedIDs` ADD CONSTRAINT `FilesIdentifiedIDs_ibfk_2` FOREIGN KEY (`fileID`) REFERENCES `fpr_formatversion` (`uuid`);
-- sanitize transfer name
SET @startingLink='a329d39b-4711-4231-b54e-b5958934dccb' COLLATE utf8_unicode_ci;
-- characterize and extract metadata
SET @characterizeExtractMetadata='303a65f6-a16f-4a06-807b-cb3425a30201' COLLATE utf8_unicode_ci;

-- Add Identify File Format
SET @identifyFileFormatMSCL='2522d680-c7d9-4d06-8b11-a28d8bd8a71f' COLLATE utf8_unicode_ci;
SET @identifyFileFormatTC='8558d885-d6c2-4d74-af46-20da45487ae7' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('9c3680a5-91cb-413f-af4e-d39c3346f8db', 0, 'identifyFileFormat_v0.0', '%IDCommand% %relativeLocation% %fileUUID%', 'objects');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@identifyFileFormatTC, 'a6b1c323-7d36-428e-846a-e7e819423577', '9c3680a5-91cb-413f-af4e-d39c3346f8db', 'Identify file format');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@identifyFileFormatMSCL, 'Characterize and extract metadata', 'Failed', '8558d885-d6c2-4d74-af46-20da45487ae7', @characterizeExtractMetadata);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('1f877d65-66c5-49da-bf51-2f1757b59c90', @identifyFileFormatMSCL, 0, @characterizeExtractMetadata, 'Completed successfully');

-- Add Select file format identification command
SET @selectFileIDCommandMSCL='f09847c2-ee51-429a-9478-a860477f6b8d' COLLATE utf8_unicode_ci;
SET @selectFileIDCommandTC='97545cb5-3397-4934-9bc5-143b774e4fa7' COLLATE utf8_unicode_ci;
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@selectFileIDCommandTC, '9c84b047-9a6d-463f-9836-eafa49743b84', NULL, 'Select file format identification command');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@selectFileIDCommandMSCL, 'Characterize and extract metadata', 'Failed', @selectFileIDCommandTC, @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('ef56e6a6-5280-4227-9799-9c1d2d7c0919', @selectFileIDCommandMSCL, 0, @identifyFileFormatMSCL, 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@selectFileIDCommandMSCL WHERE microServiceChainLink=@startingLink;

-- Remove identifyFilesByExtension
SET @loadLabels='1b1a4565-b501-407b-b40f-2f20889423f1';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@loadLabels WHERE microServiceChainLink=@characterizeExtractMetadata;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@loadLabels WHERE pk=@characterizeExtractMetadata;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink='1297fb61-ba59-4286-9a7f-0c55203f99e8';
DELETE FROM MicroServiceChainLinks WHERE pk='1297fb61-ba59-4286-9a7f-0c55203f99e8';

-- Remove more identifyFilesByExtension
-- X -> remove link -> Y
SET @del = 'a5bb37b4-41b4-46cc-b10d-fbc82d87edf0' COLLATE utf8_unicode_ci;
SET @Y='8c425901-13c7-4ea2-8955-2abdbaa3d67a';
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@Y where defaultNextChainLink=@del;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@Y where nextMicroServiceChainLink=@del;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@del;
DELETE FROM MicroServiceChainLinks WHERE pk=@del;
SET @del = '9b06bf64-5b81-4ae7-9618-f3b653547896' COLLATE utf8_unicode_ci;
SET @Y='634918c4-1f06-4f62-9ed2-a3383aa2e962';
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@Y WHERE defaultNextChainLink=@del;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@Y where nextMicroServiceChainLink=@del;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@del;
DELETE FROM MicroServiceChainLinks WHERE pk=@del;

-- Remove select format identification tool in SIP and its children
SET @resumeAfterNormalizationFileIdentificationToolSelected='83484326-7be7-4f9f-b252-94553cd42370';
SET @magiclink1='f63970a2-dc63-4ab4-80a6-9bfd72e3cf5a' COLLATE utf8_unicode_ci;
SET @magiclink2='c73acd63-19c9-4ca8-912c-311107d0454e' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@resumeAfterNormalizationFileIdentificationToolSelected WHERE microServiceChainLink in (@magiclink1, @magiclink2);
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@resumeAfterNormalizationFileIdentificationToolSelected WHERE pk in (@magiclink1, @magiclink2);
-- nodes to delete
SET @d1='56b42318-3eb3-466c-8a0d-7ac272136a96' COLLATE utf8_unicode_ci;
SET @d2='a4f7ebb7-3bce-496f-a6bc-ef73c5ce8118' COLLATE utf8_unicode_ci;
SET @d3='5bddbb67-76b4-4bcb-9b85-a0d9337e7042' COLLATE utf8_unicode_ci;
SET @d4='37f2e794-6485-4524-a384-37b3209916ed' COLLATE utf8_unicode_ci;
SET @d5='766b23ad-65ed-46a3-aa2e-b9bdaf3386d0' COLLATE utf8_unicode_ci;
SET @d6='d7a0e33d-aa3c-435f-a6ef-8e39f2e7e3a0' COLLATE utf8_unicode_ci;
SET @d7='b549130c-943b-4791-b1f6-93b837990138' COLLATE utf8_unicode_ci;
SET @d8='5fbecef2-49e9-4585-81a2-267b8bbcd568' COLLATE utf8_unicode_ci;
SET @d9='4c4281a1-43cd-4c6e-b1dc-573bd1a23c43' COLLATE utf8_unicode_ci;
SET @d10='982229bd-73b8-432e-a1d9-2d9d15d7287d' COLLATE utf8_unicode_ci;
SET @d11='91d7e5f3-d89b-4c10-83dd-ab417243f583' COLLATE utf8_unicode_ci;
SET @d12='fbebca6d-53bc-42ef-98ea-3f707e53832e' COLLATE utf8_unicode_ci;
SET @d13='f4dea20e-f3fe-4a37-b20f-0e70a7bc960e' COLLATE utf8_unicode_ci;
SET @d14='f87f13d2-8aae-45c9-bc8a-e5c32a37654e' COLLATE utf8_unicode_ci;
SET @d15='aa5b8a69-ce6d-49f7-a07f-4683ccd6fcbf' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8, @d9, @d10, @d11, @d12, @d13, @d14, @d15);
DELETE FROM MicroServiceChainChoice WHERE chainAvailable IN (SELECT pk FROM MicroServiceChains WHERE startingLink IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8, @d9, @d10, @d11, @d12, @d13, @d14, @d15));
DELETE FROM MicroServiceChains WHERE startingLink IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8, @d9, @d10, @d11, @d12, @d13, @d14, @d15);
DELETE FROM MicroServiceChainLinks WHERE defaultNextChainLink IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8, @d9, @d10, @d11, @d12, @d13, @d14, @d15);
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8, @d9, @d10, @d11, @d12, @d13, @d14, @d15);

-- /Issue 5575


-- Issue 5633 'Add Select file format identification command watched dir

-- Insert move to watched dir before Select file format ID command
-- NOTE to make this work with multiple chains, may have to set UnitVar for where to go after chain starts, like with Normalization
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('3e8f5b9e-b3a6-4782-a944-749de6ae234d', 0, 'moveTransfer_v0.0', '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/selectFormatIDToolTransfer/."  "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('38cea9c4-d75c-48f9-ba88-8052e9d3aa61', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '3e8f5b9e-b3a6-4782-a944-749de6ae234d', 'Move to select file ID tool');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('d1b27e9e-73c8-4954-832c-36bd1e00c802', 'Characterize and extract metadata', 'Failed', '38cea9c4-d75c-48f9-ba88-8052e9d3aa61', @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('6740b87f-6d30-4f43-8848-1371fe9b08c5', 'd1b27e9e-73c8-4954-832c-36bd1e00c802', 0, NULL, 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='d1b27e9e-73c8-4954-832c-36bd1e00c802' WHERE microServiceChainLink='a329d39b-4711-4231-b54e-b5958934dccb';

-- Add MicroServiceChain pointing to Select file format ID command
SET @selectFormatIDChain='bd94cc9b-7990-45a2-a255-a1b70936f9f2';
INSERT INTO MicroServiceChains(pk, startingLink, description) VALUES (@selectFormatIDChain, @selectFileIDCommandMSCL, 'Identify file format');

-- Add WatchedDirectory for folder/chain
SET @watchedDirExpectTransfer='f9a3a93b-f184-4048-8072-115ffac06b5d';
INSERT INTO WatchedDirectories(pk, watchedDirectoryPath, chain, expectedType) VALUES ('11a4f280-9b43-45a0-9ebd-ec7a115ccc62', "%watchDirectoryPath%workFlowDecisions/selectFormatIDToolTransfer/", @selectFormatIDChain, @watchedDirExpectTransfer);

-- / Issue 5633


-- Issue 5674
-- Add MSCL choice for run format identification before normalization (in Ingest)

-- Add Identify File Format
SET @selectFileIDCommandMSCLIngest='7a024896-c4f7-4808-a240-44c87c762bc5' COLLATE utf8_unicode_ci;
SET @identifyFileFormatMSCLIngest='2dd53959-8106-457d-a385-fee57fc93aa9' COLLATE utf8_unicode_ci;
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@identifyFileFormatMSCLIngest, 'Normalize', 'Failed', @identifyFileFormatTC, '7d728c39-395f-4892-8193-92f086c0546f');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('71a09b45-3f64-4618-af51-6a960ae16754', @identifyFileFormatMSCLIngest, 0, @resumeAfterNormalizationFileIdentificationToolSelected, 'Completed successfully');
-- Add Select file format identification command
SET @selectFileIDCommandTCIngest='f8d0b7df-68e8-4214-a49d-60a91ed27029' COLLATE utf8_unicode_ci;
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@selectFileIDCommandTCIngest, '9c84b047-9a6d-463f-9836-eafa49743b84', NULL, 'Select pre-normalize file format identification command');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@selectFileIDCommandMSCLIngest, 'Normalize', 'Failed', @selectFileIDCommandTCIngest, @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('ab61e4b6-1167-461f-921e-ebcb5126ff89', @selectFileIDCommandMSCLIngest, 0, @identifyFileFormatMSCLIngest, 'Completed successfully');
-- Add skip option to select format id command (in both places)
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ("1f77af0a-2f7a-468f-af8c-653a9e61ca4f", @selectFileIDCommandMSCL, "Skip File Identification", '{"%IDCommand%":"None"}');
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ("3c1faec7-7e1e-4cdd-b3bd-e2f05f4baa9b", @selectFileIDCommandMSCLIngest, "Use existing data", '{"%IDCommand%":"None"}');

-- Insert move to watched dir before Select file format ID command
-- NOTE to make this work with multiple chains, may have to set UnitVar for where to go after chain starts, like with Normalization
SET @moveToFormatMSCL='a58bd669-79af-4999-8654-951f638d4457' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('179373e8-a6b4-4274-a245-ca3f4b105396', 0, 'moveSIP_v0.0', '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/selectFormatIDToolIngest/."  "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('8b846431-5da9-4743-906d-2cdc4e777f8f', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '179373e8-a6b4-4274-a245-ca3f4b105396', 'Move to select file ID tool');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@moveToFormatMSCL, 'Normalize', 'Failed', '8b846431-5da9-4743-906d-2cdc4e777f8f', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('eb5c83b1-1f60-4f77-85af-ee8cccf01924', @moveToFormatMSCL, 0, NULL, 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink =@moveToFormatMSCL WHERE microServiceChainLink IN (@magiclink1, @magiclink2);
UPDATE MicroServiceChainLinks SET defaultNextChainLink = @moveToFormatMSCL WHERE pk IN (@magiclink1, @magiclink2);


-- Add MicroServiceChain pointing to Select file format ID command
SET @selectFormatIDChain2='0ea3a6f9-ff37-4f32-ac01-eec5393f008a';
INSERT INTO MicroServiceChains(pk, startingLink, description) VALUES (@selectFormatIDChain2, @selectFileIDCommandMSCLIngest, 'Pre-normalize identify file format');

-- Add WatchedDirectory for folder/chain
SET @watchedDirExpectSIP='76e66677-40e6-41da-be15-709afb334936';
INSERT INTO WatchedDirectories(pk, watchedDirectoryPath, chain, expectedType) VALUES ('50c378ed-6a88-4988-bf21-abe1ea3e0115', "%watchDirectoryPath%workFlowDecisions/selectFormatIDToolIngest/", @selectFormatIDChain2, @watchedDirExpectSIP);



-- This is from AIP->DIP workflow
-- UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@selectFileIDCommandMSCLIngest WHERE microServiceChainLink='b063c4ce-ada1-4e72-a137-800f1c10905c';


-- /Issue 5674


-- Issue 5759

-- Clean up of Transfer MSCL
DELETE FROM MicroServiceChainLinksExitCodes WHERE pk='d82b17d1-ad41-43a3-90a8-2649a2ab9375';
DELETE FROM MicroServiceChainLinks WHERE pk='ea69c596-3903-4de7-9ea0-d1b8da73473a';
UPDATE MicroServiceChainLinks SET currentTask='ad38cdea-d1da-4d06-a7e5-6f75da85a718' WHERE currentTask='10846796-f1ee-499a-9908-4c49f8edd7e6';
DELETE FROM TasksConfigs WHERE pk='10846796-f1ee-499a-9908-4c49f8edd7e6';
DELETE FROM StandardTasksConfigs WHERE pk='f6dcdd6f-fcd4-4314-9eec-765ea776116b';

-- Remove stubbed chain of 'Create single SIP'
SET @chainStart='6d88a276-860b-40e9-b941-772a654d6a51' COLLATE utf8_unicode_ci;
SET @c2 = '5f99ca60-67b8-4d70-8173-fc22ebda9202' COLLATE utf8_unicode_ci;
SET @c3 = 'e564b156-804f-4ab0-92ea-43bf1de95c40' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChains WHERE startingLink=@chainStart;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@chainStart, @c2, @c3);
DELETE FROM MicroServiceChainLinks WHERE pk IN (@chainStart, @c2, @c3);
DELETE FROM TasksConfigs WHERE pk='95678fce-e651-4b5e-8cb7-c596b18b8320';
DELETE FROM StandardTasksConfigs WHERE pk='b0034946-4a5f-4ee4-a4f8-bcbc9ff7e1e9';

-- Merge DSPACE with standard transfer & delete extra MSCLs
SET @sanitizeObjectNames='2584b25c-8d98-44b7-beca-2b3ea2ea2505' COLLATE utf8_unicode_ci;
SET @dspaceIDMETS='8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinks SET defaultNextChainLink = @sanitizeObjectNames WHERE pk=@dspaceIDMETS;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@sanitizeObjectNames WHERE microServiceChainLink=@dspaceIDMETS;
SET @d1 = 'd2c2b65d-36c6-4636-9459-b5f0b4b0065a' COLLATE utf8_unicode_ci; -- index
SET @d2 = '8a0bc7c6-f7c2-4656-a690-976660c66a8a' COLLATE utf8_unicode_ci; -- move to completed
SET @d3 = '730df394-6690-42f3-8b68-37f029d4d03e' COLLATE utf8_unicode_ci; -- set file perm
SET @d4 = 'be093c77-7bdc-406e-a1fd-7ebe01d0fd9b' COLLATE utf8_unicode_ci; -- load labels
SET @d5 = 'd817d32d-10d8-46c7-a68e-9eab82d8cd77' COLLATE utf8_unicode_ci; -- id by ext
SET @d6 = '7688473b-7740-4281-a903-7caae1cde29c' COLLATE utf8_unicode_ci; -- char and extract
SET @d7 = '4a332ca2-4742-4fba-acc4-6f6b78e7da88' COLLATE utf8_unicode_ci; -- sanitize transfer name
SET @d8 = '710cc1ca-090c-422f-8afc-f89858d64610' COLLATE utf8_unicode_ci; -- sanitize object names
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8);
SET foreign_key_checks = 0;
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8);
SET foreign_key_checks = 1;
DELETE FROM TasksConfigs WHERE pk IN (SELECT currentTask FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2, @d4, @d5));

-- Merge maildir with standard transfer & delete extra MSCLs
SET @sanitizeTransferName='a329d39b-4711-4231-b54e-b5958934dccb' COLLATE utf8_unicode_ci;
SET @maildirSanitizeObj='c8f7bf7b-d903-42ec-bfdf-74d357ac4230' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@sanitizeTransferName WHERE microServiceChainLink=@maildirSanitizeObj;
SET @d0='3e636c6a-8a59-4a8a-b754-bf0fcd402194' COLLATE utf8_unicode_ci; -- move completed
SET @d1='112b1cb9-f9dd-4317-b603-65cac35da4c5' COLLATE utf8_unicode_ci; -- file perm
SET @d2='1efe11c1-f6e7-4baf-9dff-98079b1cdf69' COLLATE utf8_unicode_ci; -- id file by ext
SET @d3='79c3a37e-0415-4262-8720-a76410500f23' COLLATE utf8_unicode_ci; -- char and extract metadata
SET @d4='51edd1ca-3dae-402c-8782-f007a5ae8f70' COLLATE utf8_unicode_ci; -- sanitize trans name
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@d0, @d1, @d2, @d3, @d4);
SET foreign_key_checks = 0;
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d0, @d1, @d2, @d3, @d4);
SET foreign_key_checks = 1;
DELETE FROM TasksConfigs WHERE pk IN (SELECT currentTask FROM MicroServiceChainLinks WHERE pk IN (@d0, @d2, @d3, @d4));

-- Index transfer contents before move to completed dir
SET @indexTransfer = 'eb52299b-9ae6-4a1f-831e-c7eee0de829f' COLLATE utf8_unicode_ci;
SET @moveCompleted = 'd27fd07e-d3ed-4767-96a5-44a2251c6d0a' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @indexTransfer WHERE microServiceChainLink='c4898520-448c-40fc-8eb3-0603b6aacfb7';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @moveCompleted WHERE microServiceChainLink=@indexTransfer;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@moveCompleted WHERE pk=@indexTransfer;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=NULL WHERE microServiceChainLink=@moveCompleted;

-- Move actually completed transfers to sharedDirectory/completed/transfers
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('8516867e-b223-41af-8069-d42b08d32e99', 0, 'moveTransfer_v0.0', '"%SIPDirectory%" "%sharedPath%completed/transfers/." "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('1df8d388-fdc9-4c37-a639-bd8b6f4a87c7', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '8516867e-b223-41af-8069-d42b08d32e99', 'Move to completed transfers directory');
UPDATE MicroServiceChainLinks SET currentTask='1df8d388-fdc9-4c37-a639-bd8b6f4a87c7' WHERE pk='3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5';
UPDATE TasksConfigs SET description='Move to SIP creation directory for completed transfers' WHERE pk='39ac9ff8-d312-4033-a2c6-44219471abda';


-- One 'Move to completedTransfers directory' TC and StandardTasksConfigs
UPDATE MicroServiceChainLinks SET currentTask = '39ac9ff8-d312-4033-a2c6-44219471abda' WHERE pk IN ('3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5', 'e564b156-804f-4ab0-92ea-43bf1de95c40');
DELETE FROM TasksConfigs WHERE pk IN ('5b5ef3c4-5f7e-417e-a1f8-ff5ca1a220b6', '45605b0a-a701-47ba-923f-8e107ac35820', 'd1342d53-f930-472f-8043-58d806285a11', '2123f249-edcb-45e2-8332-f59633189fd5', 'cf8d4bf9-fe4b-4b45-8442-678963ad9966');
DELETE FROM StandardTasksConfigs WHERE pk IN ('a851b8a3-d074-419f-ab18-78de0d0cd5b0', '15afe1ca-bf7a-438d-b3bf-ee517cd43ad8');

-- Add maildir specific file ID and characterization chain likns
UPDATE TasksConfigs SET description='Characterize and extract metadata for attachments' WHERE pk='445d6579-ee40-47d0-af6c-e2f6799f450d';
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('bd382151-afd0-41bf-bb7a-b39aef728a32', 'Characterize and extract metadata', 'Failed', '445d6579-ee40-47d0-af6c-e2f6799f450d', @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('5b2542c8-2088-4541-8bf9-a750eacb4ac5', 'bd382151-afd0-41bf-bb7a-b39aef728a32', 0, '1b1a4565-b501-407b-b40f-2f20889423f1', 'Completed successfully');

SET @identifyFileFormatMSCLTransferMaildir='0e41c244-6c3e-46b9-a554-65e66e5c9324' COLLATE utf8_unicode_ci;
SET @identifyFileFormatMaildirTC='a75ee667-3a1c-4950-9194-e07d0e6bf545' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('02fd0952-4c9c-4da6-9ea3-a1409c87963d', 0, 'identifyFileFormat_v0.0', '%IDCommand% %relativeLocation% %fileUUID%', 'objects/attachments');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@identifyFileFormatMaildirTC, 'a6b1c323-7d36-428e-846a-e7e819423577', '02fd0952-4c9c-4da6-9ea3-a1409c87963d', 'Identify file format of attachments');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@identifyFileFormatMSCLTransferMaildir, 'Characterize and extract metadata', 'Failed', @identifyFileFormatMaildirTC, 'bd382151-afd0-41bf-bb7a-b39aef728a32');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('6ff56b9a-2e0d-4117-a6ee-0ba51e6da708', @identifyFileFormatMSCLTransferMaildir, 0, 'bd382151-afd0-41bf-bb7a-b39aef728a32', 'Completed successfully');


-- Add a Set Unit Variable for maildir with the File ID MSCL
SET @fileIDCmdTransfer='fileIDcommand-transfer' COLLATE utf8_unicode_ci;
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink) VALUES ('65263ec0-f3ff-4fd5-9cd3-cf6f51ef92c7', @fileIDCmdTransfer, NULL, @identifyFileFormatMSCLTransferMaildir);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('0bb3f551-1418-4b99-8094-05a43fcd9537', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', '65263ec0-f3ff-4fd5-9cd3-cf6f51ef92c7', 'Set files to identify');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('4417b129-fab3-4503-82dd-740f8e774bff', 'Rename with transfer UUID', 'Failed', '0bb3f551-1418-4b99-8094-05a43fcd9537', 'fdfac6e5-86c0-4c81-895c-19a9edadedef');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('5035f15f-90a9-4beb-9251-c24ec3e530d7', '4417b129-fab3-4503-82dd-740f8e774bff', 0, 'fdfac6e5-86c0-4c81-895c-19a9edadedef', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='4417b129-fab3-4503-82dd-740f8e774bff' WHERE microServiceChainLink='da2d650e-8ce3-4b9a-ac97-8ca4744b019f';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='4417b129-fab3-4503-82dd-740f8e774bff' WHERE pk='da2d650e-8ce3-4b9a-ac97-8ca4744b019f';

-- Add a Get Unit Variable for which File ID stuff to run
-- objects or objects/attachments
INSERT INTO TasksConfigsUnitVariableLinkPull (pk, variable, variableValue, defaultMicroServiceChainLink) VALUES ('97ddf0be-7b07-48b1-82f6-6a3b49edde2b', @fileIDCmdTransfer, NULL, @identifyFileFormatMSCL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('7a96f085-924b-483e-bc63-440323bce587', 'c42184a3-1a7f-4c4d-b380-15d8d97fdd11', '97ddf0be-7b07-48b1-82f6-6a3b49edde2b', 'Determine which files to identify');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('c3269a0a-91db-44e8-96d0-9c748cf80177', 'Characterize and extract metadata', 'Failed', '7a96f085-924b-483e-bc63-440323bce587', @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('55dd25a7-944a-4a99-8b94-a508d28d0b38', 'c3269a0a-91db-44e8-96d0-9c748cf80177', 0, NULL, 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='c3269a0a-91db-44e8-96d0-9c748cf80177' WHERE microServiceChainLink=@selectFileIDCommandMSCL;

-- /Issue 5759


-- Issue 5759, 5248
-- Maildir support
SET @fileIDCmdIngest='fileIDcommand-ingest' COLLATE utf8_unicode_ci;
-- Add a Get Unit Variable for which File ID stuff to run
INSERT INTO TasksConfigsUnitVariableLinkPull (pk, variable, variableValue, defaultMicroServiceChainLink) VALUES ('ce6d43be-ac11-431d-be8b-570a09b6913e', @fileIDCmdIngest, NULL, @identifyFileFormatMSCLIngest);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('75377725-8759-4cf7-9f83-700b96f72ac4', 'c42184a3-1a7f-4c4d-b380-15d8d97fdd11', 'ce6d43be-ac11-431d-be8b-570a09b6913e', 'Determine which files to identify');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('24d9ff02-a29b-48b2-a68e-cebd30fe3851', 'Normalize', 'Failed', '75377725-8759-4cf7-9f83-700b96f72ac4', '7d728c39-395f-4892-8193-92f086c0546f');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('1985e136-3522-4f33-aff9-1b0008472ed2', '24d9ff02-a29b-48b2-a68e-cebd30fe3851', 0, @identifyFileFormatMSCLIngest, 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='24d9ff02-a29b-48b2-a68e-cebd30fe3851' WHERE microServiceChainLink='7a024896-c4f7-4808-a240-44c87c762bc5';

-- Add maildir specific file ID chain link
SET @identifyFileFormatMSCLIngestMaildir = 'd9493000-4bb7-4c43-851f-73e57d1b69e9' COLLATE utf8_unicode_ci;
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@identifyFileFormatMSCLIngestMaildir, 'Normalize', 'Failed', @identifyFileFormatMaildirTC, '83484326-7be7-4f9f-b252-94553cd42370');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('99a4c796-073f-4cda-ba18-5e147d110f68', @identifyFileFormatMSCLIngestMaildir, 0, '83484326-7be7-4f9f-b252-94553cd42370', 'Completed successfully');

-- Add check if maildir AIP, and set unit vars for file ID & normalization
-- Set norm dir
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink) VALUES ('f226ecea-ae91-42d5-b039-39a1125b1c30', 'normalizationDirectory', 'objects/attachments', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('99324102-ebe8-415d-b5d8-b299ab2f4703', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', 'f226ecea-ae91-42d5-b039-39a1125b1c30', 'Set files to normalize');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('823b0d76-9f3c-410d-83ab-f3c2cdd9ab22', 'Rename SIP directory with SIP UUID', 'Failed', '99324102-ebe8-415d-b5d8-b299ab2f4703', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('32cae09e-0262-46b8-ba76-eb6cf6be1272', '823b0d76-9f3c-410d-83ab-f3c2cdd9ab22', 0, 'e3a6d178-fa65-4086-a4aa-6533e8f12d51', 'Completed successfully');
-- Set file ID MSCL
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink) VALUES ('42454e81-e776-44cc-ae9f-b40e7e5c7738', @fileIDCmdIngest, NULL, @identifyFileFormatMSCLIngestMaildir);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('fa2307df-e42a-4553-aaf5-b08879b0cbf4', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', '42454e81-e776-44cc-ae9f-b40e7e5c7738', 'Set files to identify');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('bdfecadc-8219-4109-885c-cfb9ef53ebc3', 'Rename SIP directory with SIP UUID', 'Failed', 'fa2307df-e42a-4553-aaf5-b08879b0cbf4', '823b0d76-9f3c-410d-83ab-f3c2cdd9ab22');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('dad05633-987d-4672-9b7c-1341cecbf59c', 'bdfecadc-8219-4109-885c-cfb9ef53ebc3', 0, '823b0d76-9f3c-410d-83ab-f3c2cdd9ab22', 'Completed successfully');
-- Maildir check
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('3f3ab7ae-766e-4405-a05a-5ee9aea5042f', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', 'c0ae5130-0c17-4fc1-91c7-aa36265a21d5', 'Check if SIP is from Maildir Transfer');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('b3d11842-0090-420a-8919-52d7039d50e6', 'Rename SIP directory with SIP UUID', 'Failed', '3f3ab7ae-766e-4405-a05a-5ee9aea5042f', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('ae13dd4f-81d6-44d5-94c8-0c19aa6c6cf8', 'b3d11842-0090-420a-8919-52d7039d50e6', 0, 'e3a6d178-fa65-4086-a4aa-6533e8f12d51', 'Completed successfully');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('42353ec8-76cb-477f-841c-4adfc8432d78', 'b3d11842-0090-420a-8919-52d7039d50e6', 179, 'bdfecadc-8219-4109-885c-cfb9ef53ebc3', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='b3d11842-0090-420a-8919-52d7039d50e6' WHERE microServiceChainLink='d1018160-aaab-4d92-adce-d518880d7c7d';

-- File logging file ID output
UPDATE StandardTasksConfigs SET standardOutputFile ='%SIPLogsDirectory%fileFormatIdentification.log' WHERE execute ='identifyFileFormat_v0.0';
UPDATE StandardTasksConfigs SET standardErrorFile ='%SIPLogsDirectory%fileFormatIdentification.log' WHERE execute ='identifyFileFormat_v0.0';

-- /Issue 5759, 5248 Maildir

-- Issue #5751
-- Insert "Extract contents" task after identification
SET @extractContentsMSCL = '1cb7e228-6e94-4c93-bf70-430af99b9264' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('8fad772e-7d2e-4cdd-89e6-7976152b6696', 0, 'extractContents_v0.0', '"%SIPUUID%" "%transferDirectory%" "%date%" "%taskUUID%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('09f73737-f7ca-4ea2-9676-d369f390e650', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '8fad772e-7d2e-4cdd-89e6-7976152b6696', 'Extract contents from compressed archives');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values (@extractContentsMSCL, 'Extract packages', 'Completed successfully', '09f73737-f7ca-4ea2-9676-d369f390e650', @characterizeExtractMetadata);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('f0ba8289-b40f-4279-a968-7496f837c9f9', @extractContentsMSCL, 0, @characterizeExtractMetadata, 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@extractContentsMSCL WHERE microServiceChainLink=@identifyFileFormatMSCL;
-- Identify files will exit non-zero if some files weren't identified, however it may have returned some identifications this task can use
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@extractContentsMSCL WHERE pk=@identifyFileFormatMSCL;

-- Remove the old extract microservice chain links, pointing them at identification instead
-- "Move to processing directory" moves to point to the first entry of the "Clean up names" group
SET @moveToProcessingDirectoryMSCL = '0e379b19-771e-4d90-a7e5-1583e4893c56' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='1c2550f1-3fc0-45d8-8bc4-4c06d720283b' WHERE microServiceChainLink=@moveToProcessingDirectoryMSCL;
UPDATE MicroServiceChainLinks SET microserviceGroup='Clean up names' WHERE pk=@moveToProcessingDirectoryMSCL;

-- Point "Create unquarantine PREMIS event" at identification
SET @createQuarantinePremisMSCL = '5158c618-6160-41d6-bbbe-ddf34b5b06bc' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@selectFileIDCommandMSCL WHERE pk=@createQuarantinePremisMSCL;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@selectFileIDCommandMSCL WHERE microServiceChainLink=@createQuarantinePremisMSCL;

SET @oldExtractMSCL='f140cc1f-1e0d-4eb1-aa93-8fa8ac52eca9' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@oldExtractMSCL;
DELETE FROM MicroServiceChainLinks WHERE pk=@oldExtractMSCL;

-- DSpace: point "extract" at identification
-- Both are separate "Move to processing directory" chains
SET @dspaceScanForVirusesMSCL='f92dabe5-9dd5-495e-a996-f8eb9ef90f48' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@dspaceScanForVirusesMSCL WHERE microServiceChainLink='d7e6404a-a186-4806-a130-7e6d27179a15';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@dspaceScanForVirusesMSCL WHERE microServiceChainLink='38c591d4-b7ee-4bc0-b993-c592bf15d97d';
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@dspaceScanForVirusesMSCL WHERE pk='38c591d4-b7ee-4bc0-b993-c592bf15d97d';

-- Remove DSpace "extract packages"
SET @dspaceExtractMSCL='28d4e61d-1f00-4e70-b79b-6a9779f8edc4' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@dspaceExtractMSCL;
DELETE FROM MicroServiceChainLinks WHERE pk=@dspaceExtractMSCL;

-- Create new set of commands that covers the second-pass identification and filename sanitization
-- Insert a second pass of "Sanitize object's file and directory names" following package extraction
SET @sanitizeNamesPostExtractionMSCL='c5ecb5a9-d697-4188-844f-9a756d8734fa' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('f368a36d-2b27-4f08-b662-2828a96d189a', 0, 'sanitizeObjectNames_v0.0', '"%SIPObjectsDirectory%" "%SIPUUID%" "%date%" "%taskUUID%" "transferDirectory" "transferUUID" "%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('57bd2747-181e-4f06-b969-dc012c592982', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', 'f368a36d-2b27-4f08-b662-2828a96d189a', "Sanitize extracted objects' file and directory names");
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values (@sanitizeNamesPostExtractionMSCL, 'Clean up names', 'Failed', '57bd2747-181e-4f06-b969-dc012c592982', '303a65f6-a16f-4a06-807b-cb3425a30201');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('345fc8d9-f44d-41d7-a439-57067cc04c10', @sanitizeNamesPostExtractionMSCL, 0, '303a65f6-a16f-4a06-807b-cb3425a30201', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@sanitizeNamesPostExtractionMSCL WHERE microServiceChainLink='1cb7e228-6e94-4c93-bf70-430af99b9264';

-- Insert a second pass of "Identify files"; this reuses the same tool from last time
SET @identifyFileFormatPostExtractionMSCL = 'aaa929e4-5c35-447e-816a-033a66b9b90b' COLLATE utf8_unicode_ci;

INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@identifyFileFormatPostExtractionMSCL, 'Extract packages', 'Failed', @identifyFileFormatTC, @characterizeExtractMetadata);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('e132d3e2-6dcd-4c81-b6f3-7a0ea04193c0', @identifyFileFormatPostExtractionMSCL, 0, @characterizeExtractMetadata, 'Completed successfully');

UPDATE MicroServiceChainLinks SET defaultNextChainLink=@identifyFileFormatPostExtractionMSCL WHERE pk=@sanitizeNamesPostExtractionMSCL;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@identifyFileFormatPostExtractionMSCL WHERE microServiceChainLink=@sanitizeNamesPostExtractionMSCL;

-- /Insert "Extract contents" task after identification


-- Issue 5889 DSpace not identify licenses and text properly

SET @idDspaceFiles = 'd0dfbd93-d2d0-44db-9945-94fd8de8a1d4' COLLATE utf8_unicode_ci;
SET @idDspaceMETS = '8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc' COLLATE utf8_unicode_ci;
SET @del = '8367ccf7-2f00-4ea5-b830-936d0a7600e3' COLLATE utf8_unicode_ci;
SET @dspaceChainStart = '2fd123ea-196f-4c9c-95c0-117aa65ed9c6' COLLATE utf8_unicode_ci;
SET @dspaceChainEnd = @idDspaceMETS;
SET @afterDspaceChain = 'eb52299b-9ae6-4a1f-831e-c7eee0de829f' COLLATE utf8_unicode_ci;

-- Merge Identify DSpace licenses and Identify DSpace Text files
UPDATE StandardTasksConfigs SET execute='identifyDspaceFiles_v0.0', arguments='"%relativeLocation%" "%SIPDirectory%" "%SIPUUID%"' WHERE pk='9ea66f4e-150b-4911-b68d-29fd5d372d2c';
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@idDspaceMETS WHERE pk=@idDspaceFiles;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@idDspaceMETS WHERE microServiceChainLink=@idDspaceFiles;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@del;
DELETE FROM MicroServiceChainLinks WHERE pk=@del;
DELETE FROM TasksConfigs WHERE pk='1c3f14e5-c542-4b79-a047-d4f901dd4f2e';
DELETE FROM StandardTasksConfigs WHERE pk='29f9d509-e740-4e44-b8dc-ab7d6e568b64';

-- Set 'specialized processing' link for DSpace files
INSERT INTO TasksConfigsSetUnitVariable(pk, variable, microServiceChainLink) VALUES ('ed98984f-69c5-45de-8a32-2c9ecf65e83f', 'postExtractSpecializedProcessing', @dspaceChainStart);
INSERT INTO TasksConfigs(pk, taskType, taskTypePKReference, description) VALUES ('06b45b5d-d06b-49a8-8f15-e9458fbae842', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', 'ed98984f-69c5-45de-8a32-2c9ecf65e83f', 'Set specialized processing link');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('f2a019ea-0601-419c-a475-1b96a927a2fb', 'Verify transfer compliance', 'Failed', '06b45b5d-d06b-49a8-8f15-e9458fbae842', @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes(pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('d6914e3c-4d4a-4b0d-9d26-eeb340ac027b', 'f2a019ea-0601-419c-a475-1b96a927a2fb', 0, 'aa9ba088-0b1e-4962-a9d7-79d7a0cbea2d', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='f2a019ea-0601-419c-a475-1b96a927a2fb' WHERE microServiceChainLink='26bf24c9-9139-4923-bf99-aa8648b1692b';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='f2a019ea-0601-419c-a475-1b96a927a2fb' WHERE pk='26bf24c9-9139-4923-bf99-aa8648b1692b';

-- Add 'specialized processing' link after extraction
INSERT INTO TasksConfigsUnitVariableLinkPull (pk, variable, defaultMicroServiceChainLink) VALUES ('49d853a9-646d-4e9f-b825-d1bcc3ba77f0', 'postExtractSpecializedProcessing', @afterDspaceChain);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('3649f0f4-2174-44af-aef9-31ebeddeb73b', 'c42184a3-1a7f-4c4d-b380-15d8d97fdd11', '49d853a9-646d-4e9f-b825-d1bcc3ba77f0', 'Check for specialized processing');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('192315ea-a1bf-44cf-8cb4-0b3edd1522a6', 'Characterize and extract metadata', 'Failed', '3649f0f4-2174-44af-aef9-31ebeddeb73b', @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('d2c5ab7b-ced1-45cd-a7da-98ab30a31259', '192315ea-a1bf-44cf-8cb4-0b3edd1522a6', 0, '2fd123ea-196f-4c9c-95c0-117aa65ed9c6', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='192315ea-a1bf-44cf-8cb4-0b3edd1522a6' WHERE microServiceChainLink='c4898520-448c-40fc-8eb3-0603b6aacfb7';

-- Move DSpace specific MSCLs to after extract packages, so files actually exist to be worked on
UPDATE MicroServiceChainLinks SET defaultNextChainLink = @afterDspaceChain WHERE pk= @dspaceChainEnd;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @afterDspaceChain WHERE microServiceChainLink=@dspaceChainEnd;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = '2584b25c-8d98-44b7-beca-2b3ea2ea2505' WHERE microServiceChainLink = 'f92dabe5-9dd5-495e-a996-f8eb9ef90f48';
-- New Group - identify DSpace files
UPDATE MicroServiceChainLinks SET microserviceGroup = "Identify DSpace files" WHERE pk in (@idDspaceFiles, @idDspaceMETS, '2fd123ea-196f-4c9c-95c0-117aa65ed9c6');
-- Move Set File Permissions to Characterize group
UPDATE MicroServiceChainLinks SET microserviceGroup = "Characterize and extract metadata" WHERE pk in ('c4898520-448c-40fc-8eb3-0603b6aacfb7');

-- /Issue 5889

-- Cleanup - Maildir use new extraction code

SET @maildirIDFormat = '0e41c244-6c3e-46b9-a554-65e66e5c9324' COLLATE utf8_unicode_ci;
SET @maildirExtract = '95616c10-a79f-48ca-a352-234cc91eaf08' COLLATE utf8_unicode_ci;
SET @extractTC = '09f73737-f7ca-4ea2-9676-d369f390e650' COLLATE utf8_unicode_ci;
SET @maildirSanitizeExtracted = '01b30826-bfc4-4e07-8ca2-4263debad642' COLLATE utf8_unicode_ci;
SET @maildirIdExtracted = '22ded604-6cc0-444b-b320-f96afb15d581' COLLATE utf8_unicode_ci;
SET @maildirCharacterize = 'bd382151-afd0-41bf-bb7a-b39aef728a32' COLLATE utf8_unicode_ci;
-- ID file format of extracted
INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, microserviceGroup) VALUES (@maildirIdExtracted, 'a75ee667-3a1c-4950-9194-e07d0e6bf545', @maildirCharacterize, 'Extract packages');
INSERT INTO MicroServiceChainLinksExitCodes(pk, microServiceChainLink, exitCode, nextMicroServiceChainLink) VALUES ('8c346844-b95d-4ed5-8fc3-694c34844de9', @maildirIdExtracted, 0, @maildirCharacterize);
-- Sanitize extracted names
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('c2c7edcc-0e65-4df7-812f-a2ee5b5d52b6', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '89b4d447-1cfc-4bbf-beaa-fb6477b00f70', "Sanitize extracted objects' file and directory names");
INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, microserviceGroup) VALUES (@maildirSanitizeExtracted, 'c2c7edcc-0e65-4df7-812f-a2ee5b5d52b6', @maildirIdExtracted, 'Extract packages');
INSERT INTO MicroServiceChainLinksExitCodes(pk, microServiceChainLink, exitCode, nextMicroServiceChainLink) VALUES ('2c4004db-5816-4bd2-b37c-a89dee2c4fe7', @maildirSanitizeExtracted, 0, @maildirIdExtracted);
-- Extract contents
INSERT INTO MicroServiceChainLinks(pk, currentTask, defaultNextChainLink, microserviceGroup) VALUES (@maildirExtract, @extractTC, @maildirCharacterize, 'Extract packages');
INSERT INTO MicroServiceChainLinksExitCodes(pk, microServiceChainLink, exitCode, nextMicroServiceChainLink) VALUES ('21a92e57-bc78-4c62-872d-fb166294132a', @maildirExtract, 0, @maildirSanitizeExtracted);
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@maildirExtract WHERE pk=@maildirIDFormat;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@maildirExtract WHERE microServiceChainLink=@maildirIDFormat;
-- Rename groups to flow better and not mis-group in GUI
UPDATE MicroServiceChainLinks SET microserviceGroup='Identify file format' WHERE pk IN ('d1b27e9e-73c8-4954-832c-36bd1e00c802', 'f09847c2-ee51-429a-9478-a860477f6b8d', 'c3269a0a-91db-44e8-96d0-9c748cf80177', '0e41c244-6c3e-46b9-a554-65e66e5c9324', '2522d680-c7d9-4d06-8b11-a28d8bd8a71f', '');
UPDATE MicroServiceChainLinks SET microserviceGroup='Extract packages' WHERE pk IN ('c5ecb5a9-d697-4188-844f-9a756d8734fa');
UPDATE MicroServiceChainLinks SET microserviceGroup='Extract attachments' WHERE pk IN ('b2552a90-e674-4a40-a482-687c046407d3');
-- Remove old extract packages for Maildir
SET @before = 'b2552a90-e674-4a40-a482-687c046407d3' COLLATE utf8_unicode_ci;
SET @del = '12d31cf0-cfc5-4ddb-a7d2-f71a8ff1dd0a' COLLATE utf8_unicode_ci;
SET @after = '21d6d597-b876-4b3f-ab85-f97356f10507' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@after WHERE pk=@before;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@after WHERE microServiceChainLink=@before;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@del;
DELETE FROM MicroServiceChainLinks WHERE pk=@del;
DELETE FROM TasksConfigs WHERE pk='17bb8c16-597f-48ac-83f1-539de9442c93';
DELETE FROM StandardTasksConfigs WHERE pk='e9509ecf-be06-4572-b217-8ec3acb24ad1';

-- Remove Extract Packages using old extract packages
-- Remove Extract packages in metadata
SET @before = 'b6b0fe37-aa26-40bd-8be8-d3acebf3ccf8' COLLATE utf8_unicode_ci;
SET @del = 'd8706e6e-7f38-4d98-9721-4f120156dca8' COLLATE utf8_unicode_ci;
SET @after = 'b21018df-f67d-469a-9ceb-ac92ac68654e' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@after WHERE pk=@before;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@after WHERE microServiceChainLink=@before;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@del;
DELETE FROM MicroServiceChainLinks WHERE pk=@del;
-- Delete TasksConfig and StandardTasksConfig?

-- Remove Extract packages in submission (1)
SET @before = '0ba9bbd9-6c21-4127-b971-12dbc43c8119' COLLATE utf8_unicode_ci;
SET @del = '3e7cc9e1-29ec-436f-92d7-0493a5b33c61' COLLATE utf8_unicode_ci;
SET @after = 'e888269d-460a-4cdf-9bc7-241c92734402' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@after WHERE pk=@before;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@after WHERE microServiceChainLink=@before;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@del;
DELETE FROM MicroServiceChainLinks WHERE pk=@del;
-- Delete TasksConfig and StandardTasksConfig?

-- Remove Extract packages in submission (2)
SET @before = '2a62f025-83ec-4f23-adb4-11d5da7ad8c2' COLLATE utf8_unicode_ci;
SET @del = '78f8953a-11cd-4125-bab7-2ca76647bd7a' COLLATE utf8_unicode_ci;
SET @after = '11033dbd-e4d4-4dd6-8bcf-48c424e222e3' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@after WHERE pk=@before;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@after WHERE microServiceChainLink=@before;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@del;
DELETE FROM MicroServiceChainLinks WHERE pk=@del;
-- Delete TasksConfig and StandardTasksConfig?

-- Removed unused 'identifyFilesByExtension_v0.0' StandardTasksConfigs/TasksConfigs
DELETE FROM StandardTasksConfigs WHERE pk IN ('5dfba5b1-f4b7-4884-8bd2-6b855a03b3f2', '5f1cea07-483f-4c88-adfe-606fed6a9a52', 'b32d79b7-1fd5-4c61-abca-3b4f168faf19');
DELETE FROM TasksConfigs WHERE pk IN ('1a9b46f4-79a6-4bc9-a725-c9862b21e0c2', '59fc6d9e-a648-443f-93f3-7f172f8e85a7', '6b173074-382a-4247-9bac-600f31f69e6c', 'bb2523de-e310-44f5-b3f1-c92eab920f26', 'bebba280-91fd-415d-89ce-1ad2b5c27c28');
-- /Cleanup
