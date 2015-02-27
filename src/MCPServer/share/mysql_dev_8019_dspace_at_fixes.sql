
-- DSpace AT sees files
UPDATE WatchedDirectories SET onlyActOnDirectories=0 WHERE pk='e3b15e28-6370-42bf-a0e1-f61e4837a2a7';

-- Add client script to extract DSpace zipped files into a dir
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('21f89353-30ba-4601-8690-7c235630736f', 0, 'fileToFolder_v1.0', '"%SIPDirectory%" "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('d9ebceed-2cfb-462b-b130-48fecdf55bbf', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '21f89353-30ba-4601-8690-7c235630736f', 'Check if file or folder');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('bda96b35-48c7-44fc-9c9e-d7c5a05016c1', 'Verify transfer compliance', 'Failed', 'd9ebceed-2cfb-462b-b130-48fecdf55bbf', '61c316a6-0a50-4f65-8767-1f44b1eeb6dd');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('c5c68ced-17d5-4b7d-b955-a56080d5b9bb', 'bda96b35-48c7-44fc-9c9e-d7c5a05016c1', 0, '26bf24c9-9139-4923-bf99-aa8648b1692b', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='bda96b35-48c7-44fc-9c9e-d7c5a05016c1' WHERE microServiceChainLink='0e1a8a6b-abcc-4ed6-b4fb-cbccfdc23ef5';
