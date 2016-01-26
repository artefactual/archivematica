-- Set task types PKs

SET @get_microservice_generated_list = 'a19bfd9f-9989-4648-9351-013a10b382ed' COLLATE utf8_unicode_ci;
SET @user_choice_from_microservice_generated_list = '01b748fe-2e9d-44e4-ae5d-113f74c9a0ba' COLLATE utf8_unicode_ci;
SET @get_user_choice_to_proceed_with = '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c' COLLATE utf8_unicode_ci;
SET @one_instance = '36b2e239-4a57-4aa5-8ebc-7a29139baca6' COLLATE utf8_unicode_ci;


-- Set chain PKs

SET @dip_store_chain_pk = '8d29eb3d-a8a8-4347-806e-3d8227ed44a1' COLLATE utf8_unicode_ci;
SET @dip_nop_chain_pk = '4500f34e-f004-4ccf-8720-5c38d0be2254' COLLATE utf8_unicode_ci;


-- Set link, task, etc. PKs

SET @dip_store_retrieve_locations_link_pk = 'd026e5a4-96cf-4e4c-938d-a74b0d211da0' COLLATE utf8_unicode_ci;
SET @dip_store_retrieve_locations_task_pk = '152c3590-7ac2-4195-9247-519ec31b6dd9' COLLATE utf8_unicode_ci;
SET @dip_store_retrieve_locations_standard_task_pk = '1c6a1a4b-9cc5-4002-8fe9-531392eb6fe3' COLLATE utf8_unicode_ci;

SET @dip_store_location_link_pk = 'cd844b6e-ab3c-4bc6-b34f-7103f88715de' COLLATE utf8_unicode_ci;
SET @dip_store_location_task_pk = 'bffda97e-9c4e-454d-87b6-88f92668f868' COLLATE utf8_unicode_ci;
SET @dip_store_location_standard_task_pk = '4368d9c2-1942-4aa6-813b-eb178732b76f' COLLATE utf8_unicode_ci;

SET @dip_store_link_pk = '653b134f-4a37-4578-a286-7f2072e89f9e' COLLATE utf8_unicode_ci;
SET @dip_store_task_pk = '2dd14de8-62c7-49a5-bfa1-dd025e7a426b' COLLATE utf8_unicode_ci;
SET @dip_store_standard_task_pk = 'some pk' COLLATE utf8_unicode_ci;

SET @dip_move_link_pk = '2e31580d-1678-474b-83e5-a53d97d150f6' COLLATE utf8_unicode_ci;
SET @dip_move_task_pk = 'a5b3b592-6139-4e9f-a94f-9679f5388eb8' COLLATE utf8_unicode_ci;
SET @dip_move_standard_task_pk = '07ad26c8-678f-4cfa-bc48-c0825fc6da21' COLLATE utf8_unicode_ci;

SET @dip_store_choice_link_pk = '5e58066d-e113-4383-b20b-f301ed4d751c' COLLATE utf8_unicode_ci;
SET @dip_store_choice_task_pk = 'abf861ee-2125-4e7e-8d85-9e1dcd020b4b' COLLATE utf8_unicode_ci;

SET @email_fail_report_link_pk = '7d728c39-395f-4892-8193-92f086c0546f' COLLATE utf8_unicode_ci;
SET @move_to_uploaded_dir_link_pk = 'e3efab02-1860-42dd-a46c-25601251b930' COLLATE utf8_unicode_ci;

SET @nop_link_pk = 'f8ee488b-5667-4417-ae15-bed9e42ee97d' COLLATE utf8_unicode_ci;
SET @nop_task_pk = '79ba8ce2-d01a-4723-83b7-5ac2b9ab2ae9' COLLATE utf8_unicode_ci;
SET @nop_standard_task_pk = '888281a1-9678-46ed-a1a0-be9f0c6d02b0' COLLATE utf8_unicode_ci;


-- Third link in chain to store DIP after upload: store DIP

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, lastModified) VALUES (@dip_store_standard_task_pk, 1, 'storeAIP_v0.0', '"%DIPsStore%" "%watchDirectoryPath%uploadedDIPs/%SIPName%-%SIPUUID%" "%SIPUUID%" "%SIPName%" "DIP"', '2014-09-11 09:09:53');

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description, lastModified) VALUES (@dip_store_task_pk, @one_instance, @dip_store_standard_task_pk, 'Store DIP', '2014-09-11 09:09:53');

INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, microserviceGroup, reloadFileList, defaultExitMessage, lastModified) VALUES (@dip_store_link_pk, @dip_store_task_pk, @email_fail_report_link_pk, 'Upload DIP', 1, 'Failed', '2014-09-11 09:09:53');

INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage, lastModified) VALUES ('8d0f7de9-8efa-4574-868c-bc85ddeea1d9', @dip_store_link_pk, 0, NULL, 'Completed successfully', '2014-09-11 09:09:53');

-- Second link in chain to store DIP after upload: ask for store DIP location

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, lastModified) VALUES (@dip_store_location_standard_task_pk, 1, '%DIPsStore%', '2014-09-11 09:09:53');

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description, lastModified) VALUES (@dip_store_location_task_pk, @user_choice_from_microservice_generated_list, @dip_store_location_standard_task_pk, 'Store DIP location', '2014-09-11 09:09:53');

INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, microserviceGroup, reloadFileList, defaultExitMessage, lastModified) VALUES (@dip_store_location_link_pk, @dip_store_location_task_pk, @email_fail_report_link_pk, 'Upload DIP', 1, 'Failed', '2014-09-11 09:09:53');

INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage, lastModified) VALUES ('7d7455e7-ca01-4ff9-ab7e-f50ab70623f1', @dip_store_location_link_pk, 0, @dip_store_link_pk, 'Completed successfully', '2014-09-11 09:09:53');

-- First link in chain to store DIP after upload: retrieve storage locations

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, lastModified) VALUES (@dip_store_retrieve_locations_standard_task_pk, 1, 'getAipStorageLocations_v0.0', 'DS', '2014-09-11 09:09:53');

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description, lastModified) VALUES (@dip_store_retrieve_locations_task_pk, @get_microservice_generated_list, @dip_store_retrieve_locations_standard_task_pk, 'Retrieve DIP Storage Locations', '2014-09-11 09:09:53');

INSERT INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, microserviceGroup, reloadFileList, defaultExitMessage, lastModified) VALUES (@dip_store_retrieve_locations_link_pk, @dip_store_retrieve_locations_task_pk, @email_fail_report_link_pk, 'Upload DIP', 1, 'Failed', '2014-09-11 09:09:53');

INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage, lastModified) VALUES ('fc9b0f42-6893-4806-b575-ec954cd1c43d', @dip_store_retrieve_locations_link_pk, 0, @dip_store_location_link_pk, 'Completed successfully', '2014-09-11 09:09:53');

-- New chain to store DIP after upload

INSERT INTO MicroServiceChains (pk, startingLink, description, lastModified) VALUES ('8d29eb3d-a8a8-4347-806e-3d8227ed44a1', @dip_store_retrieve_locations_link_pk, 'Store DIP', '2014-09-11 09:09:53');


-- Link in chain for confirming post-upload completion without storage

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, lastModified) VALUES (@nop_standard_task_pk, 0, 'echo_v0.0', '"Completed."', '2012-10-01 17:25:01');

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description, lastModified) VALUES (@nop_task_pk, @one_instance, @nop_standard_task_pk, 'Completed', '2012-10-01 17:25:11');

INSERT INTO MicroServiceChainLinks (pk, currentTask, microserviceGroup, reloadFileList, defaultExitMessage, lastModified) VALUES (@nop_link_pk, @nop_task_pk, 'Upload DIP', 1, 'Failed', '2012-10-01 17:25:06');

INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage, lastModified) VALUES ('fc8b0f42-6893-4806-b575-ec954cd1c43d', @nop_link_pk, 0, NULL, 'Completed successfully', '2014-09-11 09:09:53');

-- New chain for confirming post-upload completion without storage

INSERT INTO MicroServiceChains (pk, startingLink, description, lastModified) VALUES (@dip_nop_chain_pk, @nop_link_pk, 'Do not store', '2014-09-11 09:09:53');


-- Second link in store DIP choice chain: choose whether to store DIP

INSERT INTO TasksConfigs (pk, taskType, description, lastModified) VALUES (@dip_store_choice_task_pk, @get_user_choice_to_proceed_with, 'Store DIP?', '2012-10-01 17:25:11');

INSERT INTO MicroServiceChainLinks (pk, currentTask, microserviceGroup, reloadFileList, defaultExitMessage, lastModified) VALUES (@dip_store_choice_link_pk, @dip_store_choice_task_pk, 'Upload DIP', 1, 'Failed', '2012-10-01 17:25:06');

INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable, lastModified) VALUES ('6ffac4ac-7b5c-4ebb-880c-ecc7588c0b51', @dip_store_choice_link_pk, @dip_store_chain_pk, '2014-09-11 09:09:53');

INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable, lastModified) VALUES ('6ffac4ac-7b5c-4ebb-880c-ecc7588c0b50', @dip_store_choice_link_pk, @dip_nop_chain_pk, '2014-09-11 09:09:53');

-- First link in store DIP choice chain: copy to uploadedDIPs

INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments, lastModified) VALUES (@dip_move_standard_task_pk, 0, 'move_v0.0', '"%SIPDirectory%" "%watchDirectoryPath%uploadedDIPs/."', '2012-10-01 17:25:01');

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description, lastModified) VALUES (@dip_move_task_pk, @one_instance, @dip_move_standard_task_pk, 'Move to the uploadedDIPs directory', '2012-10-01 17:25:11');

INSERT INTO MicroServiceChainLinks (pk, currentTask, microserviceGroup, reloadFileList, defaultExitMessage, lastModified) VALUES (@dip_move_link_pk, @dip_move_task_pk, 'Upload DIP', 1, 'Failed', '2012-10-01 17:25:06');

INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage, lastModified) VALUES ('c4bd05e3-d7b9-4c67-a153-40b760e30eb7', @dip_move_link_pk, 0, @dip_store_choice_link_pk, 'Completed successfully', '2012-10-01 17:25:07');

-- New chain for choice as to whether to store DIP after upload

INSERT INTO MicroServiceChains (pk, startingLink, description, lastModified) VALUES ('d456dfde-1cdb-4178-babc-1a4537fe1b87', @dip_move_link_pk, 'Store DIP', '2014-09-11 09:09:53');


-- Update upload links to direct to new chain
SET @upload_atom_tail = '651236d2-d77f-4ca7-bfe9-6332e96608ff' COLLATE utf8_unicode_ci;
SET @upload_cdm_tail = 'f12ece2c-fb7e-44de-ba87-7e3c5b6feb74' COLLATE utf8_unicode_ci;
SET @upload_atk_tail = 'bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1' COLLATE utf8_unicode_ci;
SET @store_start_link_pk = @dip_move_link_pk COLLATE utf8_unicode_ci;

UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink = @store_start_link_pk where microServiceChainLink IN (@upload_atom_tail, @upload_cdm_tail, @upload_atk_tail);
