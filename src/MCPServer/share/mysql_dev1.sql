-- Issue 5244
ALTER TABLE Jobs CHANGE directory directory LONGTEXT;
-- /Issue 5244

-- Issue 5084
-- If user restarts while waiting to choose compression algorithm, the SIP job is orphaned
-- Tail of chain = Prepare AIP = 3e25bda6-5314-4bb4-aa1e-90900dce887d
-- Start of new chain = Select Compression algorithm = 01d64f58-8295-4b7b-9cab-8f1b153a504f

-- add move after prepare AIP
SET @microserviceGroup = 'Prepare AIP';
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';
SET @MoveTransferToFailedLink = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd';

SET @XLink = '3e25bda6-5314-4bb4-aa1e-90900dce887d' COLLATE utf8_unicode_ci;
-- SET @YLink = '1cd3b36a-5252-4a69-9b1c-3b36829288ab';

SET @TasksConfigPKReference = 'ae090b70-0234-40ea-bc11-4be27370515f';
SET @TasksConfig = '18dceb0a-dfb1-4b18-81a7-c6c5c578c5f1';
SET @MicroServiceChainLink = '002716a1-ae29-4f36-98ab-0d97192669c4';
SET @MicroServiceChainLinksExitCodes = '2858403b-895f-4ea3-b7b7-388de75fbb39';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @NextMicroServiceChainLink = NULL;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'moveSIP_v0.0', '"%SIPDirectory%" "%watchDirectoryPath%workFlowDecisions/compressionAIPDecisions/." "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Move to compressionAIPDecisions directory');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- set non zero exit code --
UPDATE MicroServiceChainLinks SET defaultNextChainLink = @MoveSIPToFailedLink WHERE pk = @XLink;

-- set zero exit code --
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @NextMicroServiceChainLink where microServiceChainLink = @XLink;


-- Add new watched directory for compressionAIP decisions, and chain for it to point to
SET @WatchedDirectory = 'dfb22984-c6eb-4c5d-939c-0df43559033e';
SET @MicroServiceChains = '27cf6ca9-11b4-41ac-9014-f8018bcbad5e';

INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChains, '01d64f58-8295-4b7b-9cab-8f1b153a504f', 'Compress AIP');

INSERT INTO WatchedDirectories (pk, watchedDirectoryPath, chain, onlyActOnDirectories, expectedType)
    VALUES (@WatchedDirectory, '%watchDirectoryPath%workFlowDecisions/compressionAIPDecisions/', @MicroServiceChains, True, '76e66677-40e6-41da-be15-709afb334936');
-- /Issue 5084


-- Issue 5034
-- mediainfo
SET @microserviceGroup = 'Normalize';
SET @XLink = '5bddbb67-76b4-4bcb-9b85-a0d9337e7042' COLLATE utf8_unicode_ci;
SET @YLink = '83484326-7be7-4f9f-b252-94553cd42370';

SET @TasksConfigPKReference = 'c7e6b467-445e-4142-a837-5b50184238fc';
SET @TasksConfig = '5f1b9002-3f89-4f9a-b960-92ac5466ef81';
SET @MicroServiceChainLink = 'a4f7ebb7-3bce-496f-a6bc-ef73c5ce8118';
SET @MicroServiceChainLinksExitCodes = '15fdd14c-68e7-464c-9b29-dd079d3a9bb0';
SET @defaultNextChainLink = @YLink;
SET @NextMicroServiceChainLink = @YLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/', FALSE, NULL, NULL, 'archivematicaMediaInfo_v0.0', '--fileUUID "%fileUUID%" --SIPUUID "%SIPUUID%" --filePath "%relativeLocation%" --eventIdentifierUUID "%taskUUID%" --date "%date%" --fileGrpUse "%fileGrpUse%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Identify file formats with MediaInfo');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;
-- set non zero exit code --
UPDATE MicroServiceChainLinks SET defaultNextChainLink = @NextMicroServiceChainLink WHERE pk = @XLink;
-- set zero exit code --
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @NextMicroServiceChainLink where microServiceChainLink = @XLink;

-- INSERT INTO `MicroServiceChains` (`pk`, `startingLink`, `description`, `replaces`, `lastModified`) VALUES ('09949bda-5332-482a-ae47-5373bd372174','5bddbb67-76b4-4bcb-9b85-a0d9337e7042','mediainfo',NULL,'2012-10-23 19:41:24');
UPDATE MicroServiceChains SET description='MediaInfo' WHERE pk = '09949bda-5332-482a-ae47-5373bd372174';

-- INSERT INTO `TasksConfigs` (`pk`, `taskType`, `taskTypePKReference`, `description`, `replaces`, `lastModified`) VALUES ('008e5b38-b19c-48af-896f-349aaf5eba9f','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','be6dda53-ef28-42dd-8452-e11734d57a91','Set SIP to normalize with mediainfo file identification.',NULL,'2012-10-23 19:41:24');
UPDATE TasksConfigs SET description='Set SIP to normalize with MediaInfo file identification.' WHERE pk = '008e5b38-b19c-48af-896f-349aaf5eba9f';
-- /Issue 5034


-- 5088 Tasks table does not have foreign key for Jobs
ALTER TABLE Tasks
ADD FOREIGN KEY (jobUUID)
REFERENCES Jobs(jobUUID);
-- /5088


-- Issue 5032 Support normalization based on FIDO file IDs --
INSERT INTO `MicroServiceChainChoice` (`pk`, `choiceAvailableAtLink`, `chainAvailable`, `replaces`, `lastModified`) VALUES ('e95b8f27-ea52-4247-bdf0-615273bc5fca','f4dea20e-f3fe-4a37-b20f-0e70a7bc960e','c76624a8-6f85-43cf-8ea7-0663502c712f',NULL,'2012-10-23 19:41:24');

SET @microserviceGroup = 'Normalize';
SET @XLink = '982229bd-73b8-432e-a1d9-2d9d15d7287d' COLLATE utf8_unicode_ci;
SET @YLink = '83484326-7be7-4f9f-b252-94553cd42370';

SET @TasksConfigPKReference = '46883944-8561-44d0-ac50-e1c3fd9aeb59';
SET @TasksConfig = '7f786b5c-c003-4ef1-97c2-c2269a04e89a';
SET @MicroServiceChainLink = '4c4281a1-43cd-4c6e-b1dc-573bd1a23c43';
SET @MicroServiceChainLinksExitCodes = 'd7653bbd-cd71-473d-b09e-fdd5b36a1d65';
SET @defaultNextChainLink = @YLink;
SET @NextMicroServiceChainLink = @YLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/', FALSE, NULL, NULL, 'archivematicaFido_v0.0', '--fileUUID "%fileUUID%" --SIPUUID "%SIPUUID%" --filePath "%relativeLocation%" --eventIdentifierUUID "%taskUUID%" --date "%date%" --fileGrpUse "%fileGrpUse%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Identify file formats with FIDO');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- set non zero exit code --
UPDATE MicroServiceChainLinks SET defaultNextChainLink = @NextMicroServiceChainLink WHERE pk = @XLink;

-- set zero exit code --
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @NextMicroServiceChainLink where microServiceChainLink = @XLink;
-- /Issue 5032 --


-- Issue 5027 Support normalization based on tika file IDs --
INSERT INTO `MicroServiceChainChoice` (`pk`, `choiceAvailableAtLink`, `chainAvailable`, `replaces`, `lastModified`) VALUES ('44304ff6-86f9-444e-975f-e578c7f3d15a','f4dea20e-f3fe-4a37-b20f-0e70a7bc960e','46824987-bd47-4139-9871-6566f5abdf1a',NULL,'2012-10-23 19:41:25'); 

SET @microserviceGroup = 'Normalize';
SET @XLink = '5fbecef2-49e9-4585-81a2-267b8bbcd568' COLLATE utf8_unicode_ci;
SET @YLink = '83484326-7be7-4f9f-b252-94553cd42370';

SET @TasksConfigPKReference = '9e32257f-161e-430e-9412-07ce7f8db8ab';
SET @TasksConfig = 'fa61df3a-98a5-47e2-a5ce-281ae1c8c3c2';
SET @MicroServiceChainLink = 'aa5b8a69-ce6d-49f7-a07f-4683ccd6fcbf';
SET @MicroServiceChainLinksExitCodes = 'b4f6e0b3-f793-4603-81a8-5d4f0ddca9d7';
SET @defaultNextChainLink = @YLink;
SET @NextMicroServiceChainLink = @YLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/', FALSE, NULL, NULL, 'archivematicaTika_v0.0', '--fileUUID "%fileUUID%" --SIPUUID "%SIPUUID%" --filePath "%relativeLocation%" --eventIdentifierUUID "%taskUUID%" --date "%date%" --fileGrpUse "%fileGrpUse%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Identify file formats with Tika');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- set non zero exit code --
UPDATE MicroServiceChainLinks SET defaultNextChainLink = @NextMicroServiceChainLink WHERE pk = @XLink;

-- set zero exit code --
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @NextMicroServiceChainLink where microServiceChainLink = @XLink;
-- /Issue 5027 --

-- issue-1843
-- --------------------------------------------------------------------------------------------------------------------------
-- Add ability to generate a DIP from an AIP.
-- -Normalization tool selection without fits already having been run
SET @microserviceGroup = 'Normalize';

-- extension
-- extension ID run
SET @TasksConfig = '59fc6d9e-a648-443f-93f3-7f172f8e85a7';
SET @MicroServiceChainLink = '91d7e5f3-d89b-4c10-83dd-ab417243f583';
SET @MicroServiceChainLinksExitCodes = 'e26b8bbb-cf7e-48b0-b510-2dc98187cd25';
SET @defaultNextChainLink = '83484326-7be7-4f9f-b252-94553cd42370';
SET @NextMicroServiceChainLink = '83484326-7be7-4f9f-b252-94553cd42370';

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- extension set
SET @TasksConfig = '04806cbd-d146-46e9-b3b6-1bd664636057';
SET @MicroServiceChainLink = 'fbebca6d-53bc-42ef-98ea-3f707e53832e';
SET @MicroServiceChainLinksExitCodes = '4400c0af-6a5b-4b7d-9ba9-1d4b6ceaab6d';
SET @defaultNextChainLink = @RunFITSLink;
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

SET @MicroServiceChains = '7161abb2-8d3f-4c76-acbe-de0b7bb79dc2';
SET @startingLink = @MicroServiceChainLink;
SET @description = 'extension (default)';
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChains, @startingLink, @description);
SET @ExtensionChain = @MicroServiceChains;


-- taskConfig run fits b8403044-12a3-4b63-8399-772b9adace15
-- Run FITS
SET @TasksConfig = 'b8403044-12a3-4b63-8399-772b9adace15';
SET @MicroServiceChainLink = 'b063c4ce-ada1-4e72-a137-800f1c10905c';
SET @MicroServiceChainLinksExitCodes = '41020480-1078-4106-94d9-964ab1af6bd2';
SET @defaultNextChainLink = '83484326-7be7-4f9f-b252-94553cd42370';
SET @NextMicroServiceChainLink = '83484326-7be7-4f9f-b252-94553cd42370';

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;
SET @RunFITSLink = @MicroServiceChainLink;

-- FITS - DROID
SET @TasksConfig = 'b8c10f19-40c9-44c8-8b9f-6fab668513f5';
SET @MicroServiceChainLink = '01292b28-9588-4a85-953b-d92b29faf4d0';
SET @MicroServiceChainLinksExitCodes = 'be2d2436-1764-46ba-a341-8ad74d282056';
SET @defaultNextChainLink = @RunFITSLink;
SET @NextMicroServiceChainLink = @RunFITSLink;

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

SET @MicroServiceChains = '32dfa5f0-5964-4aa4-8132-9abb5b539644';
SET @startingLink = @MicroServiceChainLink;
SET @description = 'FITS - DROID';
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChains, @startingLink, @description);
SET @FITSDROIDChain = @MicroServiceChains;

-- FITS - ffident
SET @TasksConfig = 'b5e6340f-07f3-4ed1-aada-7a7f049b19b9';
SET @MicroServiceChainLink = 'd7681789-5f98-49bb-85d4-c01b34dac5b9';
SET @MicroServiceChainLinksExitCodes = '3a6947d3-d3a6-4bfa-9b01-de62209367e1';
SET @defaultNextChainLink = @RunFITSLink;
SET @NextMicroServiceChainLink = @RunFITSLink;

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

SET @MicroServiceChains = '12aaa737-4abd-45ea-a442-8f9f2666fa98';
SET @startingLink = @MicroServiceChainLink;
SET @description = 'FITS - ffident';
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChains, @startingLink, @description);
SET @FITSffidentChain = @MicroServiceChains;

-- FITS - JHOVE
SET @TasksConfig = '76135f22-6dba-417f-9833-89ecbe9a3d99';
SET @MicroServiceChainLink = 'cf26b361-dd5f-4b62-a493-6ee02728bd5f';
SET @MicroServiceChainLinksExitCodes = 'b741a8b8-5c79-4748-80e0-6ec88236043b';
SET @defaultNextChainLink = @RunFITSLink;
SET @NextMicroServiceChainLink = @RunFITSLink;

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

SET @MicroServiceChains = '040feba9-4039-48b3-bf7d-a5a5e5f4ce85';
SET @startingLink = @MicroServiceChainLink;
SET @description = 'FITS - JHOVE';
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChains, @startingLink, @description);
SET @FITSJHOVEChain = @MicroServiceChains;

-- FITS - summary 
SET @TasksConfig = 'c87ec738-b679-4d8e-8324-73038ccf0dfd';
SET @MicroServiceChainLink = 'f3efc52e-22e1-4337-b8ed-b38dac0f9f77';
SET @MicroServiceChainLinksExitCodes = '8aa5fa19-cd87-4abf-b1ee-84f23f145be8';
SET @defaultNextChainLink = @RunFITSLink;

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

SET @MicroServiceChains = 'b96411f1-bbf4-425a-adcf-8e7bfac2b85b';
SET @startingLink = @MicroServiceChainLink;
SET @description = 'FITS - summary';
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChains, @startingLink, @description);
SET @FITSSummaryChain = @MicroServiceChains;

-- FITS - file utility
SET @TasksConfig = '0732af8f-d60b-43e0-8f75-8e89039a05a8';
SET @MicroServiceChainLink = '2d751fc6-dc9d-4c52-b0d9-a4454cefb359';
SET @MicroServiceChainLinksExitCodes = 'd5838814-8874-4fe1-b375-2e044cdf05c2';
SET @defaultNextChainLink = @RunFITSLink;
SET @NextMicroServiceChainLink = @RunFITSLink;


INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

SET @MicroServiceChains = '522d85ae-298c-42ff-ab6c-bb5bf795c1ca';
SET @startingLink = @MicroServiceChainLink;
SET @description = 'FITS - file utility';
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChains, @startingLink, @description);
SET @FITSFileUtilityChain = @MicroServiceChains;




-- Choose tool
SET @TasksConfigPKReference = NULL;
SET @TasksConfig = '1cd60a70-f78e-4625-9381-3863ff819f33';
SET @MicroServiceChainLink = 'd05eaa5e-344b-4daa-b78b-c9f27c76499d';
SET @MicroServiceChainLinksExitCodes = '36e4f87a-fd87-4a6d-851b-2718b61db637';
SET @defaultNextChainLink = @NextMicroServiceChainLink;
SET @rejectTransferMicroserviceChain = '1b04ec43-055c-43b7-9543-bd03c6a778ba';

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', @TasksConfigPKReference, 'Select format identification tool');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
-- FIDO
SET @MicroServiceChainChoice = '3bc061c1-d69b-461e-b1a0-e1562cd47ceb';
SET @chainAvailable = 'c76624a8-6f85-43cf-8ea7-0663502c712f';
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);
-- MediaInfo
SET @MicroServiceChainChoice = '433ff828-f7d8-4675-8e90-939d9552ba22';
SET @chainAvailable = '09949bda-5332-482a-ae47-5373bd372174';
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);
-- Tika
SET @MicroServiceChainChoice = '636fcc25-8553-49c8-bccf-9ce46008321f';
SET @chainAvailable = '46824987-bd47-4139-9871-6566f5abdf1a';
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);
-- FITS DROID
SET @MicroServiceChainChoice = '62db9efd-03a0-4f6f-9285-4584bef361e0';
SET @chainAvailable = @FITSDROIDChain;
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);
-- FITS - ffident
SET @MicroServiceChainChoice = '06a6c312-0296-43ab-8e6b-c25170b67bc5';
SET @chainAvailable = @FITSffidentChain;
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);
-- FITS - JHOVE
SET @MicroServiceChainChoice = 'da620806-cfc6-4381-ac16-d1b7caaf80e0';
SET @chainAvailable = @FITSJHOVEChain;
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);
-- FITS - summary
SET @MicroServiceChainChoice = '17a26daf-fccb-4a61-ba0e-0ab6b6de7eca';
SET @chainAvailable = @FITSSummaryChain;
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);
-- FITS - file utility
SET @MicroServiceChainChoice = '8bd23ab1-7cb1-413e-833b-622a50ed891c';
SET @chainAvailable = @FITSFileUtilityChain;
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);
-- Extension
SET @MicroServiceChainChoice = 'b37a1802-ca59-47f2-bab1-99958ff4132b';
SET @chainAvailable = @ExtensionChain;
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);

SET @MicroServiceChains = 'b3b90ab1-39e2-4dea-84a7-34e4c3a13415';
set @NextMicroServiceChainLink = @MicroServiceChainLink;
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChains, @MicroServiceChainLink, 'Select file id type - without existing fits/fileIDbyExt');

SET @WatchedDirectory = 'cb790b11-227a-4e9b-9a7f-e0db198036a4';
INSERT INTO WatchedDirectories (pk, watchedDirectoryPath, chain, onlyActOnDirectories, expectedType)
    VALUES (@WatchedDirectory, '%watchDirectoryPath%workFlowDecisions/selectFileIDTool/', @MicroServiceChains, True, '76e66677-40e6-41da-be15-709afb334936');

-- -/Normalization tool selection without fits already having been run
DROP TABLE IF EXISTS FauxFileIDsMap;
CREATE TABLE `FauxFileIDsMap` (
  `pk` int(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
  `fauxSIPUUID` varchar(36) DEFAULT NULL,
  `fauxFileUUID` varchar(36) DEFAULT NULL,
  `fileUUID` varchar(36) DEFAULT NULL,
  FOREIGN KEY (`fauxFileUUID`) REFERENCES `Files` (`fileUUID`),
  FOREIGN KEY (`fauxSIPUUID`) REFERENCES `SIPs` (`sipUUID`)
);

-- --------------------------------------------------------------------------------------------------------------------------
-- Add ability to generate a DIP from an AIP.
-- Normalize from service or original, approve normalizaiton
-- - <alter old workflows>
SET @microserviceGroup = 'Normalize';

SET @XLink = '06d5979d-cd45-4a33-a139-0a606a52aa06';
SET @YLink = '0b5ad647-5092-41ce-9fe5-1cc376d0bc3f' COLLATE utf8_unicode_ci;

SET @TasksConfigPKReference = 'e076e08f-5f14-4fc3-93d0-1e80ca727f34';
SET @TasksConfig = 'c4b2e8ce-fe02-45d4-9b0f-b163bffcc05f';
SET @MicroServiceChainLink = 'c4e109d6-38ee-4c92-b83d-bc4d360f6f2e';
SET @MicroServiceChainLinksExitCodes = '8e8166c3-aca3-4eea-aa66-1522117f0b97';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @NextMicroServiceChainLink = @YLink;

INSERT INTO TasksConfigsUnitVariableLinkPull (pk, variable, variableValue, defaultMicroServiceChainLink)
    VALUES (@TasksConfigPKReference, 'postApproveNormalizationLink', '', @YLink);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'c42184a3-1a7f-4c4d-b380-15d8d97fdd11', @TasksConfigPKReference, 'Load post approve normalization link');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- set non zero exit code --
-- UPDATE MicroServiceChainLinks SET defaultNextChainLink = @MoveSIPToFailedLink WHERE pk = @XLink;

-- set zero exit code --
-- UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @NextMicroServiceChainLink where microServiceChainLink = @XLink;

UPDATE MicroServiceChains SET startingLink = @MicroServiceChainLink WHERE startingLink = @YLink;


SET @XLink = 'e543a615-e497-45e2-99ae-dfac4777e99c';
SET @YLink = 'b443ba1a-a0b6-4f7c-aeb2-65bd83de5e8b' COLLATE utf8_unicode_ci;

SET @TasksConfigPKReference = '7477907c-79ec-4d48-93ae-9e0cbbfd2b65';
SET @TasksConfig = '5092ff10-097b-4bac-a4d8-9b4766aaf40d';
SET @MicroServiceChainLink = '2307b24a-a019-4b5b-a520-a6fff270a852';
SET @MicroServiceChainLinksExitCodes = 'bd03ec7a-7d3f-4562-b50f-02ce4f56e344';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @NextMicroServiceChainLink = @YLink;

INSERT INTO TasksConfigsUnitVariableLinkPull (pk, variable, variableValue, defaultMicroServiceChainLink)
    VALUES (@TasksConfigPKReference, 'postApproveNormalizationLink', '', @YLink);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'c42184a3-1a7f-4c4d-b380-15d8d97fdd11', @TasksConfigPKReference, 'Load post approve normalization link');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- set non zero exit code --
-- UPDATE MicroServiceChainLinks SET defaultNextChainLink = @MoveSIPToFailedLink WHERE pk = @XLink;

-- set zero exit code --
-- UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @NextMicroServiceChainLink where microServiceChainLink = @XLink;

UPDATE MicroServiceChains SET startingLink = @MicroServiceChainLink WHERE startingLink = @YLink;

-- - </alter old workflows>
-- - create new ones

-- ab0d38 loads finished with manual normalized link. 'returnFromManualNormalized'

SET @TasksConfigPKReference = NULL;
SET @TasksConfig = '9413e636-1209-40b0-a735-74ec785ea14a';
SET @MicroServiceChainLink = 'b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3';
SET @MicroServiceChainLinksExitCodes = '94bf222b-55e0-4bce-b02b-6b6127eee72d';
SET @defaultNextChainLink = @NextMicroServiceChainLink;
SET @rejectTransferMicroserviceChain = '1b04ec43-055c-43b7-9543-bd03c6a778ba';

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', @TasksConfigPKReference, 'Normalize');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);

-- Normalize for access
SET @MicroServiceChainChoice = '47d090b7-f0c6-472f-84a1-fc9809dfa00f';
SET @chainAvailable = 'fb7a326e-1e50-4b48-91b9-4917ff8d0ae8';
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);
-- Normalize service files for access
SET @MicroServiceChainChoice = '91d8699a-9fa3-4956-ad3c-d993da05efe7';
SET @chainAvailable = 'e600b56d-1a43-4031-9d7c-f64f123e5662';
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);
-- Normalize manually
SET @MicroServiceChainChoice = '2df531df-339d-49c0-a5fe-5e655596b566';
SET @chainAvailable = 'c34bd22a-d077-4180-bf58-01db35bdb644';
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES                
    (@MicroServiceChainChoice, @MicroServiceChainLink, @chainAvailable);

SET @WatchedDirectory = 'a9c1fb41-244c-410d-bef6-51cb48d975e2';
SET @MicroServiceChains = '503d240c-c5a0-4bd5-a5f2-e3e44bd0018a';
set @NextMicroServiceChainLink = @MicroServiceChainLink;
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChains, @MicroServiceChainLink, 'Select file id type - without existing fits/fileIDbyExt');

INSERT INTO WatchedDirectories (pk, watchedDirectoryPath, chain, onlyActOnDirectories, expectedType)
    VALUES (@WatchedDirectory, '%watchDirectoryPath%workFlowDecisions/selectNormalizationPath/', @MicroServiceChains, True, '76e66677-40e6-41da-be15-709afb334936');
-- --------------------------------------------------------------------------------------------------------------------------

-- Generate DIP 1.0
SET @TasksConfig = '95d2ddff-a5e5-49cd-b4da-a5dd6fd3d2eb';
SET @TasksConfigPKReference = 'a51af5c7-0ed4-41c2-9142-fc9e43e83960';
SET @MicroServiceChainLink = '82c0eca0-d9b6-4004-9d77-ded9286a9ac7';
SET @MicroServiceChainLinksExitCodes = 'e0199503-2b98-47a6-89d9-3a1a91d042c3';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'generateDIPFromAIPGenerateDIP_v0.0','\"%SIPUUID%\" \"%SIPDirectory%\" \"%date%\"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Generate DIP');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, 'd5a2ef60-a757-483c-a71a-ccbffe6b80da');
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- copy thumbnails to DIP 1.1
SET @TasksConfig = '90e0993d-23d4-4d0c-8b7d-73717b58f20e';
SET @MicroServiceChainLink = '1c0f5926-fd76-4571-a706-aa6564555199';
SET @MicroServiceChainLinksExitCodes = '1ce8c9af-bdea-4a6d-ac6e-710205e9dbfb';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- Rename DIP files with original file UUIDs 
SET @TasksConfig = '4d2ed238-1b35-43fb-9753-fcac0ede8da4';
SET @TasksConfigPKReference = '5f5ca409-8009-4732-a47c-1a35c72abefc';
SET @MicroServiceChainLink = '25b5dc50-d42d-4ee2-91fc-5dcc3eef30a7';
SET @MicroServiceChainLinksExitCodes = '0a1a232b-23a6-4a84-a2af-76baadc87139';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'DIP/objects', FALSE, NULL, NULL, 'renameDIPFauxToOrigUUIDs_v0.0','"%SIPUUID%" "%relativeLocation%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Rename DIP files with original UUIDs');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @LinkAfterNormalization = @MicroServiceChainLink;


-- Move to normalize access from original/service decision
SET @TasksConfig = '596a7fd5-a86b-489c-a9c0-3aa64b836cec';
SET @TasksConfigPKReference = '55eec242-68fa-4a1b-a3cd-458c087a017b';
SET @MicroServiceChainLink = 'f2a6f2a5-2f92-47da-b63b-30326625f6ae';
SET @MicroServiceChainLinksExitCodes = '0823e0c7-ab6f-4088-bb09-4cbca4666008';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/workFlowDecisions/selectNormalizationPath/.\" \"%SIPUUID%\" \"%sharedPath%\"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Move to select normalization path.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, NULL);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- Set 'postApproveNormalizationLink'
SET @TasksConfig = '24deba11-c719-4c64-a53c-e08c85663c40';
SET @TasksConfigPKReference = '95fb93a5-ef63-4ceb-8572-c0ddf88ef3ea';
SET @MicroServiceChainLink = '5e4f7467-8637-49b2-a584-bae83dabf762';
SET @MicroServiceChainLinksExitCodes = '6243c80d-8db3-45a2-bc29-ca5d039f0de5';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, microServiceChainLink)
    VALUES (@TasksConfigPKReference, 'postApproveNormalizationLink', '0f0c1f33-29f2-49ae-b413-3e043da5df61');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', @TasksConfigPKReference, 'Set resume link - postApproveNormalizationLink');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- SET 'returnFromManualNormalized'
SET @TasksConfig = '29937fd7-b482-4180-8037-1b57d71e903c';
SET @TasksConfigPKReference = 'ba7bafe6-7241-4ffe-a0b8-97ca3c68eac1';
SET @MicroServiceChainLink = '4df4cc06-3b03-4c6f-b5c4-bec12a97dc90';
SET @MicroServiceChainLinksExitCodes = '6cb712b2-0961-4e93-91e5-9ea5f8ac8b65';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, microServiceChainLink)
    VALUES (@TasksConfigPKReference, 'returnFromManualNormalized', @LinkAfterNormalization);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', @TasksConfigPKReference, 'Set resume link - returnFromManualNormalized');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink2 = @MicroServiceChainLink;


-- Move to Select & run file id tool
SET @TasksConfig = '56aef696-b752-42de-9c6d-0a436bcc6870';
SET @TasksConfigPKReference = '33e7f3af-e414-484f-8468-1db09cb4258b';
SET @MicroServiceChainLink = 'a2173b55-abff-4d8f-97b9-79cc2e0a64fa';
SET @MicroServiceChainLinksExitCodes = 'cb61ce7b-4ba0-483e-8dfa-5c30af4927db';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/workFlowDecisions/selectFileIDTool/.\" \"%SIPUUID%\" \"%sharedPath%\"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Move to select and run file id tool');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, NULL);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;
SET @MoveToSelectRunFileIDToolLink = @MicroServiceChainLink;

/* Redo normalization
*/
--
SET @TasksConfig = 'fe354b27-dbb2-4454-9c1c-340d85e67b78';
SET @MicroServiceChainLink = 'f30b23d4-c8de-453d-9b92-50b86e21d3d5';
SET @MicroServiceChainLinksExitCodes = '00bde88b-b4da-44f3-b0a6-2b96276931ce';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- Set variable: reNormalize
SET @TasksConfig = 'ce48a9f5-4513-49e2-83db-52b01234705b';
SET @TasksConfigPKReference = 'c26b2859-7a96-462f-880a-0cd8d1b0ac32';
SET @MicroServiceChainLink = '635ba89d-0ad6-4fc9-acc3-e6069dffdcd5';
SET @MicroServiceChainLinksExitCodes = '767d6a50-5a17-436c-84f9-68c5991c9a57';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, microServiceChainLink)
    VALUES (@TasksConfigPKReference, 'reNormalize', @NextMicroServiceChainLink);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', @TasksConfigPKReference, 'Set re-normalize link');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @MoveToSelectRunFileIDToolLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;
/* /Redo normalization
*/

-- SET resumeAfterNormalizationFileIdentificationToolSelected
SET @TasksConfig = 'ec503c22-1f4d-442f-b546-f90c9a9e5c86';
SET @TasksConfigPKReference = 'd8e2c7b2-5452-4c26-b57a-04caafe9f95c';
SET @MicroServiceChainLink = '29dece8e-55a4-4f2c-b4c2-365ab6376ceb';
SET @MicroServiceChainLinksExitCodes = 'affffa5f-33b2-43cc-84e0-f7f378c9600e';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, microServiceChainLink)
    VALUES (@TasksConfigPKReference, 'resumeAfterNormalizationFileIdentificationToolSelected', @NextMicroServiceChainLink2);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', @TasksConfigPKReference, 'Set resume link');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink2 = @MicroServiceChainLink;

-- set maildir FileIDs
SET @TasksConfig = '032347f1-c0fb-4c6c-96ba-886ac8ac636c';
SET @TasksConfigPKReference = 'ec688528-d492-4de3-a176-b777734153b1';
SET @MicroServiceChainLink = '83d5e887-6f7c-48b0-bd81-e3f00a9da772';
SET @MicroServiceChainLinksExitCodes = '88ccca76-c4d0-4172-b722-0c0ecb3d7d46';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'setMaildirFileGrpUseAndFileIDs_v0.0', '"%SIPUUID%" "%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Set file group use and fileIDs for maildir AIP');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink2);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- Is maildir AIP--
SET @TasksConfig = '09fae382-37ac-45bb-9b53-d1608a44742c';
SET @TasksConfigPKReference = 'c0ae5130-0c17-4fc1-91c7-aa36265a21d5';
SET @MicroServiceChainLink = 'e4e19c32-16cc-4a7f-a64d-a1f180bdb164';
SET @MicroServiceChainLinksExitCodes = '6d87f2f2-9d5a-4216-8dbf-6201a9ee8cca';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'isMaildirAIP_v0.0', '"%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Is maildir AIP');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 179, @NextMicroServiceChainLink);
SET @MicroServiceChainLinksExitCodes = 'c1f6f15d-2ce9-43fd-841c-1fd916f9fd2e';    
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink2);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- assign faux file UUIDs --
SET @TasksConfig = '5a9fbb03-2434-4034-b20f-bcc6f971a8e5';
SET @TasksConfigPKReference = '4c25f856-6639-42b5-9120-3ac166dce932';
SET @MicroServiceChainLink = '58fcd2fd-bcdf-4e49-ad99-7e24cc8c3ba5';
SET @MicroServiceChainLinksExitCodes = '2a41dd56-1d56-49d9-86f5-2d6d301377e3';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'assignFauxFileUUIDs_v0.0', '"%SIPUUID%" "%SIPDirectory%" "%date%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Assign file UUIDs');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- restructure to sip format
SET @TasksConfig = '135dd73d-845a-412b-b17e-23941a3d9f78';
SET @TasksConfigPKReference = '2808a160-82df-40a8-a6ca-330151584968';
SET @MicroServiceChainLink = '31fc3f66-34e9-478f-8d1b-c29cd0012360';
SET @MicroServiceChainLinksExitCodes = '8609a2ef-9da2-4803-ad4f-605bfff10795';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'restructureBagAIPToSIP_v0.0', '"%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Restructure from bag AIP to SIP directory format');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- determin AIP version --
SET @TasksConfig = 'cd53e17c-1dd1-4e78-9086-e6e013a64536';
SET @TasksConfigPKReference = 'feec6329-c21a-48b6-b142-cd3c810e846f';
SET @MicroServiceChainLink = '60b0e812-ebbe-487e-810f-56b1b6fdd819';
SET @MicroServiceChainLinksExitCodes = '6e06fd5e-3892-4e79-b64f-069876bd95a1';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'determineAIPVersionKeyExitCode_v0.0', '"%SIPUUID%" "%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Determin processing path for this AIP version.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 100, @NextMicroServiceChainLink);
SET @MicroServiceChainLinksExitCodes = '7f2d5239-b464-4837-8e01-0fc43e31395d';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @MoveSIPToFailedLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- move to processing directory
SET @TasksConfig = '74146fe4-365d-4f14-9aae-21eafa7d8393';
SET @MicroServiceChainLink = 'c103b2fb-9a6b-4b68-8112-b70597a6cd14';
SET @MicroServiceChainLinksExitCodes = '7a49c825-aeeb-4609-a3ba-2c2979888591';
SET @defaultNextChainLink = @MoveSIPToFailedLink;


INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- SET Permissions --
SET @TasksConfig = '10846796-f1ee-499a-9908-4c49f8edd7e6';
SET @MicroServiceChainLink = '77c722ea-5a8f-48c0-ae82-c66a3fa8ca77';
SET @MicroServiceChainLinksExitCodes = 'd1b46b7e-57cd-4120-97d6-50f8e385f56e';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '260ef4ea-f87d-4acf-830d-d0de41e6d2af';

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChain, @MicroServiceChainLink, 'Create DIP from AIP');


-- approve transfer --
SET @TasksConfigPKReference = NULL;
SET @TasksConfig = 'c450501a-251f-4de7-acde-91c47cf62e36';
SET @MicroServiceChainLink = '9520386f-bb6d-4fb9-a6b6-5845ef39375f';
SET @MicroServiceChainLinksExitCodes = '813b81f2-770f-4fb2-86f5-64576a83426f';
SET @defaultNextChainLink = @NextMicroServiceChainLink;
SET @rejectTransferMicroserviceChain = '1b04ec43-055c-43b7-9543-bd03c6a778ba';
SET @MicroServiceChainChoice1 = 'c7bbb25e-599b-4511-8392-151088f87dce';
SET @MicroServiceChainChoice2 = '73671d95-dfcc-4b77-91b6-ca7f194f8def';


INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', @TasksConfigPKReference, 'Create DIP from AIP');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES (@MicroServiceChainChoice1, @MicroServiceChainLink, @MicroServiceChain);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES (@MicroServiceChainChoice2, @MicroServiceChainLink, @rejectTransferMicroserviceChain);
    
SET @MicroServiceChain = '9918b64c-b898-407b-bce4-a65aa3c11b89';
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChain, @MicroServiceChainLink, 'createDIPFromAIP-wdChain');

-- create watched directory --
SET @WatchedDirectory = '77ac4a58-8b4f-4519-ad0a-1a35dedb47b4';
INSERT INTO WatchedDirectories (pk, watchedDirectoryPath, chain, onlyActOnDirectories, expectedType)
    VALUES (@WatchedDirectory, '%watchDirectoryPath%system/createDIPFromAIP/', @MicroServiceChain, 1, '76e66677-40e6-41da-be15-709afb334936');
    
-- /issue-1843


-- Issue 5005
--
-- Add microservice chain link to DSpace "Complete transfer" microchain to index transfer files

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments)
    VALUES ('14780202-4aab-43f4-94ed-3bf9a040d055', 0, 'elasticSearchIndex_v0.0', '\"%SIPDirectory%\" \"%SIPUUID%\"');

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES ('e0b25af2-1ce4-4ed3-b14f-87843fbd4c93', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '14780202-4aab-43f4-94ed-3bf9a040d055', 'Index transfer contents');

INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink)
    VALUES ('d2c2b65d-36c6-4636-9459-b5f0b4b0065a', 'Complete transfer', 'Failed', 'e0b25af2-1ce4-4ed3-b14f-87843fbd4c93', NULL);

INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage)
    VALUES ('46b4ff53-11f6-49a3-9aa7-1d5d56a63fa2', 'd2c2b65d-36c6-4636-9459-b5f0b4b0065a', 0, NULL, 'Completed successfully');

UPDATE MicroServiceChainLinks SET defaultNextChainLink='d2c2b65d-36c6-4636-9459-b5f0b4b0065a' WHERE pk='8a0bc7c6-f7c2-4656-a690-976660c66a8a';

UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='d2c2b65d-36c6-4636-9459-b5f0b4b0065a' WHERE microServiceChainLink='8a0bc7c6-f7c2-4656-a690-976660c66a8a';

-- /Issue 5005

-- Issue 5187 Develop Storage Service --
-- Remove StorageDirectories and SourceDirectories - in storage service now
DROP TABLE IF EXISTS `StorageDirectories`;
DROP TABLE IF EXISTS `SourceDirectories`;
DELETE FROM `MicroServiceChoiceReplacementDic` WHERE description = 'Store AIP in standard Archivematica Directory';

-- Split storeAIP into several sequential scripts: verifyAIP, storeAIP and indexAIP

-- Verify AIP
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('ae6b87d8-59c8-4ffa-b417-ce93ab472e74', 0, 'verifyAIP_v0.0', '\"%SIPUUID%\" \"%SIPDirectory%%AIPFilename%\"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('b57b3564-e271-4226-a5f9-2c7cf1661a83', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', 'ae6b87d8-59c8-4ffa-b417-ce93ab472e74', 'Verify AIP');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('3f543585-fa4f-4099-9153-dd6d53572f5c', 'Store AIP', 'Failed', 'b57b3564-e271-4226-a5f9-2c7cf1661a83', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('b060a877-9a59-450c-8da0-f32b97b1a516', '3f543585-fa4f-4099-9153-dd6d53572f5c', 0, '20515483-25ed-4133-b23e-5bb14cab8e22', 'Completed successfully');
UPDATE MicroServiceChainLinks SET defaultNextChainLink='3f543585-fa4f-4099-9153-dd6d53572f5c' WHERE pk='5f213529-ced4-49b0-9e30-be4e0c9b81d5';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='3f543585-fa4f-4099-9153-dd6d53572f5c' WHERE microServiceChainLink='5f213529-ced4-49b0-9e30-be4e0c9b81d5';

-- Index AIP
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('81f36881-9e54-4c75-a5b2-838cfb2ca228', 0, 'indexAIP_v0.0', '\"%SIPUUID%\" \"%SIPName%\" \"%SIPDirectory%%AIPFilename%\"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('134a1a94-22f0-4e67-be17-23a4c7178105', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '81f36881-9e54-4c75-a5b2-838cfb2ca228', 'Index AIP');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('48703fad-dc44-4c8e-8f47-933df3ef6179', 'Store AIP', 'Failed', '134a1a94-22f0-4e67-be17-23a4c7178105', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('0783a1ab-f70e-437b-8bec-cd1f2135ba2a', '48703fad-dc44-4c8e-8f47-933df3ef6179', 0, 'd5a2ef60-a757-483c-a71a-ccbffe6b80da', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='48703fad-dc44-4c8e-8f47-933df3ef6179' WHERE microServiceChainLink='20515483-25ed-4133-b23e-5bb14cab8e22';

-- Fetch AIP Store Locations from Storage Service, instead of using MicroServiceChoiceReplacementDic
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('857fb861-8aa1-45c0-95f5-c5af66764142', 0, 'getAipStorageLocations_v0.0', '');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('75e00332-24a3-4076-aed1-e3dc44379227', 'a19bfd9f-9989-4648-9351-013a10b382ed', '857fb861-8aa1-45c0-95f5-c5af66764142', 'Retrieve AIP Storage Locations');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('49cbcc4d-067b-4cd5-b52e-faf50857b35a', 'Store AIP', 'Failed', '75e00332-24a3-4076-aed1-e3dc44379227', '2d32235c-02d4-4686-88a6-96f4d6c7b1c3');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('7deb2533-ae68-4ffa-9217-85d5bb4bfd62', '49cbcc4d-067b-4cd5-b52e-faf50857b35a', 0, 'b320ce81-9982-408a-9502-097d0daa48fa', 'Completed successfully');
UPDATE MicroServiceChains SET startingLink='49cbcc4d-067b-4cd5-b52e-faf50857b35a' WHERE startingLink='b320ce81-9982-408a-9502-097d0daa48fa';
-- Store AIP Location gets info from MicroService
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute) VALUES ('ebab9878-f42e-4451-a24a-ec709889a858', 0, '%AIPsStore%');
UPDATE TasksConfigs SET taskType='01b748fe-2e9d-44e4-ae5d-113f74c9a0ba', taskTypePKReference='ebab9878-f42e-4451-a24a-ec709889a858' WHERE pk='fb64af31-8f8a-4fe5-a20d-27ee26c9dda2';

-- /Issue 5187 Develop Storage Service

-- Issue 5246
-- Skip 'Create removal from backlog PREMIS events' for SIPS that were never in backlog
-- new MicroServiceChain for auto-created SIPS
INSERT INTO `MicroServiceChains` (`pk`, `startingLink`, `description`, `replaces`, `lastModified`) VALUES ('fefdcee4-dd84-4b55-836f-99ef880ecdb6','db6d3830-9eb4-4996-8f3a-18f4f998e07f','Automatic SIP Creation complete',NULL,'2013-08-22 16:25:08');
-- WatchedDirectory system/autoProcessSIP should point at new chain
UPDATE WatchedDirectories SET chain='fefdcee4-dd84-4b55-836f-99ef880ecdb6' WHERE pk='88f9c08e-ebc3-4334-9126-79d0489e8f39';
-- /Issue 5246

-- Issue 1929
-- Store pass/fail reports in database for easy reference
CREATE TABLE Reports (
  pk int(10) unsigned NOT NULL AUTO_INCREMENT,
  unitType VARCHAR(50) DEFAULT NULL,
  unitName VARCHAR(50) DEFAULT NULL,
  unitIdentifier VARCHAR(50) DEFAULT NULL,
  content LONGTEXT,
  created timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (pk)
);
-- /Issue 1929

-- Issue 5484

-- Update compression algorithm choices
UPDATE MicroServiceChoiceReplacementDic SET description='7z using lzma', replacementDic='{\"%AIPCompressionAlgorithm%\":\"7z-lzma\"}' WHERE pk='c96353b9-0d55-46cf-baa0-d7c3e180dd43';
UPDATE MicroServiceChoiceReplacementDic SET description='7z using bzip2', replacementDic='{\"%AIPCompressionAlgorithm%\":\"7z-bzip2\"}' WHERE pk='9475447c-9889-430c-9477-6287a9574c5b';
-- Add pbzip choice
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic, replaces, lastModified) VALUES ('f61b00a1-ef2e-4dc4-9391-111c6f42b9a7','01d64f58-8295-4b7b-9cab-8f1b153a504f','Parallel bzip2','{\"%AIPCompressionAlgorithm%\":\"pbzip2-\"}',NULL,'2013-08-19 17:25:08');
-- delete 0-copy option
DELETE FROM MicroServiceChoiceReplacementDic WHERE pk='727e3506-961d-4eeb-8178-e290946c329a';
-- Add AIPFilename to SIPs table
ALTER TABLE SIPs ADD aipFilename TEXT NULL DEFAULT NULL;
-- Update Compress AIP job config
UPDATE StandardTasksConfigs SET execute='compressAIP_v0.0', arguments='%AIPCompressionAlgorithm% %AIPCompressionLevel% %SIPDirectory% %SIPName% %SIPUUID%' WHERE pk='4dc2b1d2-acbb-47e7-88ca-570281f3236f';
-- Use %AIPFilename% where needed
UPDATE StandardTasksConfigs SET arguments='\"%AIPsStore%\" \"%SIPDirectory%%AIPFilename%\" \"%SIPUUID%\" \"%SIPName%\"' where pk='7df9e91b-282f-457f-b91a-ad6135f4337d';
UPDATE StandardTasksConfigs SET arguments='775 \"%SIPDirectory%%AIPFilename%\"' WHERE pk='ba937c55-6148-4f45-a9ad-9697c0cf11ed';

-- /Issue 5484

-- Issue 5159 AIP Pointer file
-- Add MicroService that generates Pointer File after Compress AIP
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('45f11547-0df9-4856-b95a-3b1ff0c658bd', 0, 'createPointerFile_v0.0', '%SIPUUID% %SIPName% %AIPCompressionAlgorithm% %SIPDirectory% %AIPFilename%');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('a20c5353-9e23-4b5d-bb34-09f2efe1e54d', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '45f11547-0df9-4856-b95a-3b1ff0c658bd', 'Create AIP Pointer File');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('0915f727-0bc3-47c8-b9b2-25dc2ecef2bb', 'Prepare AIP', 'Failed', 'a20c5353-9e23-4b5d-bb34-09f2efe1e54d', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('f5644951-ecaa-42bc-9286-ed4ee220b58f', '0915f727-0bc3-47c8-b9b2-25dc2ecef2bb', 0, '5fbc344c-19c8-48be-a753-02dac987428c', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='0915f727-0bc3-47c8-b9b2-25dc2ecef2bb' WHERE microServiceChainLink='d55b42c8-c7c5-4a40-b626-d248d2bd883f';
-- /Issue 5159
