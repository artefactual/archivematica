
/*
mysql> SELECT * from MicroServiceChainLinksExitCodes WHERE nextMicroServiceChainLink = '74665638-5d8f-43f3-b7c9-98c4c8889766';
+--------------------------------------+--------------------------------------+----------+--------------------------------------+-----------+------------------------+----------+---------------------+
| pk                                   | microServiceChainLink                | exitCode | nextMicroServiceChainLink            | playSound | exitMessage            | replaces | lastModified        |
+--------------------------------------+--------------------------------------+----------+--------------------------------------+-----------+------------------------+----------+---------------------+
| 7386614c-6b85-4fc2-9aec-1b7a8d4adb8a | 67b44f8f-bc97-4cb3-b6dd-09dba3c99d30 |        0 | 74665638-5d8f-43f3-b7c9-98c4c8889766 | NULL      | Completed successfully | NULL     | 2012-10-01 17:25:07 |
+--------------------------------------+--------------------------------------+----------+--------------------------------------+-----------+------------------------+----------+---------------------+
1 row in set (0.00 sec)

mysql> SELECT * from MicroServiceChainLinksExitCodes WHERE nextMicroServiceChainLink = 'e219ed78-2eda-4263-8c0f-0c7f6a86c33e';
+--------------------------------------+--------------------------------------+----------+--------------------------------------+-----------+------------------------+----------+---------------------+
| pk                                   | microServiceChainLink                | exitCode | nextMicroServiceChainLink            | playSound | exitMessage            | replaces | lastModified        |
+--------------------------------------+--------------------------------------+----------+--------------------------------------+-----------+------------------------+----------+---------------------+
| c35e05aa-5bb0-454f-8ff3-66ffc625f7ef | 67b44f8f-bc97-4cb3-b6dd-09dba3c99d30 |      179 | e219ed78-2eda-4263-8c0f-0c7f6a86c33e | NULL      | Completed successfully | NULL     | 2012-10-01 17:25:07 |
+--------------------------------------+--------------------------------------+----------+--------------------------------------+-----------+------------------------+----------+---------------------+
1 row in set (0.00 sec)
*/

SET @microserviceGroup  = 'Normalize';

SET @TasksConfig = 'fe354b27-dbb2-4454-9c1c-340d85e67b78';
SET @TasksConfigPKReference = 'c15de53e-a5b2-41a1-9eee-1a7b4dd5447a';
SET @MicroServiceChainLink = '8ba83807-2832-4e41-843c-2e55ad10ea0b';
SET @MicroServiceChainLinksExitCodes = '9b010021-a969-4a16-98c2-0db1ecd5d6d9';
SET @defaultNextChainLink = '74665638-5d8f-43f3-b7c9-98c4c8889766';
INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'retryNormalizeRemoveNormalized_v0.0', '--SIPDirectory "%SIPDirectory%" --SIPUUID "%SIPUUID%" --preservation --access');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Remove preservation and access normalized files to renormalize.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @defaultNextChainLink); 
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- new task to set reset --

SET @TasksConfig = '4745d0bb-910c-4c0d-8b81-82d7bfca7819';
SET @TasksConfigPKReference = '76eaa4d2-fd4f-4741-b68c-df5b96ba81d1';
SET @MicroServiceChainLink = '5d6a103c-9a5d-4010-83a8-6f4c61eb1478';
SET @MicroServiceChainLinksExitCodes = '6f9575c3-4b84-45bf-920d-b8115e4806f4';
SET @defaultNextChainLink = '74665638-5d8f-43f3-b7c9-98c4c8889766';
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES (@TasksConfigPKReference, 'reNormalize', NULL, @NextMicroServiceChainLink);
    
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES (@TasksConfig, '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', @TasksConfigPKReference, 'Set remove preservation and access normalized files to renormalize link.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @defaultNextChainLink); 
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @NextMicroServiceChainLink WHERE nextMicroServiceChainLink = '74665638-5d8f-43f3-b7c9-98c4c8889766'  AND microServiceChainLink != @MicroServiceChainLink;

SET @TasksConfig = 'bacb088a-66ef-4590-b855-69f21dfdf87a';
SET @TasksConfigPKReference = '352fc88d-4228-4bc8-9c15-508683dabc58';
SET @MicroServiceChainLink = '8de9fe10-932f-4151-88b0-b50cf271e156';
SET @MicroServiceChainLinksExitCodes = '8a526305-0805-4680-8dd8-3f7dd3da7854';
SET @defaultNextChainLink = 'e219ed78-2eda-4263-8c0f-0c7f6a86c33e';
INSERT INTO StandardTasksConfigs (pk, filterFileEnd, filterFileStart, filterSubDir, requiresOutputLock, standardOutputFile, standardErrorFile, execute, arguments)
    VALUES (@TasksConfigPKReference, NULL, NULL, NULL, FALSE, NULL, NULL, 'retryNormalizeRemoveNormalized_v0.0', '--SIPDirectory "%SIPDirectory%" --SIPUUID "%SIPUUID%" --preservation --access');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @TasksConfigPKReference, 'Remove preservation normalized files to renormalize.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @defaultNextChainLink); 
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- new task to set reset --

SET @TasksConfig = '97cc7629-c580-44db-8a41-68b6b2f23be4';
SET @TasksConfigPKReference = 'b5808a0f-e842-4820-837a-832d18398ebb';
SET @MicroServiceChainLink = '9e3dd445-551d-42d1-89ba-fe6dff7c6ee6';
SET @MicroServiceChainLinksExitCodes = 'c6e80559-2eda-484d-9f5e-bd365b11278f';
SET @defaultNextChainLink = 'e219ed78-2eda-4263-8c0f-0c7f6a86c33e';
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES (@TasksConfigPKReference, 'reNormalize', NULL, @NextMicroServiceChainLink);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES (@TasksConfig, '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', @TasksConfigPKReference, 'Set remove preservation normalized files to renormalize link.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @defaultNextChainLink); 
SET @NextMicroServiceChainLink = @MicroServiceChainLink;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @NextMicroServiceChainLink WHERE nextMicroServiceChainLink = 'e219ed78-2eda-4263-8c0f-0c7f6a86c33e' AND microServiceChainLink != @MicroServiceChainLink;


UPDATE  TasksConfigs SET description = 'Select normalization file identification tool' where pk = '85a2ec9b-5a80-497b-af60-04926c0bf183';




