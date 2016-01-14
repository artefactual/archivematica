-- Remove NULL values from boolena
UPDATE StandardTasksConfigs SET requiresOutputLock=False WHERE requiresOutputLock=NULL;

-- Delete MSCLs with no TasksConfig
DELETE FROM MicroServiceChainLinks WHERE pk IN ('0ca642b8-d6e7-4204-ac66-7209c3bae1b0', '0cc7077a-5c55-4229-ab7d-f92935e4f3d6', '0ceb8f18-8896-409b-891f-694c40d990fe', '0cf7efd6-5475-4eb2-b11c-ac796a59f1af', '0d381b64-dadd-4d3c-886e-8f4dd508e3a8', '0dd6144f-8ca8-4f0c-9596-0bb44f30065c', '0df8ce53-7a3b-4780-8bcc-2a8680130c88');

-- Add synthetic key to FPCommandOutput
CREATE INDEX `FPCommandOutput_ae27b939` ON `FPCommandOutput` (`fileUUID`);
ALTER TABLE FPCommandOutput DROP PRIMARY KEY;
ALTER TABLE FPCommandOutput ADD COLUMN `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY;

-- Add lastmodified to IDCommand
UPDATE fpr_idcommand SET lastmodified='2014-09-16T00:00:00Z' WHERE uuid='a8e45bc1-eb35-4545-885c-dd552f1fde9a';