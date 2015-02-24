-- Insert default values into the ArchivesSpaceConfig table.
-- Leaving all other values null/blank is consistent with default ATK config.
INSERT INTO administration_archivesspaceconfig (pk, port) VALUES ('5e6b9fb2-0ed0-41c4-b5cb-94d25de1a5dc', 8089);

-- The new chain - begins with selecting config, then calls upload script.
-- The magic that pops open a new window happens in the dashboard UI,
-- and isn't handled here.
SET @archivesspace_upload_chain = '3572f844-5e69-4000-a24b-4e32d3487f82' COLLATE utf8_unicode_ci;
SET @archivesspace_select_config_tc = '5ded9d05-dd24-484a-a8b2-73ec5d35aa63' COLLATE utf8_unicode_ci;
SET @archivesspace_select_config_mscl = 'a0db8294-f02a-4f49-a557-b1310a715ffc' COLLATE utf8_unicode_ci;

-- Add the new DIP upload script
SET @archivesspace_upload_stc = '10a0f352-aeb7-4c13-8e9e-e81bda9bca29' COLLATE utf8_unicode_ci;
SET @archivesspace_upload_tc = '71eaef05-264d-453e-b8c4-7b7e2c7ac889' COLLATE utf8_unicode_ci;
SET @archivesspace_upload_mscl = 'ff89a530-0540-4625-8884-5a2198dea05a' COLLATE utf8_unicode_ci;

INSERT INTO StandardTasksConfigs (pk, execute, arguments, requiresOutputLock) VALUES (@archivesspace_upload_stc, 'upload-archivesspace_v0.0', '--host "%host%" --port "%port%" --user "%user%" --passwd "%passwd%" --dip_location "%SIPDirectory%" --dip_name "%SIPName%" --dip_uuid "%SIPUUID%" --restrictions "%restrictions%" --object_type "%object_type%" --xlink_actuate "%xlink_actuate%" --xlink_show "%xlink_show%" --use_statement "%use_statement%" --uri_prefix "%uri_prefix%" --access_conditions "%access_conditions%" --use_conditions "%use_conditions%"', 0);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@archivesspace_upload_tc, '36b2e239-4a57-4aa5-8ebc-7a29139baca6', @archivesspace_upload_stc, 'Upload to ArchivesSpace');
INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, microServiceGroup) VALUES (@archivesspace_upload_mscl, @archivesspace_upload_tc, 'e3efab02-1860-42dd-a46c-25601251b930', 'Upload DIP');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink) VALUES ('aa18a6d3-5d08-4827-99e7-b52abddcb812', @archivesspace_upload_mscl, 0, NULL);

-- MSCL for "choose config"
-- Empty string for taskTypePKReference is intentional;
-- this is consistent with ArchivistsToolkit.
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES (@archivesspace_select_config_tc, '9c84b047-9a6d-463f-9836-eafa49743b84', '', 'Choose Config for ArchivesSpace DIP Upload');
INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, microServiceGroup) VALUES (@archivesspace_select_config_mscl, @archivesspace_select_config_tc, @archivesspace_upload_mscl, 'Upload DIP');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink) VALUES ('1f53c86a-0afc-4eda-861d-c1501cb40e04', @archivesspace_select_config_mscl, 0, @archivesspace_upload_mscl);

-- Create a new chain, beginning with "choose config",
-- then insert a choice in the "Upload DIP?" choice
INSERT INTO MicroServiceChains (pk, startingLink, description) VALUES (@archivesspace_upload_chain, @archivesspace_select_config_mscl, 'Upload DIP to ArchivesSpace');
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable) VALUES ('96fecb69-c020-4b54-abfb-2b157afe5cdb', '92879a29-45bf-4f0b-ac43-e64474f0f2f9', @archivesspace_upload_chain);

-- Insert a dummy ReplacementDict for ArchivesSpace, which will be replaced
-- the first time the user saves anything in the settings
INSERT INTO MicroServiceChoiceReplacementDic (pk, choiceAvailableAtLink, description, replacementDic) VALUES ('f8749dd2-0923-4b57-a074-45cd92ace56f', @archivesspace_select_config_mscl, 'ArchivesSpace Config', '{"%port%": "8089", "%object_type%": "", "%host%": "localhost", "%xlink_show%": "new", "%use_statement%": "Image-Service", "%uri_prefix%": "http://www.example.com/", "%xlink_actuate%": "onRequest", "%access_conditions%": "", "%use_conditions%": "", "%restrictions%": "premis", "%passwd%": "admin", "%user%": "admin"}');
