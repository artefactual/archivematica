-- Move load labels to after charaterize (same group)
SET @loadLabelsMSCL = '1b1a4565-b501-407b-b40f-2f20889423f1' COLLATE utf8_unicode_ci;
SET @newAfterMSCL = '192315ea-a1bf-44cf-8cb4-0b3edd1522a6' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@newAfterMSCL WHERE nextMicroServiceChainLink=@loadLabelsMSCL;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@newAfterMSCL WHERE defaultNextChainLink=@loadLabelsMSCL;
UPDATE MicroServiceChains SET startingLink=@newAfterMSCL WHERE startingLink=@loadLabelsMSCL;

UPDATE MicroServiceChainLinks SET defaultNextChainLink=@loadLabelsMSCL WHERE defaultNextChainLink = 'dae3c416-a8c2-4515-9081-6dbd7b265388';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@loadLabelsMSCL WHERE nextMicroServiceChainLink = 'dae3c416-a8c2-4515-9081-6dbd7b265388';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='dae3c416-a8c2-4515-9081-6dbd7b265388' WHERE pk = @loadLabelsMSCL;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='dae3c416-a8c2-4515-9081-6dbd7b265388' WHERE microServiceChainLink = @loadLabelsMSCL;

-- Remove extra set file permissions
SET @d1 = 'c4898520-448c-40fc-8eb3-0603b6aacfb7' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@d1;
DELETE FROM MicroServiceChainLinks WHERE pk=@d1;

-- Add validation MSCL after charaterize
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, filterSubDir) VALUES ('1d3ef137-b060-4b33-b13f-25aa9346877b', 0, 'validateFile_v1.0', '"%relativeLocation%" "%fileUUID%" "%SIPUUID%"', 'objects');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('530a3999-422f-4abb-a6be-bd29cbed04a4', 'a6b1c323-7d36-428e-846a-e7e819423577', '1d3ef137-b060-4b33-b13f-25aa9346877b', 'Validate formats');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('a536828c-be65-4088-80bd-eb511a0a063d', 'Validation', 'Failed', '530a3999-422f-4abb-a6be-bd29cbed04a4', 'dae3c416-a8c2-4515-9081-6dbd7b265388');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('434066e6-8205-4832-a71f-cc9cd8b539d2', 'a536828c-be65-4088-80bd-eb511a0a063d', 0, 'dae3c416-a8c2-4515-9081-6dbd7b265388', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='a536828c-be65-4088-80bd-eb511a0a063d' WHERE microServiceChainLink='1b1a4565-b501-407b-b40f-2f20889423f1';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='a536828c-be65-4088-80bd-eb511a0a063d' WHERE pk='1b1a4565-b501-407b-b40f-2f20889423f1';

-- Change group for check for specialized processing
UPDATE MicroServiceChainLinks SET microserviceGroup='Examine contents' WHERE pk='192315ea-a1bf-44cf-8cb4-0b3edd1522a6';
-- Failing index transfer contents should not skip transfer XML creation
UPDATE MicroServiceChainLinks SET defaultNextChainLink='db99ab43-04d7-44ab-89ec-e09d7bbdc39d' WHERE pk='eb52299b-9ae6-4a1f-831e-c7eee0de829f';
