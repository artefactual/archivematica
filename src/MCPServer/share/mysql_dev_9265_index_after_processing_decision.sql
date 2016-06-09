-- Remove the original "index transfer contents" microservice during ingest

SET @updateTransferIndex = 'd46f6af8-bc4e-4369-a808-c0fedb439fef' COLLATE utf8_unicode_ci;
SET @sendToBacklog = 'abd6d60c-d50f-4660-a189-ac1b34fafe85' COLLATE utf8_unicode_ci;

SET @index_transfer_contents = 'eb52299b-9ae6-4a1f-831e-c7eee0de829f' COLLATE utf8_unicode_ci;
SET @create_transfer_metadata_xml = 'db99ab43-04d7-44ab-89ec-e09d7bbdc39d' COLLATE utf8_unicode_ci;

-- "Check for specialized processing" should point at the chainlink after indexing
UPDATE TasksConfigsUnitVariableLinkPull
    SET defaultMicroServiceChainLink=@create_transfer_metadata_xml
    WHERE defaultMicroServiceChainLink=@index_transfer_contents;

-- "Identify DSpace METS file" should point at the chainlink after indexing
UPDATE MicroServiceChainLinks
    SET defaultNextChainLink=@create_transfer_metadata_xml
    WHERE pk='8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc';
UPDATE MicroServiceChainLinksExitCodes
    SET nextMicroServiceChainLink=@create_transfer_metadata_xml
    WHERE nextMicroServiceChainLink=@index_transfer_contents;

-- Delete STC from the old indexing MSCL, and exit codes rows
DELETE FROM StandardTasksConfigs WHERE pk='2c9fd8e4-a4f9-4aa6-b443-de8a9a49e396';
DELETE FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink=@index_transfer_contents;

-- Instead of updating the status of the file in the backlog,
-- index the files freshly with a "backlog" status
UPDATE TasksConfigs
    SET description='Index transfer contents'
    WHERE pk='d6a0dec1-63e7-4c7c-b4c0-e68f0afcedd3';

UPDATE StandardTasksConfigs
    SET execute='elasticSearchIndex_v0.0',
        arguments='"%SIPDirectory%" "%SIPUUID%" "backlog"'
    WHERE pk='16ce41d9-7bfa-4167-bca8-49fe358f53ba';

-- Also move this MSCL to the beginning of the "send to backlog" chain,
-- since it requires having the files still physically accessible
UPDATE MicroServiceChains
    SET startingLink=@updateTransferIndex
    WHERE startingLink=@sendToBacklog;

UPDATE MicroServiceChainLinksExitCodes
    SET nextMicroServiceChainLink=@sendToBacklog
    WHERE microServiceChainLink=@updateTransferIndex;

-- Finally, mark nextMicroServiceChainLink as null for the new last link
UPDATE MicroServiceChainLinksExitCodes
    SET nextMicroServiceChainLink=NULL
    WHERE microServiceChainLink='561bbb52-d95c-4004-b0d3-739c0a65f406';
