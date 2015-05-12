-- Remove the unused "Sounds" table and all foreign keys to it
ALTER TABLE MicroServiceChainLinks DROP FOREIGN KEY MicroServiceChainLinks_ibfk_3;
ALTER TABLE MicroServiceChainLinks DROP COLUMN defaultPlaySound;

ALTER TABLE MicroServiceChainLinksExitCodes DROP FOREIGN KEY MicroServiceChainLinksExitCodes_ibfk_3;
ALTER TABLE MicroServiceChainLinksExitCodes DROP COLUMN playSound;

DROP TABLE Sounds;
