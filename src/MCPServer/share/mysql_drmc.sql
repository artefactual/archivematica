# Change name of chain

UPDATE MicroServiceChains set description='Upload to DRMC' WHERE description='Upload DIP to Atom';

# Add copy to NetX link
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('5b4b5329-c19c-4120-a7d7-290ff8e3410f', 0, 'copyToNetX_v0.0', '--uuid %SIPUUID%');

INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('a498e816-b263-4dda-8592-8e232509730e', '36b2e239-4a57-4aa5-8ebc-7a29139baca6', '5b4b5329-c19c-4120-a7d7-290ff8e3410f', 'Copy DIP to NetX');

INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('7f4e18eb-cf37-418b-b6db-d6f4e0aa9c27', 'Upload DIP', 'Failed', 'a498e816-b263-4dda-8592-8e232509730e', 'e3efab02-1860-42dd-a46c-25601251b930');

INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('4facf5ea-b0fe-4374-8651-1fa3f9ac0bb8', '7f4e18eb-cf37-418b-b6db-d6f4e0aa9c27', 0, 'e3efab02-1860-42dd-a46c-25601251b930', 'Completed successfully');

# Add chain that does a copy to NetX
INSERT INTO MicroServiceChains (pk, startingLink, description, replaces) VALUES ('f79080c5-f9a5-4b05-9d13-3880015c6f02', '7f4e18eb-cf37-418b-b6db-d6f4e0aa9c27', 'Copy DIP to NetX', NULL);

# Add chain that doesn't copy to NetX
INSERT INTO MicroServiceChains (pk, startingLink, description, replaces) VALUES ('3eee99e4-2532-43ec-bc5f-3c021182b265', 'e3efab02-1860-42dd-a46c-25601251b930', 'No Copy to NetX', NULL);

# Add chain choice link and options
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('52553a08-1c1d-4efa-baf9-d57698608c8a', '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c', '6ddac748-a6ec-410f-b5c1-89712bb0c2a3', 'Upload DIP');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) values ('884fc8aa-b1dc-484a-8ecc-abe828e04b89', 'Upload DIP', 'Failed', '52553a08-1c1d-4efa-baf9-d57698608c8a', 'e3efab02-1860-42dd-a46c-25601251b930');
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable, replaces) VALUES ('db70f543-26e1-4505-8d9f-0003e7ef2359', '884fc8aa-b1dc-484a-8ecc-abe828e04b89', 'f79080c5-f9a5-4b05-9d13-3880015c6f02', NULL);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable, replaces) VALUES ('ca8a274f-deb0-4ab4-8b2b-8bf88f08fbe3', '884fc8aa-b1dc-484a-8ecc-abe828e04b89', '3eee99e4-2532-43ec-bc5f-3c021182b265', NULL);

# Place chain choice link after DIP upload link
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='884fc8aa-b1dc-484a-8ecc-abe828e04b89' WHERE microServiceChainLink='651236d2-d77f-4ca7-bfe9-6332e96608ff';

-- MOMA CUSTOMIZATION - Normalization failures, issue 6845
UPDATE MicroServiceChainLinksExitCodes E
    SET E.exitMessage='Failed'
    WHERE E.exitCode = 1
    AND E.microServiceChainLink IN
        (SELECT MSCL.pk FROM MicroServiceChainLinks MSCL INNER JOIN TasksConfigs TC ON MSCL.currentTask = TC.pk WHERE description LIKE 'Normalize%');
-- /MOMA CUSTOMIZATION
