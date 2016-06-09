ALTER TABLE `Files` ADD COLUMN `checksumType` VARCHAR(36) NULL AFTER `checksum`;
UPDATE `Files` SET `checksumType` = 'sha256' WHERE `checksumType` IS NULL;
INSERT INTO DashboardSettings (name, value) VALUES ('checksum_type', 'sha256');

-- Expand checksum column so it can hold larger hashes (such as SHA-512)
ALTER TABLE `Files` CHANGE COLUMN `checksum` `checksum` VARCHAR(128) CHARACTER SET 'utf8' COLLATE 'utf8_unicode_ci' NULL DEFAULT NULL;

-- Remove checksumtype from create bag parameters
UPDATE StandardTasksConfigs SET arguments='create "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPDirectory%" "logs/" "objects/" "METS.%SIPUUID%.xml" "thumbnails/" "metadata/" --writer filesystem' WHERE pk='045f84de-2669-4dbc-a31b-43a4954d0481';
