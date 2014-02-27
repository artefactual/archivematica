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
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values (@examineContentsMSCL, 'Characterize and extract metadata', 'Failed', '869c4c44-6e7d-4473-934d-80c7b95a8310', '1b1a4565-b501-407b-b40f-2f20889423f1');
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
UPDATE MicroServiceChainLinks SET defaultNextChainLink='7d0616b2-afed-41a6-819a-495032e86291' WHERE pk='208d441b-6938-44f9-b54a-bd73f05bc764';


-- /Issue 6131

