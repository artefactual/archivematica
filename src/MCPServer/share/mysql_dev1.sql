-- Common
SET @MoveTransferToFailedLink = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd';
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';
SET @identifyFileFormatMSCL='2522d680-c7d9-4d06-8b11-a28d8bd8a71f' COLLATE utf8_unicode_ci;
SET @characterizeExtractMetadata = '303a65f6-a16f-4a06-807b-cb3425a30201' COLLATE utf8_unicode_ci;
SET @watchedDirExpectTransfer = 'f9a3a93b-f184-4048-8072-115ffac06b5d' COLLATE utf8_unicode_ci;
SET @watchedDirExpectSIP = '76e66677-40e6-41da-be15-709afb334936' COLLATE utf8_unicode_ci;

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

-- Issue 6217
-- Prompts the user to add metadata just before the METS file will be generated
SET @metadata_reminder_watch_chain  = '86fbea68-d08c-440f-af2c-dac68556db12';
SET @metadata_reminder_watch_stc    = 'b6b39093-297e-4180-ad61-274bc9c5b451';
SET @metadata_reminder_watch_tc     = '1cf09019-56a1-47eb-8fe0-9bbff158892d';
SET @metadata_reminder_watch_mscl   = '54b73077-a062-41cc-882c-4df1eba447d9';
SET @metadata_reminder_mscl         = 'eeb23509-57e2-4529-8857-9d62525db048';
SET @metadata_reminder_config       = '5c149b3b-8fb3-431c-a577-11cf349cfb38';
SET @metadata_reminder_tc           = '9f0388ae-155c-4cbf-9e15-525ff03e025f';
SET @metadata_prepare_mscl          = 'ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0' COLLATE utf8_unicode_ci;
SET @metadata_prepare_chain         = '5727faac-88af-40e8-8c10-268644b0142d';

-- Insert reminder "question"
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@metadata_reminder_tc, '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', @metadata_reminder_config, 'Reminder: add metadata if desired');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask) VALUES (@metadata_reminder_mscl, 'Process metadata directory', @metadata_reminder_tc);
-- Insert reminder chain for WD
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@metadata_reminder_watch_chain, @metadata_reminder_mscl, 'Move to metadata reminder');
-- Insert post-reminder chain
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@metadata_prepare_chain, @metadata_prepare_mscl, 'Continue');
-- Insert move to reminder Watched Directory
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES (@metadata_reminder_watch_stc, 0, 'moveSIP_v0.0', '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/metadataReminder/."  "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@metadata_reminder_watch_tc, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @metadata_reminder_watch_stc, 'Move to metadata reminder');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@metadata_reminder_watch_mscl, 'Process metadata directory', 'Failed', @metadata_reminder_watch_tc, @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('bb20acc4-ca05-4800-831d-2ef585f32e2a', @metadata_reminder_watch_mscl, 0, NULL, 'Completed successfully');
-- Insert Reminder watched directory
INSERT INTO WatchedDirectories (pk, watchedDirectoryPath, chain, expectedType) VALUES ('7ac9aec3-396a-485d-8695-d7015121d865', "%watchDirectoryPath%workFlowDecisions/metadataReminder/", @metadata_reminder_watch_chain, @watchedDirExpectSIP);
-- Insert choice
INSERT INTO MicroServiceChainChoice (pk, choiceavailableatlink, chainAvailable) VALUES (@metadata_reminder_config, @metadata_reminder_mscl, @metadata_prepare_chain);

-- Move Generate METS and related question to before split in path
SET @virus_scan = '8bc92801-4308-4e3b-885b-1a89fdcd3014' COLLATE utf8_unicode_ci;
SET @remove_mn_dirs = '75fb5d67-5efa-4232-b00b-d85236de0d3f' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@remove_mn_dirs WHERE microServiceChainLink=@virus_scan;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@metadata_reminder_watch_mscl WHERE microServiceChainLink=@remove_mn_dirs;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@metadata_reminder_watch_mscl WHERE pk=@remove_mn_dirs;
-- Post generate METS go back to preservation/access split
SET @load_post_metadata_mscl = 'f1e286f9-4ec7-4e19-820c-dae7b8ea7d09' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@load_post_metadata_mscl WHERE microServiceChainLink=@metadata_prepare_mscl;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@load_post_metadata_mscl WHERE pk=@metadata_prepare_mscl;
-- Update where load links point to
UPDATE TasksConfigsSetUnitVariable SET microServiceChainLink='378ae4fc-7b62-40af-b448-a1ab47ac2c0c' WHERE pk='6b4600f2-6df6-42cb-b611-32938b46a9cf';
UPDATE TasksConfigsSetUnitVariable SET microServiceChainLink='65240550-d745-4afe-848f-2bf5910457c9' WHERE pk='771dd17a-02d1-403b-a761-c70cc9cc1d1a';

-- Remove unneeded
SET @del_mscl_1='fa5b0c43-ed7b-4c7e-95a8-4f9ec7181260' COLLATE utf8_unicode_ci;
SET @del_mscl_2='cccc2da4-e9b8-43a0-9ca2-7383eff0fac9' COLLATE utf8_unicode_ci;
SET @del_tc_1='23650e92-092d-4ace-adcc-c627c41b127e' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@del_mscl_1, @del_mscl_2);
DELETE FROM MicroServiceChainLinks WHERE pk=@del_mscl_1;
DELETE FROM MicroServiceChainLinks WHERE pk=@del_mscl_2;
DELETE FROM TasksConfigs WHERE pk=@del_tc_1;

-- /Issue 6217

-- Issue 5955
-- Fix group on METS gen
UPDATE MicroServiceChainLinks SET microserviceGroup = "Prepare AIP" WHERE pk IN ('ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0', '65240550-d745-4afe-848f-2bf5910457c9');
-- /Issue 5955

-- Issue 5803 AIC

-- Create METS.xml file
INSERT INTO StandardTasksConfigs(pk, execute, arguments) VALUES ('1f3f4e3b-2f5a-47a2-8d1c-27a6f1b94b95', 'createMETS_v2.0', '--baseDirectoryPath "%SIPDirectory%" --baseDirectoryPathString "SIPDirectory" --fileGroupIdentifier "%SIPUUID%" --fileGroupType "sipUUID" --xmlFile "%SIPDirectory%METS.%SIPUUID%.xml"');
INSERT INTO TasksConfigs(pk, taskType, taskTypePKReference, description) VALUES ('8ea17652-a136-4251-b460-d50b0c7090eb', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '1f3f4e3b-2f5a-47a2-8d1c-27a6f1b94b95', 'Generate METS.xml document');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('53e14112-21bb-46f0-aed3-4e8c2de6678f', 'Prepare AIC', 'Failed', '8ea17652-a136-4251-b460-d50b0c7090eb', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('27e94795-ae8e-4e7d-942f-346024167c76', '53e14112-21bb-46f0-aed3-4e8c2de6678f', 0, '3ba518ab-fc47-4cba-9b5c-79629adac10b', 'Completed successfully');
-- Create thumbnail dir
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('9e810686-d747-4da1-9908-876fb89ac78e', 'Prepare AIC', 'Failed', 'ea463bfd-5fa2-4936-b8c3-1ce3b74303cf', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('0b689082-e35b-4bc5-b2da-6773398ea6a7', '9e810686-d747-4da1-9908-876fb89ac78e', 0, '53e14112-21bb-46f0-aed3-4e8c2de6678f', 'Completed successfully');
-- Insert create AIC METS MSCL
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('77e6b5ec-acf7-44d0-b250-32cbe014499d', 0, 'createAIC_METS_v1.0', '"%SIPUUID%" "%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('741a09ee-8143-4216-8919-1046571af3e9', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '77e6b5ec-acf7-44d0-b250-32cbe014499d', 'Create AIC METS file');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('142d0a36-2b88-4b98-8a33-d809f667ecef', 'Prepare AIC', 'Failed', '741a09ee-8143-4216-8919-1046571af3e9', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('bff46a44-5493-4217-b858-81e840f1ca8b', '142d0a36-2b88-4b98-8a33-d809f667ecef', 0, '9e810686-d747-4da1-9908-876fb89ac78e', 'Completed successfully');
-- Include default SIP processingMCP
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('d29105f0-161d-449d-9c34-5a5ea3263f8e', 'Prepare AIC', 'Failed', 'f89b9e0f-8789-4292-b5d0-4a330c0205e1', '142d0a36-2b88-4b98-8a33-d809f667ecef');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('1977601d-0a2d-4ccc-9aa6-571d4b6b0804', 'd29105f0-161d-449d-9c34-5a5ea3263f8e', 0, '142d0a36-2b88-4b98-8a33-d809f667ecef', 'Completed successfully');
-- Restructure for compliance
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('0c2c9c9a-25b2-4a2d-a790-103da79f9604', 'Prepare AIC', 'Failed', '3ae4931e-886e-4e0a-9a85-9b047c9983ac', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('b981edfd-d9d8-498f-a7f2-1765d6833923', '0c2c9c9a-25b2-4a2d-a790-103da79f9604', 0, 'd29105f0-161d-449d-9c34-5a5ea3263f8e', 'Completed successfully');
-- Move to processing dir
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('efd15406-fd6c-425b-8772-d460e1e79009', 'Prepare AIC', 'Failed', '74146fe4-365d-4f14-9aae-21eafa7d8393', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('7941ee5a-f093-4cfb-bacc-03dfb7d51e15', 'efd15406-fd6c-425b-8772-d460e1e79009', 0, '0c2c9c9a-25b2-4a2d-a790-103da79f9604', 'Completed successfully');
-- Set permissions
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('f8cb20e6-27aa-44f6-b5a1-dd53b5fc71f6', 'Prepare AIC', 'Failed', 'ad38cdea-d1da-4d06-a7e5-6f75da85a718', @MoveSIPToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('4aa64bfe-3574-4bd4-8f6f-7c4cb0575f85', 'f8cb20e6-27aa-44f6-b5a1-dd53b5fc71f6', 0, 'efd15406-fd6c-425b-8772-d460e1e79009', 'Completed successfully');
-- Approve/reject AIC
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('81f2a21b-a7a0-44e4-a2f6-9a6cf742b052', '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', NULL, 'Approve AIC');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('6404ce13-8619-48ba-b12f-aa7a034153ac', 'Approve AIC', 'Failed', '81f2a21b-a7a0-44e4-a2f6-9a6cf742b052', @MoveSIPToFailedLink);
-- Reject AIC choice
INSERT INTO MicroServiceChainChoice(pk, choiceAvailableAtLink, chainAvailable) VALUES ('e981fb29-7f93-4719-99ba-f2d22455f3ed', '6404ce13-8619-48ba-b12f-aa7a034153ac', '169a5448-c756-4705-a920-737de6b8d595');
-- Approve AIC choice
INSERT INTO MicroServiceChains(pk, startingLink, description) VALUES ('5f34245e-5864-4199-aafc-bc0ada01d4cd', 'f8cb20e6-27aa-44f6-b5a1-dd53b5fc71f6', 'Approve AIC');
INSERT INTO MicroServiceChainChoice(pk, choiceAvailableAtLink, chainAvailable) VALUES ('bebc5174-09b8-49e6-8dd6-4896e49fdc5e', '6404ce13-8619-48ba-b12f-aa7a034153ac', '5f34245e-5864-4199-aafc-bc0ada01d4cd');

-- Add WatchedDir MSC
INSERT INTO MicroServiceChains(pk, startingLink, description) VALUES ('0766af55-a950-44d0-a79b-9f2bb65f92c8', '6404ce13-8619-48ba-b12f-aa7a034153ac', 'Create AIC');
-- WatchedDirectory
INSERT INTO WatchedDirectories(pk, watchedDirectoryPath, chain, expectedType) VALUES ('aae2a1df-b012-492d-8d84-4fd9bcc25b71', '%watchDirectoryPath%system/createAIC/', '0766af55-a950-44d0-a79b-9f2bb65f92c8', '76e66677-40e6-41da-be15-709afb334936');

-- Add Part of AIC to Dublin Core
ALTER TABLE Dublincore ADD isPartOf longtext;

-- Updated bagit command to put metadata/ in the payload too
UPDATE StandardTasksConfigs SET arguments='create "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%METS.%SIPUUID%.xml" "%SIPDirectory%thumbnails/" "%SIPDirectory%metadata/" --writer filesystem --payloadmanifestalgorithm "sha512"' WHERE pk='045f84de-2669-4dbc-a31b-43a4954d0481';

-- Add sipType to SIPs table
ALTER TABLE SIPs ADD sipType varchar(8);

-- IndexAIP and storeAIP uses sipType
UPDATE StandardTasksConfigs SET arguments='"%SIPUUID%" "%SIPName%" "%SIPDirectory%%AIPFilename%" "%SIPType%"' WHERE pk='81f36881-9e54-4c75-a5b2-838cfb2ca228';
UPDATE StandardTasksConfigs SET arguments='"%AIPsStore%" "%SIPDirectory%%AIPFilename%" "%SIPUUID%" "%SIPName%" "%SIPType%"' WHERE pk='7df9e91b-282f-457f-b91a-ad6135f4337d';

-- /Issue 5803 AIC

-- Issue 6261
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('44d3789b-10ad-4a9c-9984-c2fe503c8720', 0, 'jsonMetadataToCSV_v0.0', '"%SIPUUID%" "%SIPDirectory%metadata/metadata.json"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('f0e49772-3e2b-480d-8c06-023efc670dcd', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '44d3789b-10ad-4a9c-9984-c2fe503c8720', 'Process transfer JSON metadata');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('8c8bac29-4102-4fd2-9d0a-a3bd2e607566', 'Reformat metadata files', 'Failed', 'f0e49772-3e2b-480d-8c06-023efc670dcd', '61c316a6-0a50-4f65-8767-1f44b1eeb6dd');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('abe6c490-9749-46fc-98aa-a6814a507d72', '8c8bac29-4102-4fd2-9d0a-a3bd2e607566', 0, 'f1bfce12-b637-443f-85f8-b6450ca01a13', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='8c8bac29-4102-4fd2-9d0a-a3bd2e607566' WHERE microServiceChainLink='370aca94-65ab-4f2a-9d7d-294a62c8b7ba';
-- /Issue 6261

-- Issue 5866 - Customizeable FPR characterization
-- Inserts a new TasksConfigs entry for the new "Characterize and extract metadata", replacing archivematicaFITS
SET @characterizeSTC = 'd6307888-f5ef-4828-80d6-fb6f707ae023' COLLATE utf8_unicode_ci;
SET @characterizeTC = '00041f5a-42cd-4b77-a6d4-6ef0f376a817' COLLATE utf8_unicode_ci;
SET @characterizeExtractMetadata='303a65f6-a16f-4a06-807b-cb3425a30201' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES (@characterizeSTC, 0, 'characterizeFile_v0.0', '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"', 'objects');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@characterizeTC, 'a6b1c323-7d36-428e-846a-e7e819423577', @characterizeSTC, "Characterize and extract metadata");
UPDATE MicroServiceChainLinks SET currentTask=@characterizeTC WHERE pk=@characterizeExtractMetadata;

-- This is necessary because we can have multiple command outputs per
-- file, not just one. The unique constraint is a combo of file and command.
ALTER TABLE FPCommandOutput
	DROP PRIMARY KEY,
	ADD PRIMARY KEY(fileUUID, ruleUUID);

-- Insert a run of identify file format before running characterize on
-- submission docs in ingest, then update that characterization so it
-- uses this new microservice.

-- The pre-existing microservice
SET @characterizeIngest = '33d7ac55-291c-43ae-bb42-f599ef428325' COLLATE utf8_unicode_ci;

SET @idToolChoiceMSCL = '087d27be-c719-47d8-9bbb-9a7d8b609c44' COLLATE utf8_unicode_ci;
SET @idToolChoiceTC = '0c95f944-837f-4ada-a396-2c7a818806c6' COLLATE utf8_unicode_ci;
SET @idSubmissionDocsMSCL = '1dce8e21-7263-4cc4-aa59-968d9793b5f2' COLLATE utf8_unicode_ci;
SET @idSubmissionDocsSTC = '82b08f3a-ca8f-4259-bd92-2fc1ab4f9974' COLLATE utf8_unicode_ci;
SET @idSubmissionDocsTC = '28e8e81c-3380-47f6-a973-e48f94104692' COLLATE utf8_unicode_ci;

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@idToolChoiceTC, '9c84b047-9a6d-463f-9836-eafa49743b84', NULL, 'Select file format identification command');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values (@idToolChoiceMSCL, 'Process submission documentation', 'Failed', @idtoolchoicetc, @MoveSIPToFailedLink);
-- Insert file ID choice after scan for viruses
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@idToolChoiceMSCL WHERE microServiceChainLink='1ba589db-88d1-48cf-bb1a-a5f9d2b17378';


INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES (@idSubmissionDocsSTC, 0, 'identifyFileFormat_v0.0', '%IDCommand% %relativeLocation% %fileUUID%', 'objects/submissionDocumentation');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@idSubmissionDocsTC, 'a6b1c323-7d36-428e-846a-e7e819423577', @idSubmissionDocsSTC, 'Identify file format');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@idSubmissionDocsMSCL, 'Process submission documentation', 'Failed', @idSubmissionDocsTC, @MoveSIPToFailedLink);

INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('c3f1a78b-0e5e-4d3f-8d32-ba9554ebddf8', @idToolChoiceMSCL, 0, @idSubmissionDocsMSCL, 'Completed successfully');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('80547eac-c724-45e1-8804-3eabf18bea47', @idSubmissionDocsMSCL, 0, @characterizeIngest, 'Completed successfully');

UPDATE StandardTasksConfigs SET execute='characterizeFile_v0.0', arguments='"%relativeLocation%" "%fileUUID%" "%SIPUUID%"' WHERE pk = '4b816807-10a7-447a-b42f-f34c8b8b3b76';

-- Insert the initial MicroServiceChoiceReplacementDics; newly-created commands will be autoinserted
-- in the future.
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ('782bbf56-e220-48b5-9eb6-6610583f2072', @idToolChoiceMSCL, 'Skip File Identification', '{"%IDCommand%":"None"}');
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ('6f9bfd67-f598-400a-aa2e-12b2657962fc', @idToolChoiceMSCL, 'Fido version 1 PUID runs Identify using Fido', '{"%IDCommand%":"1c7dd02f-dfd8-46cb-af68-5b305aea1d6e"}');
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ('724b17a2-668b-4ef6-9f3b-860d8dfcbb29', @idToolChoiceMSCL, 'File Extension version 0.1 file extension runs Identify by File Extension', '{"%IDCommand%":"41efbe1b-3fc7-4b24-9290-d0fb5d0ea9e9"}');

-- Unify a pair of sets of chainlinks that duplicated identical behaviour needlessly
--
-- Move the "set unit variable" chainlinks to the top of the chain;
-- both of these then converge into an identical chain afterwards.
--
-- This path is followed if normalization is performed
SET @setResumeLink1 = 'c168f1ee-5d56-4188-8521-09f0c5475133' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='77a7fa46-92b9-418e-aa88-fbedd4114c9f' WHERE microServiceChainLink=@setResumeLink1;
UPDATE MicroServiceChainLinks SET defaultNextChainLink='e4b0c713-988a-4606-82ea-4b565936d9a7' WHERE pk='ee438694-815f-4b74-97e1-8e7dde2cc6d5';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='e4b0c713-988a-4606-82ea-4b565936d9a7' WHERE microServiceChainLink='ee438694-815f-4b74-97e1-8e7dde2cc6d5';
UPDATE TasksConfigsSetUnitVariable SET microServiceChainLink=@setResumeLink1 WHERE pk='5035632e-7879-4ece-bf43-2fc253026ff5';

-- This is an alternate path into the first chain; needs to be updated
-- to point at the new first chainlink.
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@setResumeLink1 WHERE microServiceChainLink='cddde867-4cf9-4248-ac31-f7052fae053f';

-- This path is followed if normalization is not performed
SET @setResumeLink2 = 'f060d17f-2376-4c0b-a346-b486446e46ce' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='77a7fa46-92b9-418e-aa88-fbedd4114c9f' WHERE microServiceChainLink=@setResumeLink2;
UPDATE TasksConfigsSetUnitVariable SET microServiceChainLink=@setResumeLink2 WHERE pk='fc9f30bf-7f6e-4e62-9f99-689c8dc2e4ec';

-- There are a couple of extra entrances to this second chain; make sure they
-- point at the new entrance so they set the resume link, then converge
-- with the rest of the chain.
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@setResumeLink2 WHERE microServiceChainLink='65916156-41a5-4ed2-9472-7dca11e6bc08';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@setResumeLink2 WHERE microServiceChainLink='14a0678f-9c2a-4995-a6bd-5acd141eeef1';
-- The previous two have a defaultNextChainLink into a failure management link,
-- but this one doesn't, so we have to update that too.
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@setResumeLink2 WHERE pk='0a6558cf-cf5f-4646-977e-7d6b4fde47e8';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@setResumeLink2 WHERE microServiceChainLink='0a6558cf-cf5f-4646-977e-7d6b4fde47e8';

-- Delete the old chain
-- MSCLs
SET @d0  = '055de204-6229-4200-87f7-e3c29f095017' COLLATE utf8_unicode_ci;
SET @d1  = 'befaf1ef-a595-4a32-b083-56eac51082b0' COLLATE utf8_unicode_ci;
SET @d2  = '9619706c-385a-472c-8144-fd5885c21532' COLLATE utf8_unicode_ci;
SET @d3  = '4ac461f9-ee69-4e03-924f-60ac0e8a4b7f' COLLATE utf8_unicode_ci;
SET @d4  = '0ba9bbd9-6c21-4127-b971-12dbc43c8119' COLLATE utf8_unicode_ci;
SET @d5  = 'e888269d-460a-4cdf-9bc7-241c92734402' COLLATE utf8_unicode_ci;
SET @d6  = 'faaea8eb-5872-4428-b609-9dd870cf5ceb' COLLATE utf8_unicode_ci;
SET @d7  = '4ef35d72-9494-431a-8cdb-8527b42664c7' COLLATE utf8_unicode_ci;
SET @d8  = '76d87f57-9718-4f68-82e6-91174674c49c' COLLATE utf8_unicode_ci;
SET @d9  = 'a536965b-e501-42aa-95eb-0656775be6f2' COLLATE utf8_unicode_ci;
SET @d10 = '88affaa2-13c5-4efb-a860-b182bd46c2c6' COLLATE utf8_unicode_ci;

DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@d0, @d1, @d2, @d3, @d4, @d6, @d7, @d8, @d9, @d10);
DELETE FROM MicroServiceChainLinksExitCodes WHERE nextMicroServiceChainLink in (@d0, @d1, @d2, @d3, @d4, @d6, @d7, @d8, @d9, @d10);
DELETE FROM MicroServiceChainLinks WHERE defaultNextChainLink in (@d0, @d1, @d2, @d3, @d4, @d6, @d7, @d8, @d9, @d10);
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d0, @d1, @d2, @d3, @d4, @d6, @d7, @d8, @d9, @d10);
-- /Issue 5866

-- Issue 5880
-- Insert the new "Examine contents" step immediately following characterization.
-- This runs bulk_extractor currently, but may be expanded into running other tools in the future.
SET @examineContentsMSCL = '100a75f4-9d2a-41bf-8dd0-aec811ae1077' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('3a17cc3f-eabc-4b58-90e8-1df2a96cf182', 0, 'examineContents_v0.0', '"%relativeLocation%" "%SIPDirectory%" "%fileUUID%"', 'objects');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('869c4c44-6e7d-4473-934d-80c7b95a8310', 'a6b1c323-7d36-428e-846a-e7e819423577', '3a17cc3f-eabc-4b58-90e8-1df2a96cf182', 'Examine contents');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values (@examineContentsMSCL, 'Examine contents', 'Failed', '869c4c44-6e7d-4473-934d-80c7b95a8310', '1b1a4565-b501-407b-b40f-2f20889423f1');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('87dcd08a-7688-425a-ae5f-2f623feb078a', @examineContentsMSCL, 0, '1b1a4565-b501-407b-b40f-2f20889423f1', 'Completed successfully');
-- Characterize and extract (normal)
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@examineContentsMSCL WHERE microServiceChainLink='303a65f6-a16f-4a06-807b-cb3425a30201';
-- Characterize and extract (maildir)
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@examineContentsMSCL WHERE microServiceChainLink='bd382151-afd0-41bf-bb7a-b39aef728a32';

-- Insert a "Examine contents?" choice
SET @examineContentsChoice = 'accea2bf-ba74-4a3a-bb97-614775c74459' COLLATE utf8_unicode_ci;
SET @examineContentsType = '7569eff6-401f-11e3-ae52-1c6f65d9668b' COLLATE utf8_unicode_ci;
-- First we create new chains - one for examination, one that picks back up immediately following examination
SET @examineChoiceChain = '96b49116-b114-47e8-95d0-b3c6ae4e80f5' COLLATE utf8_unicode_ci;
SET @examineChain = '06f03bb3-121d-4c85-bec7-abbc5320a409' COLLATE utf8_unicode_ci;
SET @postExamineChain = 'e0a39199-c62a-4a2f-98de-e9d1116460a8' COLLATE utf8_unicode_ci;
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@examineChain, @examineContentsMSCL, 'Examine contents');
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@postExamineChain, '1b1a4565-b501-407b-b40f-2f20889423f1', 'Skip examine contents');

-- Next we make sure we move it into a new watched directory before executing the choice
SET @examineContentsWatchDirectorySTC = 'f62e7309-61b3-4318-a770-ab40595bc7b8' COLLATE utf8_unicode_ci;
SET @examineContentsWatchDirectoryTC = '08fc82e7-bc15-4608-8171-50475e8071e2' COLLATE utf8_unicode_ci;
SET @examineContentsWatchDirectoryMSCL = 'dae3c416-a8c2-4515-9081-6dbd7b265388' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES (@examineContentsWatchDirectorySTC, 0, 'moveTransfer_v0.0', '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/examineContentsChoice/."  "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@examineContentsWatchDirectoryTC, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @examineContentsWatchDirectorySTC, 'Move to examine contents');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@examineContentsWatchDirectoryMSCL, 'Examine contents', 'Failed', @examineContentsWatchDirectoryTC, @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('72559113-a0a6-4ba8-8b17-c855389e5f16', @examineContentsWatchDirectoryMSCL, 0, NULL, 'Completed successfully');

-- Next create the choice itself and point the chains there
INSERT INTO TasksConfigs (pk, taskType, description) VALUES (@examineContentsType, '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', 'Examine contents?');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask) VALUES (@examineContentsChoice, 'Examine contents', 'Failed', @examineContentsType);

-- New watched directory entry, pointing at this chainlink
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@examineChoiceChain, @examineContentsChoice, 'Examine contents?');
INSERT INTO WatchedDirectories(pk, watchedDirectoryPath, chain, expectedType) VALUES ('da0ce3b8-07c4-4a89-8313-15df5884ac48', "%watchDirectoryPath%workFlowDecisions/examineContentsChoice/", @examineChoiceChain, 'f9a3a93b-f184-4048-8072-115ffac06b5d');

-- Insert the two choices - examine, or don't examine
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable) VALUES ('913ee4f7-35f4-44a0-9249-eb1cfc270d4e', @examineContentsChoice, @examineChain);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable) VALUES ('64e33508-c51d-4d96-9523-1a0c3b0809b1', @examineContentsChoice, @postExamineChain);
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@examineContentsWatchDirectoryMSCL WHERE nextMicroServiceChainLink=@examineContentsMSCL;

-- Ensure the default link for "Characterize and extract metadata" goes to a sensible place
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@examineContentsWatchDirectoryMSCL WHERE pk=@characterizeExtractMetadata;

-- /Issue 5880

-- Issue 6217
-- Serialize JSON metadata to disk, so it can be pulled back into the DB later
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('ed6daadf-a594-4327-b85c-7219c5832369', 0, 'saveDublinCore_v0.0', '"%SIPUUID%" "%relativeLocation%metadata/dc.json"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('e5789749-00df-4b6c-af12-47eeabc8926a', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', 'ed6daadf-a594-4327-b85c-7219c5832369', 'Serialize Dublin Core metadata to disk');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('f378ec85-adcc-4ee6-ada2-bc90cfe20efb', 'Create SIP from Transfer', 'Failed', 'e5789749-00df-4b6c-af12-47eeabc8926a', '39a128e3-c35d-40b7-9363-87f75091e1ff');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('12fb389b-06c4-43d4-b647-9727c410088f', 'f378ec85-adcc-4ee6-ada2-bc90cfe20efb', 0, '39a128e3-c35d-40b7-9363-87f75091e1ff', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='f378ec85-adcc-4ee6-ada2-bc90cfe20efb' WHERE microServiceChainLink='8f639582-8881-4a8b-8574-d2f86dc4db3d';

-- Load Dublin Core metadata back from disk into the database
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('cc8a1a4f-ccc8-4639-947e-01d0a5fddbb7', 0, 'loadDublinCore_v0.0', '"%SIPUUID%" "%relativeLocation%metadata/dc.json"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('efb7bf8e-4624-4b52-bf90-e3d389099fd9', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', 'cc8a1a4f-ccc8-4639-947e-01d0a5fddbb7', 'Load Dublin Core metadata from disk');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('970b7d17-7a6b-4d51-808b-c94b78c0d97f', 'Clean up names', 'Failed', 'efb7bf8e-4624-4b52-bf90-e3d389099fd9', '7d728c39-395f-4892-8193-92f086c0546f');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('5ffe0c72-5a98-4fa5-8281-a266471ffb2c', '970b7d17-7a6b-4d51-808b-c94b78c0d97f', 0, '15a2df8a-7b45-4c11-b6fa-884c9b7e5c67', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='970b7d17-7a6b-4d51-808b-c94b78c0d97f' WHERE microServiceChainLink='a46e95fe-4a11-4d3c-9b76-c5d8ea0b094d';
-- /Issue 6217

-- Issue 6131 add restructure for compliance to SIP creation
-- Insert restructureForComplianceSIP after Verify SIP compliance if it fails
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('285a7b4d-155b-4f5b-ab35-daa6414303f9', 0, 'restructureForComplianceSIP_v0.0', '"%SIPDirectory%" "%SIPUUID%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('8e06349b-d4a3-420a-9a64-69553bd9a183', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '285a7b4d-155b-4f5b-ab35-daa6414303f9', 'Attempt restructure for compliance');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('7d0616b2-afed-41a6-819a-495032e86291', 'Verify SIP compliance', 'Failed', '8e06349b-d4a3-420a-9a64-69553bd9a183', 'f025f58c-d48c-4ba1-8904-a56d2a67b42f');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('18080f7f-e6aa-4448-bc6c-c928ff2629cb', '7d0616b2-afed-41a6-819a-495032e86291', 0, 'd1018160-aaab-4d92-adce-d518880d7c7d', 'Completed successfully');
UPDATE MicroServiceChainLinks SET defaultNextChainLink='7d0616b2-afed-41a6-819a-495032e86291', defaultExitMessage='Completed successfully' WHERE pk='208d441b-6938-44f9-b54a-bd73f05bc764';

-- Update move to backlog to talk to the storage service
UPDATE StandardTasksConfigs SET execute='moveToBacklog_v1.0', arguments='"%SIPUUID%" "%SIPDirectory%"' WHERE pk='9f25a366-f7a4-4b59-b219-2d5f259a1be9';

-- Add failedSIPCleanup to Failed and Rejected SIP paths
-- Add Failed
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('bad1aea1-404c-4a0a-8f0a-83f09bf99fd5', 0, 'failedSIPCleanup_v1.0', '"fail" "%SIPUUID%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('7d5cb258-1ce2-4510-bd04-3517abbe8fbc', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', 'bad1aea1-404c-4a0a-8f0a-83f09bf99fd5', 'Cleanup failed SIP');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('b2ef06b9-bca4-49da-bc5c-866d7b3c4bb1', 'Failed SIP', 'Failed', '7d5cb258-1ce2-4510-bd04-3517abbe8fbc', '828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('6a4ef1c6-d54d-46d6-af8e-8a8851fa744e', 'b2ef06b9-bca4-49da-bc5c-866d7b3c4bb1', 0, '828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='b2ef06b9-bca4-49da-bc5c-866d7b3c4bb1' WHERE microServiceChainLink='7d728c39-395f-4892-8193-92f086c0546f';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='b2ef06b9-bca4-49da-bc5c-866d7b3c4bb1' WHERE pk='7d728c39-395f-4892-8193-92f086c0546f';

-- Add Rejected STC, TC
SET @rejectCleanupTC = '2d8f4aa1-76ad-4c88-af81-f7f494780628';
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('44758789-e1b5-4cfe-8011-442612da2d3b', 0, 'failedSIPCleanup_v1.0', '"reject" "%SIPUUID%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@rejectCleanupTC, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '44758789-e1b5-4cfe-8011-442612da2d3b', 'Cleanup rejected SIP');

-- Add Rejected for normalize/approve normalize
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('19c94543-14cb-4158-986b-1d2b55723cd8', 'Reject SIP', 'Failed', @rejectCleanupTC, '3467d003-1603-49e3-b085-e58aa693afed');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('a0bb8527-e58f-4043-a7c4-c4fc5e34d786', '19c94543-14cb-4158-986b-1d2b55723cd8', 0, '3467d003-1603-49e3-b085-e58aa693afed', 'Completed successfully');
UPDATE MicroServiceChains SET startingLink='19c94543-14cb-4158-986b-1d2b55723cd8' WHERE startingLink='3467d003-1603-49e3-b085-e58aa693afed';

-- Add Rejected for store AIP
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('f2e784a0-356b-4b92-9a5a-11887aa3cf48', 'Reject AIP', 'Failed', @rejectCleanupTC, '0d7f5dc2-b9af-43bf-b698-10fdcc5b014d');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('0f4bcf43-0aaf-4901-a860-bd68a5567709', 'f2e784a0-356b-4b92-9a5a-11887aa3cf48', 0, '0d7f5dc2-b9af-43bf-b698-10fdcc5b014d', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='f2e784a0-356b-4b92-9a5a-11887aa3cf48' WHERE microServiceChainLink='bfade79c-ab7b-11e2-bace-08002742f837';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='f2e784a0-356b-4b92-9a5a-11887aa3cf48' WHERE pk='bfade79c-ab7b-11e2-bace-08002742f837';


-- /Issue 6131

-- Issue 6589 - Uncompressed AIPs
--
-- Inserts a new compression choice associated with the compression
-- choice selection MSCL
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ('dc04c4c0-07ea-4796-b643-66d967ed33a4', '01d64f58-8295-4b7b-9cab-8f1b153a504f', 'Uncompressed', '{"%AIPCompressionAlgorithm%":"None-"}');

-- Inserts a check right before clearing out bagged files, which branches to
-- one of two alternate versions of the microservice.
-- If an AIP is uncompressed (read: a directory), then we don't want to delete
-- the uncompressed bag as that *is* the AIP. The original MSCL did this
-- unconditionally.
--
-- First, the new version of the microservice chain link;
-- this is exactly the same as the old one, minus deleting the uncompressed AIP.
SET @removeAllButAIPDirectoryMSCL = '63f35161-ba76-4a43-8cfa-c38c6a2d5b2f' COLLATE utf8_unicode_ci;
SET @removeAllButAIPDirectoryTC = '83755035-1dfd-4e25-9031-e1178be4bb84' COLLATE utf8_unicode_ci;
SET @removeAllButAIPDirectorySTC = 'd17b25c7-f83c-4862-904b-8074150b1395' COLLATE utf8_unicode_ci;

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES (@removeAllButAIPDirectorySTC, 0, 'remove_v0.0', '-R "%SIPDirectory%METS.%SIPUUID%.xml" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@removeAllButAIPDirectoryTC, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @removeAllButAIPDirectorySTC, 'Remove bagged files');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@removeAllButAIPDirectoryMSCL, 'Prepare AIP', 'Failed', @removeAllButAIPDirectoryTC, '7d728c39-395f-4892-8193-92f086c0546f');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('7aad879a-ffc4-4276-8e6e-eeb89a5bc0fa', @removeAllButAIPDirectoryMSCL, 0, '7c44c454-e3cc-43d4-abe0-885f93d693c6', 'Completed successfully');

-- Next insert the new check
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('8c96ba0c-44e5-4ff8-8c73-0c567d52e2d4', 0, 'test_v0.0', '-d "%SIPDirectory%%AIPFilename%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('ee00a5c7-a69c-46cf-a5e0-a9e2f18e563e', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '8c96ba0c-44e5-4ff8-8c73-0c567d52e2d4', 'Check if AIP is a file or directory');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('91dc1ab1-487e-4121-a6c5-d8441da7a422', 'Prepare AIP', 'Failed', 'ee00a5c7-a69c-46cf-a5e0-a9e2f18e563e', '7d728c39-395f-4892-8193-92f086c0546f');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='91dc1ab1-487e-4121-a6c5-d8441da7a422' WHERE microServiceChainLink='5fbc344c-19c8-48be-a753-02dac987428c';

-- The exit code of this test (0 if a directory, 1 otherwise) is used to branch to two
-- different versions of the deletion task, which then progress to the same followup
-- link.
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('4f85bfa3-1e4a-4698-8b02-5eb1bd434c5d', '91dc1ab1-487e-4121-a6c5-d8441da7a422', 0, @removeAllButAIPDirectoryMSCL, 'Completed successfully');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('b992b4c5-97da-4a0b-a434-a114cfa39329', '91dc1ab1-487e-4121-a6c5-d8441da7a422', 1, '746b1f47-2dad-427b-8915-8b0cb7acccd8', 'Completed successfully');
-- /Issue 6589

-- Issue 6565 OCR
-- Inserts a new "transcribe file" microservice.
-- This is a new microservice that runs FPR commands to create transcription
-- derivatives of content. The initial command provided by Archivematica will
-- run OCR on images.
--
-- Insert choice of whether or not to transcribe
SET @transcribeChoiceMSCL = '7079be6d-3a25-41e6-a481-cee5f352fe6e' COLLATE utf8_unicode_ci;
SET @transcribeChoiceTC = '4c64875e-9f31-4596-96d9-f99bc886bb24' COLLATE utf8_unicode_ci;
SET @preTranscribeMSCL = '77a7fa46-92b9-418e-aa88-fbedd4114c9f' COLLATE utf8_unicode_ci;
SET @postTranscribeMSCL = 'f574b2a0-6e0b-4c74-ac5b-a73ddb9593a0' COLLATE utf8_unicode_ci;

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@transcribeChoiceTC, '9c84b047-9a6d-463f-9836-eafa49743b84', NULL, 'Transcribe SIP contents');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@transcribeChoiceMSCL, 'Transcribe SIP contents', 'Failed', @transcribeChoiceTC, @transcribeFileMSCL);
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@transcribeChoiceMSCL WHERE pk=@preTranscribeMSCL;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@transcribeChoiceMSCL WHERE microServiceChainLink=@preTranscribeMSCL;

SET @transcribeYes = '5a9985d3-ce7e-4710-85c1-f74696770fa9' COLLATE utf8_unicode_ci;
SET @transcribeNo = '1170e555-cd4e-4b2f-a3d6-bfb09e8fcc53' COLLATE utf8_unicode_ci;
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES (@transcribeYes, @transcribeChoiceMSCL, 'Yes', '{"%transcribe%": "True"}');
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES (@transcribeNo, @transcribeChoiceMSCL, 'No', '{"%transcribe%": "False"}');

SET @transcribeFileMSCL = '2900f6d8-b64c-4f2a-8f7f-bb60a57394f6' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('657bdd72-8f18-4477-8018-1f6c8df7ad85', 0, 'transcribeFile_v0.0', '"%taskUUID%" "%fileUUID%" "%transcribe%"', 'objects');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('297e7ebd-71bb-41e9-b1b7-945b6a9f00c5', 'a6b1c323-7d36-428e-846a-e7e819423577', '657bdd72-8f18-4477-8018-1f6c8df7ad85', 'Transcribe');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values (@transcribeFileMSCL, 'Transcribe SIP contents', 'Failed', '297e7ebd-71bb-41e9-b1b7-945b6a9f00c5', @postTranscribeMSCL);

INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('22ebafb1-3ec3-406a-939d-4eb9f3b8bbd1', @transcribeChoiceMSCL, 0, @transcribeFileMSCL, 'Completed successfully');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('804d4d23-e81b-4d81-8e67-1a3b5470c841', @transcribeFileMSCL, 0, @postTranscribeMSCL, 'Completed successfully');

-- Copy OCR data into DIP
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('5c4f877f-b352-4977-b51b-53ebc437b08c', 0, 'copyRecursive_v0.0', '"%SIPObjectsDirectory%metadata/OCRfiles" "%SIPDirectory%DIP"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('102cd6b0-5d30-4e04-9b62-4e9f12d74549', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '5c4f877f-b352-4977-b51b-53ebc437b08c', 'Copy OCR data to DIP directory');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('43c72f8b-3cea-4b4c-b99d-cfdefdfcc270', 'Prepare DIP', 'Failed', '102cd6b0-5d30-4e04-9b62-4e9f12d74549', '7d728c39-395f-4892-8193-92f086c0546f');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('95ba6779-2ed2-47ea-a7ad-df4a4cf3764d', '43c72f8b-3cea-4b4c-b99d-cfdefdfcc270', 0, '6ee25a55-7c08-4c9a-a114-c200a37146c4', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='43c72f8b-3cea-4b4c-b99d-cfdefdfcc270' WHERE microServiceChainLink='ad011cc2-b0eb-4f51-96bb-400149a2ea11';

-- "Assign file UUIDs to metadata" - disable updating the fileGrpUse to avoid
-- clobbering the fileGrpUse set by the Transcribe microservice
UPDATE StandardTasksConfigs
	SET arguments='--sipUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%" --use "metadata" --disable-update-filegrpuse'
	WHERE pk='34966164-9800-4ae1-91eb-0a0c608d72d5';
-- /Issue 6565 OCR

-- Issue 6566 Tree
--
-- First, some surgery: unify several of the "scan for virus" nodes, so that
-- the directory tree microservice is guaranteed to run.
SET @scanForViruses = '1c2550f1-3fc0-45d8-8bc4-4c06d720283b' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@scanForViruses WHERE pk='38c591d4-b7ee-4bc0-b993-c592bf15d97d';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@scanForViruses WHERE microServiceChainLink='38c591d4-b7ee-4bc0-b993-c592bf15d97d';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@scanForViruses WHERE microServiceChainLink='d7e6404a-a186-4806-a130-7e6d27179a15';

SET @treeChoiceChain = 'f6df8882-d076-441e-bb00-2f58d5eda098' COLLATE utf8_unicode_ci;
SET @treeChain = 'df54fec1-dae1-4ea6-8d17-a839ee7ac4a7' COLLATE utf8_unicode_ci;
SET @noTreeChain = 'e9eaef1e-c2e0-4e3b-b942-bfb537162795' COLLATE utf8_unicode_ci;
set @treeMSCL = '4efe00da-6ed0-45dd-89ca-421b78c4b6be' COLLATE utf8_unicode_ci;

SET @preTreeChoiceMSCL = '1c2550f1-3fc0-45d8-8bc4-4c06d720283b' COLLATE utf8_unicode_ci;
set @postTreeMSCL = '2584b25c-8d98-44b7-beca-2b3ea2ea2505' COLLATE utf8_unicode_ci;

SET @treeChoiceWatchMSCL = '559d9b14-05bf-4136-918a-de74a821b759' COLLATE utf8_unicode_ci;
SET @treeChoiceWatchTC = '48416179-7ae4-47cc-a0aa-f9847da08c63' COLLATE utf8_unicode_ci;
SET @treeChoiceWatchSTC = '760a9654-de3e-4ea7-bb76-eeff06acdf95' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES (@treeChoiceWatchSTC, 0, 'moveTransfer_v0.0', '"%SIPDirectory%" "%sharedPath%watchedDirectories/workFlowDecisions/createTree/." "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@treeChoiceWatchTC, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @treechoiceWatchSTC, 'Move to generate transfer tree');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@treeChoiceWatchMSCL, 'Generate transfer structure report', 'Failed', @treeChoiceWatchTC, @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('d312ae33-3555-472e-803c-ef8076cb789b', @treeChoiceWatchMSCL, 0, NULL, 'Completed successfully');

SET @treeChoiceMSCL = '56eebd45-5600-4768-a8c2-ec0114555a3d' COLLATE utf8_unicode_ci;
SET @treeChoiceTC = 'f1ebd62a-fbf3-4790-88e8-4a3abec4ba00' COLLATE utf8_unicode_ci;
INSERT INTO TasksConfigs (pk, taskType, description) VALUES (@treeChoiceTC, '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', 'Generate transfer structure report');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, defaultExitMessage, currentTask) VALUES (@treeChoiceMSCL, 'Generate transfer structure report', 'Failed', @treeChoiceTC);

INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@treeChoiceChain, @treeChoiceMSCL, 'Generate transfer structure report');
INSERT INTO WatchedDirectories(pk, watchedDirectoryPath, chain, expectedType) VALUES ('e237217e-7b07-48f0-8129-36da0abfc97f', '%watchDirectoryPath%workFlowDecisions/createTree/', @treeChoiceChain, @watchedDirExpectTransfer);

UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@treeChoiceWatchMSCL WHERE microServiceChainLink=@preTreeChoiceMSCL;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@treeChoiceWatchMSCL WHERE pk=@preTreeChoiceMSCL;

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('f1a272df-bb3f-463e-95c0-6d2062bddfb8', 0, 'createDirectoryTree_v0.0', '"%SIPObjectsDirectory%" -o "%SIPDirectory%metadata/directory_tree.txt"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('ede67763-2a12-4e8f-8c36-e266d3f05c6b', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', 'f1a272df-bb3f-463e-95c0-6d2062bddfb8', 'Save directory tree');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values (@treeMSCL, 'Generate transfer structure report', 'Failed', 'ede67763-2a12-4e8f-8c36-e266d3f05c6b', @postTreeMSCL);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('882486b7-034e-49b8-bc65-2f6d8946bdcd', @treeMSCL, 0, @postTreeMSCL, 'Completed successfully');

INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@treeChain, @treeMSCL, 'Yes');
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@noTreeChain, @postTreeMSCL, 'No');
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable) VALUES ('171c7418-53c1-4d00-bcac-f77012050d1b', @treeChoiceMSCL, @treeChain);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable) VALUES ('63f0e429-1435-48e2-8eb0-dcb68e507168', @treeChoiceMSCL, @noTreeChain);
-- /Issue 6566 Tree

-- Issue 5356 Transfer metadata
ALTER TABLE Transfers
	ADD COLUMN transferMetadataSetRowUUID VARCHAR(36),
	ADD CONSTRAINT FOREIGN KEY (transferMetadataSetRowUUID) REFERENCES TransferMetadataSets (pk) ON DELETE CASCADE;

INSERT INTO Taxonomies (pk, name) VALUES ('312fc2b3-d786-458d-a762-57add7f96c22', 'Disk media formats');
INSERT INTO Taxonomies (pk, name) VALUES ('f6980e68-bac2-46db-842b-da4eba4ba418', 'Disk media densities');
INSERT INTO Taxonomies (pk, name) VALUES ('31e0bdc9-1114-4427-9f37-ca284577dcac', 'Filesystem types');
INSERT INTO Taxonomies (pk, name) VALUES ('fbf318db-4908-4971-8273-1094d2ba29a6', 'Disk imaging interfaces');
INSERT INTO Taxonomies (pk, name) VALUES ('cc4231ef-9886-4722-82ec-917e60d3b2c7', 'Disk image format');
INSERT INTO Taxonomies (pk, name) VALUES ('cae76c7f-4d8e-48ee-9522-4b3fbf492516', 'Disk imaging software');

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('fc69452c-ca57-448d-a46b-873afdd55e15', UNIX_TIMESTAMP(), 'Media number', 'media_number', 'text', 0);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('a9a4efa8-d8ab-4b32-8875-b10da835621c', UNIX_TIMESTAMP(), 'Label text', 'label_text', 'textarea', 1);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('367ef53b-49d6-4a4e-8b2f-10267d6a7db1', UNIX_TIMESTAMP(), 'Media manufacture', 'media_manufacture', 'text', 2);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('277727e4-b621-4f68-acb4-5689f81f31cd', UNIX_TIMESTAMP(), 'Serial number', 'serial_number', 'text', 3);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('13f97ff6-b312-4ab6-aea1-8438a55ae581', UNIX_TIMESTAMP(), 'Media format', 'media_format', 'select', '312fc2b3-d786-458d-a762-57add7f96c22', 4);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('a0d80573-e6ef-412e-a7a7-69bdfe3f6f8f', UNIX_TIMESTAMP(), 'Media density', 'media_density', 'select', 'f6980e68-bac2-46db-842b-da4eba4ba418', 5);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('c9344f6f-f881-4d2e-9ffa-26b7f5e42a11', UNIX_TIMESTAMP(), 'Source filesystem', 'source_filesystem', 'select', '31e0bdc9-1114-4427-9f37-ca284577dcac', 6);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('7ab79b42-1c84-420e-9169-e6bdf20141df', UNIX_TIMESTAMP(), 'Imaging process notes', 'imaging_process_notes', 'textarea', 7);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('af677693-524d-42af-be6c-d0f6a8976db1', UNIX_TIMESTAMP(), 'Imaging interface', 'imaging_interface', 'select', 'fbf318db-4908-4971-8273-1094d2ba29a6', 8);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('2c1844af-1217-4fdb-afbe-a052a91b7265', UNIX_TIMESTAMP(), 'Examiner', 'examiner', 'text', 9);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('38df3f82-5695-46d3-b4e2-df68a872778a', UNIX_TIMESTAMP(), 'Imaging date', 'imaging_date', 'text', 10);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('32f0f054-96d1-42ed-add6-7aa053237b02', UNIX_TIMESTAMP(), 'Imaging success', 'imaging_success', 'text', 11);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('d3b5b380-8901-4e68-8c40-3d59578810f4', UNIX_TIMESTAMP(), 'Image format', 'image_format', 'select', 'cc4231ef-9886-4722-82ec-917e60d3b2c7', 12);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('0c1b4233-fbe7-463f-8346-be6542574b86', UNIX_TIMESTAMP(), 'Imaging software', 'imaging_software', 'select', 'cae76c7f-4d8e-48ee-9522-4b3fbf492516', 13);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('0a9e346a-f08c-4e0d-9753-d9733f7205e5', UNIX_TIMESTAMP(), 'Image fixity', 'image_fixity', 'textarea', 14);

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('867ab18d-e860-445f-a254-8fcdebfe95b6', '312fc2b3-d786-458d-a762-57add7f96c22', '3.5" floppy');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('c41922d6-e716-4822-a385-e2fb0009465b', '312fc2b3-d786-458d-a762-57add7f96c22', '5.25" floppy');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('e4edb250-d70a-4f63-8234-948b05b1163e', 'f6980e68-bac2-46db-842b-da4eba4ba418', 'Single density');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('82a367f5-8157-4ac4-a5eb-3b59aac78d16', 'f6980e68-bac2-46db-842b-da4eba4ba418', 'Double density');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('0d6d40b5-8bf8-431d-8dd2-23d6b0b17ca0', '31e0bdc9-1114-4427-9f37-ca284577dcac', 'FAT');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('db34d5e1-0c93-4faa-bb1c-c5f5ebae6764', '31e0bdc9-1114-4427-9f37-ca284577dcac', 'HFS');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('35097f1b-094a-40bc-ba0c-f1260b50042a', 'fbf318db-4908-4971-8273-1094d2ba29a6', 'Catweasel');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('53e7764a-f711-486d-a0aa-8ec10d1d8da5', 'fbf318db-4908-4971-8273-1094d2ba29a6', 'Firewire');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('6774c7ce-a760-4f29-a7a3-b948f3769f71', 'fbf318db-4908-4971-8273-1094d2ba29a6', 'USB');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('6e368167-ea3e-45cd-adf2-60513a7e1802', 'fbf318db-4908-4971-8273-1094d2ba29a6', 'IDE');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('fcefbea2-848c-4685-9032-18a87cbc7a04', 'cc4231ef-9886-4722-82ec-917e60d3b2c7', 'AFF3');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('a3a6e30d-810f-4300-8461-1b41a7b383f1', 'cc4231ef-9886-4722-82ec-917e60d3b2c7', 'AD1');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('38ad5611-f05a-45d4-ac20-541c89bf0167', 'cae76c7f-4d8e-48ee-9522-4b3fbf492516', 'FTK imager 3.1.0.1514');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('6836caa4-8a0f-465e-be1b-4d8c547a7bf4', 'cae76c7f-4d8e-48ee-9522-4b3fbf492516', 'Kryoflux');

-- Write the metadata to disk right before moving to SIP or transfer backlog
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('290c1989-4d8a-4b6e-80bd-9ff43439aeca', 0, 'createTransferMetadata_v0.0', '--sipUUID "%SIPUUID%" --xmlFile "%SIPDirectory%"metadata/transfer_metadata.xml');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('81304470-37ef-4abb-99d9-ca075a9f440e', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '290c1989-4d8a-4b6e-80bd-9ff43439aeca', 'Create transfer metadata XML');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask) values ('db99ab43-04d7-44ab-89ec-e09d7bbdc39d', 'Complete transfer', 'Failed', '81304470-37ef-4abb-99d9-ca075a9f440e');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('e7837301-3891-4d0f-8b86-6f0a95d5a30b', 'db99ab43-04d7-44ab-89ec-e09d7bbdc39d', 0, 'd27fd07e-d3ed-4767-96a5-44a2251c6d0a', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='db99ab43-04d7-44ab-89ec-e09d7bbdc39d' WHERE microServiceChainLink='eb52299b-9ae6-4a1f-831e-c7eee0de829f';
-- /Issue 5356 Transfer metadata

-- Issue 6539 Extract package chain naming
-- Rename "extract"/"do not extract" to "yes"/"no"
UPDATE MicroServiceChains SET description='Yes' WHERE pk='01d80b27-4ad1-4bd1-8f8d-f819f18bf685';
UPDATE MicroServiceChains SET description='No' WHERE pk='79f1f5af-7694-48a4-b645-e42790bbf870';
-- Rename "delete"/"do not delete" to "yes"/"no"
UPDATE MicroServiceChoiceReplacementDic SET description='Yes' WHERE pk='85b1e45d-8f98-4cae-8336-72f40e12cbef';
UPDATE MicroServiceChoiceReplacementDic SET description='No' WHERE pk='72e8443e-a8eb-49a8-ba5f-76d52f960bde';
-- /Issue 6539 Extract package chain naming

-- Issue 6350 Extract package prompt
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('93039c6d-5ef7-4a95-bf07-5f89c8886808', 0, 'hasPackages_v0.0', '%SIPUUID%');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('d9ce0690-a8f9-40dc-a8b5-b021f578f8ff', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '93039c6d-5ef7-4a95-bf07-5f89c8886808', 'Determine if transfer contains packages');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('b944ec7f-7f99-491f-986d-58914c9bb4fa', 'Extract packages', 'Failed', 'd9ce0690-a8f9-40dc-a8b5-b021f578f8ff', NULL);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('4ba2d89a-d741-4868-98a7-6202d0c57163', 'b944ec7f-7f99-491f-986d-58914c9bb4fa', 0, 'dec97e3c-5598-4b99-b26e-f87a435a6b7f', 'Completed successfully');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('2b3f01ca-7101-4801-96a9-ede85dba319c', 'b944ec7f-7f99-491f-986d-58914c9bb4fa', 1, '303a65f6-a16f-4a06-807b-cb3425a30201', 'Completed successfully');

UPDATE MicroServiceChains SET startingLink='b944ec7f-7f99-491f-986d-58914c9bb4fa' WHERE pk='c868840c-cf0b-49db-a684-af4248702954';
-- /Issue 6350 Extract package prompt

-- Issue #6347 extracted files not virus scanned
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('51bce222-4157-427c-aca9-a670083db223', 1, 'archivematicaClamscan_v0.0', '"%fileUUID%" "%relativeLocation%" "%date%" "%taskUUID%"', 'objects/');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('5370a0cb-da97-4983-868a-1376d7737af5', 'a6b1c323-7d36-428e-846a-e7e819423577', '51bce222-4157-427c-aca9-a670083db223', 'Scan for viruses on extracted files');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('7d33f228-0fa8-4f4c-a66b-24f8e264c214', 'Extract packages', 'Failed', '5370a0cb-da97-4983-868a-1376d7737af5', @MoveTransferToFailedLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('73028cdb-b35d-4490-a89c-d0fe35c68054', '7d33f228-0fa8-4f4c-a66b-24f8e264c214', 0, 'aaa929e4-5c35-447e-816a-033a66b9b90b', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='7d33f228-0fa8-4f4c-a66b-24f8e264c214' WHERE microServiceChainLink='bdce640d-6e94-49fe-9300-3192a7e5edac';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='7d33f228-0fa8-4f4c-a66b-24f8e264c214' WHERE pk='bdce640d-6e94-49fe-9300-3192a7e5edac';
-- Remove hanging unused scan for viruses
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink='f92dabe5-9dd5-495e-a996-f8eb9ef90f48';
DELETE FROM MicroServiceChainLinks WHERE pk='f92dabe5-9dd5-495e-a996-f8eb9ef90f48';
-- Fix microserviceGroup
UPDATE MicroServiceChainLinks SET microserviceGroup='Scan for viruses' WHERE pk='d7e6404a-a186-4806-a130-7e6d27179a15';
-- Update to fail if virus scan to fail transfer/SIP if MSCL fails
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@MoveTransferToFailedLink WHERE pk IN ('21d6d597-b876-4b3f-ab85-f97356f10507', '1c2550f1-3fc0-45d8-8bc4-4c06d720283b');
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@MoveSIPToFailedLink WHERE pk IN ('1ba589db-88d1-48cf-bb1a-a5f9d2b17378', '8bc92801-4308-4e3b-885b-1a89fdcd3014');
-- /Issue #6347 extracted files not virus scanned

-- Issue 7012 - Normalization ID failure
-- File ID pre-normalization was incorrectly set to jump to failure instead
-- of moving to the next link in normalization.
UPDATE MicroServiceChainLinks SET defaultNextChainLink='83484326-7be7-4f9f-b252-94553cd42370' WHERE pk='2dd53959-8106-457d-a385-fee57fc93aa9';
-- /Issue 7012 - Normalization ID failure

-- Issue 6965 - remove 'create sip manually'
SET @manualSIPMSC = '9634868c-b183-4d65-8587-2f53f7ff5a0a' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainChoice WHERE chainAvailable=@manualSIPMSC;
DELETE FROM MicroServiceChains WHERE pk=@manualSIPMSC;
-- /Issue 6965 - remove 'create sip manually'

-- Issue 6564 DIP storage
SET @dip_storage_chain = '2748bedb-12aa-4b10-a556-66e7205580a4' COLLATE utf8_unicode_ci;

-- Store DIP (uses the existing store AIP script)
SET @dip_storage_mscl = 'e85a01f1-4061-4049-8922-5694b25c23a2' COLLATE utf8_unicode_ci;
SET @dip_storage_stc = '1f6f0cd1-acaf-40fb-bb2a-047383b8c977' COLLATE utf8_unicode_ci;
SET @dip_storage_tc = '85ce72dd-627a-4d0d-b118-fdaedf8ed8e6' COLLATE utf8_unicode_ci;

-- Get DIP storage locations from the storage service
SET @dip_storage_location_mscl = 'ed5d8475-3793-4fb0-a8df-94bd79b26a4c' COLLATE utf8_unicode_ci;
SET @dip_storage_locations_stc = '5a6d1a88-1c2f-40b5-adec-ad7e533340ff' COLLATE utf8_unicode_ci;
SET @dip_storage_locations_tc = '21292501-0c12-4376-8fb1-413286060dc2' COLLATE utf8_unicode_ci;

-- Let user select DIP storage location
SET @dip_storage_choose_location_mscl = 'b7a83da6-ed5a-47f7-a643-1e9f9f46e364' COLLATE utf8_unicode_ci;
SET @dip_storage_choose_location_stc = '1fa7994d-9106-4d5a-892c-539af7e4ad8d' COLLATE utf8_unicode_ci;
SET @dip_storage_choose_location_tc = '55123c46-78c9-4b5d-ad92-2b1f3eb658af' COLLATE utf8_unicode_ci;

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES (@dip_storage_locations_stc, 1, 'getAipStorageLocations_v0.0', 'DS');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@dip_storage_locations_tc, 'a19bfd9f-9989-4648-9351-013a10b382ed', @dip_storage_locations_stc, 'Retrieve DIP Storage Locations');
INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, defaultExitMessage, microserviceGroup) VALUES (@dip_storage_location_mscl, @dip_storage_locations_tc, @MoveSIPToFailedLink, 'Failed', 'Upload DIP');

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute) VALUES (@dip_storage_choose_location_stc, 1, '%DIPsStore%');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@dip_storage_choose_location_tc, '01b748fe-2e9d-44e4-ae5d-113f74c9a0ba', @dip_storage_choose_location_stc, 'Store DIP location');
INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, defaultExitMessage, microserviceGroup) VALUES (@dip_storage_choose_location_mscl, @dip_storage_choose_location_tc, @MoveSIPToFailedLink, 'Failed', 'Upload DIP');

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES (@dip_storage_stc, 1, 'storeAIP_v0.0', '"%DIPsStore%" "%watchDirectoryPath%uploadDIP/%SIPName%-%SIPUUID%" "%SIPUUID%" "%SIPName%" "DIP"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@dip_storage_tc, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @dip_storage_stc, 'Store DIP');
INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, defaultExitMessage, microserviceGroup) VALUES (@dip_storage_mscl, @dip_storage_tc, @MoveSIPToFailedLink, 'Failed', 'Upload DIP');


INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('68d19ada-9c7a-47b3-bedc-66788d5e9e3e', @dip_storage_location_mscl, 0, @dip_storage_choose_location_mscl, 'Completed successfully');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('637afa7b-d970-4076-aa4e-d62dfc6bb0b6', @dip_storage_choose_location_mscl, 0, @dip_storage_mscl, 'Completed successfully');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('9a028152-f3a2-4b98-82e1-8f77c594d1de', @dip_storage_mscl, 0, 'e3efab02-1860-42dd-a46c-25601251b930', 'Completed successfully');

INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@dip_storage_chain, @dip_storage_location_mscl, 'Store DIP');
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable) VALUES ('cb15da43-5c1b-478a-b25c-2ef69eff1dbf', '92879a29-45bf-4f0b-ac43-e64474f0f2f9', @dip_storage_chain);
-- /Issue 6564

-- Issue 6788 - Add post store AIP hook
SET @postStoreMSCL = 'b7cf0d9a-504f-4f4e-9930-befa817d67ff' COLLATE utf8_unicode_ci;
SET @postStoreTC = 'f09c1aa1-8a5d-49d1-ba60-2866e026eed9' COLLATE utf8_unicode_ci;
SET @postStoreSTC = 'ab404b46-9c54-4ca5-87f1-b69a8d2299a1' COLLATE utf8_unicode_ci;
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES (@postStoreSTC, 0, 'postStoreAIPHook_v1.0', '"%SIPUUID%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@postStoreTC, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @postStoreSTC, 'Clean up after storing AIP');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@postStoreMSCL, 'Store AIP', 'Failed', @postStoreTC, 'd5a2ef60-a757-483c-a71a-ccbffe6b80da');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('c3c8e23c-1c8a-4c24-b8a1-3d6e8a8c3a7b', @postStoreMSCL, 0, 'd5a2ef60-a757-483c-a71a-ccbffe6b80da', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@postStoreMSCL WHERE microServiceChainLink='48703fad-dc44-4c8e-8f47-933df3ef6179';
-- /Issue 6788 - Add post store AIP hook
