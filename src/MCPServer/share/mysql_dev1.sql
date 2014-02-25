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
