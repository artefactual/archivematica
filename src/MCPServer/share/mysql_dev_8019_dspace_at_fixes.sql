
-- DSpace AT sees files
UPDATE WatchedDirectories SET onlyActOnDirectories=0 WHERE pk='e3b15e28-6370-42bf-a0e1-f61e4837a2a7';

-- Add client script to extract DSpace zipped files into a dir
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('21f89353-30ba-4601-8690-7c235630736f', 0, 'fileToFolder_v1.0', '"%SIPDirectory%" "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('d9ebceed-2cfb-462b-b130-48fecdf55bbf', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '21f89353-30ba-4601-8690-7c235630736f', 'Check if file or folder');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('bda96b35-48c7-44fc-9c9e-d7c5a05016c1', 'Verify transfer compliance', 'Failed', 'd9ebceed-2cfb-462b-b130-48fecdf55bbf', '61c316a6-0a50-4f65-8767-1f44b1eeb6dd');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('c5c68ced-17d5-4b7d-b955-a56080d5b9bb', 'bda96b35-48c7-44fc-9c9e-d7c5a05016c1', 0, '26bf24c9-9139-4923-bf99-aa8648b1692b', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='bda96b35-48c7-44fc-9c9e-d7c5a05016c1' WHERE microServiceChainLink='0e1a8a6b-abcc-4ed6-b4fb-cbccfdc23ef5';

-- Delete unused MSCLs
SET @d1='663a11f6-91cb-4fef-9aa7-2594b3752e4c' COLLATE utf8_unicode_ci;
SET @d2='a132193a-2e79-4221-a092-c51839d566fb' COLLATE utf8_unicode_ci;
SET @d3='9e4e39be-0dad-41bc-bee0-35cb71e693df' COLLATE utf8_unicode_ci;
SET @d4='e888269d-460a-4cdf-9bc7-241c92734402' COLLATE utf8_unicode_ci;
-- Transfer backup
SET @d5='9fa0a0d1-25bb-4507-a5f7-f177d7fa920d' COLLATE utf8_unicode_ci;
SET @d6='c1339015-e15b-4303-8f37-a2516669ac4e' COLLATE utf8_unicode_ci;
SET @d7='a72afc44-fa28-4de7-b35f-c79b9f01aa5c' COLLATE utf8_unicode_ci;
SET @d8='478512a6-10e4-410a-847d-ce1e25d8d31c' COLLATE utf8_unicode_ci;

DELETE FROM TasksConfigsAssignMagicLink WHERE execute = @d5;
DELETE FROM MicroServiceChainChoice WHERE choiceAvailableAtLink IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8);
DELETE FROM MicroServiceChains WHERE pk IN ('a7f8f67f-401f-4665-b7b3-35496fd5017c', '2884ed7c-8c4c-4fa9-a6eb-e27bcaf9ab92');
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@d1, @d2, @d3, @d4, @d5, @d6, @d7, @d8);


-- Delete all TasksConfigs that don't have MicroServiceChainLinks pointing at them
DELETE FROM TasksConfigs USING TasksConfigs LEFT OUTER JOIN MicroServiceChainLinks ON currentTask=TasksConfigs.pk WHERE MicroServiceChainLinks.pk is NULL;
-- Delete all StandardTasksConfigs that don't have TasksConfigs pointing at them
DELETE FROM StandardTasksConfigs USING StandardTasksConfigs LEFT OUTER JOIN TasksConfigs ON taskTypePKReference=StandardTasksConfigs.pk WHERE TasksConfigs.pk is NULL;
