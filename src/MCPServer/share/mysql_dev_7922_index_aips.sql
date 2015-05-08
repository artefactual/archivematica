
-- Remove 'remove indexed files' from rejected Store AIP
UPDATE MicroServiceChains SET startingLink='f2e784a0-356b-4b92-9a5a-11887aa3cf48' WHERE pk='433f4e6b-1ef4-49f8-b1e4-49693791a806';
SET @removeIndexedAIPFiles='bfade79c-ab7b-11e2-bace-08002742f837' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@removeIndexedAIPFiles;

-- Remove elasticSearchIndexProcessAIP links (contents have been merged into indexAIP)
SET @indexAIPfiles='3ba518ab-fc47-4cba-9b5c-79629adac10b' COLLATE utf8_unicode_ci;
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='3e25bda6-5314-4bb4-aa1e-90900dce887d' WHERE nextMicroServiceChainLink=@indexAIPfiles;
UPDATE MicroServiceChainLinks SET defaultNextChainLink='3e25bda6-5314-4bb4-aa1e-90900dce887d' WHERE defaultNextChainLink=@indexAIPfiles;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@indexAIPfiles;
