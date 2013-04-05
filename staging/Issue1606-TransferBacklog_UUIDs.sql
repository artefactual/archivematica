SET @microserviceGroup = 'Create SIP from Transfer';
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
SET @TasksConfig = '8b345691-53ce-4129-86e2-3ea0922770f6';
SET @TasksConfigPKReference = '6e7157ac-51a0-4533-bc77-54bfc990ca9d';
SET @MicroServiceChainLink = '64e395b4-ddb8-47f3-8a4c-79bfd3f2d88b';
SET @MicroServiceChainLinksExitCodes = '3f03f208-6bc1-429b-b400-e4f3140c0dbe';
SET @defaultNextChainLink = @NextMicroServiceChainLink;
SET @MicroServiceChain = '01399d6e-1c7c-4128-923e-d2adb6ee4a10';


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




-- Updating transfer file index --
SET @TasksConfig = 'd6a0dec1-63e7-4c7c-b4c0-e68f0afcedd3';
SET @TasksConfigPKReference = '16ce41d9-7bfa-4167-bca8-49fe358f53ba';
SET @MicroServiceChainLink = 'd46f6af8-bc4e-4369-a808-c0fedb439fef';
SET @MicroServiceChainLinksExitCodes = '042bda05-ab8b-4ad2-b281-e0c2a9490f15';
SET @defaultNextChainLink = @MoveTransferToFailedLink;
SET @NextMicroServiceChainLink = NULL;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'backlogUpdatingTransferFileIndex_v0.0', '"%SIPUUID%" "%SIPName%" "%SIPDirectory%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Updating transfer file index');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- Move to backlog --
SET @TasksConfig = 'f1586bd7-f550-4588-9f45-07a212db7994';
SET @TasksConfigPKReference = '9f25a366-f7a4-4b59-b219-2d5f259a1be9';
SET @MicroServiceChainLink = 'abd6d60c-d50f-4660-a189-ac1b34fafe85';
SET @MicroServiceChainLinksExitCodes = '029e7f42-4c35-4df0-b081-bd623fc6d6a7';
SET @defaultNextChainLink = @MoveTransferToFailedLink;


INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'moveTransfer_v0.0', '"%SIPDirectory%" "%sharedPath%transferBacklog/original/." "%SIPUUID%" "%sharedPath%" "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Move transfer to backlog');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- add chain --
SET @MicroServiceChain = '7065d256-2f47-4b7d-baec-2c4699626121';
INSERT INTO MicroServiceChains (pk, startingLink, description)
    VALUES (@MicroServiceChain, @MicroServiceChainLink, 'Send to backlog');


-- Add to options --
SET @MicroServiceChainChoice = '4a266d37-6c3d-49f7-b1ac-b93c0906945f';
SET @choiceAvailableAtLink = 'bb194013-597c-4e4a-8493-b36d190f8717';
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable )
    VALUES (@MicroServiceChainChoice, @choiceAvailableAtLink, @MicroServiceChain);


