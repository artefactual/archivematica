-- Common
SET @MoveTransferToFailedLink = '61c316a6-0a50-4f65-8767-1f44b1eeb6dd';
SET @MoveSIPToFailedLink = '7d728c39-395f-4892-8193-92f086c0546f';
-- /Common

-- Issue 6020

-- Updated remove unneeded files to remove excess args
UPDATE StandardTasksConfigs SET arguments='"%relativeLocation%" "%fileUUID%"' WHERE pk='49b803e3-8342-4098-bb3f-434e1eb5cfa8';

-- Add remove unneeded files to Transfer, before file ID
INSERT INTO StandardTasksConfigs (pk, requiresOutputLock, execute, arguments) VALUES ('66aa823d-3b72-4d13-9ad6-c5e6580857b8', 1, 'removeUnneededFiles_v0.0', '"%relativeLocation%" "%fileUUID%"'); -- not in objects/
INSERT INTO TasksConfigs (pk, taskType, taskTypePKReference, description) VALUES ('85308c8b-b299-4453-bf40-9ac61d134015', 'a6b1c323-7d36-428e-846a-e7e819423577', '66aa823d-3b72-4d13-9ad6-c5e6580857b8', 'Remove unneeded files');
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('5d780c7d-39d0-4f4a-922b-9d1b0d217bca', 'Verify transfer compliance', 'Failed', '85308c8b-b299-4453-bf40-9ac61d134015', 'ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('9cb81a5c-a7a1-43a8-8eb6-3e999923e03c', '5d780c7d-39d0-4f4a-922b-9d1b0d217bca', 0, 'ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='5d780c7d-39d0-4f4a-922b-9d1b0d217bca' WHERE microServiceChainLink='50b67418-cb8d-434d-acc9-4a8324e7fdd2';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='5d780c7d-39d0-4f4a-922b-9d1b0d217bca' WHERE pk='50b67418-cb8d-434d-acc9-4a8324e7fdd2';

-- Add remove unneeded and hidden files to Transfer after extract
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('bdce640d-6e94-49fe-9300-3192a7e5edac', 'Extract packages', 'Failed', 'ef0bb0cf-28d5-4687-a13d-2377341371b5', 'aaa929e4-5c35-447e-816a-033a66b9b90b');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('9a07d5a1-1418-4007-9c7e-55462ca63751', 'bdce640d-6e94-49fe-9300-3192a7e5edac', 0, 'aaa929e4-5c35-447e-816a-033a66b9b90b', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='bdce640d-6e94-49fe-9300-3192a7e5edac' WHERE microServiceChainLink='c5ecb5a9-d697-4188-844f-9a756d8734fa';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='bdce640d-6e94-49fe-9300-3192a7e5edac' WHERE pk='c5ecb5a9-d697-4188-844f-9a756d8734fa';
-- Update for maildir
INSERT INTO MicroServiceChainLinks(pk, microserviceGroup, defaultExitMessage, currentTask, defaultNextChainLink) VALUES ('e19f8eed-faf9-4e04-bf1f-e9418f2b2b11', 'Extract packages', 'Failed', 'ef0bb0cf-28d5-4687-a13d-2377341371b5', '22ded604-6cc0-444b-b320-f96afb15d581');
INSERT INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink, exitCode, nextMicroServiceChainLink, exitMessage) VALUES ('0ef15153-0d41-4b93-bdb3-4158cec405a3', 'e19f8eed-faf9-4e04-bf1f-e9418f2b2b11', 0, '22ded604-6cc0-444b-b320-f96afb15d581', 'Completed successfully');
UPDATE MicroServiceChainLinksExitCodes SET nextMicroServiceChainLink='e19f8eed-faf9-4e04-bf1f-e9418f2b2b11' WHERE microServiceChainLink='01b30826-bfc4-4e07-8ca2-4263debad642';
UPDATE MicroServiceChainLinks SET defaultNextChainLink='e19f8eed-faf9-4e04-bf1f-e9418f2b2b11' WHERE pk='01b30826-bfc4-4e07-8ca2-4263debad642';

-- /Issue 6020

-- Issue 5232
-- Update CONTENTdm example to put http:// in front of ContentdmServer
UPDATE MicroServiceChoiceReplacementDic SET replacementDic='{\"%ContentdmServer%\":\"http://111.222.333.444:81\", \"%ContentdmUser%\":\"usernamebar\", \"%ContentdmGroup%\":\"456\"}' WHERE pk='c001db23-200c-4195-9c4a-65f206f817f2';
UPDATE MicroServiceChoiceReplacementDic SET replacementDic='{\"%ContentdmServer%\":\"http://localhost\", \"%ContentdmUser%\":\"usernamefoo\", \"%ContentdmGroup%\":\"123\"}' WHERE pk='ce62eec6-0a49-489f-ac4b-c7b8c93086fd';
-- /Issue 5232

-- Issue 5356
CREATE TABLE TransferMetadataSets (
  pk VARCHAR(50) NOT NULL,
  createdTime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  transferType VARCHAR(50) NOT NULL,
  PRIMARY KEY (pk)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE Transfers ADD COLUMN transferMetadataSetRowUUID VARCHAR(50);

CREATE TABLE TransferMetadataFields (
  pk varchar(50) NOT NULL,
  createdTime timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fieldLabel VARCHAR(50) DEFAULT '',
  fieldName VARCHAR(50) NOT NULL,
  fieldType VARCHAR(50) NOT NULL,
  optionTaxonomyUUID VARCHAR(50) NOT NULL,
  sortOrder INT(11) DEFAULT 0,
  PRIMARY KEY (pk)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('fc69452c-ca57-448d-a46b-873afdd55e15', UNIX_TIMESTAMP(), 'Media number', 'media_number', 'text', 0);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('a9a4efa8-d8ab-4b32-8875-b10da835621c', UNIX_TIMESTAMP(), 'Label text', 'label_text', 'textarea', 1);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('367ef53b-49d6-4a4e-8b2f-10267d6a7db1', UNIX_TIMESTAMP(), 'Media manufacture', 'media_manufacture', 'text', 2);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('277727e4-b621-4f68-acb4-5689f81f31cd', UNIX_TIMESTAMP(), 'Serial number', 'serial_number', 'text', 3);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('13f97ff6-b312-4ab6-aea1-8438a55ae581', UNIX_TIMESTAMP(), 'Media format', 'media_format', 'select', '312fc2b3-d786-458d-a762-57add7f96c22', 4);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('a0d80573-e6ef-412e-a7a7-69bdfe3f6f8f', UNIX_TIMESTAMP(), 'Media density', 'media_density', 'select', 'f6980e68-bac2-46db-842b-da4eba4ba418', 5);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('c9344f6f-f881-4d2e-9ffa-26b7f5e42a11', UNIX_TIMESTAMP(), 'Source filesystem', 'source_filesystem', 'select', '31e0bdc9-1114-4427-9f37-ca284577dcac', 6);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('7ab79b42-1c84-420e-9169-e6bdf20141df', UNIX_TIMESTAMP(), 'Imaging process notes', 'imaging_process_notes', 'textarea', 7);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('af677693-524d-42af-be6c-d0f6a8976db1', UNIX_TIMESTAMP(), 'Imaging interface', 'imaging_interface', 'select', 'fbf318db-4908-4971-8273-1094d2ba29a6', 8);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('2c1844af-1217-4fdb-afbe-a052a91b7265', UNIX_TIMESTAMP(), 'Examiner', 'examiner', 'text', 9);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('38df3f82-5695-46d3-b4e2-df68a872778a', UNIX_TIMESTAMP(), 'Imaging date', 'imaging_date', 'text', 10);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('32f0f054-96d1-42ed-add6-7aa053237b02', UNIX_TIMESTAMP(), 'Imaging success', 'imaging_success', 'text', 11);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('d3b5b380-8901-4e68-8c40-3d59578810f4', UNIX_TIMESTAMP(), 'Image format', 'image_format', 'select', 'cc4231ef-9886-4722-82ec-917e60d3b2c7', 12);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, optionTaxonomyUUID, sortOrder)
    VALUES ('0c1b4233-fbe7-463f-8346-be6542574b86', UNIX_TIMESTAMP(), 'Imaging software', 'imaging_software', 'select', 'cae76c7f-4d8e-48ee-9522-4b3fbf492516', 13);

INSERT INTO TransferMetadataFields (pk, createdTime, fieldLabel, fieldName, fieldType, sortOrder)
    VALUES ('0a9e346a-f08c-4e0d-9753-d9733f7205e5', UNIX_TIMESTAMP(), 'Image fixity', 'image_fixity', 'text', 14);

CREATE TABLE TransferMetadataFieldValues (
  pk varchar(50) NOT NULL,
  createdTime timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  setUUID VARCHAR(50) NOT NULL,
  filePath longtext NOT NULL,
  fieldUUID VARCHAR(50) NOT NULL,
  fieldValue LONGTEXT DEFAULT '',
  PRIMARY KEY (pk)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE Taxonomies (
  pk varchar(50) NOT NULL,
  createdTime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  name VARCHAR(255) DEFAULT '',
  type VARCHAR(50) NOT NULL DEFAULT 'open',
  PRIMARY KEY (pk)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE TaxonomyTerms (
  pk varchar(50) NOT NULL,
  createdTime timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  taxonomyUUID varchar(50) NOT NULL,
  term varchar(255) DEFAULT '',
  PRIMARY KEY (pk)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO Taxonomies (pk, name) VALUES ('312fc2b3-d786-458d-a762-57add7f96c22', 'Disk media formats');
INSERT INTO Taxonomies (pk, name) VALUES ('f6980e68-bac2-46db-842b-da4eba4ba418', 'Disk media densities');
INSERT INTO Taxonomies (pk, name) VALUES ('31e0bdc9-1114-4427-9f37-ca284577dcac', 'Filesystem types');
INSERT INTO Taxonomies (pk, name) VALUES ('fbf318db-4908-4971-8273-1094d2ba29a6', 'Disk imaging interfaces');
INSERT INTO Taxonomies (pk, name) VALUES ('cc4231ef-9886-4722-82ec-917e60d3b2c7', 'Disk image format');
INSERT INTO Taxonomies (pk, name) VALUES ('cae76c7f-4d8e-48ee-9522-4b3fbf492516', 'Disk imaging software');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('867ab18d-e860-445f-a254-8fcdebfe95b6', '312fc2b3-d786-458d-a762-57add7f96c22', '3.5" floppy');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('c41922d6-e716-4822-a385-e2fb0009465b', '312fc2b3-d786-458d-a762-57add7f96c22', '5.25" floppy');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('e4edb250-d70a-4f63-8234-948b05b1163e', 'f6980e68-bac2-46db-842b-da4eba4ba418', 'Single density');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('82a367f5-8157-4ac4-a5eb-3b59aac78d16', 'f6980e68-bac2-46db-842b-da4eba4ba418', 'Double density');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('0d6d40b5-8bf8-431d-8dd2-23d6b0b17ca0', '31e0bdc9-1114-4427-9f37-ca284577dcac', 'FAT');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('db34d5e1-0c93-4faa-bb1c-c5f5ebae6764', '31e0bdc9-1114-4427-9f37-ca284577dcac', 'HFS');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('35097f1b-094a-40bc-ba0c-f1260b50042a', 'fbf318db-4908-4971-8273-1094d2ba29a6', 'Catweasel');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('53e7764a-f711-486d-a0aa-8ec10d1d8da5', 'fbf318db-4908-4971-8273-1094d2ba29a6', 'Firewire');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('6774c7ce-a760-4f29-a7a3-b948f3769f71', 'fbf318db-4908-4971-8273-1094d2ba29a6', 'USB');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('6e368167-ea3e-45cd-adf2-60513a7e1802', 'fbf318db-4908-4971-8273-1094d2ba29a6', 'IDE');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('fcefbea2-848c-4685-9032-18a87cbc7a04', 'cc4231ef-9886-4722-82ec-917e60d3b2c7', 'AFF3');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('a3a6e30d-810f-4300-8461-1b41a7b383f1', 'cc4231ef-9886-4722-82ec-917e60d3b2c7', 'AD1');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('38ad5611-f05a-45d4-ac20-541c89bf0167', 'cae76c7f-4d8e-48ee-9522-4b3fbf492516', 'FTK imager 3.1.0.1514');

INSERT INTO TaxonomyTerms (pk, taxonomyUUID, term)
  VALUES ('6836caa4-8a0f-465e-be1b-4d8c547a7bf4', 'cae76c7f-4d8e-48ee-9522-4b3fbf492516', 'Kryoflux');
-- /Issue 5356
