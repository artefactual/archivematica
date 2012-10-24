SET @microserviceGroup  = 'Normalize';

-- resume on resume after tool selected --
INSERT INTO TasksConfigsUnitVariableLinkPull (pk, variable, variableValue)
    VALUES ('003b52a6-f80a-409c-95f9-82dd770aa132', 'resumeAfterNormalizationFileIdentificationToolSelected', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('26ec68d5-8d33-4fe2-bc11-f06d80fb23e0', 'c42184a3-1a7f-4c4d-b380-15d8d97fdd11', '003b52a6-f80a-409c-95f9-82dd770aa132', 'Resume after normalization file identification tool selected.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('83484326-7be7-4f9f-b252-94553cd42370', @microserviceGroup, '26ec68d5-8d33-4fe2-bc11-f06d80fb23e0', NULL);
SET @MicroServiceChainLink = '83484326-7be7-4f9f-b252-94553cd42370';
/* INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('8c712075-1cf9-4a59-93ab-71af69b7ac90', @MicroServiceChainLink, 0, NULL); */
SET @NextMicroServiceChainLink = @MicroServiceChainLink;



-- set variable tool --

-- set variable tool 1 --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('4093954b-5e44-4fe9-9a47-14c82158a00d', 'normalizationFileIdentificationToolIdentifierTypes', 'FileIDTypes.pk = \'ac5d97dc-df9e-48b2-81c5-4a8b044355fa\' OR FileIDTypes.pk = \'f794555f-50ad-4fd4-9eab-67bc47c431ab\'', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('b8c10f19-40c9-44c8-8b9f-6fab668513f5', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', '4093954b-5e44-4fe9-9a47-14c82158a00d', 'Set SIP to normalize with FITS-Droid file identification.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('56b42318-3eb3-466c-8a0d-7ac272136a96', @microserviceGroup, 'b8c10f19-40c9-44c8-8b9f-6fab668513f5', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = '56b42318-3eb3-466c-8a0d-7ac272136a96';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('0a3282be-d556-427a-9415-29cda78bb273', @MicroServiceChainLink, 0, '83484326-7be7-4f9f-b252-94553cd42370');
INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES ('c44e0251-1c69-482d-a679-669b70d09fb1', @MicroServiceChainLink,  'DROID');
SET @ToolMicroServiceChain1 = 'c44e0251-1c69-482d-a679-669b70d09fb1';


-- set variable tool 2 --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('f130c16d-d419-4063-8c8b-2e4c3ad138bb', 'normalizationFileIdentificationToolIdentifierTypes', 'FileIDTypes.pk = \'afdbee13-eec5-4182-8c6c-f5638ee290f3\'', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('1e516ea6-6814-4292-9ea9-552ebfaa0d23', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', 'f130c16d-d419-4063-8c8b-2e4c3ad138bb', 'Set SIP to normalize with FIDO file identification.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('982229bd-73b8-432e-a1d9-2d9d15d7287d', @microserviceGroup, '1e516ea6-6814-4292-9ea9-552ebfaa0d23', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = '982229bd-73b8-432e-a1d9-2d9d15d7287d';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('82c97f8d-087d-4636-9dd9-59bbc04e6520', @MicroServiceChainLink, 0, '83484326-7be7-4f9f-b252-94553cd42370');
INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES ('c76624a8-6f85-43cf-8ea7-0663502c712f', @MicroServiceChainLink,  'FIDO');
SET @ToolMicroServiceChain2 = 'c76624a8-6f85-43cf-8ea7-0663502c712f';

-- set variable tool 3 --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('202e00f4-595e-41fb-9a96-b8ec8c76318e', 'normalizationFileIdentificationToolIdentifierTypes', 'FileIDTypes.pk = \'16ae42ff-1018-4815-aac8-cceacd8d88a8\'', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('04806cbd-d146-46e9-b3b6-1bd664636057', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', '202e00f4-595e-41fb-9a96-b8ec8c76318e', 'Set SIP to normalize with file extension file identification.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('b549130c-943b-4791-b1f6-93b837990138', @microserviceGroup, '04806cbd-d146-46e9-b3b6-1bd664636057', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = 'b549130c-943b-4791-b1f6-93b837990138';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('98793316-123f-47a1-a789-d57df73f2f46', @MicroServiceChainLink, 0, '83484326-7be7-4f9f-b252-94553cd42370');
INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES ('229e34d9-3768-4b78-97b7-6cd4a2f07868', @MicroServiceChainLink,  'file extension');
SET @ToolMicroServiceChain3 = '229e34d9-3768-4b78-97b7-6cd4a2f07868';

-- set variable tool 4 --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('9329d1d8-03f9-4c5e-81ec-7010552d0a3e', 'normalizationFileIdentificationToolIdentifierTypes', 'FileIDTypes.pk = \'076cce1b-9b46-4343-a193-11c2662c9e02\' OR FileIDTypes.pk = \'237d393f-aba2-44ae-b61c-76232d383883\'', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('0732af8f-d60b-43e0-8f75-8e89039a05a8', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', '9329d1d8-03f9-4c5e-81ec-7010552d0a3e', 'Set SIP to normalize with FITS-file utility file identification.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('f87f13d2-8aae-45c9-bc8a-e5c32a37654e', @microserviceGroup, '0732af8f-d60b-43e0-8f75-8e89039a05a8', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = 'f87f13d2-8aae-45c9-bc8a-e5c32a37654e';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('6e803217-232b-4b5f-a1a4-306fd1b8cb08', @MicroServiceChainLink, 0, '83484326-7be7-4f9f-b252-94553cd42370');
INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES ('50f47870-3932-4a88-879d-d021a24758ad', @MicroServiceChainLink,  'file utility');
SET @ToolMicroServiceChain4 = '50f47870-3932-4a88-879d-d021a24758ad';

-- set variable tool 5 --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('6c02936d-552a-415e-b3c1-6d681b01d1c6', 'normalizationFileIdentificationToolIdentifierTypes', 'FileIDTypes.pk = \'8e39a076-d359-4c60-b6f4-38f7ae6adcdf\'', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('b5e6340f-07f3-4ed1-aada-7a7f049b19b9', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', '6c02936d-552a-415e-b3c1-6d681b01d1c6', 'Set SIP to normalize with FITS-ffident file identification.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('37f2e794-6485-4524-a384-37b3209916ed', @microserviceGroup, 'b5e6340f-07f3-4ed1-aada-7a7f049b19b9', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = '37f2e794-6485-4524-a384-37b3209916ed';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('262c7658-0073-4638-899c-a97e6f3ad0ae', @MicroServiceChainLink, 0, '83484326-7be7-4f9f-b252-94553cd42370');
INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES ('1d8836cf-ac02-437c-9283-4ddb7b018810', @MicroServiceChainLink,  'ffident');
SET @ToolMicroServiceChain5 = '1d8836cf-ac02-437c-9283-4ddb7b018810';

-- set variable tool 6 --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('face6ee9-42d5-46ff-be1b-a645594b2da8', 'normalizationFileIdentificationToolIdentifierTypes', 'FileIDTypes.pk = \'b0bcccfb-04bc-4daa-a13c-77c23c2bda85\' OR FileIDTypes.pk = \'dc551ed2-9d2f-4c8a-acce-760fb740af48\'', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('76135f22-6dba-417f-9833-89ecbe9a3d99', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', 'face6ee9-42d5-46ff-be1b-a645594b2da8', 'Set SIP to normalize with FITS-JHOVE file identification.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('766b23ad-65ed-46a3-aa2e-b9bdaf3386d0', @microserviceGroup, '76135f22-6dba-417f-9833-89ecbe9a3d99', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = '766b23ad-65ed-46a3-aa2e-b9bdaf3386d0';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('84771d70-62b1-4894-b369-be58937dab49', @MicroServiceChainLink, 0, '83484326-7be7-4f9f-b252-94553cd42370');
INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES ('d607f083-7c86-49a2-bc36-06a03db28a80', @MicroServiceChainLink,  'JHOVE');
SET @ToolMicroServiceChain6 = 'd607f083-7c86-49a2-bc36-06a03db28a80';

-- set variable tool 7 --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('be6dda53-ef28-42dd-8452-e11734d57a91', 'normalizationFileIdentificationToolIdentifierTypes', 'FileIDTypes.pk = \'9ffdc6e8-f25a-4e5b-aaca-02769c4e7b7f\' ', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('008e5b38-b19c-48af-896f-349aaf5eba9f', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', 'be6dda53-ef28-42dd-8452-e11734d57a91', 'Set SIP to normalize with mediainfo file identification.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('5bddbb67-76b4-4bcb-9b85-a0d9337e7042', @microserviceGroup, '008e5b38-b19c-48af-896f-349aaf5eba9f', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = '5bddbb67-76b4-4bcb-9b85-a0d9337e7042';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('46a6cc67-e0cb-4390-bb6c-d52ca48849f7', '5bddbb67-76b4-4bcb-9b85-a0d9337e7042', 0, '83484326-7be7-4f9f-b252-94553cd42370');
INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES ('09949bda-5332-482a-ae47-5373bd372174', @MicroServiceChainLink,  'mediainfo');
SET @ToolMicroServiceChain7 = '09949bda-5332-482a-ae47-5373bd372174';

-- set variable tool 8 --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('42e656d6-4816-417f-b45e-92dadd0dfde5', 'normalizationFileIdentificationToolIdentifierTypes', 'FileIDTypes.pk = \'1d8f3bb3-da8a-4ef6-bac7-b65942df83fc\'', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('582883b9-9338-4e73-8873-371b666038fe', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', '42e656d6-4816-417f-b45e-92dadd0dfde5', 'Set SIP to normalize with Tika file identification.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('5fbecef2-49e9-4585-81a2-267b8bbcd568', @microserviceGroup, '582883b9-9338-4e73-8873-371b666038fe', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = '5fbecef2-49e9-4585-81a2-267b8bbcd568';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('4e8ea9d2-243e-4a31-9b42-f9f8522b3ffb', '5fbecef2-49e9-4585-81a2-267b8bbcd568', 0, '83484326-7be7-4f9f-b252-94553cd42370');
INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES ('46824987-bd47-4139-9871-6566f5abdf1a', @MicroServiceChainLink,  'Tika');
SET @ToolMicroServiceChain8 = '46824987-bd47-4139-9871-6566f5abdf1a';

-- set variable tool 9 --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('471ff5ad-1fd3-4540-9245-360cc8c9b389', 'normalizationFileIdentificationToolIdentifierTypes', 'FileIDTypes.pk = \'c26227f7-fca8-4d98-9d8e-cfab86a2dd0a\' OR FileIDTypes.pk = \'cff7437f-20c6-440a-b801-37c647da2cf1\'', NULL);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('c87ec738-b679-4d8e-8324-73038ccf0dfd', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', '471ff5ad-1fd3-4540-9245-360cc8c9b389', 'Set SIP to normalize with FITS-FITS file identification.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('d7a0e33d-aa3c-435f-a6ef-8e39f2e7e3a0', @microserviceGroup, 'c87ec738-b679-4d8e-8324-73038ccf0dfd', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = 'd7a0e33d-aa3c-435f-a6ef-8e39f2e7e3a0';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('8d16a0ee-e781-4f8d-953f-e5876c723796', 'd7a0e33d-aa3c-435f-a6ef-8e39f2e7e3a0', 0, '83484326-7be7-4f9f-b252-94553cd42370');
INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES ('586006d1-f3af-4b5f-9f1a-c893244fa7a9', @MicroServiceChainLink,  'FITS');
SET @ToolMicroServiceChain9 = '586006d1-f3af-4b5f-9f1a-c893244fa7a9';

/* 
-- set variable tool x --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('', 'normalizationFileIdentificationToolIdentifierTypes', '', NULL);
INSERT INTO TasksConfigs (pk, tas           kType, taskTypePKReference, description)
    VALUES
    ('', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', LAST_INSERT_ID(), 'Set SIP to normalize with FITS- file identification.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('', @microserviceGroup, LAST_INSERT_ID(), @NextMicroServiceChainLink);
SET @MicroServiceChainLink = LAST_INSERT_ID();

INSERT INTO MicroServiceChains (pk, startingLink, description) 
    VALUES ('', @MicroServiceChainLink,  'Do not normalize');
SET @ToolMicroServiceChain# = LAST_INSERT_ID();
*/

-- split on choice --
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('85a2ec9b-5a80-497b-af60-04926c0bf183', '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',      NULL, 'Identify');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('f4dea20e-f3fe-4a37-b20f-0e70a7bc960e', @microserviceGroup, '85a2ec9b-5a80-497b-af60-04926c0bf183', NULL);
SET @MicroServiceChainLink = 'f4dea20e-f3fe-4a37-b20f-0e70a7bc960e';
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES
    ('45bf3f08-9db6-4ced-bd7b-ee60c901176c', @MicroServiceChainLink, @ToolMicroServiceChain1);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES
    ('e95b8f27-ea52-4247-bdf0-615273bc5fca', @MicroServiceChainLink, @ToolMicroServiceChain2);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES
    ('3b2a1c62-a967-44f8-9f5e-855a0d8ff2c1', @MicroServiceChainLink, @ToolMicroServiceChain3);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES
    ('ae708d67-c806-47f7-a76e-7598299aa656', @MicroServiceChainLink, @ToolMicroServiceChain4);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES
    ('8da1a706-61e7-40d7-ade3-9fcba9364543', @MicroServiceChainLink, @ToolMicroServiceChain5);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES
    ('9063783c-0bda-4488-b2ac-e8f7bd48973c', @MicroServiceChainLink, @ToolMicroServiceChain6);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES
    ('8240d294-ad72-4a7f-8c67-6777e165a642', @MicroServiceChainLink, @ToolMicroServiceChain7);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES
    ('44304ff6-86f9-444e-975f-e578c7f3d15a', @MicroServiceChainLink, @ToolMicroServiceChain8);
INSERT INTO MicroServiceChainChoice (pk, choiceAvailableAtLink, chainAvailable)
    VALUES
    ('98ed7059-9fe4-4dc1-bc81-fb9b51ddecc2', @MicroServiceChainLink, @ToolMicroServiceChain9);
SET @NextMicroServiceChainLink = @MicroServiceChainLink;


-- set resume after tool selected --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('f85bbe03-8aca-4211-99b7-ddb7dfb24da1', 'resumeAfterNormalizationFileIdentificationToolSelected', NULL, 'cb8e5706-e73f-472f-ad9b-d1236af8095f');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('e62e4b85-e3f1-4550-8e40-3939e6497e92', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', 'f85bbe03-8aca-4211-99b7-ddb7dfb24da1', 'Set resume link after tool selected.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('c73acd63-19c9-4ca8-912c-311107d0454e', @microserviceGroup, 'e62e4b85-e3f1-4550-8e40-3939e6497e92', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = 'c73acd63-19c9-4ca8-912c-311107d0454e';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('2a478b90-5f0c-45c0-91fe-099e8389096c', @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink2 = @MicroServiceChainLink;


-- set resume after tool selected --
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES ('1871a1a5-1937-4c4d-ab05-3b0c04a0bca1', 'resumeAfterNormalizationFileIdentificationToolSelected', NULL, '7509e7dc-1e1b-4dce-8d21-e130515fce73');
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    ('e476ac7e-d3e8-43fa-bb51-5a9cf42b2713', '6f0b612c-867f-4dfd-8e43-5b35b7f882d7', '1871a1a5-1937-4c4d-ab05-3b0c04a0bca1', 'Set resume link after tool selected.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES ('f63970a2-dc63-4ab4-80a6-9bfd72e3cf5a', @microserviceGroup, 'e476ac7e-d3e8-43fa-bb51-5a9cf42b2713', @NextMicroServiceChainLink);
SET @MicroServiceChainLink = 'f63970a2-dc63-4ab4-80a6-9bfd72e3cf5a';
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES ('30d5cb9f-6d0e-40d3-9d64-1632f98770fc', @MicroServiceChainLink, 0, @NextMicroServiceChainLink);
SET @NextMicroServiceChainLink3 = @MicroServiceChainLink;


-- SET THE magic chain links --
UPDATE TasksConfigsAssignMagicLink SET execute=@NextMicroServiceChainLink2 WHERE execute='cb8e5706-e73f-472f-ad9b-d1236af8095f';
UPDATE TasksConfigsAssignMagicLink SET execute=@NextMicroServiceChainLink3 WHERE execute='7509e7dc-1e1b-4dce-8d21-e130515fce73';

 
/*
-- SET variable re-normalize --x3
INSERT INTO TasksConfigsSetUnitVariable (pk, variable, variableValue, microServiceChainLink)
    VALUES (pk, variable, variableValue, microServiceChainLink);
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
    VALUES
    (pk, taskType, LAST_INSERT_ID(), 'Find thumbnail links to run.');
INSERT INTO MicroServiceChainLinks (pk, microserviceGroup, currentTask, defaultNextChainLink)
    VALUES (pk, @microserviceGroup, LAST_INSERT_ID(), NULL);
SET @MicroServiceChainLink = LAST_INSERT_ID();
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink)
    VALUES (pk, @MicroServiceChainLink, 0, '83484326-7be7-4f9f-b252-94553cd42370');
SET @NextMicroServiceChainLink = @MicroServiceChainLink;

*/
