
SET foreign_key_checks = 0;
DELETE FROM DefaultCommandsForClassifications;
DELETE FROM CommandRelationships;
DELETE FROM FileIDsBySingleID;
DELETE FROM FileIDGroupMembers;
DELETE FROM FileIDs;
DELETE FROM FileIDTypes;
DELETE FROM SubGroups;
DELETE FROM Groups;
DELETE FROM Commands;
DELETE FROM CommandClassifications;
DELETE FROM CommandTypes;
DELETE FROM CommandsSupportedBy;
SET foreign_key_checks = 1;
