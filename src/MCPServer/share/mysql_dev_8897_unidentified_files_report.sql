-- Add file extension column to Files table. This is used in the unidentified files report to group files together.
ALTER TABLE `Files` ADD COLUMN `extension` VARCHAR(128) NULL;
