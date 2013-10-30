-- Common
SET @MoveTransferToFailedLink = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd';
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';
SET @identifyFileFormatMSCL='2522d680-c7d9-4d06-8b11-a28d8bd8a71f' COLLATE utf8_unicode_ci;
SET @characterizeExtractMetadata = '303a65f6-a16f-4a06-807b-cb3425a30201' COLLATE utf8_unicode_ci;
SET @watchedDirExpectTransfer = 'f9a3a93b-f184-4048-8072-115ffac06b5d' COLLATE utf8_unicode_ci;

-- /Common

-- Issue 6020

-- Updated remove unneeded files to remove excess args
UPDATE StandardTasksConfigs SET arguments='"%relativeLocation%" "%fileUUID%"' WHERE pk='49b803e3-8342-4098-bb3f-434e1eb5cfa8';

-- Add remove unneeded files to Transfer, before file ID
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('66aa823d-3b72-4d13-9ad6-c5e6580857b8', 1, 'removeUnneededFiles_v0.0', '"%relativeLocation%" "%fileUUID%"'); -- not in objects/
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('85308c8b-b299-4453-bf40-9ac61d134015', 'a6b1c323-7d36-428e-846a-e7e819423577', '66aa823d-3b72-4d13-9ad6-c5e6580857b8', 'Remove unneeded files');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('5d780c7d-39d0-4f4a-922b-9d1b0d217bca', 'Verify transfer compliance', 'Failed', '85308c8b-b299-4453-bf40-9ac61d134015', 'ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('9cb81a5c-a7a1-43a8-8eb6-3e999923e03c', '5d780c7d-39d0-4f4a-922b-9d1b0d217bca', 0, 'ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='5d780c7d-39d0-4f4a-922b-9d1b0d217bca' WHERE microServiceChainLink='50b67418-cb8d-434d-acc9-4a8324e7fdd2';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='5d780c7d-39d0-4f4a-922b-9d1b0d217bca' WHERE pk='50b67418-cb8d-434d-acc9-4a8324e7fdd2';

-- Add remove unneeded and hidden files to Transfer after extract
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('bdce640d-6e94-49fe-9300-3192a7e5edac', 'Extract packages', 'Failed', 'ef0bb0cf-28d5-4687-a13d-2377341371b5', 'aaa929e4-5c35-447e-816a-033a66b9b90b');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('9a07d5a1-1418-4007-9c7e-55462ca63751', 'bdce640d-6e94-49fe-9300-3192a7e5edac', 0, 'aaa929e4-5c35-447e-816a-033a66b9b90b', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='bdce640d-6e94-49fe-9300-3192a7e5edac' WHERE microServiceChainLink='c5ecb5a9-d697-4188-844f-9a756d8734fa';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='bdce640d-6e94-49fe-9300-3192a7e5edac' WHERE pk='c5ecb5a9-d697-4188-844f-9a756d8734fa';
-- Update for maildir
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('e19f8eed-faf9-4e04-bf1f-e9418f2b2b11', 'Extract packages', 'Failed', 'ef0bb0cf-28d5-4687-a13d-2377341371b5', '22ded604-6cc0-444b-b320-f96afb15d581');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('0ef15153-0d41-4b93-bdb3-4158cec405a3', 'e19f8eed-faf9-4e04-bf1f-e9418f2b2b11', 0, '22ded604-6cc0-444b-b320-f96afb15d581', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='e19f8eed-faf9-4e04-bf1f-e9418f2b2b11' WHERE microServiceChainLink='01b30826-bfc4-4e07-8ca2-4263debad642';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='e19f8eed-faf9-4e04-bf1f-e9418f2b2b11' WHERE pk='01b30826-bfc4-4e07-8ca2-4263debad642';

-- /Issue 6020

-- Issue 5232
-- Update CONTENTdm example to put http:// in front of ContentdmServer
UPDATE MicroServiceChoiceReplacementDic SET replacementDic='{\"%ContentdmServer%\":\"http://111.222.333.444:81\", \"%ContentdmUser%\":\"usernamebar\", \"%ContentdmGroup%\":\"456\"}' WHERE pk='c001db23-200c-4195-9c4a-65f206f817f2';
UPDATE MicroServiceChoiceReplacementDic SET replacementDic='{\"%ContentdmServer%\":\"http://localhost\", \"%ContentdmUser%\":\"usernamefoo\", \"%ContentdmGroup%\":\"123\"}' WHERE pk='ce62eec6-0a49-489f-ac4b-c7b8c93086fd';
-- /Issue 5232

-- Issue 5895 - make package extraction optional
SET @extractContentsMSCL = '1cb7e228-6e94-4c93-bf70-430af99b9264' COLLATE utf8_unicode_ci;
SET @extractChoiceChain = 'c868840c-cf0b-49db-a684-af4248702954' COLLATE utf8_unicode_ci;
SET @extractChain = '01d80b27-4ad1-4bd1-8f8d-f819f18bf685' COLLATE utf8_unicode_ci;
SET @postExtractChain = '79f1f5af-7694-48a4-b645-e42790bbf870' COLLATE utf8_unicode_ci;
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@extractChain, @extractContentsMSCL, 'Extract');
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@postExtractChain, @characterizeExtractMetadata, 'Do not extract');


SET @extractChoiceWatchSTC = '8daffda4-397c-4f56-85db-c4376bf6891e' COLLATE utf8_unicode_ci;
SET @extractChoiceWatchTC = 'a68d7873-86cf-42d3-a95e-68b62f92f0f9' COLLATE utf8_unicode_ci;
SET @extractChoiceWatchMSCL = 'cc16178b-b632-4624-9091-822dd802a2c6' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES (@extractChoiceWatchSTC, 0, 'moveTransfer_v0.0', '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/extractPackagesChoice/."  "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@extractChoiceWatchTC, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @extractChoiceWatchSTC, 'Move to extract packages');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@extractChoiceWatchMSCL, 'Extract packages', 'Failed', @extractChoiceWatchTC, @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('9157ab64-b4d9-4e87-afc8-d2027d8ff1f4', @extractChoiceWatchMSCL, 0, NULL, 'Completed successfully');

SET @extractChoiceTC = 'a4a4679f-72b8-48da-a202-e0a25fbc41bf' COLLATE utf8_unicode_ci;
SET @extractChoiceMSCL = 'dec97e3c-5598-4b99-b26e-f87a435a6b7f' COLLATE utf8_unicode_ci;
INSERT INTO TasksConfigs (pk, taskType, description) VALUES (@extractChoiceTC, '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', 'Extract packages?');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask) VALUES (@extractChoiceMSCL, 'Extract packages', 'Failed', @extractChoiceTC);

INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@extractChoiceChain, @extractChoiceMSCL, 'Extract packages');
INSERT INTO WatchedDirectories (pk, watchedDirectoryPath, chain, expectedType) VALUES ('64198d4e-ec61-46fe-b043-228623c2b26f', "%watchDirectoryPath%workFlowDecisions/extractPackagesChoice/", @extractChoiceChain, @watchedDirExpectTransfer);

INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable) VALUES ('25bab081-384f-4462-be01-9dfef2dd6f30', @extractChoiceMSCL, @extractChain);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable) VALUES ('3fab588e-58dd-4d86-a5ce-2e4b67774c28', @extractChoiceMSCL, @postExtractChain);

UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@extractChoiceWatchMSCL WHERE microServiceChainLink=@identifyFileFormatMSCL;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@extractChoiceWatchMSCL WHERE pk=@identifyFileFormatMSCL;

-- /Issue 5895
