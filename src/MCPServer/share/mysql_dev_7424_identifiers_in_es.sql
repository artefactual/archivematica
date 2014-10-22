-- Compressed AIP path no longer needed in indexAIP;
-- instead pass the SIP directory, which contains the metadata files
UPDATE StandardTasksConfigs SET arguments='"%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%SIPType%"' WHERE pk='81f36881-9e54-4c75-a5b2-838cfb2ca228';

-- Don't delete the AIP METS, to avoid needing to re-extract it from the AIP
-- during indexAIP.
UPDATE StandardTasksConfigs SET arguments='-R "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"' WHERE pk='d12b6b59-1f1c-47c2-b1a3-2bf898740eae';
UPDATE StandardTasksConfigs SET arguments='-R "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"' WHERE pk='d17b25c7-f83c-4862-904b-8074150b1395';
