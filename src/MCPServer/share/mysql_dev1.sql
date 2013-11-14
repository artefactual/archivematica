-- Common
SET @MoveTransferToFailedLink = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd';
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';

-- /Common

-- Issue 5955

-- Tasksconfigs for all preservation options
SET @normalizePresTC = '51e31d21-3e92-4c9f-8fec-740f559285f2' COLLATE utf8_unicode_ci;
SET @normalizeAccTC = '2d9483ef-7dbb-4e7e-a9c6-76ed4de52da9' COLLATE utf8_unicode_ci;
SET @normalizeThumTC = 'a8489361-b731-4d4a-861d-f4da1767665f' COLLATE utf8_unicode_ci;
SET @normalizeAccServTC = 'ddcd9c7d-6615-4524-bb5d-ae7c1b6acbbb' COLLATE utf8_unicode_ci;
SET @normalizeThumServTC = '21f8f2b6-d285-490a-9276-bfa87a0a4fb9' COLLATE utf8_unicode_ci;

-- Original, preservation
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('7478e34b-da4b-479b-ad2e-5a3d4473364f', 0, 'normalize_v1.0', 'preservation "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "original"', 'objects/');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@normalizePresTC, 'a6b1c323-7d36-428e-846a-e7e819423577', '7478e34b-da4b-479b-ad2e-5a3d4473364f', 'Normalize for preservation');
-- Original, access
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('3c256437-6435-4307-9757-fbac5c07541c', 0, 'normalize_v1.0', 'access "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "original"', 'objects/');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@normalizeAccTC, 'a6b1c323-7d36-428e-846a-e7e819423577', '3c256437-6435-4307-9757-fbac5c07541c', 'Normalize for access');
-- Original, Thumbnails
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('8fe4a2c3-d43c-41e4-aeb9-18e8f57c9ccf', 0, 'normalize_v1.0', 'thumbnail "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "original"', 'objects/');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@normalizeThumTC, 'a6b1c323-7d36-428e-846a-e7e819423577', '8fe4a2c3-d43c-41e4-aeb9-18e8f57c9ccf', 'Normalize for thumbnails');
-- Service, Access
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('6dccf7b3-4282-46f9-a805-1297c6ea482b', 0, 'normalize_v1.0', 'access "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "service"', 'objects/');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@normalizeAccServTC, 'a6b1c323-7d36-428e-846a-e7e819423577', '6dccf7b3-4282-46f9-a805-1297c6ea482b', 'Normalize for access');
-- Service, Thumbnails
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('26309e7d-6435-4700-9171-131005f29cbb', 0, 'normalize_v1.0', 'thumbnail "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "service"', 'objects/');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@normalizeThumServTC, 'a6b1c323-7d36-428e-846a-e7e819423577', '26309e7d-6435-4700-9171-131005f29cbb', 'Normalize for thumbnails');

-- Normalize Preservation & Access Chain
-- Add Preservation in P&A
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('440ef381-8fe8-4b6e-9198-270ee5653454', 'Normalize', 'Failed', @normalizePresTC, '39ac9205-cb08-47b1-8bc3-d3375e37d9eb');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('b5157984-6f63-4903-a582-ff1f104e6009', '440ef381-8fe8-4b6e-9198-270ee5653454', 0, '39ac9205-cb08-47b1-8bc3-d3375e37d9eb', 'Completed successfully');
-- Add Access in P&A
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0', 'Normalize', 'Failed', @normalizeAccTC, '440ef381-8fe8-4b6e-9198-270ee5653454');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('b87ee978-0f02-4852-af21-4511a43010e6', 'bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0', 0, '440ef381-8fe8-4b6e-9198-270ee5653454', 'Completed successfully');
-- Add Thumbnail in P&A
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('092b47db-6f77-4072-aed3-eb248ab69e9c', 'Normalize', 'Failed', @normalizeThumTC, 'bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('d4c81458-05b5-434d-a972-46ae43417213', '092b47db-6f77-4072-aed3-eb248ab69e9c', 0, 'bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='092b47db-6f77-4072-aed3-eb248ab69e9c' WHERE microServiceChainLink='4103a5b0-e473-4198-8ff7-aaa6fec34749';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='092b47db-6f77-4072-aed3-eb248ab69e9c' WHERE pk='4103a5b0-e473-4198-8ff7-aaa6fec34749';

-- Normalize Access chain
-- Add Thumbnail to Access
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('8ce130d4-3f7e-46ec-868a-505cf9033d96', 'Normalize', 'Failed', @normalizeThumTC, 'ef8bd3f3-22f5-4283-bfd6-d458a2d18f22');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('00c7c131-5849-4bd6-a245-3edae7448bff', '8ce130d4-3f7e-46ec-868a-505cf9033d96', 0, 'ef8bd3f3-22f5-4283-bfd6-d458a2d18f22', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='8ce130d4-3f7e-46ec-868a-505cf9033d96' WHERE microServiceChainLink='56da7758-913a-4cd2-a815-be140ed09357';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='8ce130d4-3f7e-46ec-868a-505cf9033d96' WHERE pk='56da7758-913a-4cd2-a815-be140ed09357';
-- Update Normalize Access to point to correct things
UPDATE MicroServiceChainLinks SET currentTask=@normalizeAccTC WHERE pk='ef8bd3f3-22f5-4283-bfd6-d458a2d18f22';

-- Do Not Normalize Chain - first
-- Update Normalize Thumbnails Service
UPDATE MicroServiceChainLinks SET currentTask=@normalizeThumServTC WHERE pk='f6fdd1a7-f0c5-4631-b5d3-19421155bd7a';

-- Normalize Thumbnails chain
-- Update to use normalize thumb service
UPDATE MicroServiceChainLinks SET currentTask=@normalizeThumServTC WHERE pk='09b85517-e5f5-415b-a950-1a60ee285242';

-- Normalize preservation chain - first
-- Add thumbnails
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21', 'Normalize', 'Failed', @normalizeThumTC, '8ce378a5-1418-4184-bf02-328a06e1d3be');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('e8c31963-29fe-4812-846e-3d18327db4b4', '180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21', 0, '8ce378a5-1418-4184-bf02-328a06e1d3be', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21' WHERE microServiceChainLink='35c8763a-0430-46be-8198-9ecb23f895c8';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21' WHERE pk='35c8763a-0430-46be-8198-9ecb23f895c8';
-- Update to use preserve original
UPDATE MicroServiceChainLinks SET currentTask=@normalizePresTC WHERE pk='8ce378a5-1418-4184-bf02-328a06e1d3be';

-- Normalize for preservation chain - another
-- Add thumbnails
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('8adb23cc-dee3-44da-8356-fa6ce849e4d6', 'Normalize', 'Failed', @normalizeThumTC, 'd77ccaa0-3a3d-46ff-877f-4edf1a8179e2');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('83c7602b-ad10-4b34-935f-d0fa225ce9b8', '8adb23cc-dee3-44da-8356-fa6ce849e4d6', 0, 'd77ccaa0-3a3d-46ff-877f-4edf1a8179e2', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='8adb23cc-dee3-44da-8356-fa6ce849e4d6' WHERE microServiceChainLink='c425258a-cf54-44f9-b39f-cf14c7966a41';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='8adb23cc-dee3-44da-8356-fa6ce849e4d6' WHERE pk='c425258a-cf54-44f9-b39f-cf14c7966a41';

-- Updated to use preserve original
UPDATE MicroServiceChainLinks SET currentTask=@normalizePresTC WHERE pk='d77ccaa0-3a3d-46ff-877f-4edf1a8179e2';

-- Not Normalize chain - another
UPDATE MicroServiceChainLinks SET currentTask = @normalizeThumServTC WHERE pk='0a6558cf-cf5f-4646-977e-7d6b4fde47e8';

-- Normalize manually chain?
-- Update thumbnails
UPDATE MicroServiceChainLinks SET currentTask = @normalizeThumServTC WHERE pk='26cf64e2-21b5-4935-a52b-71695870f1f2';

-- Normalize Service Files for Access Chain
-- Add Service Thumbnail normalization
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('62f21582-3925-47f6-b17e-90f46323b0d1', 0, 'normalize_v1.0', 'thumbnail "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "service"', 'objects/service');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('7fd4e564-bed2-42c7-a186-7ae615381516', 'a6b1c323-7d36-428e-846a-e7e819423577', '62f21582-3925-47f6-b17e-90f46323b0d1', 'Normalize service files for thumbnails');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('e950cd98-574b-4e57-9ef8-c2231e1ce451', 'Normalize', 'Failed', '7fd4e564-bed2-42c7-a186-7ae615381516', '5c0d8661-1c49-4023-8a67-4991365d70fb');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('fe27318c-9ee1-470f-a9ce-0f8103cc78a5', 'e950cd98-574b-4e57-9ef8-c2231e1ce451', 0, '5c0d8661-1c49-4023-8a67-4991365d70fb', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='e950cd98-574b-4e57-9ef8-c2231e1ce451' WHERE microServiceChainLink='f3a39155-d655-4336-8227-f8c88e4b7669';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='e950cd98-574b-4e57-9ef8-c2231e1ce451' WHERE pk='f3a39155-d655-4336-8227-f8c88e4b7669';
-- Updated to use Service Access Norm
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('339f300d-62d1-4a46-97c2-57244f54d32e', 0, 'normalize_v1.0', 'access "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "service"', 'objects/service');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('246c34b0-b785-485f-971b-0ed9f82e1ae3', 'a6b1c323-7d36-428e-846a-e7e819423577', '339f300d-62d1-4a46-97c2-57244f54d32e', 'Normalize service files for access');
UPDATE MicroServiceChainLinks SET currentTask='246c34b0-b785-485f-971b-0ed9f82e1ae3' WHERE pk='5c0d8661-1c49-4023-8a67-4991365d70fb';

-- Submission documentation
SET @normalizeThumSubDocTC = 'd3d0e81b-7cfd-4bf7-b8e3-976468c3d6fd' COLLATE utf8_unicode_ci;
SET @normalizePresSubDocTC = '66af78b5-f756-46aa-90af-6215088cf2e0' COLLATE utf8_unicode_ci;
-- Submission Documentation, preservation
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('c097d320-3422-4b72-8691-7ff1b67ca176', 0, 'normalize_v1.0', 'preservation "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "submissionDocumentation"', 'objects/submissionDocumentation');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@normalizePresSubDocTC, 'a6b1c323-7d36-428e-846a-e7e819423577', 'c097d320-3422-4b72-8691-7ff1b67ca176', 'Normalize submission documentation for preservation');
-- Submission Documentation, Thumbnails
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('57f2f1d2-7e02-40a3-a586-28e718074736', 0, 'normalize_v1.0', 'thumbnail "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "submissionDocumentation"', 'objects/submissionDocumentation');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@normalizeThumSubDocTC, 'a6b1c323-7d36-428e-846a-e7e819423577', '57f2f1d2-7e02-40a3-a586-28e718074736', 'Normalize submission documentation for thumbnails');

-- Update Submission Doc to point at new TC
UPDATE MicroServiceChainLinks SET currentTask=@normalizeThumSubDocTC WHERE pk IN ('634918c4-1f06-4f62-9ed2-a3383aa2e962', '8c425901-13c7-4ea2-8955-2abdbaa3d67a');
UPDATE MicroServiceChainLinks SET currentTask=@normalizePresSubDocTC WHERE pk IN ('a697cfaa-208b-4479-b737-d8008aa9e037', 'bf7cfca8-f8b9-45d7-bd6a-b6ab9fd381bc');

-- Add extra MicroServiceChainLinksExitCodes for exit code 1 and 2 as success
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink) 
    SELECT UUID(), microServiceChainLink, 1, nextMicroServiceChainLink 
    FROM MicroServiceChainLinksExitCodes
    WHERE exitCode = 0 AND microServiceChainLink IN (SELECT M.pk FROM MicroServiceChainLinks M JOIN TasksConfigs C ON currentTask = C.pk JOIN StandardTasksConfigs S ON taskTypePKReference = S.pk WHERE execute ='normalize_v1.0');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink) 
    SELECT UUID(), microServiceChainLink, 2, nextMicroServiceChainLink 
    FROM MicroServiceChainLinksExitCodes
    WHERE exitCode = 0 AND microServiceChainLink IN (SELECT M.pk FROM MicroServiceChainLinks M JOIN TasksConfigs C ON currentTask = C.pk JOIN StandardTasksConfigs S ON taskTypePKReference = S.pk WHERE execute ='normalize_v1.0');

-- Remove old normalization chains
-- This table will no longer be used
DROP TABLE TasksConfigsStartLinkForEachFile;
-- "Find access links to run"
SET @mscl1='bf11cf60-c7aa-478f-98a6-2dd9647aa35f' COLLATE utf8_unicode_ci;
SET @mscl2='eca5731c-d6a3-4e20-a83f-dde167dd7642' COLLATE utf8_unicode_ci;
-- "Find type to process as"
SET @mscl3='d02ac4b4-eb48-45ee-a1b4-ba1e9f0eff78' COLLATE utf8_unicode_ci;
-- "Find access links to run" chain that includes thumbnail/preservation
SET @mscl4='f7a8ff81-e00e-4583-857d-7d9a1fdc93f8' COLLATE utf8_unicode_ci;
SET @mscl5='760b0bcb-e001-49d1-9936-30cfe2ca0ea1' COLLATE utf8_unicode_ci;
SET @mscl6='eafd05a1-9aac-464e-83ce-a16d5429c7a1' COLLATE utf8_unicode_ci;
-- "Find thumbnail links to run"
SET @mscl7='28b9c4bc-1383-4992-9baf-c455dde1393d' COLLATE utf8_unicode_ci;
-- "Find preservation links to run"
SET @mscl8='6c4f4838-4573-4f08-8082-3aacf04f9dac' COLLATE utf8_unicode_ci;
SET @mscl9='c1fe87ad-25d4-4753-8dd5-b7b597616765' COLLATE utf8_unicode_ci;
-- "Find access links to run"
SET @mscl10='4fac5503-8fff-4c18-acf4-5b4d62654e0f' COLLATE utf8_unicode_ci;
-- "Find thumbnail links to run"
SET @mscl11='4081dc41-48df-4658-a286-0d02eca7d953' COLLATE utf8_unicode_ci;

DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@mscl1, @mscl2, @mscl3, @mscl4, @mscl5, @mscl6, @mscl7, @mscl8, @mscl9, @mscl10, @mscl11);
DELETE FROM MicroServiceChains WHERE startingLink IN (@mscl1, @mscl2, @mscl3, @mscl4, @mscl5, @mscl6, @mscl7, @mscl8, @mscl9, @mscl10, @mscl11);
DELETE FROM MicroServiceChainLinks WHERE pk IN (@mscl1, @mscl2, @mscl3, @mscl4, @mscl5, @mscl6, @mscl7, @mscl8, @mscl9, @mscl10, @mscl11);
DELETE FROM StandardTasksConfigs WHERE pk IN
(SELECT taskTypePKReference from MicroServiceChainLinks INNER JOIN TasksConfigs ON currentTask = TasksConfigs.pk
 WHERE MicroServiceChainLinks.pk IN (@mscl1, @mscl2, @mscl3, @mscl4, @mscl5, @mscl6, @mscl7, @mscl8, @mscl9, @mscl10, @mscl11));
DELETE FROM TasksConfigs WHERE pk IN
(SELECT currentTask FROM MicroServiceChainLinks WHERE MicroServiceChainLinks.pk in (@mscl1, @mscl2, @mscl3, @mscl4, @mscl5, @mscl6, @mscl7, @mscl8, @mscl9, @mscl10, @mscl11));

-- Remove all entries dealing with the old taskTypes
SET @splitTT = '75cf8446-1cb0-474c-8245-75850d328e91' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (SELECT pk FROM MicroServiceChainLinks WHERE currentTask IN (SELECT pk FROM TasksConfigs WHERE taskType=@splitTT));
DELETE FROM MicroServiceChainLinks WHERE currentTask IN (SELECT pk FROM TasksConfigs WHERE taskType=@splitTT);
DELETE FROM TasksConfigs WHERE taskType=@splitTT;
SET @transcodeTT = '5e70152a-9c5b-4c17-b823-c9298c546eeb' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (SELECT pk FROM MicroServiceChainLinks WHERE currentTask IN (SELECT pk FROM TasksConfigs WHERE taskType=@transcodeTT));
DELETE FROM MicroServiceChainLinks WHERE currentTask IN (SELECT pk FROM TasksConfigs WHERE taskType=@transcodeTT);
DELETE FROM TasksConfigs WHERE taskType=@transcodeTT;
SET @splitFileIdTT = '405b061b-361e-4e75-be27-834a1bc25f5c' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (SELECT pk FROM MicroServiceChainLinks WHERE currentTask IN (SELECT pk FROM TasksConfigs WHERE taskType=@splitFileIdTT));
DELETE FROM MicroServiceChains WHERE startingLink IN (SELECT pk FROM MicroServiceChainLinks WHERE currentTask IN (SELECT pk FROM TasksConfigs WHERE taskType=@splitFileIdTT));
DELETE FROM MicroServiceChainLinks WHERE currentTask IN (SELECT pk FROM TasksConfigs WHERE taskType=@splitFileIdTT);
DELETE FROM StandardTasksConfigs WHERE pk IN (SELECT taskTypePKReference FROM TasksConfigs WHERE taskType=@splitFileIdTT);
DELETE FROM TasksConfigs WHERE taskType=@splitFileIdTT;


-- Fix group on METS gen
UPDATE MicroServiceChainLinks SET microserviceGroup = "Prepare AIP" WHERE pk IN ('ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0', '65240550-d745-4afe-848f-2bf5910457c9');
-- /Issue 5955
