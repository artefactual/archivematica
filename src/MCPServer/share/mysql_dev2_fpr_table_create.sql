BEGIN;
CREATE TABLE IF NOT EXISTS `fpr_format` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `uuid` varchar(36) NOT NULL UNIQUE,
    `description` varchar(128) NOT NULL,
    `group_id` varchar(36) NOT NULL,
    `slug` varchar(50) NOT NULL
)
;
CREATE TABLE IF NOT EXISTS `fpr_formatgroup` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `uuid` varchar(36) NOT NULL UNIQUE,
    `description` varchar(128) NOT NULL,
    `slug` varchar(50) NOT NULL
)
;
ALTER TABLE `fpr_format` ADD CONSTRAINT `group_id_refs_uuid_5f6777a9` FOREIGN KEY (`group_id`) REFERENCES `fpr_formatgroup` (`uuid`);
CREATE TABLE IF NOT EXISTS `fpr_formatversion` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `replaces_id` varchar(36),
    `enabled` bool NOT NULL,
    `uuid` varchar(36) NOT NULL UNIQUE,
    `format_id` varchar(36) NOT NULL,
    `description` varchar(128),
    `access_format` bool NOT NULL,
    `preservation_format` bool NOT NULL,
    `lastmodified` datetime NOT NULL,
    `slug` varchar(50) NOT NULL
)
;
ALTER TABLE `fpr_formatversion` ADD CONSTRAINT `format_id_refs_uuid_f14962b4` FOREIGN KEY (`format_id`) REFERENCES `fpr_format` (`uuid`);
ALTER TABLE `fpr_formatversion` ADD CONSTRAINT `replaces_id_refs_uuid_4a1558fd` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_formatversion` (`uuid`);
CREATE TABLE IF NOT EXISTS `fpr_idcommand` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `replaces_id` varchar(36),
    `enabled` bool NOT NULL,
    `uuid` varchar(36) NOT NULL UNIQUE,
    `description` varchar(256) NOT NULL,
    `script` longtext NOT NULL,
    `script_type` varchar(16) NOT NULL,
    `lastmodified` datetime NOT NULL
)
;
ALTER TABLE `fpr_idcommand` ADD CONSTRAINT `replaces_id_refs_uuid_dc5c8519` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_idcommand` (`uuid`);
CREATE TABLE IF NOT EXISTS `fpr_idrule` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `replaces_id` varchar(36),
    `enabled` bool NOT NULL,
    `uuid` varchar(36) NOT NULL UNIQUE,
    `command_id` varchar(36) NOT NULL,
    `format_id` varchar(36) NOT NULL,
    `command_output` longtext NOT NULL,
    `lastmodified` datetime NOT NULL
)
;
ALTER TABLE `fpr_idrule` ADD CONSTRAINT `command_id_refs_uuid_9f407367` FOREIGN KEY (`command_id`) REFERENCES `fpr_idcommand` (`uuid`);
ALTER TABLE `fpr_idrule` ADD CONSTRAINT `format_id_refs_uuid_419026e2` FOREIGN KEY (`format_id`) REFERENCES `fpr_formatversion` (`uuid`);
ALTER TABLE `fpr_idrule` ADD CONSTRAINT `replaces_id_refs_uuid_a57a01f5` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_idrule` (`uuid`);
CREATE TABLE IF NOT EXISTS `fpr_idtool` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `uuid` varchar(36) NOT NULL UNIQUE,
    `description` varchar(256) NOT NULL,
    `version` varchar(64) NOT NULL,
    `enabled` bool NOT NULL,
    `slug` varchar(50) NOT NULL
)
;
CREATE TABLE IF NOT EXISTS `fpr_idtoolconfig` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `replaces_id` varchar(36),
    `enabled` bool NOT NULL,
    `uuid` varchar(36) NOT NULL UNIQUE,
    `tool_id` varchar(36) NOT NULL,
    `config` varchar(4) NOT NULL,
    `command_id` varchar(36) NOT NULL,
    `lastmodified` datetime NOT NULL,
    `slug` varchar(50) NOT NULL
)
;
ALTER TABLE `fpr_idtoolconfig` ADD CONSTRAINT `command_id_refs_uuid_5a4f8385` FOREIGN KEY (`command_id`) REFERENCES `fpr_idcommand` (`uuid`);
ALTER TABLE `fpr_idtoolconfig` ADD CONSTRAINT `tool_id_refs_uuid_25ccc6cb` FOREIGN KEY (`tool_id`) REFERENCES `fpr_idtool` (`uuid`);
ALTER TABLE `fpr_idtoolconfig` ADD CONSTRAINT `replaces_id_refs_uuid_e2cc2a3d` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_idtoolconfig` (`uuid`);
CREATE TABLE IF NOT EXISTS `fpr_fprule` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `replaces_id` varchar(36),
    `enabled` bool NOT NULL,
    `uuid` varchar(36) NOT NULL UNIQUE,
    `purpose` varchar(16) NOT NULL,
    `command_id` varchar(36) NOT NULL,
    `format_id` varchar(36) NOT NULL,
    `lastmodified` datetime NOT NULL
)
;
ALTER TABLE `fpr_fprule` ADD CONSTRAINT `format_id_refs_uuid_365f2da7` FOREIGN KEY (`format_id`) REFERENCES `fpr_formatversion` (`uuid`);
ALTER TABLE `fpr_fprule` ADD CONSTRAINT `replaces_id_refs_uuid_50262b13` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_fprule` (`uuid`);
CREATE TABLE IF NOT EXISTS `fpr_fpcommand_tool` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `fpcommand_id` integer NOT NULL,
    `fptool_id` integer NOT NULL,
    UNIQUE (`fpcommand_id`, `fptool_id`)
)
;
CREATE TABLE IF NOT EXISTS `fpr_fpcommand` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `replaces_id` varchar(36),
    `enabled` bool NOT NULL,
    `uuid` varchar(36) NOT NULL UNIQUE,
    `description` varchar(256) NOT NULL,
    `command` longtext NOT NULL,
    `script_type` varchar(16) NOT NULL,
    `output_location` longtext,
    `output_format_id` varchar(36) NOT NULL,
    `command_usage` varchar(16) NOT NULL,
    `verification_command_id` varchar(36),
    `event_detail_command_id` varchar(36),
    `lastmodified` datetime NOT NULL
)
;
ALTER TABLE `fpr_fpcommand` ADD CONSTRAINT `output_format_id_refs_uuid_e187d88f` FOREIGN KEY (`output_format_id`) REFERENCES `fpr_formatversion` (`uuid`);
ALTER TABLE `fpr_fprule` ADD CONSTRAINT `command_id_refs_uuid_37ce2045` FOREIGN KEY (`command_id`) REFERENCES `fpr_fpcommand` (`uuid`);
ALTER TABLE `fpr_fpcommand_tool` ADD CONSTRAINT `fpcommand_id_refs_id_3cd7cf7b` FOREIGN KEY (`fpcommand_id`) REFERENCES `fpr_fpcommand` (`id`);
ALTER TABLE `fpr_fpcommand` ADD CONSTRAINT `replaces_id_refs_uuid_bd1394fd` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_fpcommand` (`uuid`);
ALTER TABLE `fpr_fpcommand` ADD CONSTRAINT `verification_command_id_refs_uuid_bd1394fd` FOREIGN KEY (`verification_command_id`) REFERENCES `fpr_fpcommand` (`uuid`);
ALTER TABLE `fpr_fpcommand` ADD CONSTRAINT `event_detail_command_id_refs_uuid_bd1394fd` FOREIGN KEY (`event_detail_command_id`) REFERENCES `fpr_fpcommand` (`uuid`);
CREATE TABLE IF NOT EXISTS `fpr_fptool` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `uuid` varchar(36) NOT NULL UNIQUE,
    `description` varchar(256) NOT NULL,
    `version` varchar(64) NOT NULL,
    `enabled` bool NOT NULL,
    `slug` varchar(50) NOT NULL
)
;
ALTER TABLE `fpr_fpcommand_tool` ADD CONSTRAINT `fptool_id_refs_id_b01f744b` FOREIGN KEY (`fptool_id`) REFERENCES `fpr_fptool` (`id`);
CREATE TABLE IF NOT EXISTS `Agent` (
    `uuid` varchar(36) NOT NULL PRIMARY KEY,
    `agentIdentifierType` varchar(100) NOT NULL,
    `agentIdentifierValue` varchar(100) NOT NULL,
    `agentName` varchar(100) NOT NULL,
    `agentType` varchar(100) NOT NULL,
    `clientIP` varchar(100) NOT NULL
)
;
CREATE TABLE IF NOT EXISTS `CommandType` (
    `pk` varchar(36) NOT NULL PRIMARY KEY,
    `replaces` varchar(50),
    `type` longtext NOT NULL,
    `lastModified` datetime NOT NULL,
    `enabled` integer
)
;
CREATE TABLE IF NOT EXISTS `Command` (
    `pk` varchar(36) NOT NULL PRIMARY KEY,
    `commandUsage` varchar(15) NOT NULL,
    `commandType` varchar(36) NOT NULL,
    `verificationCommand` varchar(36),
    `eventDetailCommand` varchar(36),
    `supportedBy` varchar(36),
    `command` longtext NOT NULL,
    `outputLocation` longtext,
    `description` longtext NOT NULL,
    `outputFileFormat` longtext,
    `replaces` varchar(36),
    `lastModified` datetime,
    `enabled` integer
)
;
CREATE TABLE IF NOT EXISTS `CommandsSupportedBy` (
    `pk` varchar(36) NOT NULL PRIMARY KEY,
    `description` longtext,
    `replaces` varchar(36),
    `lastModified` datetime NOT NULL,
    `enabled` integer
)
;
CREATE TABLE IF NOT EXISTS `FileIDType` (
    `pk` varchar(36) NOT NULL PRIMARY KEY,
    `description` longtext,
    `replaces` varchar(50),
    `lastModified` datetime NOT NULL,
    `enabled` integer
)
;
CREATE TABLE IF NOT EXISTS `FileID` (
    `pk` varchar(36) NOT NULL PRIMARY KEY,
    `description` longtext NOT NULL,
    `validPreservationFormat` integer,
    `validAccessFormat` integer,
    `fileidtype_id` varchar(36),
    `replaces` varchar(36),
    `lastModified` datetime NOT NULL,
    `enabled` integer,
    `format_id` varchar(36)
)
;
ALTER TABLE `FileID` ADD CONSTRAINT `format_id_refs_uuid_59596453` FOREIGN KEY (`format_id`) REFERENCES `fpr_formatversion` (`uuid`);
CREATE TABLE IF NOT EXISTS `CommandClassification` (
    `pk` varchar(36) NOT NULL PRIMARY KEY,
    `classification` longtext,
    `replaces` varchar(50),
    `lastModified` datetime NOT NULL,
    `enabled` integer
)
;
CREATE TABLE IF NOT EXISTS `CommandRelationship` (
    `pk` varchar(36) NOT NULL PRIMARY KEY,
    `commandClassification` varchar(36) NOT NULL,
    `command` varchar(36),
    `fileID` varchar(36),
    `replaces` varchar(36),
    `lastModified` datetime NOT NULL,
    `enabled` integer
)
;
CREATE TABLE IF NOT EXISTS `FileIDsBySingleID` (
    `pk` varchar(36) NOT NULL PRIMARY KEY,
    `fileID` varchar(36),
    `id` longtext NOT NULL,
    `tool` longtext NOT NULL,
    `toolVersion` longtext,
    `replaces` varchar(50),
    `lastModified` datetime NOT NULL,
    `enabled` integer
)
;
COMMIT;
