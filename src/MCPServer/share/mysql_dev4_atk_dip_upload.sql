DROP TABLE IF EXISTS `administration_archiviststoolkitconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `administration_archiviststoolkitconfig` (
  `pk` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `host` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `port` int(11) DEFAULT NULL,
  `dbname` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `dbuser` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `dbpass` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `atuser` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `premis` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ead_actuate` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ead_show` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `object_type` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `use_statement` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `uri_prefix` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `access_conditions` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `use_conditions` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

DROP table IF EXISTS AtkDIPObjectResourcePairing;
CREATE TABLE AtkDIPObjectResourcePairing (
  pk INT(11) NOT NULL AUTO_INCREMENT,
  dipUUID VARCHAR(255) NOT NULL,
  fileUUID VARCHAR(255) NOT NULL,
  resourceId INT(11),
  resourceComponentId INT(11),
  PRIMARY KEY (pk)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

INSERT INTO `MicroServiceChainLinks` (`pk`, `currentTask`, `defaultNextChainLink`, `defaultPlaySound`, `microserviceGroup`, `reloadFileList`, `defaultExitMessage`, `replaces`, `lastModified`) VALUES ('5bddbb67-76b4-4bcb-9b85-a0d9337e7042','008e5b38-b19c-48af-896f-349aaf5eba9f','83484326-7be7-4f9f-b252-94553cd42370',NULL,'Normalize',1,'Failed',NULL,'2012-10-23 19:41:24');

INSERT INTO `MicroServiceChainLinks` (`pk`, `currentTask`, `defaultNextChainLink`, `defaultPlaySound`, `microserviceGroup`, `reloadFileList`, `defaultExitMessage`, `replaces`, `lastModified`) VALUES ('f4dea20e-f3fe-4a37-b20f-0e70a7bc960e','85a2ec9b-5a80-497b-af60-04926c0bf183',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-23 19:41:24');

INSERT INTO `TasksConfigs` (`pk`, `taskType`, `taskTypePKReference`, `description`, `replaces`, `lastModified`) VALUES ('4d56a90c-8d9f-498c-8331-cf469fcb3147','9c84b047-9a6d-463f-9836-eafa49743b84','','Choose Config for Archivists Toolkit DIP Upload',NULL,'2013-03-25 20:25:01');

INSERT INTO `TasksConfigs` (`pk`, `taskType`, `taskTypePKReference`, `description`, `replaces`, `lastModified`) VALUES ('bcff2873-f006-442e-9628-5eadbb8d0db7','36b2e239-4a57-4aa5-8ebc-7a29139baca6','a650921e-b754-4e61-9713-1457cf52e77d','Upload to Archivists Toolkit',NULL,'2013-03-25 20:25:01');

-- Link that runs ATK DIP upload script
INSERT INTO `MicroServiceChainLinks` (`pk`, `currentTask`, `defaultNextChainLink`, `defaultPlaySound`, `microserviceGroup`, `reloadFileList`, `defaultExitMessage`, `replaces`, `lastModified`) VALUES ('bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1','bcff2873-f006-442e-9628-5eadbb8d0db7','e3efab02-1860-42dd-a46c-25601251b930',NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 07:25:06');

-- Link that allows selection of ATK config
INSERT INTO `MicroServiceChainLinks` (`pk`, `currentTask`, `defaultNextChainLink`, `defaultPlaySound`, `microserviceGroup`, `reloadFileList`, `defaultExitMessage`, `replaces`, `lastModified`) VALUES ('7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1','4d56a90c-8d9f-498c-8331-cf469fcb3147','bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1',NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 07:25:06');

INSERT INTO `MicroServiceChains` (`pk`, `startingLink`, `description`, `replaces`, `lastModified`) VALUES ('09949bda-5332-482a-ae47-5373bd372174','5bddbb67-76b4-4bcb-9b85-a0d9337e7042','mediainfo',NULL,'2012-10-23 19:41:24');

INSERT INTO `MicroServiceChainChoice` (`pk`, `choiceAvailableAtLink`, `chainAvailable`, `replaces`, `lastModified`) VALUES ('8240d294-ad72-4a7f-8c67-6777e165a642','f4dea20e-f3fe-4a37-b20f-0e70a7bc960e','09949bda-5332-482a-ae47-5373bd372174',NULL,'2012-10-23 19:41:25');

INSERT INTO `MicroServiceChains` (`pk`, `startingLink`, `description`, `replaces`, `lastModified`) VALUES ('f11409ad-cf3c-4e7f-b0d5-4be32d98229b','7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1','Upload DIP to Archivists Toolkit',NULL,'2013-03-25 20:25:01');

INSERT INTO `MicroServiceChoiceReplacementDic` (`pk`, `choiceAvailableAtLink`, `description`, `replacementDic`, `replaces`, `lastModified`) VALUES ('5395d1ea-a892-4029-b5a8-5264a17bbade','7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1','Archivists Toolkit Config','{\"%host%\":\"localhost\", \"%port%\":\"3306\", \"%dbname%\":\"atk01\", \"%dbuser%\":\"ATUser\", \"%dbpass%\":\"\", \"%atuser%\":\"atkuser\", \"%restrictions%\":\"premis\", \"%object_type%\":\"\", \"%ead_actuate%\":\"onRequest\", \"%ead_show%\":\"new\", \"%use_statement%\":\"Image-Service\",\"%uri_prefix%\":\"http:www.example.com/\", \"%access_conditions%\":\"\", \"%use_conditions%\":\"\"}',NULL,'2013-03-22 20:25:00');

INSERT INTO `StandardTasksConfigs` (`pk`, `filterFileEnd`, `filterFileStart`, `filterSubDir`, `requiresOutputLock`, `standardOutputFile`, `standardErrorFile`, `execute`, `arguments`, `replaces`, `lastModified`) VALUES ('a650921e-b754-4e61-9713-1457cf52e77d',NULL,NULL,NULL,0,NULL,NULL,'upload-archivistsToolkit_v0.0','--host=%host% --port=%port% --dbname=%dbname% --dbuser=%dbuser% --dbpass=%dbpass% --atuser=%atuser% --dip_location=%SIPDirectory% --dip_name=%SIPName% --dip_uuid=%SIPUUID% --restrictions=%restrictions% --object_type=%object_type% --ead_actuate=%ead_actuate% --ead_show=%ead_show% --use_statement=%use_statement% --uri_prefix=%uri_prefix% --access_conditions=%access_conditions% --use_conditions=%use_conditions%',NULL,'2013-03-22 21:42:00');

INSERT INTO `MicroServiceChainChoice` (`pk`, `choiceAvailableAtLink`, `chainAvailable`, `replaces`, `lastModified`) VALUES ('4197199a-897a-47eb-b573-59c90ba1373a','92879a29-45bf-4f0b-ac43-e64474f0f2f9','f11409ad-cf3c-4e7f-b0d5-4be32d98229b',NULL,'2012-10-02 00:25:05');

INSERT INTO `MicroServiceChainLinksExitCodes` (`pk`, `microServiceChainLink`, `exitCode`, `nextMicroServiceChainLink`, `playSound`, `exitMessage`, `replaces`, `lastModified`) VALUES ('6fe4c525-f337-408a-abcc-1caf2d3ee003','bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1',0, NULL, NULL,'Completed successfully',NULL,'2012-10-02 00:25:07');

INSERT INTO `MicroServiceChainLinksExitCodes` (`pk`, `microServiceChainLink`, `exitCode`, `nextMicroServiceChainLink`, `playSound`, `exitMessage`, `replaces`, `lastModified`) VALUES ('9e7cc8ee-4732-4dfa-86c4-cdb8b9c710da','7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1',0, 'bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1', NULL,'Completed successfully',NULL,'2012-10-02 00:25:07');
