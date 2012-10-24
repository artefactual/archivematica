SET @microserviceGroup  = 'Normalize';
-- create chain that loads the chain link for repeat norm --

SET @TasksConfig = 'ce52ace2-68fc-4bfb-8444-f32ec8c01783';
SET @TasksConfigPKReference = 'e56e168e-d339-45b4-bc2a-a3eb24390f0f';
SET @MicroServiceChainLink = 'b15c0ba6-e247-4512-8b56-860fd2b6299d';
SET @MicroServiceChainLinksExitCodes = '730c63c4-7b81-4710-a4d0-0efe49c14708';
SET @defaultNextChainLink = NULL;
SET @MicroServiceChain = 'cbe9b4a3-e4e6-4a32-8d7c-3adfc409cb6f';
INSERT INTO TasksConfigsUnitVariableLinkPull (pk, variable, variableValue)
    VALUES (@TasksConfigPKReference, 'reNormalize', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (@TasksConfig, 'c42184a3-1a7f-4c4d-b380-15d8d97fdd11', @TasksConfigPKReference, 'Determine what to remove to re-normalize.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (@MicroServiceChainLink, @microserviceGroup, @TasksConfig, @defaultNextChainLink);
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (@MicroServiceChainLinksExitCodes, @MicroServiceChainLink, 0, @defaultNextChainLink); 
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES (@MicroServiceChain, @MicroServiceChainLink,  'Redo normalization');
SET @MicroServiceChain2 = @MicroServiceChain;

-- add the option of that chain to both Approve normalizations --


/*
SELECT * FROM MicroServiceChainChoice WHERE choiceAvailableAtLink = 'de909a42-c5b5-46e1-9985-c031b50e9d30';
SELECT * FROM MicroServiceChainChoice WHERE choiceAvailableAtLink = '150dcb45-46c3-4529-b35f-b0a8a5a553e9';
*/

SET @MicroServiceChainChoice = 'a053c274-3047-40fa-b004-9f320ce0bb22';
SET @choiceAvailableAtLink = 'de909a42-c5b5-46e1-9985-c031b50e9d30';
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable) 
    VALUES (@MicroServiceChainChoice, @choiceAvailableAtLink, @MicroServiceChain);
    
SET @MicroServiceChainChoice = 'aa62acec-97ba-466c-8197-833a794c5bba';
SET @choiceAvailableAtLink = '150dcb45-46c3-4529-b35f-b0a8a5a553e9';
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable) 
    VALUES (@MicroServiceChainChoice, @choiceAvailableAtLink, @MicroServiceChain);

