-- Insert a "move to processing directory" immediately after "create tree";
-- this ensures that the transfer is not inside a watched directory when the
-- name is sanitized.
-- Without this, it's possible for the newly-named microservice to be picked up
-- as a new transfer, causing it to run through the microservice chain links
-- in this watched directory twice.
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('cb6cd728-fe54-4a50-a6cc-1c5bd9fa1198', 0, 'moveTransfer_v0.0', '"%SIPDirectory%" "%processingDirectory%." "%SIPUUID%" "%sharedPath%"');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('9f7029af-739d-4ec1-840d-b92d1d30f0c7', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', 'cb6cd728-fe54-4a50-a6cc-1c5bd9fa1198', 'Move to processing directory');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('6eca2676-b4ed-48d9-adb0-374e1d5c6e71', 'Generate transfer structure report', 'Failed', '9f7029af-739d-4ec1-840d-b92d1d30f0c7', '61c316a6-0a50-4f65-8767-1f44b1eeb6dd');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('310746b8-3580-40b7-a9ff-0730c8466fbb', '6eca2676-b4ed-48d9-adb0-374e1d5c6e71', 0, '56eebd45-5600-4768-a8c2-ec0114555a3d', 'Completed successfully');
UPDATE MicroServiceChains SET startingLink='6eca2676-b4ed-48d9-adb0-374e1d5c6e71' WHERE pk='f6df8882-d076-441e-bb00-2f58d5eda098';
