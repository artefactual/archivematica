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

-- Issue 5894 - Make package deletion optional
SET @extractDeleteChoiceTC = '86a832aa-bd37-44e2-ba02-418fb82e34f1' COLLATE utf8_unicode_ci;
SET @extractDeleteChoiceMSCL = 'f19926dd-8fb5-4c79-8ade-c83f61f55b40' COLLATE utf8_unicode_ci;
INSERT INTO TasksConfigs (pk, taskType, description) VALUES (@extractDeleteChoiceTC, '9c84b047-9a6d-463f-9836-eafa49743b84', 'Delete package after extraction?');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask) VALUES (@extractDeleteChoiceMSCL, 'Extract packages', 'Failed', @extractDeleteChoiceTC);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('59363759-0e3d-4635-965d-7670b489201b', @extractDeleteChoiceMSCL, 0, @extractContentsMSCL, 'Completed successfully');
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ('85b1e45d-8f98-4cae-8336-72f40e12cbef', @extractDeleteChoiceMSCL, 'Delete', '{"%DeletePackage%":"True"}');
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ('72e8443e-a8eb-49a8-ba5f-76d52f960bde', @extractDeleteChoiceMSCL, 'Do not delete', '{"%DeletePackage%":"False"}');

UPDATE MicroServiceChains SET startingLink=@extractDeleteChoiceMSCL WHERE pk=@extractChain;
UPDATE StandardTasksConfigs SET arguments='"%SIPUUID%" "%transferDirectory%" "%date%" "%taskUUID%" "%DeletePackage%"' WHERE pk='8fad772e-7d2e-4cdd-89e6-7976152b6696';

-- /Issue 5895

-- Issue 6067
-- All of these columns may at some point contain a non-Unicode filename,
-- so they need to be one of the various binary datatypes instead of "text"
ALTER TABLE Tasks MODIFY fileName longblob;
ALTER TABLE Tasks MODIFY arguments varbinary(1000);
ALTER TABLE Tasks MODIFY stdOut longblob;
ALTER TABLE Tasks MODIFY stdError longblob;

ALTER TABLE Files MODIFY originalLocation longblob;
ALTER TABLE Files MODIFY currentLocation longblob;

ALTER TABLE Events MODIFY eventOutcomeDetailNote longblob;
-- /Issue 6067

-- Issue 5216

-- Add Chain Choice for 'Add manual normalization metadata'
-- MSCL move to watched dir - terminate
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('38920eaa-09a2-470c-bb3d-791d66ec359c', 0, 'moveSIP_v0.0', '"%SIPDirectory%" "%sharedPath%watchedDirectories/manualNormalizationMetadata/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('fa8b1f81-0d79-4f9a-a888-fc3292f2d992', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '38920eaa-09a2-470c-bb3d-791d66ec359c', 'Move to manual normalization metadata directory');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('b366e9c5-95f6-49f1-957c-a8f7bb601120', 'Normalize', 'Failed', 'fa8b1f81-0d79-4f9a-a888-fc3292f2d992', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('5ce2e89a-ea14-4445-bc92-d287bf02afb3', 'b366e9c5-95f6-49f1-957c-a8f7bb601120', 0, NULL, 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='b366e9c5-95f6-49f1-957c-a8f7bb601120' WHERE microServiceChainLink='91ca6f1f-feb5-485d-99d2-25eed195e330';
-- MSCL move currently processing
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('50ddfe31-de9d-4a25-b0aa-fd802520607b', 'Normalize', 'Failed', '74146fe4-365d-4f14-9aae-21eafa7d8393', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('8008c4a7-bea2-43b0-83ff-b6df0ceb3937', '50ddfe31-de9d-4a25-b0aa-fd802520607b', 0, 'ab0d3815-a9a3-43e1-9203-23a40c00c551', 'Completed successfully');
-- MSCL done MN metadata - Use replacement dict since only one path
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('71d0caff-1257-4843-8df7-82615724d5a5', '9c84b047-9a6d-463f-9836-eafa49743b84', 'a9d91e76-8639-4cfa-9189-54c139cbac60', 'Add manual normalization metadata?');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('a50570ee-2acf-4205-81fd-ddf11c1a6582', 'Normalize', 'Failed', '71d0caff-1257-4843-8df7-82615724d5a5', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('8b65763d-de29-4ce8-b42f-9e244d6d701f', 'a50570ee-2acf-4205-81fd-ddf11c1a6582', 0, '50ddfe31-de9d-4a25-b0aa-fd802520607b', 'Completed successfully');
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ('a9d91e76-8639-4cfa-9189-54c139cbac60', 'a50570ee-2acf-4205-81fd-ddf11c1a6582', 'Metadata entered', '{"%Unused%":"%Unused%"}');
-- MSC manual normalization event detail chain
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES ('e2382ce4-6ee0-4445-aca3-0764ebae94ac', 'a50570ee-2acf-4205-81fd-ddf11c1a6582', 'Manual normalization metadata entry wait');
-- WatchedDir to start up Add manual normalization metadata chain
INSERT INTO WatchedDirectories (pk, watchedDirectoryPath, chain, expectedType) VALUES ('0a621b7d-6cbd-4193-b1d4-b4b90fbc2461', '%watchDirectoryPath%manualNormalizationMetadata/', 'e2382ce4-6ee0-4445-aca3-0764ebae94ac', '76e66677-40e6-41da-be15-709afb334936');

-- /Issue 5216

-- Issue 6217
-- Prompts the user to add metadata just before the METS file will be generated
SET @metadata_reminder_watch_chain  = '86fbea68-d08c-440f-af2c-dac68556db12';
SET @metadata_reminder_watch_stc    = 'b6b39093-297e-4180-ad61-274bc9c5b451';
SET @metadata_reminder_watch_tc     = '1cf09019-56a1-47eb-8fe0-9bbff158892d';
SET @metadata_reminder_watch_mscl   = '54b73077-a062-41cc-882c-4df1eba447d9';
SET @metadata_reminder_mscl         = 'eeb23509-57e2-4529-8857-9d62525db048';
SET @metadata_reminder_config       = '5c149b3b-8fb3-431c-a577-11cf349cfb38';
SET @metadata_reminder_tc           = '9f0388ae-155c-4cbf-9e15-525ff03e025f';
SET @metadata_prepare_mscl          = 'ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0';
SET @metadata_prepare_chain         = '5727faac-88af-40e8-8c10-268644b0142d';

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@metadata_reminder_tc, '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', @metadata_reminder_config, 'Reminder: add metadata if desired');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask) VALUES (@metadata_reminder_mscl, 'Process metadata directory', @metadata_reminder_tc);

INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@metadata_reminder_watch_chain, @metadata_reminder_mscl, 'Move to metadata reminder');
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@metadata_prepare_chain, @metadata_prepare_mscl, 'Continue');

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES (@metadata_reminder_watch_stc, 0, 'moveTransfer_v0.0', '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/metadataReminder/."  "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@metadata_reminder_watch_tc, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @metadata_reminder_watch_stc, 'Move to metadata reminder');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@metadata_reminder_watch_mscl, 'Process metadata directory', 'Failed', @metadata_reminder_watch_tc, @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('bb20acc4-ca05-4800-831d-2ef585f32e2a', @metadata_reminder_watch_mscl, 0, NULL, 'Completed successfully');

INSERT INTO WatchedDirectories (pk, watchedDirectoryPath, chain, expectedType) VALUES ('7ac9aec3-396a-485d-8695-d7015121d865', "%watchDirectoryPath%workFlowDecisions/metadataReminder/", @metadata_reminder_watch_chain, @watchedDirExpectTransfer);

INSERT INTO MicroServiceChainChoice (pk, choiceavailableatlink, chainAvailable) VALUES (@metadata_reminder_config, @metadata_reminder_mscl, @metadata_prepare_chain);
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@metadata_reminder_watch_mscl WHERE microServiceChainLink='75fb5d67-5efa-4232-b00b-d85236de0d3f';
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@metadata_reminder_watch_mscl WHERE pk='75fb5d67-5efa-4232-b00b-d85236de0d3f';
-- /Issue 6217
