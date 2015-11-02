ALTER TABLE `Files` ADD COLUMN `checksumType` VARCHAR(36) NULL AFTER `checksum`;
UPDATE `Files` SET `checksumType` = 'sha256' WHERE `checksumType` IS NULL;

-- Update updateSizeAndChecksum_v0.0 microservice to take a checksum type argument:
UPDATE StandardTasksConfigs SET arguments='--filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date% --checksumType "%checksumType%"' WHERE pk='0bdecdc8-f5ef-48dd-8a89-f937d2b3f2f9';
