-- TEMPORARY
-- TODO Update this so it
-- A) autodetects transfer type OR
-- B) add a Dataverse type that sets postExtractSpecializedProcessing

SET @parseDataverseMSCL = '830f7002-e644-456b-8cba-fddaad7f1fbf' COLLATE utf8_unicode_ci;
SET @failTransfer = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd' COLLATE utf8_unicode_ci;

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('7cba173b-a631-4a2f-b49e-0627e779a7ed', 0, 'parseDataverse', '%SIPDirectory% %SIPUUID%');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('99718d08-8867-42f3-b74c-a75dc8d4c61a', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '7cba173b-a631-4a2f-b49e-0627e779a7ed', 'Parse Dataverse METS');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values (@parseDataverseMSCL, 'Parse external files', 'Failed', '99718d08-8867-42f3-b74c-a75dc8d4c61a', @failTransfer);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('c28944e8-362c-4db7-858d-f1a10ab0317c', @parseDataverseMSCL, 0, 'db99ab43-04d7-44ab-89ec-e09d7bbdc39d', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@parseDataverseMSCL WHERE microServiceChainLink='8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc';
-- Update default MCL for postExtractSpecializedProcessing to point at dataverse parsing
UPDATE TasksConfigsUnitVariableLinkPull SET defaultMicroServiceChainLink=@parseDataverseMSCL WHERE pk='49d853a9-646d-4e9f-b825-d1bcc3ba77f0';
