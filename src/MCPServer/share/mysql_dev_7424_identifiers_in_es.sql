-- Compressed AIP path no longer needed in indexAIP;
-- instead pass the SIP directory, which contains the metadata files
UPDATE StandardTasksConfigs SET arguments='"%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%SIPType%"' WHERE pk='81f36881-9e54-4c75-a5b2-838cfb2ca228';

-- Don't delete the AIP METS, to avoid needing to re-extract it from the AIP
-- during indexAIP.
UPDATE StandardTasksConfigs SET arguments='-R "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"' WHERE pk='d12b6b59-1f1c-47c2-b1a3-2bf898740eae';
UPDATE StandardTasksConfigs SET arguments='-R "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"' WHERE pk='d17b25c7-f83c-4862-904b-8074150b1395';

-- Copies submission documentation back into the root of the SIP directory,
-- so it's available to be used by indexAIP without extraction from
-- a compressed AIP.
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('919dfbcd-b328-4a7e-9340-569a9d8859df', 0, 'copySubmissionDocs_v0.0', '"%SIPDirectory%" "%SIPName%-%SIPUUID%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('2894f4ea-0d11-431f-a7de-c2f765bd55a6', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '919dfbcd-b328-4a7e-9340-569a9d8859df', 'Copy submission documentation');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('0a63befa-327d-4655-a021-341b639ee9ed', 'Prepare AIP', 'Failed', '2894f4ea-0d11-431f-a7de-c2f765bd55a6', '7d728c39-395f-4892-8193-92f086c0546f');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('264fdc03-9102-4eb6-b671-09e48b136d27', '0a63befa-327d-4655-a021-341b639ee9ed', 0, '0915f727-0bc3-47c8-b9b2-25dc2ecef2bb', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='0a63befa-327d-4655-a021-341b639ee9ed' WHERE microServiceChainLink='d55b42c8-c7c5-4a40-b626-d248d2bd883f';

