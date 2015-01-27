-- Insert a new microservice, after package extraction, which creates
-- a second structMap documenting the final state of the transfer.
SET @characterizeExtractMSCL='303a65f6-a16f-4a06-807b-cb3425a30201' COLLATE utf8_unicode_ci;
SET @processedStructmapSTC='fefd486c-e6ce-4229-ac3d-cf53e66f46cc' COLLATE utf8_unicode_ci;
SET @processedStructmapTC='275b3640-68a6-4c4e-adc1-888ea3fdfba5' COLLATE utf8_unicode_ci;
SET @processedStructmapMSCL='307edcde-ad10-401c-92c4-652917c993ed' COLLATE utf8_unicode_ci;

INSERT INTO StandardTasksConfigs (pk, execute, arguments, requiresOutputLock) VALUES (@processedStructmapSTC, 'createProcessedStructmap_v0.0', '--sipUUID "%SIPUUID%" --basePath "%SIPDirectory%" --xmlFile "%SIPDirectory%"metadata/submissionDocumentation/METS.xml --basePathString "transferDirectory" --fileGroupIdentifier "transfer_id"', 0);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@processedStructmapTC, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @processedStructmapSTC, 'Add processed structMap to METS.xml document');
INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, microServiceGroup, defaultExitMessage) VALUES (@processedStructmapMSCL, @processedStructmapTC, '61c316a6-0a50-4f65-8767-1f44b1eeb6dd', 'Update METS.xml document', 'Failed');
UPDATE MicroServiceChains SET startingLink=@processedStructmapMSCL WHERE startingLink='303a65f6-a16f-4a06-807b-cb3425a30201';
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@processedStructmapMSCL WHERE microServiceChainLink='b944ec7f-7f99-491f-986d-58914c9bb4fa' AND exitCode=1;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink=@processedStructmapMSCL WHERE microServiceChainLink='1cb7e228-6e94-4c93-bf70-430af99b9264' AND exitCode=0;
UPDATE MicroServiceChainLinks SET defaultNextChainLink=@processedStructmapMSCL WHERE pk='1cb7e228-6e94-4c93-bf70-430af99b9264';
INSERT INTO MicroServiceChainLinksExitCodes (microServiceChainLink, exitCode, nextMicroServiceChainLink) VALUES (@processedStructmapMSCL, 0, @characterizeExtractMSCL);
