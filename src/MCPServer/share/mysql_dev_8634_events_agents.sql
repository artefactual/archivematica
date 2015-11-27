-- Make Events and Agents many-to-many

-- Remove linkingAgentIdentifier
ALTER TABLE Events DROP COLUMN linkingAgentIdentifier;
-- TODO do data migration here

-- Add m2m table
-- SQL from Django
CREATE TABLE `Events_agents` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `event_id` bigint(20) unsigned NOT NULL,
    `agent_id` int(10) unsigned NOT NULL,
    UNIQUE (`event_id`, `agent_id`)
)
;

-- Add foreign key constraints
ALTER TABLE `Events_agents` ADD CONSTRAINT `event_id_refs_pk_ecd5fd57` FOREIGN KEY (`event_id`) REFERENCES `Events` (`pk`);
ALTER TABLE `Events_agents` ADD CONSTRAINT `agent_id_refs_pk_cec91718` FOREIGN KEY (`agent_id`) REFERENCES `Agents` (`pk`);
