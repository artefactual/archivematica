-- these delete statements are optinal - they remove rows from the
-- MicroServiceChainLinks table that are no longer used by Archivematica
-- if your database has Jobs that reference any of these ChainLinks,
-- then you will not be able to delete those particular ChainLinks
-- which is fine.

-- Don't use weird normalization node, remove unitVars for that
SET @d1 = '29dece8e-55a4-4f2c-b4c2-365ab6376ceb' COLLATE utf8_unicode_ci;
SET @d2 = '635ba89d-0ad6-4fc9-acc3-e6069dffdcd5' COLLATE utf8_unicode_ci;
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink IN (@d1, @d2);
DELETE FROM MicroServiceChainLinks WHERE pk IN (@d1, @d2);
