/*
Insert new link between X and Y. 
old: X -> Y
new: X -> newLink -> Y
*/


/*
Notes on types of tasks:
mysql> select * from TaskTypes;
+--------------------------------------+--------------------------------------------------+----------+---------------------+
| pk                                   | description                                      | replaces | lastModified        |
+--------------------------------------+--------------------------------------------------+----------+---------------------+
| 01b748fe-2e9d-44e4-ae5d-113f74c9a0ba | Get user choice from microservice generated list | NULL     | 2012-10-01 17:25:10 |
| 3590f73d-5eb0-44a0-91a6-5b2db6655889 | assign magic link                                | NULL     | 2012-10-01 17:25:10 |
| 36b2e239-4a57-4aa5-8ebc-7a29139baca6 | one instance                                     | NULL     | 2012-10-01 17:25:10 |
| 405b061b-361e-4e75-be27-834a1bc25f5c | Split Job into many links based on file ID       | NULL     | 2012-10-01 17:25:10 |
| 5e70152a-9c5b-4c17-b823-c9298c546eeb | Transcoder task type                             | NULL     | 2012-10-01 17:25:10 |
| 61fb3874-8ef6-49d3-8a2d-3cb66e86a30c | get user choice to proceed with                  | NULL     | 2012-10-01 17:25:10 |
| 6f0b612c-867f-4dfd-8e43-5b35b7f882d7 | linkTaskManagerSetUnitVariable                   | NULL     | 2012-10-22 10:05:07 |
| 6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9 | goto magic link                                  | NULL     | 2012-10-01 17:25:10 |
| 75cf8446-1cb0-474c-8245-75850d328e91 | Split creating Jobs for each file                | NULL     | 2012-10-01 17:25:10 |
| 9c84b047-9a6d-463f-9836-eafa49743b84 | get replacement dic from user choice             | NULL     | 2012-10-01 17:25:10 |
| a19bfd9f-9989-4648-9351-013a10b382ed | Get microservice generated list in stdOut        | NULL     | 2012-10-01 17:25:10 |
| a6b1c323-7d36-428e-846a-e7e819423577 | for each file                                    | NULL     | 2012-10-01 17:25:10 |
| c42184a3-1a7f-4c4d-b380-15d8d97fdd11 | linkTaskManagerUnitVariableLinkPull              | NULL     | 2012-10-22 10:03:13 |
+--------------------------------------+--------------------------------------------------+----------+---------------------+
*/

SET @microserviceGroup = 'Normalize';
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';
SET @MoveTransferToFailedLink = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd';


SET @XLink = 'a46e95fe-4a11-4d3c-9b76-c5d8ea0b094d';
SET @YLink = '1cd3b36a-5252-4a69-9b1c-3b36829288ab';

SET @TasksConfigPKReference = '';
SET @TasksConfig = '';
SET @MicroServiceChainLink = '';
SET @MicroServiceChainLinksExitCodes = '';
SET @defaultNextChainLink = @MoveSIPToFailedLink;
SET @NextMicroServiceChainLink = @YLink;

INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, 'objects/manualNormalization/', FALSE, NULL, NULL, 'manualNormalizationIdentifyFilesIncluded_v0.0', '"%fileUUID%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'a6b1c323-7d36-428e-846a-e7e819423577', @TasksConfigPKReference, 'Identify manually normalized files');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

-- set non zero exit code --
-- UPDATE MicroServiceChainLinks SET defaultNextChainLink = @NextMicroServiceChainLink WHERE pk = @XLink;

-- set zero exit code --
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @NextMicroServiceChainLink where microServiceChainLink = @XLink;

