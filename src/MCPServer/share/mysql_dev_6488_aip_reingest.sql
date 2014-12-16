-- Move MD reminder to start of submission docs
SET @mdReminderMSCL = '54b73077-a062-41cc-882c-4df1eba447d9' COLLATE utf8_unicode_ci;
SET @afterMdReminderMSCL = '77a7fa46-92b9-418e-aa88-fbedd4114c9f' COLLATE utf8_unicode_ci;
SET @createMETSMSCL='ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@createMETSMSCL WHERE defaultNextChainLink=@mdReminderMSCL;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@createMETSMSCL WHERE nextMicroServiceChainLink=@mdReminderMSCL;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@mdReminderMSCL WHERE defaultNextChainLink=@afterMdReminderMSCL;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@mdReminderMSCL WHERE nextMicroServiceChainLink=@afterMdReminderMSCL;
UPDATE MicroServiceChains SET startingLink=@afterMdReminderMSCL WHERE startingLink=@createMETSMSCL;
-- Set MD reminder group
UPDATE MicroServiceChainLinks SET microserviceGroup='Add final metadata' WHERE pk IN (@mdReminderMSCL, 'eeb23509-57e2-4529-8857-9d62525db048', @afterMdReminderMSCL);

-- Add jsonMetadataToCSV to during post-norm metadata processing 8c8bac29-4102-4fd2-9d0a-a3bd2e607566
SET @metadataMSCL = 'b0ffcd90-eb26-4caf-8fab-58572d205f04' COLLATE utf8_unicode_ci;
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('38b99e0c-7066-49c4-82ed-d77bd7f019a1', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '44d3789b-10ad-4a9c-9984-c2fe503c8720', 'Process JSON metadata');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES (@metadataMSCL, 'Process metadata directory', 'Failed', '38b99e0c-7066-49c4-82ed-d77bd7f019a1', 'e4b0c713-988a-4606-82ea-4b565936d9a7');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('f1292ec3-4749-4e64-a924-c2089f97c583', @metadataMSCL, 0, 'e4b0c713-988a-4606-82ea-4b565936d9a7', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@metadataMSCL WHERE microServiceChainLink='ee438694-815f-4b74-97e1-8e7dde2cc6d5';
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@metadataMSCL WHERE pk='ee438694-815f-4b74-97e1-8e7dde2cc6d5';
-- /ingest jsonMetadataToCSV
