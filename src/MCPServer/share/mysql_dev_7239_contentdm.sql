-- Move select upload type to after content DM selection
-- Do not query server if upload type is project client

-- Remove question from direct upload chain, hardcode direct upload
UPDATE MicroServiceChainLinks SET defaultNextChainLink='f12ece2c-fb7e-44de-ba87-7e3c5b6feb74' WHERE pk='9304d028-8387-4ab5-9539-0aab9ac5bdb1';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='f12ece2c-fb7e-44de-ba87-7e3c5b6feb74' WHERE microServiceChainLink='9304d028-8387-4ab5-9539-0aab9ac5bdb1';
UPDATE StandardTasksConfigs SET arguments='--uuid="%SIPName%-%SIPUUID%" --dipDir "%SIPDirectory%" --collection "%ContentdmCollection%" --server "%ContentdmServer%" --ingestFormat "directupload" --outputDir "%watchDirectoryPath%uploadedDIPs"' WHERE pk='f9f7793c-5a70-4ffd-9727-159c1070e4f5';

-- New MSCL with hardcoded projectclient
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('55aaecd2-5f02-4d7c-a3ce-2155e1bcf0a5', 0, 'restructureDIPForContentDMUpload_v0.0', '--uuid="%SIPName%-%SIPUUID%" --dipDir "%SIPDirectory%" --collection "%ContentdmCollection%" --server "%ContentdmServer%" --ingestFormat "projectclient" --outputDir "%watchDirectoryPath%uploadedDIPs"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('5fba7639-eb98-4680-95c8-48401acbc507', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '55aaecd2-5f02-4d7c-a3ce-2155e1bcf0a5', 'Restructure DIP for CONTENTdm upload');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('0b6c6591-e77c-413c-9e4c-febd4d812cd6', 'Upload DIP', 'Failed', '5fba7639-eb98-4680-95c8-48401acbc507', 'e3efab02-1860-42dd-a46c-25601251b930');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('dfdae930-77a1-4165-8b68-a998a0c4dd48', '0b6c6591-e77c-413c-9e4c-febd4d812cd6', 0, 'e3efab02-1860-42dd-a46c-25601251b930', 'Completed successfully');

-- New project client chain
SET @project_client_chain = '01889cd4-68fc-418d-9f3f-7f54b0bf7431' COLLATE utf8_unicode_ci;
SET @direct_upload_chain = '526eded3-2280-4f10-ac86-eff6c464cc81' COLLATE utf8_unicode_ci;
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@project_client_chain, '0b6c6591-e77c-413c-9e4c-febd4d812cd6', 'Project client');
UPDATE MicroServiceChains SET description='Direct upload' WHERE pk=@direct_upload_chain;

SET @upload_type_choice_mscl = '45f01e11-47c7-45a3-a99b-48677eb321a5' COLLATE utf8_unicode_ci;

-- New chain choices for direct upload & project client
INSERT INTO MicroServiceChainChoice(pk, choiceAvailableAtLink, chainAvailable) VALUES ('b9702e35-57ec-43c2-988c-aae1795eed73', @upload_type_choice_mscl, @project_client_chain);
INSERT INTO MicroServiceChainChoice(pk, choiceAvailableAtLink, chainAvailable) VALUES ('6001ab96-b9b3-41cc-9b58-12be0536588c', @upload_type_choice_mscl, @direct_upload_chain);

-- Convert replacement dict to chain choice
DELETE FROM MicroServiceChoiceReplacementDic WHERE choiceAvailableAtLink=@upload_type_choice_mscl;
UPDATE TasksConfigs SET taskType='61fb3874-8ef6-49d3-8a2d-3cb66e86a30c' WHERE pk IN (SELECT currentTask FROM MicroServiceChainLinks WHERE pk=@upload_type_choice_mscl);
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=NULL WHERE microServiceChainLink=@upload_type_choice_mscl;

-- New upload type question chain
SET @upload_type_choice_msc = '9514865d-7ed6-4184-b65f-a99d041e291d' COLLATE utf8_unicode_ci;
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@upload_type_choice_msc, @upload_type_choice_mscl, 'Upload DIP to CONTENTdm');
UPDATE MicroServiceChainChoice SET chainAvailable=@upload_type_choice_msc WHERE pk='1b408994-ac47-4166-8a9b-4ef4bde09474';

