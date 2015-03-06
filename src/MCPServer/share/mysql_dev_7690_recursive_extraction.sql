
-- Add check for extractable files after aaa9
SET @hasPackageSTC = '93039c6d-5ef7-4a95-bf07-5f89c8886808' COLLATE utf8_unicode_ci;
SET @newPackageMSCL = 'bd792750-a55b-42e9-903a-8c898bb77df1' COLLATE utf8_unicode_ci;
SET @continueMSCL = '307edcde-ad10-401c-92c4-652917c993ed' COLLATE utf8_unicode_ci;
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('cadd5e12-82b2-43ec-813e-85cd42b2d511', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @hasPackageSTC, 'Determine if transfer still contains packages');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@newPackageMSCL, 'Extract packages', 'Failed', 'cadd5e12-82b2-43ec-813e-85cd42b2d511', @continueMSCL);
-- If not continue
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('3ba57fba-c1c2-4898-a5ae-9052dc5dd018', @newPackageMSCL, 1, @continueMSCL, 'Completed successfully');
-- If yes, return to 1cb7 extract contents
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('f8597642-7254-43a7-8857-8ca053d0fba5', @newPackageMSCL, 0, '1cb7e228-6e94-4c93-bf70-430af99b9264', 'Completed successfully');

UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@newPackageMSCL WHERE microServiceChainLink='aaa929e4-5c35-447e-816a-033a66b9b90b';
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@newPackageMSCL WHERE pk='aaa929e4-5c35-447e-816a-033a66b9b90b';

UPDATE StandardTasksConfigs SET arguments='"%IDCommand%" "%relativeLocation%" "%fileUUID%" --disable-reidentify' WHERE pk='9c3680a5-91cb-413f-af4e-d39c3346f8db';
