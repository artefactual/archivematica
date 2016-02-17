-- Add SIPUUID argument to restructureForCompliance_v0.0
UPDATE `StandardTasksConfigs` SET `arguments` = '"%SIPDirectory%" "%SIPUUID%"' WHERE `execute` = 'restructureForCompliance_v0.0';

-- Add sharedPath argument to updateSizeAndChecksum_v0.0
UPDATE `StandardTasksConfigs` SET `arguments` = '"%sharedPath%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"' WHERE `execute` = 'updateSizeAndChecksum_v0.0';
