/*
Select * from StandardTasksConfigs WHERE StandardTasksConfigs.filterSubDir like 'objects/sub%';

SELECT pk, description FROM TaskTypes;
+--------------------------------------+--------------------------------------------------+
| pk                                   | description                                      |
+--------------------------------------+--------------------------------------------------+
| 01b748fe-2e9d-44e4-ae5d-113f74c9a0ba | Get user choice from microservice generated list |
| 3590f73d-5eb0-44a0-91a6-5b2db6655889 | assign magic link                                |
| 36b2e239-4a57-4aa5-8ebc-7a29139baca6 | one instance                                     |
| 405b061b-361e-4e75-be27-834a1bc25f5c | Split Job into many links based on file ID       |
| 5e70152a-9c5b-4c17-b823-c9298c546eeb | Transcoder task type                             |
| 61fb3874-8ef6-49d3-8a2d-3cb66e86a30c | get user choice to proceed with                  |
| 6f0b612c-867f-4dfd-8e43-5b35b7f882d7 | linkTaskManagerSetUnitVariable                   |
| 6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9 | goto magic link                                  |
| 75cf8446-1cb0-474c-8245-75850d328e91 | Split creating Jobs for each file                |
| 9c84b047-9a6d-463f-9836-eafa49743b84 | get replacement dic from user choice             |
| a19bfd9f-9989-4648-9351-013a10b382ed | Get microservice generated list in stdOut        |
| a6b1c323-7d36-428e-846a-e7e819423577 | for each file                                    |
| c42184a3-1a7f-4c4d-b380-15d8d97fdd11 | linkTaskManagerUnitVariableLinkPull              |
+--------------------------------------+--------------------------------------------------+
*/

SET @microserviceGroup = 'Process metadata directory';
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';
SET @MoveTransferToFailedLink = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd';


-- return
SET @TasksConfigPKReference = '49c816cd-b443-498f-9369-9274d060ddd3';
SET @TasksConfig = 'a493f430-d905-4f68-a742-f4393a43e694';
SET @MicroServiceChainLink = 'f1e286f9-4ec7-4e19-820c-dae7b8ea7d09';
SET @MicroServiceChainLinksExitCodes = 'bbc7cbfd-c3aa-4625-8782-a461615137ed';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '1b785f4c-6ead-4d92-a9be-34e451e7ad7c';

INSERT INTO TasksConfigsUnitVariableLinkPull (pk, variable, variableValue, defaultMicroServiceChainLink)
    VALUES (@TasksConfigPKReference, 'returnFromMetadataProcessing', NULL, NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'c42184a3-1a7f-4c4d-b380-15d8d97fdd11', @TasksConfigPKReference, 'Load finished with metadata processing link');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;
SET @loadFinishedManualNormalizationLink = @MicroServiceChainLink;

-- remove files without linking information
SET @TasksConfigPKReference = 'a32fc538-efd1-4be0-95a9-5ee40cbc70fd';
SET @TasksConfig = '28a34ba7-e565-45f6-8209-ec6ea9481d2d';
SET @MicroServiceChainLink = 'eb14475a-a5a7-43a2-ac10-7132f1c758fa';
SET @MicroServiceChainLinksExitCodes = '3c077fcd-86b1-45fd-992b-38b04e5846ac';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '4510164b-5480-46e5-8f6d-bc44bbb07185';

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Remove files without linking information (failed normalization artifacts etc.)');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- Normalize to preservation format.
SET @TasksConfigPKReference = 'dc0ad2bc-18ab-4eaf-80e0-de1831ad4aea';
SET @TasksConfig = '9caf9bae-0542-4797-9cd2-6971dae04a4b';
SET @MicroServiceChainLink = '7a5655a8-0750-4e20-8a0a-0935e04ebc52';
SET @MicroServiceChainLinksExitCodes = '6833066f-25c8-4893-9935-dd69cda9d33f';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = 'b02fbd24-ac47-4cce-93f7-a84fe08ef3a8';

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/metadata', 0, NULL, NULL, 'echo_v0.0', '"%relativeLocation%"  "%fileUUID%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Relate manual normalized preservation files to the original files');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- Identify Files By extension
SET @TasksConfigPKReference = '8e4b0d03-b07f-421e-a089-ce60edd625cb';
SET @TasksConfig = '352a43ca-2d97-4140-8b74-cb92a801fa31';
SET @MicroServiceChainLink = '2b1c8cca-ea96-4628-8e79-74e149f7a075';
SET @MicroServiceChainLinksExitCodes = 'be4a4096-9a3e-45a3-9648-7f9c8f89ffdf';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = 'bd2788df-b615-47be-8d3c-c9cdfdd31433';

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/metadata', 0, NULL, NULL, 'identifyFilesByExtension_v0.0', '"%relativeLocation%"  "%fileUUID%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Identify Files ByExtension');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- characterize and extract metadata
SET @TasksConfigPKReference = 'da8e0821-34c7-41b6-a12e-aeaa55e27e1f';
SET @TasksConfig = '04e99ffc-ee3a-4723-a799-f4a22103c84e';
SET @MicroServiceChainLink = '8d3ea3c8-26e2-4cc7-8237-5e2e2d1e3c9e';
SET @MicroServiceChainLinksExitCodes = '5f8cd23c-4f89-48d6-b3e8-01ec091aaa33';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '3ed71f75-d249-4095-a0de-d4a8c9e12a07';

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/metadata', 0, NULL, NULL, 'FITS_v0.0', '"%relativeLocation%" "%SIPLogsDirectory%fileMeta/%fileUUID%.xml" "%date%" "%taskUUID%" "%fileUUID%" "%fileGrpUse%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Characterize and extract metadata on metadata');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- scan for viri
SET @TasksConfigPKReference = '7316e6ed-1c1a-4bf6-a570-aead6b544e41';
SET @TasksConfig = '8850aeff-8553-4ff1-ab31-99b5392a458b';
SET @MicroServiceChainLink = '8bc92801-4308-4e3b-885b-1a89fdcd3014';
SET @MicroServiceChainLinksExitCodes = '919909a4-b66f-4bca-af3d-fc8ec6f94047';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = 'cf1a12ee-e3ce-4317-af07-37a0667996e0';

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/metadata', 1, NULL, '%SIPLogsDirectory%clamAVScan.txt', 'archivematicaClamscan_v0.0', '"%fileUUID%" "%relativeLocation%" "%date%" "%taskUUID%"');   
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Scan for viruses in metadata');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- sanitize
SET @TasksConfigPKReference = '58b192eb-0507-4a83-ae5a-f5e260634c2a';
SET @TasksConfig = '7b07859b-015e-4a17-8bbf-0d46f910d687';
SET @MicroServiceChainLink = 'b21018df-f67d-469a-9ceb-ac92ac68654e';
SET @MicroServiceChainLinksExitCodes = 'fd465136-38f3-47b8-80dd-f02d5fa9888a';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '62c6fb06-014a-402b-a146-c8a9e6706917';

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/metadata', 0, '%SIPLogsDirectory%filenameCleanup.log', '%SIPLogsDirectory%filenameCleanup.log', 'sanitizeObjectNames_v0.0', '"%SIPDirectory%objects/metadata/" "%SIPUUID%" "%date%" "%taskUUID%" "SIPDirectory" "sipUUID" "%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Sanitize file and directory names in metadata');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- extract packages
SET @TasksConfigPKReference = '36cc5356-6db1-4f3e-8155-1f92f958d2a4';
SET @TasksConfig = 'faf6306b-76aa-415c-9087-16cc366ac6e7';
SET @MicroServiceChainLink = 'd8706e6e-7f38-4d98-9721-4f120156dca8';
SET @MicroServiceChainLinksExitCodes = '7f047ea3-7d69-4adc-b786-019f887c15fb';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '3989544b-8852-43ee-aec1-bb1d194cb399';

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/metadata', 1, '%SIPLogsDirectory%extraction.log', '%SIPLogsDirectory%extraction.log', 'transcoderExtractPackages_v0.0', '"%relativeLocation%" "%SIPObjectsDirectory%" "%SIPLogsDirectory%" "%date%" "%taskUUID%" "%fileUUID%"');   
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Extract packages in metadata');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- Assign checksums
SET @TasksConfigPKReference = 'e377b543-d9b8-47a9-8297-4f95ca7600b3';
SET @TasksConfig = '5bd51fcb-6a68-4c5f-b99e-4fc36f51c40c';
SET @MicroServiceChainLink = 'b6b0fe37-aa26-40bd-8be8-d3acebf3ccf8';
SET @MicroServiceChainLinksExitCodes = 'a0f33c59-081b-4427-b430-43b811cf0594';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '1287685e-e27a-4541-8fa8-4bdd026b181c';

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/metadata', 0, NULL, NULL, 'updateSizeAndChecksum_v0.0', '--filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Assign checksums and file sizes to metadata ');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- Assign file UUIDS
SET @TasksConfigPKReference = '34966164-9800-4ae1-91eb-0a0c608d72d5';
SET @TasksConfig = 'dc2994f2-6de6-4c46-81f7-54676c5054aa';
SET @MicroServiceChainLink = 'dc9d4991-aefa-4d7e-b7b5-84e3c4336e74';
SET @MicroServiceChainLinksExitCodes = '4de0e894-8eda-49eb-a915-124b4f6c3608';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '2f8b1933-163f-4504-951c-41a08bf21ce5';

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/metadata', 1, '%SIPLogsDirectory%FileUUIDs.log', '%SIPLogsDirectory%FileUUIDsError.log', 'assignFileUUIDs_v0.0', '--sipUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%" --use "metadata"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Assign file UUIDs to metadata');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- move metadata directory into objects directory (when from transfer?)

SET @TasksConfigPKReference = 'ce13677c-8ad4-4af0-92c8-ae8763f5094d';
SET @TasksConfig = 'ba0d0244-1526-4a99-ab65-43bfcd704e70';
SET @MicroServiceChainLink = 'e4b0c713-988a-4606-82ea-4b565936d9a7';
SET @MicroServiceChainLinksExitCodes = 'ff97354f-9fdd-4c85-8a33-cb9e96b48229';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '09f98230-da0c-4f29-8fe8-26e823971a88';

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, 1, NULL, NULL, 'move_v0.0', '"%SIPDirectory%metadata" "%SIPDirectory%objects/metadata"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Move metadata to objects directory');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- set link when finished metadata directory processing
SET @TasksConfigPKReference = '6b4600f2-6df6-42cb-b611-32938b46a9cf';
SET @TasksConfig = '0cbfd02e-94bc-4f0d-8e56-f7af6379c3ca';
SET @MicroServiceChainLink = 'f060d17f-2376-4c0b-a346-b486446e46ce';
SET @MicroServiceChainLinksExitCodes = '7458e131-3beb-40cb-9880-32dec49f1592';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO TasksConfigsSetUnitVariable (pk, variable, microServiceChainLink)
    VALUES (@TasksConfigPKReference, 'returnFromMetadataProcessing', 'fa5b0c43-ed7b-4c7e-95a8-4f9ec7181260');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', @TasksConfigPKReference, 'Set resume link after processing metadata directory');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);



UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@MicroServiceChainLink  WHERE microServiceChainLink = '88affaa2-13c5-4efb-a860-b182bd46c2c6';
UPDATE MicroServiceChainLinks SET defaultNextChainLink = @MicroServiceChainLink WHERE pk = '88affaa2-13c5-4efb-a860-b182bd46c2c6';


SET @TasksConfigPKReference = '771dd17a-02d1-403b-a761-c70cc9cc1d1a';
SET @TasksConfig = '449530ec-cd94-4d8c-aae0-3b7cd2e2d5f9';
SET @MicroServiceChainLink = 'c168f1ee-5d56-4188-8521-09f0c5475133';
SET @MicroServiceChainLinksExitCodes = '938e6215-77f4-4ebc-abdd-ed511ebc5357';
SET @defaultNextChainLink = @MoveSIPToFailedLink;

INSERT INTO TasksConfigsSetUnitVariable (pk, variable, microServiceChainLink)
    VALUES (@TasksConfigPKReference, 'returnFromMetadataProcessing', '75fb5d67-5efa-4232-b00b-d85236de0d3f');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', @TasksConfigPKReference, 'Set resume link after processing metadata directory');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);


UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@MicroServiceChainLink  WHERE microServiceChainLink = 'ee438694-815f-4b74-97e1-8e7dde2cc6d5';
UPDATE MicroServiceChainLinks SET defaultNextChainLink = @MicroServiceChainLink WHERE pk = 'ee438694-815f-4b74-97e1-8e7dde2cc6d5';

-- check why two normalize metadata to preservation format? probably one is thumbnail. (with dip)


UPDATE StandardTasksConfigs SET arguments = 'create "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%METS.%SIPUUID%.xml" "%SIPDirectory%thumbnails/" --writer filesystem --payloadmanifestalgorithm "sha512"' WHERE execute = 'bagit_v0.0';

UPDATE StandardTasksConfigs SET arguments = '-R "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPDirectory%METS.%SIPUUID%.xml" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"' WHERE pk = 'd12b6b59-1f1c-47c2-b1a3-2bf898740eae';

