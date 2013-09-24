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
) ENGINE=InnoDB;
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
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('9c3680a5-91cb-413f-af4e-d39c3346f8db', 0, 'identifyFileFormat_v0.0', '%IDCommand% %relativeLocation% %fileUUID%', 'objects');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('8558d885-d6c2-4d74-af46-20da45487ae7', 'a6b1c323-7d36-428e-846a-e7e819423577', '9c3680a5-91cb-413f-af4e-d39c3346f8db', 'Identify file format');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values (@identifyFileFormatMSCL, 'Characterize and extract metadata', 'Failed', '8558d885-d6c2-4d74-af46-20da45487ae7', @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('1f877d65-66c5-49da-bf51-2f1757b59c90', @identifyFileFormatMSCL, 0, @characterizeExtractMetadata, 'Completed successfully');

-- Add Select file format identification command
SET @selectFileIDCommandMSCL='f09847c2-ee51-429a-9478-a860477f6b8d' COLLATE utf8_unicode_ci;
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('97545cb5-3397-4934-9bc5-143b774e4fa7', '9c84b047-9a6d-463f-9836-eafa49743b84', NULL, 'Select file format identification command');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values (@selectFileIDCommandMSCL, 'Characterize and extract metadata', 'Failed', '97545cb5-3397-4934-9bc5-143b774e4fa7', @MoveTransferToFailedLink);
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
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('3e8f5b9e-b3a6-4782-a944-749de6ae234d', 0, 'moveTransfer_v0.0', '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/selectFormatIDTool/."  "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('38cea9c4-d75c-48f9-ba88-8052e9d3aa61', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '3e8f5b9e-b3a6-4782-a944-749de6ae234d', 'Move to select file ID tool');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('d1b27e9e-73c8-4954-832c-36bd1e00c802', 'Characterize and extract metadata', 'Failed', '38cea9c4-d75c-48f9-ba88-8052e9d3aa61', @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('6740b87f-6d30-4f43-8848-1371fe9b08c5', 'd1b27e9e-73c8-4954-832c-36bd1e00c802', 0, NULL, 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='d1b27e9e-73c8-4954-832c-36bd1e00c802' WHERE microServiceChainLink='a329d39b-4711-4231-b54e-b5958934dccb';

-- Add MicroServiceChain pointing to Select file format ID command
SET @selectFormatIDChain='bd94cc9b-7990-45a2-a255-a1b70936f9f2';
INSERT INTO MicroServiceChains(pk, startingLink, description) VALUES (@selectFormatIDChain, @selectFileIDCommandMSCL, 'Identify file format');

-- Add WatchedDirectory for folder/chain
SET @watchedDirExpectTransfer='f9a3a93b-f184-4048-8072-115ffac06b5d';
INSERT INTO WatchedDirectories(pk, watchedDirectoryPath, chain, expectedType) VALUES ('11a4f280-9b43-45a0-9ebd-ec7a115ccc62', "%watchDirectoryPath%workFlowDecisions/selectFormatIDTool/", @selectFormatIDChain, @watchedDirExpectTransfer);

-- / Issue 5633
