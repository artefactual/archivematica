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
SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

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
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Remove files without linking information (failed normalization artifacts etc.)');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- Normalize to preservation format.
SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

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
SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

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
SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

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
SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

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
SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

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
SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

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
SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

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
SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

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

SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @MicroServiceChain = '';

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
SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = 'f060d17f-2376-4c0b-a346-b486446e46ce';
SET @MicroServiceChainLinksExitCodes = '';
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


SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = 'c168f1ee-5d56-4188-8521-09f0c5475133';
SET @MicroServiceChainLinksExitCodes = '';
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

