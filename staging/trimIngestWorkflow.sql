SET @microserviceGroup = 'TRIM transfer';
-- create chain that loads the chain link for repeat norm --

/*
./../dev-helper recreate-db; ./addUUIDs.py ./trimIngestWorkflow.sql;mysql -u root MCP --execute "source ./trimIngestWorkflow_UUIDs.sql"

mysql> SELECT description, pk FROM TaskTypes;
+--------------------------------------------------+--------------------------------------+
| description                                      | pk                                   |
+--------------------------------------------------+--------------------------------------+
| Get user choice from microservice generated list | 01b748fe-2e9d-44e4-ae5d-113f74c9a0ba |
| assign magic link                                | 3590f73d-5eb0-44a0-91a6-5b2db6655889 |
| one instance                                     | 36b2e239-4a57-4aa5-8ebc-7a29139baca6 |
| Split Job into many links based on file ID       | 405b061b-361e-4e75-be27-834a1bc25f5c |
| Transcoder task type                             | 5e70152a-9c5b-4c17-b823-c9298c546eeb |
| get user choice to proceed with                  | 61fb3874-8ef6-49d3-8a2d-3cb66e86a30c |
| linkTaskManagerSetUnitVariable                   | 6f0b612c-867f-4dfd-8e43-5b35b7f882d7 |
| goto magic link                                  | 6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9 |
| Split creating Jobs for each file                | 75cf8446-1cb0-474c-8245-75850d328e91 |
| get replacement dic from user choice             | 9c84b047-9a6d-463f-9836-eafa49743b84 |
| Get microservice generated list in stdOut        | a19bfd9f-9989-4648-9351-013a10b382ed |
| for each file                                    | a6b1c323-7d36-428e-846a-e7e819423577 |
| linkTaskManagerUnitVariableLinkPull              | c42184a3-1a7f-4c4d-b380-15d8d97fdd11 |



*/
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';
SET @MoveTransferToFailedLink = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd';

/*
SET @TasksConfig = '';
SET @TasksConfigPKReference = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @NextMicroServiceChainLink;
SET @MicroServiceChain = '';


INSERT INTO TasksConfigsUnitVariableLinkPull (pk, variable, variableValue)
    VALUES (@TasksConfigPKReference, 'reNormalize', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Determine what to remove to re-normalize.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @defaultNextChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChain, @MicroServiceChainLink, 'Redo normalization');
SET @MicroServiceChain2 = @MicroServiceChain;


-- add option to create sip for each directory in the transfer --
*/


-- restructure for compliance --
-- * process normal after * --
-- * similar to def restructureBagForComplianceFileUUIDsAssigned(unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith = "%transferDirectory%"): --
SET @TasksConfig = '';
SET @TasksConfigPKReference = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveTransferToFailedLink;
SET @NextMicroServiceChainLink = NULL;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'trimRestructureForCompliance_v0.0', '"%SIPUUID%" "%SIPName%" "%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Restructure TRIM for compliance');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- verify checksums --
SET @TasksConfig = '';
SET @TasksConfigPKReference = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveTransferToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'trimVerifyChecksums_v0.0', '"%SIPUUID%" "%SIPName%" "%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Verify TRIM checksums');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- verify manifests --
SET @TasksConfig = '';
SET @TasksConfigPKReference = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveTransferToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'trimVerifyManifest_v0.0', '"%SIPUUID%" "%SIPName%" "%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Verify TRIM manifest');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- assign checksums --
SET @TasksConfig = '6405c283-9eed-410d-92b1-ce7d938ef080';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveTransferToFailedLink;
SET @MicroServiceChain = '';

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- assign file uuids --
SET @TasksConfig = 'feac0c04-3511-4e91-9403-5c569cff7bcc';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveTransferToFailedLink;
SET @MicroServiceChain = '';

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- set transfer type --
SET @TasksConfig = '';
SET @TasksConfigPKReference = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveTransferToFailedLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'archivematicaSetTransferType_v0.0', '"%SIPUUID%" "TRIM"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Set transfer type: TRIM');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- move to the processing directory --
SET @TasksConfig = '7c02a87b-7113-4851-97cd-2cf9d3fc0010';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveTransferToFailedLink;


INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- SET Permissions --
SET @TasksConfig = '10846796-f1ee-499a-9908-4c49f8edd7e6';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveTransferToFailedLink;
SET @MicroServiceChain = '';

INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChain, @MicroServiceChainLink, 'Approve transfer');

-- approve transfer --
SET @TasksConfigPKReference = NULL;
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @NextMicroServiceChainLink;
SET @rejectTransferMicroserviceChain = '1b04ec43-055c-43b7-9543-bd03c6a778ba';
SET @MicroServiceChainChoice1 = '';
SET @MicroServiceChainChoice2 = '';


INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', @TasksConfigPKReference, 'Approve transfer');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES (@MicroServiceChainChoice1, @MicroServiceChainLink, @MicroServiceChain);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES (@MicroServiceChainChoice2, @MicroServiceChainLink, @rejectTransferMicroserviceChain);
    
SET @MicroServiceChain = '';
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChain, @MicroServiceChainLink, 'TRIM Ingest');

-- create watched directory --
SET @WatchedDirectory = '';
INSERT INTO WatchedDirectories (pk, watchedDirectoryPath, chain, onlyActOnDirectories, expectedType)
    VALUES (@WatchedDirectory, '%watchDirectoryPath%activeTransfers/TRIM/', @MicroServiceChain, 1, 'f9a3a93b-f184-4048-8072-115ffac06b5d');



