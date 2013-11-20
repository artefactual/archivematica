-- MySQL dump 10.13  Distrib 5.5.34, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: MCP
-- ------------------------------------------------------
-- Server version	5.5.34-0ubuntu0.12.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Accesses`
--

DROP TABLE IF EXISTS `Accesses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Accesses` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `SIPUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `target` longtext COLLATE utf8_unicode_ci,
  `resource` longtext COLLATE utf8_unicode_ci,
  `status` longtext COLLATE utf8_unicode_ci,
  `statusCode` tinyint(3) unsigned DEFAULT NULL,
  `exitCode` tinyint(3) unsigned DEFAULT NULL,
  `createdTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Accesses`
--

LOCK TABLES `Accesses` WRITE;
/*!40000 ALTER TABLE `Accesses` DISABLE KEYS */;
/*!40000 ALTER TABLE `Accesses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Agent`
--

DROP TABLE IF EXISTS `Agent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Agent` (
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `agentIdentifierType` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `agentIdentifierValue` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `agentName` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `agentType` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `clientIP` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Agent`
--

LOCK TABLES `Agent` WRITE;
/*!40000 ALTER TABLE `Agent` DISABLE KEYS */;
/*!40000 ALTER TABLE `Agent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Agents`
--

DROP TABLE IF EXISTS `Agents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Agents` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `agentIdentifierType` longtext COLLATE utf8_unicode_ci,
  `agentIdentifierValue` longtext COLLATE utf8_unicode_ci,
  `agentName` longtext COLLATE utf8_unicode_ci,
  `agentType` longtext COLLATE utf8_unicode_ci,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Agents`
--

LOCK TABLES `Agents` WRITE;
/*!40000 ALTER TABLE `Agents` DISABLE KEYS */;
INSERT INTO `Agents` VALUES (1,'preservation system','Archivematica-0.10','Archivematica','software'),(2,'repository code','ORG','Your Organization Name Here','organization');
/*!40000 ALTER TABLE `Agents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ArchivematicaRightsStatement`
--

DROP TABLE IF EXISTS `ArchivematicaRightsStatement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ArchivematicaRightsStatement` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `metadataAppliesToType` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `metadataAppliesToidentifier` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `fkRightsStatement` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatement` (`fkRightsStatement`),
  KEY `metadataAppliesToType` (`metadataAppliesToType`),
  CONSTRAINT `ArchivematicaRightsStatement_ibfk_2` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`),
  CONSTRAINT `ArchivematicaRightsStatement_ibfk_3` FOREIGN KEY (`metadataAppliesToType`) REFERENCES `MetadataAppliesToTypes` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ArchivematicaRightsStatement`
--

LOCK TABLES `ArchivematicaRightsStatement` WRITE;
/*!40000 ALTER TABLE `ArchivematicaRightsStatement` DISABLE KEYS */;
/*!40000 ALTER TABLE `ArchivematicaRightsStatement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AtkDIPObjectResourcePairing`
--

DROP TABLE IF EXISTS `AtkDIPObjectResourcePairing`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `AtkDIPObjectResourcePairing` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `dipUUID` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `fileUUID` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `resourceId` int(11) DEFAULT NULL,
  `resourceComponentId` int(11) DEFAULT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AtkDIPObjectResourcePairing`
--

LOCK TABLES `AtkDIPObjectResourcePairing` WRITE;
/*!40000 ALTER TABLE `AtkDIPObjectResourcePairing` DISABLE KEYS */;
/*!40000 ALTER TABLE `AtkDIPObjectResourcePairing` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DashboardSettings`
--

DROP TABLE IF EXISTS `DashboardSettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DashboardSettings` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `value` longtext COLLATE utf8_unicode_ci,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DashboardSettings`
--

LOCK TABLES `DashboardSettings` WRITE;
/*!40000 ALTER TABLE `DashboardSettings` DISABLE KEYS */;
/*!40000 ALTER TABLE `DashboardSettings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Derivations`
--

DROP TABLE IF EXISTS `Derivations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Derivations` (
  `pk` bigint(20) NOT NULL AUTO_INCREMENT,
  `sourceFileUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `derivedFileUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `relatedEventUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `sourceFileUUID` (`sourceFileUUID`),
  KEY `derivedFileUUID` (`derivedFileUUID`),
  CONSTRAINT `Derivations_ibfk_1` FOREIGN KEY (`sourceFileUUID`) REFERENCES `Files` (`fileUUID`),
  CONSTRAINT `Derivations_ibfk_2` FOREIGN KEY (`derivedFileUUID`) REFERENCES `Files` (`fileUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Derivations`
--

LOCK TABLES `Derivations` WRITE;
/*!40000 ALTER TABLE `Derivations` DISABLE KEYS */;
/*!40000 ALTER TABLE `Derivations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Dublincore`
--

DROP TABLE IF EXISTS `Dublincore`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Dublincore` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `metadataAppliesToType` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `metadataAppliesToidentifier` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `title` longtext COLLATE utf8_unicode_ci,
  `creator` longtext COLLATE utf8_unicode_ci,
  `subject` longtext COLLATE utf8_unicode_ci,
  `description` longtext COLLATE utf8_unicode_ci,
  `publisher` longtext COLLATE utf8_unicode_ci,
  `contributor` longtext COLLATE utf8_unicode_ci,
  `date` longtext COLLATE utf8_unicode_ci,
  `type` longtext COLLATE utf8_unicode_ci,
  `format` longtext COLLATE utf8_unicode_ci,
  `identifier` longtext COLLATE utf8_unicode_ci,
  `source` longtext COLLATE utf8_unicode_ci,
  `relation` longtext COLLATE utf8_unicode_ci,
  `language` longtext COLLATE utf8_unicode_ci,
  `coverage` longtext COLLATE utf8_unicode_ci,
  `rights` longtext COLLATE utf8_unicode_ci,
  PRIMARY KEY (`pk`),
  KEY `metadataAppliesToType` (`metadataAppliesToType`),
  CONSTRAINT `Dublincore_ibfk_1` FOREIGN KEY (`metadataAppliesToType`) REFERENCES `MetadataAppliesToTypes` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Dublincore`
--

LOCK TABLES `Dublincore` WRITE;
/*!40000 ALTER TABLE `Dublincore` DISABLE KEYS */;
/*!40000 ALTER TABLE `Dublincore` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ElasticsearchIndexBackup`
--

DROP TABLE IF EXISTS `ElasticsearchIndexBackup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ElasticsearchIndexBackup` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `docId` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `indexName` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `typeName` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `data` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ElasticsearchIndexBackup`
--

LOCK TABLES `ElasticsearchIndexBackup` WRITE;
/*!40000 ALTER TABLE `ElasticsearchIndexBackup` DISABLE KEYS */;
/*!40000 ALTER TABLE `ElasticsearchIndexBackup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Events`
--

DROP TABLE IF EXISTS `Events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Events` (
  `pk` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `fileUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `eventIdentifierUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `eventType` longtext COLLATE utf8_unicode_ci,
  `eventDateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `eventDetail` longtext COLLATE utf8_unicode_ci,
  `eventOutcome` longtext COLLATE utf8_unicode_ci,
  `eventOutcomeDetailNote` longtext COLLATE utf8_unicode_ci,
  `linkingAgentIdentifier` int(11) DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `fileUUID` (`fileUUID`),
  CONSTRAINT `Events_ibfk_1` FOREIGN KEY (`fileUUID`) REFERENCES `Files` (`fileUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Events`
--

LOCK TABLES `Events` WRITE;
/*!40000 ALTER TABLE `Events` DISABLE KEYS */;
/*!40000 ALTER TABLE `Events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FPCommandOutput`
--

DROP TABLE IF EXISTS `FPCommandOutput`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FPCommandOutput` (
  `fileUUID` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `content` longtext COLLATE utf8_unicode_ci,
  `ruleUUID` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`fileUUID`),
  KEY `FPCommandOutput_ibfk_2` (`ruleUUID`),
  CONSTRAINT `FPCommandOutput_ibfk_1` FOREIGN KEY (`fileUUID`) REFERENCES `Files` (`fileUUID`),
  CONSTRAINT `FPCommandOutput_ibfk_2` FOREIGN KEY (`ruleUUID`) REFERENCES `fpr_fprule` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FPCommandOutput`
--

LOCK TABLES `FPCommandOutput` WRITE;
/*!40000 ALTER TABLE `FPCommandOutput` DISABLE KEYS */;
/*!40000 ALTER TABLE `FPCommandOutput` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FauxFileIDsMap`
--

DROP TABLE IF EXISTS `FauxFileIDsMap`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FauxFileIDsMap` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `fauxSIPUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `fauxFileUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `fileUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `fauxFileUUID` (`fauxFileUUID`),
  KEY `fauxSIPUUID` (`fauxSIPUUID`),
  CONSTRAINT `FauxFileIDsMap_ibfk_1` FOREIGN KEY (`fauxFileUUID`) REFERENCES `Files` (`fileUUID`),
  CONSTRAINT `FauxFileIDsMap_ibfk_2` FOREIGN KEY (`fauxSIPUUID`) REFERENCES `SIPs` (`sipUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FauxFileIDsMap`
--

LOCK TABLES `FauxFileIDsMap` WRITE;
/*!40000 ALTER TABLE `FauxFileIDsMap` DISABLE KEYS */;
/*!40000 ALTER TABLE `FauxFileIDsMap` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `FileExtensions`
--

DROP TABLE IF EXISTS `FileExtensions`;
/*!50001 DROP VIEW IF EXISTS `FileExtensions`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `FileExtensions` (
  `FileUUID` tinyint NOT NULL,
  `extension` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `Files`
--

DROP TABLE IF EXISTS `Files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Files` (
  `fileUUID` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `originalLocation` longtext COLLATE utf8_unicode_ci,
  `currentLocation` longtext COLLATE utf8_unicode_ci,
  `sipUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `transferUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `removedTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `enteredSystem` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fileSize` bigint(20) unsigned DEFAULT NULL,
  `checksum` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `fileGrpUse` varchar(50) COLLATE utf8_unicode_ci DEFAULT 'Original',
  `fileGrpUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `label` longtext COLLATE utf8_unicode_ci,
  PRIMARY KEY (`fileUUID`),
  KEY `currentLocation` (`currentLocation`(255)) USING BTREE,
  KEY `sipUUID` (`sipUUID`),
  KEY `transferUUID` (`transferUUID`),
  CONSTRAINT `Files_ibfk_1` FOREIGN KEY (`sipUUID`) REFERENCES `SIPs` (`sipUUID`),
  CONSTRAINT `Files_ibfk_2` FOREIGN KEY (`transferUUID`) REFERENCES `Transfers` (`transferUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Files`
--

LOCK TABLES `Files` WRITE;
/*!40000 ALTER TABLE `Files` DISABLE KEYS */;
/*!40000 ALTER TABLE `Files` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `FilesByUnit`
--

DROP TABLE IF EXISTS `FilesByUnit`;
/*!50001 DROP VIEW IF EXISTS `FilesByUnit`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `FilesByUnit` (
  `fileUUID` tinyint NOT NULL,
  `originalLocation` tinyint NOT NULL,
  `currentLocation` tinyint NOT NULL,
  `unitUUID` tinyint NOT NULL,
  `unitType` tinyint NOT NULL,
  `removedTime` tinyint NOT NULL,
  `enteredSystem` tinyint NOT NULL,
  `fileSize` tinyint NOT NULL,
  `checksum` tinyint NOT NULL,
  `fileGrpUse` tinyint NOT NULL,
  `fileGrpUUID` tinyint NOT NULL,
  `label` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `FilesIDs`
--

DROP TABLE IF EXISTS `FilesIDs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FilesIDs` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `fileUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `formatName` longtext COLLATE utf8_unicode_ci,
  `formatVersion` longtext COLLATE utf8_unicode_ci,
  `formatRegistryName` longtext COLLATE utf8_unicode_ci,
  `formatRegistryKey` longtext COLLATE utf8_unicode_ci,
  PRIMARY KEY (`pk`),
  KEY `fileUUID` (`fileUUID`),
  CONSTRAINT `FilesIDs_ibfk_1` FOREIGN KEY (`fileUUID`) REFERENCES `Files` (`fileUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FilesIDs`
--

LOCK TABLES `FilesIDs` WRITE;
/*!40000 ALTER TABLE `FilesIDs` DISABLE KEYS */;
/*!40000 ALTER TABLE `FilesIDs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FilesIdentifiedIDs`
--

DROP TABLE IF EXISTS `FilesIdentifiedIDs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FilesIdentifiedIDs` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `fileUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `fileID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `fileUUID` (`fileUUID`),
  KEY `fileID` (`fileID`),
  CONSTRAINT `FilesIdentifiedIDs_ibfk_2` FOREIGN KEY (`fileID`) REFERENCES `fpr_formatversion` (`uuid`),
  CONSTRAINT `FilesIdentifiedIDs_ibfk_1` FOREIGN KEY (`fileUUID`) REFERENCES `Files` (`fileUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FilesIdentifiedIDs`
--

LOCK TABLES `FilesIdentifiedIDs` WRITE;
/*!40000 ALTER TABLE `FilesIdentifiedIDs` DISABLE KEYS */;
/*!40000 ALTER TABLE `FilesIdentifiedIDs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Groups`
--

DROP TABLE IF EXISTS `Groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Groups` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `description` text COLLATE utf8_unicode_ci,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `enabled` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`pk`),
  KEY `Groups` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Groups`
--

LOCK TABLES `Groups` WRITE;
/*!40000 ALTER TABLE `Groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `Groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Jobs`
--

DROP TABLE IF EXISTS `Jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Jobs` (
  `jobUUID` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `jobType` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL,
  `createdTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `createdTimeDec` decimal(24,10) NOT NULL DEFAULT '0.0000000000',
  `directory` longtext COLLATE utf8_unicode_ci,
  `SIPUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `unitType` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `currentStep` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `microserviceGroup` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL DEFAULT '0',
  `MicroServiceChainLinksPK` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `subJobOf` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`jobUUID`),
  KEY `MicroServiceChainLinksPK` (`MicroServiceChainLinksPK`),
  CONSTRAINT `Jobs_ibfk_1` FOREIGN KEY (`MicroServiceChainLinksPK`) REFERENCES `MicroServiceChainLinks` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Jobs`
--

LOCK TABLES `Jobs` WRITE;
/*!40000 ALTER TABLE `Jobs` DISABLE KEYS */;
/*!40000 ALTER TABLE `Jobs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MetadataAppliesToTypes`
--

DROP TABLE IF EXISTS `MetadataAppliesToTypes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MetadataAppliesToTypes` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `description` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `MetadataAppliesToTypes` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MetadataAppliesToTypes`
--

LOCK TABLES `MetadataAppliesToTypes` WRITE;
/*!40000 ALTER TABLE `MetadataAppliesToTypes` DISABLE KEYS */;
INSERT INTO `MetadataAppliesToTypes` VALUES ('3e48343d-e2d2-4956-aaa3-b54d26eb9761','SIP',NULL,'2012-10-02 00:25:05'),('45696327-44c5-4e78-849b-e027a189bf4d','Transfer',NULL,'2012-10-02 00:25:05'),('7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17','File',NULL,'2012-10-02 00:25:05');
/*!40000 ALTER TABLE `MetadataAppliesToTypes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MicroServiceChainChoice`
--

DROP TABLE IF EXISTS `MicroServiceChainChoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MicroServiceChainChoice` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `choiceAvailableAtLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `chainAvailable` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `MicroServiceChainChoice` (`pk`),
  KEY `chainAvailable` (`chainAvailable`),
  KEY `choiceAvailableAtLink` (`choiceAvailableAtLink`),
  CONSTRAINT `MicroServiceChainChoice_ibfk_1` FOREIGN KEY (`chainAvailable`) REFERENCES `MicroServiceChains` (`pk`),
  CONSTRAINT `MicroServiceChainChoice_ibfk_2` FOREIGN KEY (`choiceAvailableAtLink`) REFERENCES `MicroServiceChainLinks` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MicroServiceChainChoice`
--

LOCK TABLES `MicroServiceChainChoice` WRITE;
/*!40000 ALTER TABLE `MicroServiceChainChoice` DISABLE KEYS */;
INSERT INTO `MicroServiceChainChoice` VALUES ('00ed2cf8-c301-4de9-a80b-f00f2cae3667','cb8e5706-e73f-472f-ad9b-d1236af8095f','b93cecd4-71f2-4e28-bc39-d32fd62c5a94',NULL,'2012-10-02 00:25:05'),('06183294-4c2a-4763-9262-c2ab0fbdf36f','cb8e5706-e73f-472f-ad9b-d1236af8095f','612e3609-ce9a-4df6-a9a3-63d634d2d934',NULL,'2012-10-02 00:25:05'),('06a6c312-0296-43ab-8e6b-c25170b67bc5','d05eaa5e-344b-4daa-b78b-c9f27c76499d','12aaa737-4abd-45ea-a442-8f9f2666fa98',NULL,'2013-11-07 22:51:35'),('093744af-64f1-4d56-9a54-69256011a349','150dcb45-46c3-4529-b35f-b0a8a5a553e9','2256d500-a26e-438d-803d-3ffe17b8caf0',NULL,'2012-10-02 00:25:05'),('15525b8f-a6b6-4c2d-98d0-943b2fb106ec','2d32235c-02d4-4686-88a6-96f4d6c7b1c3','433f4e6b-1ef4-49f8-b1e4-49693791a806',NULL,'2012-10-02 00:25:05'),('15cc9db5-00d8-411b-81bc-9a5062c640fe','9fa0a0d1-25bb-4507-a5f7-f177d7fa920d','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('15e370a2-1381-42b0-aab7-baf6095cee39','05f99ffd-abf2-4f5a-9ec8-f80a59967b89','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('176ee50a-0a9b-455b-bd60-ea2e95de9d4e','f3a58cbb-20a8-4c6d-9ae4-1a5f02c1a28e','333643b7-122a-4019-8bef-996443f3ecc5',NULL,'2012-10-02 00:25:05'),('1786f77e-4035-49c1-b966-32dbb6b189eb','998044bb-6260-452f-a742-cfb19e80125b','d381cf76-9313-415f-98a1-55c91e4d78e0',NULL,'2012-10-02 00:25:05'),('17a26daf-fccb-4a61-ba0e-0ab6b6de7eca','d05eaa5e-344b-4daa-b78b-c9f27c76499d','b96411f1-bbf4-425a-adcf-8e7bfac2b85b',NULL,'2013-11-07 22:51:35'),('1b408994-ac47-4166-8a9b-4ef4bde09474','92879a29-45bf-4f0b-ac43-e64474f0f2f9','526eded3-2280-4f10-ac86-eff6c464cc81',NULL,'2012-10-02 00:25:05'),('1e350acc-b9c3-4845-8521-24b041495df3','ab69c494-23b7-4f50-acff-2e00cf7bffda','a6ed697e-6189-4b4e-9f80-29209abc7937',NULL,'2012-10-02 00:25:05'),('29797e14-9528-455f-87d1-2026d54cf1bd','bb194013-597c-4e4a-8493-b36d190f8717','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('2df531df-339d-49c0-a5fe-5e655596b566','b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3','c34bd22a-d077-4180-bf58-01db35bdb644',NULL,'2013-11-07 22:51:35'),('2e0a75d8-5f76-44d6-b5c3-e7d6ff5be58d','b963a646-0569-43c4-89a2-e3b814c5c08e','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('2e8ca13c-00f6-4610-b76c-13ba94d0e75d','15402367-2d3f-475e-b251-55532347a3c2','167dc382-4ab1-4051-8e22-e7f1c1bf3e6f',NULL,'2012-10-02 00:25:05'),('313839ac-5e04-4b50-9793-87dcf4c63390','150dcb45-46c3-4529-b35f-b0a8a5a553e9','169a5448-c756-4705-a920-737de6b8d595',NULL,'2012-10-02 00:25:05'),('320440c5-d0c0-40a0-9659-7fa811ece50a','cb8e5706-e73f-472f-ad9b-d1236af8095f','c34bd22a-d077-4180-bf58-01db35bdb644',NULL,'2013-01-05 01:09:14'),('32bd0709-8c59-4f74-80fb-c17b03279589','bb194013-597c-4e4a-8493-b36d190f8717','9634868c-b183-4d65-8587-2f53f7ff5a0a',NULL,'2012-10-02 00:25:05'),('35c8e6a3-42c3-411a-b6b5-3d83d1759db7','cb8e5706-e73f-472f-ad9b-d1236af8095f','89cb80dd-0636-464f-930d-57b61e3928b2',NULL,'2012-10-02 00:25:05'),('399293b8-0d58-41b5-89c5-5edde497448b','b963a646-0569-43c4-89a2-e3b814c5c08e','1cb2ef0e-afe8-45b5-8d8f-a1e120f06605',NULL,'2012-10-02 00:25:05'),('399982e9-ebba-43da-b815-cddbeef3b551','7509e7dc-1e1b-4dce-8d21-e130515fce73','a6ed697e-6189-4b4e-9f80-29209abc7937',NULL,'2012-10-02 00:25:05'),('39bcba03-d251-4974-8a7b-45b2444e19a8','92879a29-45bf-4f0b-ac43-e64474f0f2f9','eea54915-2a85-49b7-a370-b1a250dd29ce',NULL,'2012-10-02 00:25:05'),('4197199a-897a-47eb-b573-59c90ba1373a','92879a29-45bf-4f0b-ac43-e64474f0f2f9','f11409ad-cf3c-4e7f-b0d5-4be32d98229b',NULL,'2012-10-02 07:25:05'),('41d23044-2616-445d-aa3e-7db0a9e05813','15402367-2d3f-475e-b251-55532347a3c2','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('47d090b7-f0c6-472f-84a1-fc9809dfa00f','b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3','fb7a326e-1e50-4b48-91b9-4917ff8d0ae8',NULL,'2013-11-07 22:51:35'),('4a266d37-6c3d-49f7-b1ac-b93c0906945f','bb194013-597c-4e4a-8493-b36d190f8717','7065d256-2f47-4b7d-baec-2c4699626121',NULL,'2013-04-05 23:08:30'),('528c0be5-fcf4-4de7-81ef-61d4b5440800','9fa0a0d1-25bb-4507-a5f7-f177d7fa920d','a7f8f67f-401f-4665-b7b3-35496fd5017c',NULL,'2012-10-02 00:25:05'),('54d5f6a8-174c-4dd8-8698-546253c8043a','5c459c1a-f998-404d-a0dd-808709510b72','082fa7d6-68e1-431c-9216-899aec92cfa7',NULL,'2012-10-02 00:25:05'),('58a48e1d-b317-47b5-b4d4-996c98e0534a','cb8e5706-e73f-472f-ad9b-d1236af8095f','a6ed697e-6189-4b4e-9f80-29209abc7937',NULL,'2012-10-02 00:25:05'),('5cfaab52-dbdb-442c-82ee-310840330613','92879a29-45bf-4f0b-ac43-e64474f0f2f9','0fe9842f-9519-4067-a691-8a363132ae24',NULL,'2012-10-02 00:25:05'),('61452cbf-f3ad-4fd4-b602-bd6f1ba303f7','19adb668-b19a-4fcb-8938-f49d7485eaf3','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('62db9efd-03a0-4f6f-9285-4584bef361e0','d05eaa5e-344b-4daa-b78b-c9f27c76499d','32dfa5f0-5964-4aa4-8132-9abb5b539644',NULL,'2013-11-07 22:51:35'),('7131abac-d1e9-4dfc-b48a-36461485c240','0c94e6b5-4714-4bec-82c8-e187e0c04d77','6953950b-c101-4f4c-a0c3-0cd0684afe5e',NULL,'2012-10-02 00:25:05'),('73671d95-dfcc-4b77-91b6-ca7f194f8def','9520386f-bb6d-4fb9-a6b6-5845ef39375f','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2013-11-07 22:51:35'),('75258260-40c1-4162-8d5b-47a6417fbbc1','755b4177-c587-41a7-8c52-015277568302','97ea7702-e4d5-48bc-b4b5-d15d897806ab',NULL,'2012-10-02 00:25:05'),('7915624c-a235-44d0-8baf-307cd3f1ded9','f3a58cbb-20a8-4c6d-9ae4-1a5f02c1a28e','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('79858774-a10d-4bcb-b5d2-abf96c169cac','f6bcc82a-d629-4a78-8643-bf6e3cb39fe6','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('8001468a-1cc6-44fe-ad33-1b5c85bf2fcf','f6bcc82a-d629-4a78-8643-bf6e3cb39fe6','c75ef451-2040-4511-95ac-3baa0f019b48',NULL,'2012-10-02 00:25:05'),('8240d294-ad72-4a7f-8c67-6777e165a642','f4dea20e-f3fe-4a37-b20f-0e70a7bc960e','09949bda-5332-482a-ae47-5373bd372174',NULL,'2012-10-24 02:41:25'),('874a7e40-3aca-40e1-bcf4-d7446bdf4662','9fa0a0d1-25bb-4507-a5f7-f177d7fa920d','2884ed7c-8c4c-4fa9-a6eb-e27bcaf9ab92',NULL,'2012-10-02 00:25:05'),('87b99397-674f-4ca8-939e-057bacd79aeb','2f83c458-244f-47e5-a302-ce463163354e','e5bc60f8-4e64-4363-bf01-bef67154cfed',NULL,'2013-01-05 01:09:14'),('8bd23ab1-7cb1-413e-833b-622a50ed891c','d05eaa5e-344b-4daa-b78b-c9f27c76499d','522d85ae-298c-42ff-ab6c-bb5bf795c1ca',NULL,'2013-11-07 22:51:35'),('91d8699a-9fa3-4956-ad3c-d993da05efe7','b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3','e600b56d-1a43-4031-9d7c-f64f123e5662',NULL,'2013-11-07 22:51:35'),('92bb65f8-3eab-484e-aae4-4d2a311358bb','bb194013-597c-4e4a-8493-b36d190f8717','61cfa825-120e-4b17-83e6-51a42b67d969',NULL,'2012-10-02 00:25:05'),('9b3bb1a8-86a8-498b-8fd1-e0e260a84a90','8db10a7b-924f-4561-87b4-cb6078c65aab','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-11-30 19:55:49'),('9d932c28-da5a-4e1b-b711-bea05cadac8a','05f99ffd-abf2-4f5a-9ec8-f80a59967b89','2ba94783-d073-4372-9bd1-8316ada02635',NULL,'2012-10-02 00:25:05'),('9edb1021-60b1-4c97-8d8d-b84bd163d452','5c459c1a-f998-404d-a0dd-808709510b72','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('a053c274-3047-40fa-b004-9f320ce0bb22','de909a42-c5b5-46e1-9985-c031b50e9d30','cbe9b4a3-e4e6-4a32-8d7c-3adfc409cb6f',NULL,'2012-10-24 17:04:11'),('a431002e-5ac5-44c8-82ac-27e426f3e07e','0c94e6b5-4714-4bec-82c8-e187e0c04d77','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('a69e8ead-dff3-4e12-9560-2cc4928e28e9','998044bb-6260-452f-a742-cfb19e80125b','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('aa62acec-97ba-466c-8197-833a794c5bba','150dcb45-46c3-4529-b35f-b0a8a5a553e9','cbe9b4a3-e4e6-4a32-8d7c-3adfc409cb6f',NULL,'2012-10-24 17:04:11'),('bcb2db4e-881f-4726-a2ad-922818c9897b','cb8e5706-e73f-472f-ad9b-d1236af8095f','e600b56d-1a43-4031-9d7c-f64f123e5662',NULL,'2012-10-02 00:25:05'),('bf622d91-0bbb-491b-b3d6-7dec6bf73b72','19adb668-b19a-4fcb-8938-f49d7485eaf3','c622426e-190e-437b-aa1a-4be9c9a7680d',NULL,'2012-10-02 00:25:05'),('c6d19691-c697-44e4-b718-3d82a10efaed','cb8e5706-e73f-472f-ad9b-d1236af8095f','fb7a326e-1e50-4b48-91b9-4917ff8d0ae8',NULL,'2012-10-02 00:25:05'),('c7bbb25e-599b-4511-8392-151088f87dce','9520386f-bb6d-4fb9-a6b6-5845ef39375f','260ef4ea-f87d-4acf-830d-d0de41e6d2af',NULL,'2013-11-07 22:51:35'),('cf0b6ef5-6bda-4f3a-a300-bf696c0a9940','755b4177-c587-41a7-8c52-015277568302','252ceb42-cc61-4833-a048-97fc0bda4759',NULL,'2012-10-02 00:25:05'),('d0fc8557-2ba2-4047-8b86-0a953900de5d','5c459c1a-f998-404d-a0dd-808709510b72','191914db-119e-4b91-8422-c77805ad8249',NULL,'2012-10-02 00:25:05'),('da620806-cfc6-4381-ac16-d1b7caaf80e0','d05eaa5e-344b-4daa-b78b-c9f27c76499d','040feba9-4039-48b3-bf7d-a5a5e5f4ce85',NULL,'2013-11-07 22:51:35'),('dc81c760-546d-4a90-85c2-b15aa3f5f27b','de909a42-c5b5-46e1-9985-c031b50e9d30','1e0df175-d56d-450d-8bee-7df1dc7ae815',NULL,'2012-10-02 00:25:05'),('e1ebb8eb-2f59-4e0e-bb7b-9bef930bf482','ab69c494-23b7-4f50-acff-2e00cf7bffda','2eae85d6-da2f-4f1c-8c33-3810b55e23aa',NULL,'2012-10-02 00:25:05'),('e584eca5-52bb-46c8-9ca0-f8ed3a1e3719','7509e7dc-1e1b-4dce-8d21-e130515fce73','e8544c5e-9cbb-4b8f-a68b-6d9b4d7f7362',NULL,'2012-10-02 00:25:05'),('e5c0da9a-8c16-41f7-8798-c90b04ac5541','de909a42-c5b5-46e1-9985-c031b50e9d30','169a5448-c756-4705-a920-737de6b8d595',NULL,'2012-10-02 00:25:05'),('e5e040db-2bc0-487b-a080-a9699cb5f05a','2d32235c-02d4-4686-88a6-96f4d6c7b1c3','9efab23c-31dc-4cbd-a39d-bb1665460cbe',NULL,'2012-10-02 00:25:05'),('e698d95e-4303-41e1-a0aa-c0b18866e3d0','8db10a7b-924f-4561-87b4-cb6078c65aab','e4a59e3e-3dba-4eb5-9cf1-c1fb3ae61fa9',NULL,'2012-11-30 19:55:49'),('f68b9e34-2808-4943-919d-9aab95eae460','7509e7dc-1e1b-4dce-8d21-e130515fce73','1ab4abd7-5f28-430b-8ea8-3ba531043521',NULL,'2012-10-02 00:25:05'),('fb06f370-24dc-4a3e-8900-6fad0159a0ab','755b4177-c587-41a7-8c52-015277568302','1b04ec43-055c-43b7-9543-bd03c6a778ba',NULL,'2012-10-02 00:25:05'),('fe49358d-e270-451a-b7e5-c12558b9c06f','05f99ffd-abf2-4f5a-9ec8-f80a59967b89','d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e',NULL,'2012-10-02 00:25:05');
/*!40000 ALTER TABLE `MicroServiceChainChoice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MicroServiceChainLinks`
--

DROP TABLE IF EXISTS `MicroServiceChainLinks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MicroServiceChainLinks` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `currentTask` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `defaultNextChainLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `defaultPlaySound` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `microserviceGroup` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `reloadFileList` tinyint(1) DEFAULT '1',
  `defaultExitMessage` varchar(50) COLLATE utf8_unicode_ci DEFAULT 'Failed',
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `MicroServiceChainLinks` (`pk`),
  KEY `currentTask` (`currentTask`),
  KEY `defaultNextChainLink` (`defaultNextChainLink`),
  KEY `defaultPlaySound` (`defaultPlaySound`),
  CONSTRAINT `MicroServiceChainLinks_ibfk_1` FOREIGN KEY (`currentTask`) REFERENCES `TasksConfigs` (`pk`),
  CONSTRAINT `MicroServiceChainLinks_ibfk_2` FOREIGN KEY (`defaultNextChainLink`) REFERENCES `MicroServiceChainLinks` (`pk`),
  CONSTRAINT `MicroServiceChainLinks_ibfk_3` FOREIGN KEY (`defaultPlaySound`) REFERENCES `Sounds` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MicroServiceChainLinks`
--

LOCK TABLES `MicroServiceChainLinks` WRITE;
/*!40000 ALTER TABLE `MicroServiceChainLinks` DISABLE KEYS */;
INSERT INTO `MicroServiceChainLinks` VALUES ('002716a1-ae29-4f36-98ab-0d97192669c4','18dceb0a-dfb1-4b18-81a7-c6c5c578c5f1','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare AIP',1,'Failed',NULL,'2013-11-07 22:51:34'),('01292b28-9588-4a85-953b-d92b29faf4d0','b8c10f19-40c9-44c8-8b9f-6fab668513f5','b063c4ce-ada1-4e72-a137-800f1c10905c',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('01b30826-bfc4-4e07-8ca2-4263debad642','c2c7edcc-0e65-4df7-812f-a2ee5b5d52b6','22ded604-6cc0-444b-b320-f96afb15d581',NULL,'Extract packages',1,'Failed',NULL,'2013-11-07 22:51:43'),('01c651cb-c174-4ba4-b985-1d87a44d6754','2f6947ee-5d92-416a-bade-b1079767e641',NULL,NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('01d64f58-8295-4b7b-9cab-8f1b153a504f','8a291152-729c-42f2-ab2e-c53b9f357799',NULL,NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('01fd7a29-deb9-4dd1-8e28-1c48fc1ac41b','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('032cdc54-0b9b-4caf-86e8-10d63efbaec0','8cda5b7a-fb44-4a61-a865-6ad01af5a150',NULL,NULL,'Create SIP from Transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('03ee1136-f6ad-4184-8dcb-34872f843e14','3e70f50d-5056-413e-a3d1-7b4b13d2b821',NULL,NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('045c43ae-d6cf-44f7-97d6-c8a602748565','48929c19-c0c7-41b2-8bd0-552b22e2d86f','50b67418-cb8d-434d-acc9-4a8324e7fdd2',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('055de204-6229-4200-87f7-e3c29f095017','a66737a0-c912-470f-9edf-983c7be0951f','befaf1ef-a595-4a32-b083-56eac51082b0',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('05f99ffd-abf2-4f5a-9ec8-f80a59967b89','f3567a6d-8a45-4174-b302-a629cdbfbe92',NULL,NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('0745a713-c7dc-451d-87c1-ec3dc28568b8','94942d82-8b87-4be3-a338-158f893573cd',NULL,NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('0915f727-0bc3-47c8-b9b2-25dc2ecef2bb','a20c5353-9e23-4b5d-bb34-09f2efe1e54d','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare AIP',1,'Failed',NULL,'2013-11-07 22:51:35'),('092b47db-6f77-4072-aed3-eb248ab69e9c','a8489361-b731-4d4a-861d-f4da1767665f','bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0',NULL,'Normalize',1,'Failed',NULL,'2013-11-15 00:31:31'),('09b85517-e5f5-415b-a950-1a60ee285242','21f8f2b6-d285-490a-9276-bfa87a0a4fb9','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-10 22:49:48'),('0a6558cf-cf5f-4646-977e-7d6b4fde47e8','21f8f2b6-d285-490a-9276-bfa87a0a4fb9','055de204-6229-4200-87f7-e3c29f095017',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('0b5ad647-5092-41ce-9fe5-1cc376d0bc3f','caaa29bc-a2b6-487b-abff-c3031a0e147a','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:39'),('0b92a510-a290-44a8-86d8-6b7139be29df','acd5e136-11ed-46fe-bf67-dc108f115d6b','f6fdd1a7-f0c5-4631-b5d3-19421155bd7a',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('0ba9bbd9-6c21-4127-b971-12dbc43c8119','63f265b3-57f5-4f14-90f5-cf0179dc366e','e888269d-460a-4cdf-9bc7-241c92734402',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('0c94e6b5-4714-4bec-82c8-e187e0c04d77','1b8b596f-b6ee-440f-b59c-5e8b39a2b46d',NULL,NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('0c96c798-9ace-4c05-b3cf-243cdad796b7','a73b3690-ac75-4030-bb03-0c07576b649b','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Include default Transfer processingMCP.xml',1,'Failed',NULL,'2012-10-02 00:25:06'),('0ca642b8-d6e7-4204-ac66-7209c3bae1b0','9c04a06d-f3f6-4cb9-bb47-ec3761c13903',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-11-10 02:08:12'),('0cc7077a-5c55-4229-ab7d-f92935e4f3d6','032bff90-0ec1-4c77-aa29-6a04183e99ef',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-11-10 02:09:39'),('0ceb8f18-8896-409b-891f-694c40d990fe','3694dc49-bcc5-4b70-8721-50de40985af7',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-11-10 02:09:44'),('0cf7efd6-5475-4eb2-b11c-ac796a59f1af','0853f765-5915-4e2d-b732-be56cdb05275',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-11-10 02:08:27'),('0d381b64-dadd-4d3c-886e-8f4dd508e3a8','17fd2d32-e84d-4103-aee1-74f72460e8f8',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-11-10 02:08:57'),('0d7f5dc2-b9af-43bf-b698-10fdcc5b014d','be4e3ee6-9be3-465f-93f0-77a4ccdfd1db',NULL,NULL,'Reject AIP',1,'Failed',NULL,'2013-03-27 20:12:26'),('0dd6144f-8ca8-4f0c-9596-0bb44f30065c','0040be51-608e-470b-8007-9edec255fe3e',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-11-10 02:08:08'),('0df8ce53-7a3b-4780-8bcc-2a8680130c88','513df2fd-62a7-4186-8f49-82b9cfbeae83',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-11-10 02:08:37'),('0e06d968-4b5b-4084-aab4-053a2a8d1679','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('0e1a8a6b-abcc-4ed6-b4fb-cbccfdc23ef5','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('0e379b19-771e-4d90-a7e5-1583e4893c56','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Clean up names',1,'Failed',NULL,'2012-10-02 00:25:06'),('0e41c244-6c3e-46b9-a554-65e66e5c9324','a75ee667-3a1c-4950-9194-e07d0e6bf545','95616c10-a79f-48ca-a352-234cc91eaf08',NULL,'Identify file format',1,'Failed',NULL,'2013-11-07 22:51:43'),('0f0c1f33-29f2-49ae-b413-3e043da5df61','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:39'),('0fc3c795-dc68-4aa0-86fc-cbd6af3302fa','0b90715c-50bc-4cb7-a390-771a7cc8180f','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-11-30 19:55:47'),('10c40e41-fb10-48b5-9d01-336cd958afe8','68920df3-66aa-44fc-b221-710dbe97680a','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:38'),('11033dbd-e4d4-4dd6-8bcf-48c424e222e3','f23a22b8-a3b0-440b-bf4e-fb6e8e6e6b14','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('14a0678f-9c2a-4995-a6bd-5acd141eeef1','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('150dcb45-46c3-4529-b35f-b0a8a5a553e9','e211ae41-bf9d-4f34-8b58-9a0dcc0bebe2',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('15402367-2d3f-475e-b251-55532347a3c2','243b67e9-4d0b-4c38-8fa4-0fa3df8a5b86',NULL,NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('154dd501-a344-45a9-97e3-b30093da35f5','76729a40-dfa1-4c1a-adbf-01fb362324f5','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('15a2df8a-7b45-4c11-b6fa-884c9b7e5c67','602e9b26-5839-4940-b230-0264bb873fe7','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-02-19 00:52:52'),('16415d2f-5642-496d-a46d-00028ef6eb0a','9371ba25-b600-485d-b2d8-cef2f39c35ed','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Create SIP from Transfer',1,'Failed',NULL,'2012-12-04 22:46:47'),('173d310c-8e40-4669-9a69-6d4c8ffd0396','73e12d44-ec3d-41a9-b138-80ec7e31ede5','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('1798e1d4-ec91-4299-a767-d10c32155d19','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21','a8489361-b731-4d4a-861d-f4da1767665f','8ce378a5-1418-4184-bf02-328a06e1d3be',NULL,'Normalize',1,'Failed',NULL,'2013-11-15 00:31:31'),('192315ea-a1bf-44cf-8cb4-0b3edd1522a6','3649f0f4-2174-44af-aef9-31ebeddeb73b','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Characterize and extract metadata',1,'Failed',NULL,'2013-11-07 22:51:43'),('19adb668-b19a-4fcb-8938-f49d7485eaf3','ad1f1ae6-658f-4281-abc2-fe2f6c5d5e8e',NULL,NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('1b1a4565-b501-407b-b40f-2f20889423f1','7beb3689-02a7-4f56-a6d1-9c9399f06842','c4898520-448c-40fc-8eb3-0603b6aacfb7',NULL,'Characterize and extract metadata',1,'Failed',NULL,'2012-10-02 00:25:06'),('1b737a9b-b4c0-4230-aa92-1e88067534b9','256e18ca-1bcd-4b14-b3d5-4efbad5663fc','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-11-30 19:55:48'),('1ba589db-88d1-48cf-bb1a-a5f9d2b17378','fecb3fe4-5c5c-4796-b9dc-c7d7cf33a9f3','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('1c0f5926-fd76-4571-a706-aa6564555199','90e0993d-23d4-4d0c-8b7d-73717b58f20e','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('1c2550f1-3fc0-45d8-8bc4-4c06d720283b','3c002fb6-a511-461e-ad16-0d2c46649374','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Scan for viruses',1,'Failed',NULL,'2012-10-02 00:25:06'),('1c7726a4-9165-4809-986a-bf4477c719ca','acd5e136-11ed-46fe-bf67-dc108f115d6b','26cf64e2-21b5-4935-a52b-71695870f1f2',NULL,'Normalize',1,'Failed',NULL,'2013-01-10 22:49:49'),('1cb7e228-6e94-4c93-bf70-430af99b9264','09f73737-f7ca-4ea2-9676-d369f390e650','303a65f6-a16f-4a06-807b-cb3425a30201',NULL,'Extract packages',1,'Completed successfully',NULL,'2013-11-07 22:51:43'),('1cd3b36a-5252-4a69-9b1c-3b36829288ab','5a3d244e-c7a1-4cd9-b1a8-2890bf1f254c','67b44f8f-bc97-4cb3-b6dd-09dba3c99d30',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('20129b22-8f28-429b-a3f2-0648090fa305','eb14ba91-20cb-4b0e-ab5d-c30bfea4dbc8','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-12-06 18:58:24'),('20515483-25ed-4133-b23e-5bb14cab8e22','bf71562c-bc87-4fd0-baa6-1d85ff751ea2','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Store AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('208d441b-6938-44f9-b54a-bd73f05bc764','e82c3c69-3799-46fd-afc1-f479f960a362','f025f58c-d48c-4ba1-8904-a56d2a67b42f',NULL,'Verify SIP compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('209400c1-5619-4acc-b091-b9d9c8fbb1c0','cfc7f6be-3984-4727-a71a-02ce27bef791','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Include default Transfer processingMCP.xml',1,'Failed',NULL,'2012-10-02 00:25:06'),('214f1004-2748-4bed-a38d-48fe500c41b9','f6fbbf4f-bf8d-49f2-a978-8d689380cafc','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-12-12 21:25:31'),('21d6d597-b876-4b3f-ab85-f97356f10507','9a0f8eac-6a9d-4b85-8049-74954fbd6594','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Scan for viruses',1,'Failed',NULL,'2012-10-02 00:25:06'),('22c0f074-07b1-445f-9e8b-bf75ac7f0b48','ad38cdea-d1da-4d06-a7e5-6f75da85a718','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Rename with transfer UUID',1,'Failed',NULL,'2012-10-02 00:25:06'),('22ded604-6cc0-444b-b320-f96afb15d581','a75ee667-3a1c-4950-9194-e07d0e6bf545','bd382151-afd0-41bf-bb7a-b39aef728a32',NULL,'Extract packages',1,'Failed',NULL,'2013-11-07 22:51:43'),('2307b24a-a019-4b5b-a520-a6fff270a852','5092ff10-097b-4bac-a4d8-9b4766aaf40d','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('2483c25a-ade8-4566-a259-c6c37350d0d6','13aaa76e-41db-4bff-8519-1f9ba8ca794f','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-12-04 20:13:09'),('2522d680-c7d9-4d06-8b11-a28d8bd8a71f','8558d885-d6c2-4d74-af46-20da45487ae7','1cb7e228-6e94-4c93-bf70-430af99b9264',NULL,'Identify file format',1,'Failed',NULL,'2013-11-07 22:51:42'),('2584b25c-8d98-44b7-beca-2b3ea2ea2505','9dd95035-e11b-4438-a6c6-a03df302933c','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Clean up names',1,'Failed',NULL,'2012-10-02 00:25:06'),('25b5dc50-d42d-4ee2-91fc-5dcc3eef30a7','4d2ed238-1b35-43fb-9753-fcac0ede8da4','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('25b8ddff-4074-4803-a0dc-bbb3acd48a97','ad38cdea-d1da-4d06-a7e5-6f75da85a718','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('26bf24c9-9139-4923-bf99-aa8648b1692b','80ebef4c-0dd1-45eb-b993-1db56a077db8','f2a019ea-0601-419c-a475-1b96a927a2fb',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-11-06 01:03:43'),('26cf64e2-21b5-4935-a52b-71695870f1f2','21f8f2b6-d285-490a-9276-bfa87a0a4fb9','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-10 22:49:49'),('2714cd07-b99f-40e3-9ae8-c97281d0d429','bf5a1f0c-1b3e-4196-b51f-f6d509091346','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('2872d007-6146-4359-b554-6e9fe7a8eca6','dde51fc1-af7d-4923-ad6a-06e670447a2a','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('288b739d-40a1-4454-971b-812127a5e03d','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('28a9f8a8-0006-4828-96d5-892e6e279f72','1c7de28f-8f18-41c7-b03a-19f900d38f34','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('29dece8e-55a4-4f2c-b4c2-365ab6376ceb','ec503c22-1f4d-442f-b546-f90c9a9e5c86','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('2a62f025-83ec-4f23-adb4-11d5da7ad8c2','abeaa79e-668b-4de0-b8cb-70f8ab8056b6','11033dbd-e4d4-4dd6-8bcf-48c424e222e3',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('2adf60a0-ecd7-441a-b82f-f77c6a3964c3','3ad0db9a-f57d-4664-ad34-947404dddd04',NULL,NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('2d32235c-02d4-4686-88a6-96f4d6c7b1c3','bec683fa-f006-48a4-b298-d33b3b681cb2',NULL,NULL,'Store AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('2d751fc6-dc9d-4c52-b0d9-a4454cefb359','0732af8f-d60b-43e0-8f75-8e89039a05a8','b063c4ce-ada1-4e72-a137-800f1c10905c',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('2dd53959-8106-457d-a385-fee57fc93aa9','8558d885-d6c2-4d74-af46-20da45487ae7','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:42'),('2e7f83f9-495a-44b3-b0cf-bff66f021a4d','3875546f-9137-4c8f-9fcc-ed112eaa6414','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Failed transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('2f83c458-244f-47e5-a302-ce463163354e','4773c7e4-df8b-4928-acdd-1e9a3235b4b1',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('2fd123ea-196f-4c9c-95c0-117aa65ed9c6','0c1664f2-dfcb-46d9-bd9e-5b604baef788','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Identify DSpace files',1,'Failed',NULL,'2012-10-02 00:25:06'),('303a65f6-a16f-4a06-807b-cb3425a30201','f6141d04-a473-47f7-b8ac-25deac01a513','1b1a4565-b501-407b-b40f-2f20889423f1',NULL,'Characterize and extract metadata',1,'Failed',NULL,'2012-10-02 00:25:06'),('31abe664-745e-4fef-a669-ff41514e0083','acd5e136-11ed-46fe-bf67-dc108f115d6b','09b85517-e5f5-415b-a950-1a60ee285242',NULL,'Normalize',1,'Failed',NULL,'2013-01-10 22:49:49'),('31fc3f66-34e9-478f-8d1b-c29cd0012360','135dd73d-845a-412b-b17e-23941a3d9f78','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('3229e01f-adf3-4294-85f7-4acb01b3fbcf','64a859be-f362-45d1-b9b4-4e15091f686f','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('333532b9-b7c2-4478-9415-28a3056d58df','e20ea90b-fa16-4576-8647-199ecde0d511',NULL,NULL,'Reject transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('33d7ac55-291c-43ae-bb42-f599ef428325','530b3b90-b97a-4aaf-836f-3a889ad1d7d2','576f1f43-a130-4c15-abeb-c272ec458d33',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('3409b898-e532-49d3-98ff-a2a1f9d988fa','3df5643c-2556-412f-a7ac-e2df95722dae','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Generate METS.xml document',1,'Failed',NULL,'2012-10-02 00:25:06'),('3467d003-1603-49e3-b085-e58aa693afed','be4e3ee6-9be3-465f-93f0-77a4ccdfd1db',NULL,NULL,'Reject SIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('35c8763a-0430-46be-8198-9ecb23f895c8','f452a117-a992-4447-9774-6a8130f05b30','180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('36609513-6502-4aca-886a-6c4ae03a9f05','4554c5f9-52f9-440c-bc69-0f7be3651949','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Approve SIP creation',1,'Failed',NULL,'2013-04-19 22:39:27'),('370aca94-65ab-4f2a-9d7d-294a62c8b7ba','bd9769ba-4182-4dd4-ba85-cff24ea8733e','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('377f8ebb-7989-4a68-9361-658079ff8138','99712faf-6cd0-48d1-9c66-35a2033057cf',NULL,NULL,'Failed transfer',1,'Failed',NULL,'2013-01-08 02:12:00'),('378ae4fc-7b62-40af-b448-a1ab47ac2c0c','90e0993d-23d4-4d0c-8b7d-73717b58f20e','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('3868c8b8-977d-4162-a319-dc487de20f11','ad38cdea-d1da-4d06-a7e5-6f75da85a718','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-11-30 19:55:48'),('38c591d4-b7ee-4bc0-b993-c592bf15d97d','62ba16c8-4a3f-4199-a48e-d557a90728e2','f92dabe5-9dd5-495e-a996-f8eb9ef90f48',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('39a128e3-c35d-40b7-9363-87f75091e1ff','73ad6c9d-8ea1-4667-ae7d-229656a49237','3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5',NULL,'Create SIP from Transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('39ac9205-cb08-47b1-8bc3-d3375e37d9eb','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('39e58573-2dbc-4939-bce0-96b2f55dae28','f872b932-90dd-4501-98c4-9fc5bac9d19a',NULL,NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('3ba518ab-fc47-4cba-9b5c-79629adac10b','d7542890-281f-4cdb-a64c-4b6bdd88c4b8','3e25bda6-5314-4bb4-aa1e-90900dce887d',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('3c526a07-c3b8-4e53-801b-7f3d0c4857a5','feac0c04-3511-4e91-9403-5c569cff7bcc','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('3e25bda6-5314-4bb4-aa1e-90900dce887d','c075014f-4051-441a-b16b-3083d5c264c5','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5','39ac9ff8-d312-4033-a2c6-44219471abda',NULL,NULL,'Create SIP from Transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('3f543585-fa4f-4099-9153-dd6d53572f5c','b57b3564-e271-4226-a5f9-2c7cf1661a83','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Store AIP',1,'Failed',NULL,'2013-11-07 22:51:35'),('4103a5b0-e473-4198-8ff7-aaa6fec34749','ea463bfd-5fa2-4936-b8c3-1ce3b74303cf','092b47db-6f77-4072-aed3-eb248ab69e9c',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('424ee8f1-6cdd-4960-8641-ed82361d3ad7','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('438dc1cf-9813-44b5-a0a3-58e09ae73b8a','fbaadb5d-63f9-440c-a607-a4ebfb973a78','2e7f83f9-495a-44b3-b0cf-bff66f021a4d',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('440ef381-8fe8-4b6e-9198-270ee5653454','51e31d21-3e92-4c9f-8fec-740f559285f2','39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Normalize',1,'Failed',NULL,'2013-11-15 00:31:31'),('4417b129-fab3-4503-82dd-740f8e774bff','0bb3f551-1418-4b99-8094-05a43fcd9537','fdfac6e5-86c0-4c81-895c-19a9edadedef',NULL,'Rename with transfer UUID',1,'Failed',NULL,'2013-11-07 22:51:43'),('4430077a-92c5-4d86-b0f8-0d31bdb731fb','3c04068f-20b8-4cbc-8166-c61faacb6628','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('45063ad6-f374-4215-a2c4-ac47be4ce2cd','b3875772-0f3b-4b03-b602-5304ded86397','61af079f-46a2-48ff-9b8a-0c78ba3a456d',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('45f01e11-47c7-45a3-a99b-48677eb321a5','06334a2c-82ed-477b-af0b-9c9f3dcade99',NULL,NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('45f4a7e3-87cf-4fb4-b4f9-e36ad8c853b1','ad38cdea-d1da-4d06-a7e5-6f75da85a718','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('46dcf7b1-3750-4f49-a9be-a4bf076e304f','2e3c3f0f-069e-4ca1-b71b-93f4880a39b5','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('46e19522-9a71-48f1-9ccd-09cabfba3f38','a71f40ec-77b2-4f13-91b6-da3d4a67a284','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('478512a6-10e4-410a-847d-ce1e25d8d31c','6af5d804-de90-4c5b-bdba-e15a89e1a3db','25b8ddff-4074-4803-a0dc-bbb3acd48a97',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('47c83e01-7556-4c13-881f-282c6d9c7d6a','c310a18a-1659-45d0-845e-06eb3321512f','4103a5b0-e473-4198-8ff7-aaa6fec34749',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('47dd6ea6-1ee7-4462-8b84-3fc4c1eeeb7f','f908bcd9-2fba-48c3-b04b-459f6ad1a4de','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('48199d23-afd0-4b9b-b8a3-cd80c7d45e7c','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('48703fad-dc44-4c8e-8f47-933df3ef6179','134a1a94-22f0-4e67-be17-23a4c7178105','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Store AIP',1,'Failed',NULL,'2013-11-07 22:51:35'),('48bfc7e1-75ed-44eb-a65c-0701c022d934','38324d67-8358-4679-902d-c20dcdfd548b','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('49cbcc4d-067b-4cd5-b52e-faf50857b35a','75e00332-24a3-4076-aed1-e3dc44379227','2d32235c-02d4-4686-88a6-96f4d6c7b1c3',NULL,'Store AIP',1,'Failed',NULL,'2013-11-07 22:51:35'),('4ac461f9-ee69-4e03-924f-60ac0e8a4b7f','2865c5e7-55c4-44d4-ab6f-144f209ad48f','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('4b75ca30-2eaf-431b-bffa-d737c8a0bf37','ad38cdea-d1da-4d06-a7e5-6f75da85a718','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('4df4cc06-3b03-4c6f-b5c4-bec12a97dc90','29937fd7-b482-4180-8037-1b57d71e903c','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('4edfe7e4-82ff-4c0a-ba5f-29f1ee14e17a','674e21f3-1c50-4185-8e5d-70b1ed4a7f3a','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('4ef35d72-9494-431a-8cdb-8527b42664c7','3f8ccc75-8109-4171-b5c4-062189745a37','76d87f57-9718-4f68-82e6-91174674c49c',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('50b67418-cb8d-434d-acc9-4a8324e7fdd2','549181ed-febe-487a-a036-ed6fdfa10a86','ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('5158c618-6160-41d6-bbbe-ddf34b5b06bc','dee46f53-8afb-4aec-820e-d495bcbeaf20','f09847c2-ee51-429a-9478-a860477f6b8d',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('52269473-5325-4a11-b38a-c4aafcbd8f54','e601b1e3-a957-487f-8cbe-54160070574d','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('55de1490-f3a0-4e1e-a25b-38b75f4f05e3','07f6f419-d51f-4c69-bca6-a395adecbee0','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('561bbb52-d95c-4004-b0d3-739c0a65f406','9649186d-e5bd-4765-b285-3b0d8e83b105','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Create SIP from Transfer',1,'Failed',NULL,'2013-04-19 22:39:27'),('56da7758-913a-4cd2-a815-be140ed09357','547f95f6-3fcd-45e1-98b6-a8a7d9097373','8ce130d4-3f7e-46ec-868a-505cf9033d96',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('576f1f43-a130-4c15-abeb-c272ec458d33','1e02e82a-2055-4f37-af3a-7dc606f9fd97','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('58fcd2fd-bcdf-4e49-ad99-7e24cc8c3ba5','5a9fbb03-2434-4034-b20f-bcc6f971a8e5','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('5b7a48e1-32ed-43f9-8ffa-e374010fcf76','ad38cdea-d1da-4d06-a7e5-6f75da85a718','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('5bddbb67-76b4-4bcb-9b85-a0d9337e7042','008e5b38-b19c-48af-896f-349aaf5eba9f','83484326-7be7-4f9f-b252-94553cd42370',NULL,'Normalize',1,'Failed',NULL,'2012-10-24 02:41:24'),('5c0d8661-1c49-4023-8a67-4991365d70fb','246c34b0-b785-485f-971b-0ed9f82e1ae3','39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('5c459c1a-f998-404d-a0dd-808709510b72','108f7f4c-72f2-4ddb-910a-24f173d64fa7',NULL,NULL,'Failed transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('5cf308fd-a6dc-4033-bda1-61689bb55ce2','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Failed transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('5d6a103c-9a5d-4010-83a8-6f4c61eb1478','4745d0bb-910c-4c0d-8b81-82d7bfca7819','74665638-5d8f-43f3-b7c9-98c4c8889766',NULL,'Normalize',1,'Failed',NULL,'2012-10-24 00:40:06'),('5e4bd4e8-d158-4c2a-be89-51e3e9bd4a06','528c8fe3-265f-45dd-b5c0-1a4ac0e15954','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Verify transfer checksum',1,'Failed',NULL,'2012-10-02 00:25:06'),('5e4f7467-8637-49b2-a584-bae83dabf762','24deba11-c719-4c64-a53c-e08c85663c40','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('5f213529-ced4-49b0-9e30-be4e0c9b81d5','74146fe4-365d-4f14-9aae-21eafa7d8393','3f543585-fa4f-4099-9153-dd6d53572f5c',NULL,'Store AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('5fbc344c-19c8-48be-a753-02dac987428c','feb27f44-3575-4d17-8e00-43aa5dc5c3dc','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('60b0e812-ebbe-487e-810f-56b1b6fdd819','cd53e17c-1dd1-4e78-9086-e6e013a64536','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('61a8de9c-7b25-4f0f-b218-ad4dde261eed','9a70cc32-2b0e-4763-a168-b81485fac366','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('61af079f-46a2-48ff-9b8a-0c78ba3a456d','54a05ec3-a34f-4404-96ec-36b527445da9',NULL,NULL,'Include default Transfer processingMCP.xml',1,'Failed',NULL,'2012-10-02 00:25:06'),('61c316a6-0a50-4f65-8767-1f44b1eeb6dd','32b2600c-6907-4cb2-b18a-3986f0842219','377f8ebb-7989-4a68-9361-658079ff8138','1a23e63b-0d5c-4573-8eef-d51e502b75b4','Failed transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('6327fdf9-9673-42a8-ace5-cccad005818b','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('635ba89d-0ad6-4fc9-acc3-e6069dffdcd5','ce48a9f5-4513-49e2-83db-52b01234705b','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('651236d2-d77f-4ca7-bfe9-6332e96608ff','7058a655-82f3-455c-9245-ad8e87e77a4f','e3efab02-1860-42dd-a46c-25601251b930',NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('65240550-d745-4afe-848f-2bf5910457c9','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('65916156-41a5-4ed2-9472-7dca11e6bc08','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('663a11f6-91cb-4fef-9aa7-2594b3752e4c','c6f9f99a-0b60-438f-9a8d-35d4989db2bb','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('66c9c178-2224-41c6-9c0b-dcb60ff57b1a','450794b5-db3e-4557-8ab8-1abd77786429','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('67a91b4b-a5af-4b54-a836-705e6cf4eeb9','f661aae0-05bf-4f55-a2f6-ef0f157231bd',NULL,NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('67b44f8f-bc97-4cb3-b6dd-09dba3c99d30','143b4734-9c33-4f6e-9af0-2dc09cf9017a','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('6b39088b-683e-48bd-ab89-9dab47f4e9e0','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('6b931965-d5f6-4611-a536-39d5901f8f70','b3b86729-470f-4301-8861-d62574966747','0a6558cf-cf5f-4646-977e-7d6b4fde47e8',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('6bd4d385-c490-4c42-a195-dace8697891c','13aaa76e-41db-4bff-8519-1f9ba8ca794f','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Include default Transfer processingMCP.xml',1,'Failed',NULL,'2012-10-02 00:25:06'),('6ee25a55-7c08-4c9a-a114-c200a37146c4','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('6fe4678a-b3fb-4144-a8a3-7386eb87247d','c5d7e646-01b1-4d4a-9e38-b89d97e77e33','e3efab02-1860-42dd-a46c-25601251b930',NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('70669a5b-01e4-4ea0-ac70-10292f87da05','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Verify SIP compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('70f41678-baa5-46e6-a71c-4b6b4d99f4a6','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('745340f5-5741-408e-be92-34c596c00209','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:39'),('74665638-5d8f-43f3-b7c9-98c4c8889766','235c3727-b138-4e62-9265-c8f07761a5fa','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('746b1f47-2dad-427b-8915-8b0cb7acccd8','55f0e6fa-834c-44f1-89f3-c912e79cea7d','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('7509e7dc-1e1b-4dce-8d21-e130515fce73','2bfd7cef-dcf8-4587-8043-2c69c612a6e3',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('755b4177-c587-41a7-8c52-015277568302','de195451-989e-48fe-ad0c-3ff2265b3410',NULL,NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('75fb5d67-5efa-4232-b00b-d85236de0d3f','33c0dea0-da6c-4b8f-8038-6e95844eea95','ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0',NULL,'Prepare AIP',1,'Failed',NULL,'2013-02-08 22:18:49'),('76d87f57-9718-4f68-82e6-91174674c49c','1a6bdb05-f66b-4708-935e-75b819637dd2','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('77a7fa46-92b9-418e-aa88-fbedd4114c9f','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('77c722ea-5a8f-48c0-ae82-c66a3fa8ca77','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('78b7adff-861d-4450-b6dd-3fabe96a849e','ce57ffbc-abd9-43dc-a09b-e888397488f2','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:39'),('7a024896-c4f7-4808-a240-44c87c762bc5','f8d0b7df-68e8-4214-a49d-60a91ed27029','2dd53959-8106-457d-a385-fee57fc93aa9',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:42'),('7a134af0-b285-4a9f-8acf-f6947b7ed072','5c831a10-5d75-44ca-9741-06fdfc72052a','56da7758-913a-4cd2-a815-be140ed09357',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('7b146689-1a04-4f58-ba86-3caf2b76ddbc','c3e3f03d-c104-48c3-8c64-4290459965f4','f3a39155-d655-4336-8227-f8c88e4b7669',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1','4d56a90c-8d9f-498c-8331-cf469fcb3147','bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1',NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 14:25:06'),('7c44c454-e3cc-43d4-abe0-885f93d693c6','502a8bc4-88b1-41b0-8821-f8afd984036e',NULL,NULL,'Store AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('7c6a0b72-f37b-4512-87f3-267644de6f80','52d646df-fd66-4157-b8aa-32786fef9481','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Verify transfer checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('7c95b242-1ce5-4210-b7d4-fdbb6c0aa5dd','6ed7ec07-5df1-470b-9a2e-a934cba8af26','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Rename with transfer UUID',1,'Failed',NULL,'2012-10-02 00:25:06'),('7d43afab-4d3e-4733-a3f2-84eb772e9e57','c5e80ef1-aa90-45b2-beb4-c42652acf3e7',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('7d728c39-395f-4892-8193-92f086c0546f','32b2600c-6907-4cb2-b18a-3986f0842219','828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c','1a23e63b-0d5c-4573-8eef-d51e502b75b4','Failed SIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('7e65c627-c11d-4aad-beed-65ceb7053fe8','f5ca3e51-35ba-4cdd-acf5-7d4fec955e76','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('823b0d76-9f3c-410d-83ab-f3c2cdd9ab22','99324102-ebe8-415d-b5d8-b299ab2f4703','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Rename SIP directory with SIP UUID',1,'Failed',NULL,'2013-11-07 22:51:43'),('828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c','59ebdcec-eacc-4daf-978a-1b0d8652cd0c',NULL,NULL,'Failed SIP',1,'Failed',NULL,'2013-01-08 02:12:00'),('82c0eca0-d9b6-4004-9d77-ded9286a9ac7','95d2ddff-a5e5-49cd-b4da-a5dd6fd3d2eb','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('83257841-594d-4a0e-a4a1-1e9269c30f3d','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('83484326-7be7-4f9f-b252-94553cd42370','26ec68d5-8d33-4fe2-bc11-f06d80fb23e0',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-23 19:41:22'),('83d5e887-6f7c-48b0-bd81-e3f00a9da772','032347f1-c0fb-4c6c-96ba-886ac8ac636c','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('87e7659c-d5de-4541-a09c-6deec966a0c0','5044f7ec-96f9-4bf1-8540-671e543c2411','61af079f-46a2-48ff-9b8a-0c78ba3a456d',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('88807d68-062e-4d1a-a2d5-2d198c88d8ca','ef024cf9-1737-4161-b48a-13b4a8abddcd','ee438694-815f-4b74-97e1-8e7dde2cc6d5',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('888a5bdc-9928-44f0-9fb7-91bc5f1e155b','6f5d5518-1ed4-49b8-9cd5-497d112c97e4','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-11-30 19:55:47'),('88affaa2-13c5-4efb-a860-b182bd46c2c6','ac99ec32-7732-4cfe-9cac-579af16f6734','f060d17f-2376-4c0b-a346-b486446e46ce',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('88d2120a-4d19-4b47-922f-7438be1f52a2','3ae4931e-886e-4e0a-9a85-9b047c9983ac','89071669-3bb6-4e03-90a3-3c8b20c7f6fe',NULL,'Failed transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('89071669-3bb6-4e03-90a3-3c8b20c7f6fe','0ae50158-a6e2-4663-a684-61d9a8384789',NULL,NULL,'Failed transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('8adb23cc-dee3-44da-8356-fa6ce849e4d6','a8489361-b731-4d4a-861d-f4da1767665f','d77ccaa0-3a3d-46ff-877f-4edf1a8179e2',NULL,'Normalize',1,'Failed',NULL,'2013-11-15 00:31:31'),('8ba83807-2832-4e41-843c-2e55ad10ea0b','fe354b27-dbb2-4454-9c1c-340d85e67b78','74665638-5d8f-43f3-b7c9-98c4c8889766',NULL,'Normalize',1,'Failed',NULL,'2012-10-24 00:40:06'),('8bc92801-4308-4e3b-885b-1a89fdcd3014','8850aeff-8553-4ff1-ab31-99b5392a458b','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process metadata directory',1,'Failed',NULL,'2013-02-13 22:03:39'),('8ce130d4-3f7e-46ec-868a-505cf9033d96','a8489361-b731-4d4a-861d-f4da1767665f','ef8bd3f3-22f5-4283-bfd6-d458a2d18f22',NULL,'Normalize',1,'Failed',NULL,'2013-11-15 00:31:31'),('8ce378a5-1418-4184-bf02-328a06e1d3be','51e31d21-3e92-4c9f-8fec-740f559285f2','83257841-594d-4a0e-a4a1-1e9269c30f3d',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('8db10a7b-924f-4561-87b4-cb6078c65aab','07bf7432-fd9b-456e-9d17-5b387087723a','3868c8b8-977d-4162-a319-dc487de20f11',NULL,'TRIM transfer',1,'Failed',NULL,'2012-11-30 19:55:48'),('8dc0284a-45f4-486e-a78d-7af3e5b8d621','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('8de9fe10-932f-4151-88b0-b50cf271e156','bacb088a-66ef-4590-b855-69f21dfdf87a','e219ed78-2eda-4263-8c0f-0c7f6a86c33e',NULL,'Normalize',1,'Failed',NULL,'2012-10-24 00:40:07'),('8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc','81d64862-a4f6-4e3f-b32e-47268d9eb9a3','eb52299b-9ae6-4a1f-831e-c7eee0de829f',NULL,'Identify DSpace files',1,'Failed',NULL,'2012-10-02 00:25:06'),('8f639582-8881-4a8b-8574-d2f86dc4db3d','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Create SIP from Transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('9071c352-aed5-444c-ac3f-b6c52dfb65ac','a2e93146-a3ff-4e6c-ae3d-76ce49ca5e1b','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('91ca6f1f-feb5-485d-99d2-25eed195e330','0a521e24-b376-4a9c-9cd6-ce41e187179a','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:38'),('92879a29-45bf-4f0b-ac43-e64474f0f2f9','16b8cc42-68b6-4751-b497-3e3a64101bbb',NULL,NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('9304d028-8387-4ab5-9539-0aab9ac5bdb1','24f82c1a-5de7-4b2a-8ac2-68a48edf252f','45f01e11-47c7-45a3-a99b-48677eb321a5',NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('9520386f-bb6d-4fb9-a6b6-5845ef39375f','c450501a-251f-4de7-acde-91c47cf62e36','77c722ea-5a8f-48c0-ae82-c66a3fa8ca77',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('95616c10-a79f-48ca-a352-234cc91eaf08','09f73737-f7ca-4ea2-9676-d369f390e650','bd382151-afd0-41bf-bb7a-b39aef728a32',NULL,'Extract packages',1,'Failed',NULL,'2013-11-07 22:51:43'),('9619706c-385a-472c-8144-fd5885c21532','3dbdc8cc-510c-4aa4-ab29-6645b84864ba','4ac461f9-ee69-4e03-924f-60ac0e8a4b7f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('998044bb-6260-452f-a742-cfb19e80125b','acf7bd62-1587-4bff-b640-5b34b7196386',NULL,NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('9e3dd445-551d-42d1-89ba-fe6dff7c6ee6','97cc7629-c580-44db-8a41-68b6b2f23be4','e219ed78-2eda-4263-8c0f-0c7f6a86c33e',NULL,'Normalize',1,'Failed',NULL,'2012-10-24 00:40:07'),('9e4e39be-0dad-41bc-bee0-35cb71e693df','b6167c79-1770-4519-829c-fa01718756f4','209400c1-5619-4acc-b091-b9d9c8fbb1c0',NULL,'Include default Transfer processingMCP.xml',1,'Failed',NULL,'2012-10-02 00:25:06'),('9e9b522a-77ab-4c17-ab08-5a4256f49d59','ff8f70b9-e345-4163-a784-29b432b12558','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:39'),('9fa0a0d1-25bb-4507-a5f7-f177d7fa920d','1423da1c-e9f8-479c-9949-4238c59899ac',NULL,NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('a132193a-2e79-4221-a092-c51839d566fb','e9f57845-4609-4e0a-a573-4b488d8a4aeb',NULL,NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('a1b65fe3-9358-479b-93b9-68f2b5e71b2b','c307d6bd-cb81-46a1-89f1-bb02a43e0a3a','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:39'),('a2173b55-abff-4d8f-97b9-79cc2e0a64fa','56aef696-b752-42de-9c6d-0a436bcc6870','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('a329d39b-4711-4231-b54e-b5958934dccb','16eaacad-e180-4be1-a13c-35ab070808a7','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Clean up names',1,'Failed',NULL,'2012-10-02 00:25:06'),('a46e95fe-4a11-4d3c-9b76-c5d8ea0b094d','04c7e0fb-ec4e-4637-a7b7-41601d5523bd','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Clean up names',1,'Failed',NULL,'2012-10-02 00:25:06'),('a536965b-e501-42aa-95eb-0656775be6f2','94da9e56-46aa-4215-bcd8-062fed887a36','88affaa2-13c5-4efb-a860-b182bd46c2c6',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('a58bd669-79af-4999-8654-951f638d4457','8b846431-5da9-4743-906d-2cdc4e777f8f','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:42'),('a6e97805-a420-41af-b708-2a56de5b47a6','7872599e-ebfc-472b-bb11-524ff728679f','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('a72afc44-fa28-4de7-b35f-c79b9f01aa5c','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('a98ba456-3dcd-4f45-804c-a40220ddc6cb','8fa944df-1baf-4f89-8106-af013b5078f4','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Failed transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('aa9ba088-0b1e-4962-a9d7-79d7a0cbea2d','dde8c13d-330e-458b-9d53-0937370695fa','45063ad6-f374-4215-a2c4-ac47be4ce2cd',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-11-06 00:59:43'),('aaa929e4-5c35-447e-816a-033a66b9b90b','8558d885-d6c2-4d74-af46-20da45487ae7','303a65f6-a16f-4a06-807b-cb3425a30201',NULL,'Extract packages',1,'Failed',NULL,'2013-11-07 22:51:43'),('ab0d3815-a9a3-43e1-9203-23a40c00c551','4ad0eecf-aa6e-4e3c-afe4-7e230cc671b2','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:38'),('ab69c494-23b7-4f50-acff-2e00cf7bffda','c409f2b0-bcb7-49ad-a048-a217811ca9b6',NULL,NULL,'Approve SIP creation',1,'Failed',NULL,'2012-10-02 00:25:06'),('abd6d60c-d50f-4660-a189-ac1b34fafe85','f1586bd7-f550-4588-9f45-07a212db7994','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Create SIP from Transfer',1,'Failed',NULL,'2013-04-05 23:08:30'),('ac85a1dc-272b-46ac-bb3e-5bf3f8e56348','a0aecc16-3f78-4579-b6d4-a10df1f89a41','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('ad011cc2-b0eb-4f51-96bb-400149a2ea11','d49684b1-badd-4802-b54e-06eb6b329140','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('b04e9232-2aea-49fc-9560-27349c8eba4e','bf9b2fb7-43bd-4c3e-9dd0-7b6f43e6cb48','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Create SIP from Transfer',1,'Failed',NULL,'2012-12-06 17:59:43'),('b063c4ce-ada1-4e72-a137-800f1c10905c','b8403044-12a3-4b63-8399-772b9adace15','83484326-7be7-4f9f-b252-94553cd42370',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('b15c0ba6-e247-4512-8b56-860fd2b6299d','ce52ace2-68fc-4bfb-8444-f32ec8c01783',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-24 17:04:11'),('b20ff203-1472-40db-b879-0e59d17de867','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('b21018df-f67d-469a-9ceb-ac92ac68654e','7b07859b-015e-4a17-8bbf-0d46f910d687','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process metadata directory',1,'Failed',NULL,'2013-02-13 22:03:39'),('b2552a90-e674-4a40-a482-687c046407d3','c74dfa47-9a6d-4a12-bffe-bf610ab75db9','21d6d597-b876-4b3f-ab85-f97356f10507',NULL,'Extract attachments',1,'Failed',NULL,'2012-10-02 00:25:06'),('b320ce81-9982-408a-9502-097d0daa48fa','fb64af31-8f8a-4fe5-a20d-27ee26c9dda2',NULL,NULL,'Store AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3','9413e636-1209-40b0-a735-74ec785ea14a','2307b24a-a019-4b5b-a520-a6fff270a852',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('b3d11842-0090-420a-8919-52d7039d50e6','3f3ab7ae-766e-4405-a05a-5ee9aea5042f','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Rename SIP directory with SIP UUID',1,'Failed',NULL,'2013-11-07 22:51:43'),('b443ba1a-a0b6-4f7c-aeb2-65bd83de5e8b','31707047-5d61-4b9f-ba58-1353d6c38e0c','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:40'),('b4567e89-9fea-4256-99f5-a88987026488','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('b6b0fe37-aa26-40bd-8be8-d3acebf3ccf8','5bd51fcb-6a68-4c5f-b99e-4fc36f51c40c','b21018df-f67d-469a-9ceb-ac92ac68654e',NULL,'Process metadata directory',1,'Failed',NULL,'2013-02-13 22:03:40'),('b6c9de5a-4a9f-41e1-a524-360bdca39893','23ad16a5-49fe-409d-98d9-f5a8de333f81','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Generate METS.xml',1,'Failed',NULL,'2012-10-02 00:25:06'),('b963a646-0569-43c4-89a2-e3b814c5c08e','fa3e0099-b891-43f6-a4bc-390d544fa3e9',NULL,NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('bb194013-597c-4e4a-8493-b36d190f8717','f1f0409b-d4f8-419a-b625-218dc1abd335',NULL,NULL,'Create SIP from Transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1','bcff2873-f006-442e-9628-5eadbb8d0db7','e3efab02-1860-42dd-a46c-25601251b930',NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 14:25:06'),('bbfbecde-370c-4e26-8087-cfa751e72e6a','d1004e1d-f938-4c68-ba70-0e0ae508cbbe',NULL,NULL,'Failed transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0','2d9483ef-7dbb-4e7e-a9c6-76ed4de52da9','440ef381-8fe8-4b6e-9198-270ee5653454',NULL,'Normalize',1,'Failed',NULL,'2013-11-15 00:31:31'),('bd382151-afd0-41bf-bb7a-b39aef728a32','445d6579-ee40-47d0-af6c-e2f6799f450d','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Characterize and extract metadata',1,'Failed',NULL,'2013-11-07 22:51:43'),('bdfecadc-8219-4109-885c-cfb9ef53ebc3','fa2307df-e42a-4553-aaf5-b08879b0cbf4','823b0d76-9f3c-410d-83ab-f3c2cdd9ab22',NULL,'Rename SIP directory with SIP UUID',1,'Failed',NULL,'2013-11-07 22:51:43'),('befaf1ef-a595-4a32-b083-56eac51082b0','30e72f4d-0999-44a1-a7ef-c8d07b179d54','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('bf6873f4-90b8-4393-9057-7f14f4687d72','483d0fc9-8f89-4699-b90b-7be250bab743','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('bfade79c-ab7b-11e2-bace-08002742f837','bfb30b76-ab7b-11e2-bace-08002742f837','0d7f5dc2-b9af-43bf-b698-10fdcc5b014d',NULL,'Reject AIP',1,'Failed',NULL,'2013-04-22 18:37:56'),('c103b2fb-9a6b-4b68-8112-b70597a6cd14','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('c1339015-e15b-4303-8f37-a2516669ac4e','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('c168f1ee-5d56-4188-8521-09f0c5475133','449530ec-cd94-4d8c-aae0-3b7cd2e2d5f9','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process metadata directory',1,'Failed',NULL,'2013-02-13 22:03:40'),('c2e6600d-cd26-42ed-bed5-95d41c06e37b','2d0b36bb-5c82-4ee5-b54c-f3e146ce370b',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('c3269a0a-91db-44e8-96d0-9c748cf80177','7a96f085-924b-483e-bc63-440323bce587','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Identify file format',1,'Failed',NULL,'2013-11-07 22:51:43'),('c379e58b-d458-46d6-a9ab-7493f685a388','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Clean up names',1,'Failed',NULL,'2012-10-02 00:25:06'),('c425258a-cf54-44f9-b39f-cf14c7966a41','72dce7bc-054c-4d2d-8971-a480cb894bdc','8adb23cc-dee3-44da-8356-fa6ce849e4d6',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('c4898520-448c-40fc-8eb3-0603b6aacfb7','ad38cdea-d1da-4d06-a7e5-6f75da85a718','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Characterize and extract metadata',1,'Failed',NULL,'2012-10-02 00:25:06'),('c4e109d6-38ee-4c92-b83d-bc4d360f6f2e','c4b2e8ce-fe02-45d4-9b0f-b163bffcc05f','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('c5ecb5a9-d697-4188-844f-9a756d8734fa','57bd2747-181e-4f06-b969-dc012c592982','aaa929e4-5c35-447e-816a-033a66b9b90b',NULL,'Extract packages',1,'Failed',NULL,'2013-11-07 22:51:43'),('c73acd63-19c9-4ca8-912c-311107d0454e','e62e4b85-e3f1-4550-8e40-3939e6497e92','a58bd669-79af-4999-8654-951f638d4457',NULL,'Normalize',1,'Failed',NULL,'2012-10-23 19:41:25'),('c77fee8c-7c4e-4871-a72e-94d499994869','6405c283-9eed-410d-92b1-ce7d938ef080','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('c8f7bf7b-d903-42ec-bfdf-74d357ac4230','da756a4e-9d8b-4992-a219-2a7fd1edf2bb','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Clean up names',1,'Failed',NULL,'2012-10-02 00:25:06'),('cb48ef2a-3394-4936-af1f-557b39620efa','6a930177-66db-49d3-b95d-10c28ee47562','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-11-30 19:55:48'),('cb8e5706-e73f-472f-ad9b-d1236af8095f','58a83299-c854-49bb-9b16-bf97813edd8e',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('cccc2da4-e9b8-43a0-9ca2-7383eff0fac9','23650e92-092d-4ace-adcc-c627c41b127e','378ae4fc-7b62-40af-b448-a1ab47ac2c0c',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0','c52736fa-2bc5-4142-a111-8b13751ed067','65240550-d745-4afe-848f-2bf5910457c9',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('cddde867-4cf9-4248-ac31-f7052fae053f','74146fe4-365d-4f14-9aae-21eafa7d8393','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('cf26b361-dd5f-4b62-a493-6ee02728bd5f','76135f22-6dba-417f-9833-89ecbe9a3d99','b063c4ce-ada1-4e72-a137-800f1c10905c',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('cf71e6ff-7740-4bdb-a6a9-f392d678c6e1','851d679e-44db-485a-9b0e-2dfbdf80c791','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('d05eaa5e-344b-4daa-b78b-c9f27c76499d','1cd60a70-f78e-4625-9381-3863ff819f33','2d751fc6-dc9d-4c52-b0d9-a4454cefb359',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('d0c463c2-da4c-4a70-accb-c4ce96ac5194','757b5f8b-0fdf-4c5c-9cff-569d63a2d209','2e7f83f9-495a-44b3-b0cf-bff66f021a4d',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('d0dfbd93-d2d0-44db-9945-94fd8de8a1d4','e6591da1-abfa-4bf2-abeb-cc0791ba5284','8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc',NULL,'Identify DSpace files',1,'Failed',NULL,'2012-10-02 00:25:06'),('d1018160-aaab-4d92-adce-d518880d7c7d','92a7b76c-7c5c-41b3-8657-ba4cdd9a8176','f025f58c-d48c-4ba1-8904-a56d2a67b42f',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('d1b27e9e-73c8-4954-832c-36bd1e00c802','38cea9c4-d75c-48f9-ba88-8052e9d3aa61','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Identify file format',1,'Failed',NULL,'2013-11-07 22:51:42'),('d2035da2-dfe1-4a56-8524-84d5732fd3a3','6405c283-9eed-410d-92b1-ce7d938ef080','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-11-30 19:55:48'),('d27fd07e-d3ed-4767-96a5-44a2251c6d0a','39ac9ff8-d312-4033-a2c6-44219471abda',NULL,NULL,'Complete transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('d3c75c96-f8c7-4674-af46-5bcce7b05f87','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Rename with transfer UUID',1,'Failed',NULL,'2012-10-02 00:25:06'),('d46f6af8-bc4e-4369-a808-c0fedb439fef','d6a0dec1-63e7-4c7c-b4c0-e68f0afcedd3','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Create SIP from Transfer',1,'Failed',NULL,'2013-04-05 23:08:30'),('d55b42c8-c7c5-4a40-b626-d248d2bd883f','bafe0ba3-420a-44f2-bb15-7509ef5c498c','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Prepare AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('d5a2ef60-a757-483c-a71a-ccbffe6b80da','525db1a2-d494-4764-a900-7ff89d67c384',NULL,NULL,'Store AIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('d7681789-5f98-49bb-85d4-c01b34dac5b9','b5e6340f-07f3-4ed1-aada-7a7f049b19b9','b063c4ce-ada1-4e72-a137-800f1c10905c',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('d77ccaa0-3a3d-46ff-877f-4edf1a8179e2','51e31d21-3e92-4c9f-8fec-740f559285f2','39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('d7e6404a-a186-4806-a130-7e6d27179a15','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Extract packages',1,'Failed',NULL,'2012-10-02 00:25:06'),('da2d650e-8ce3-4b9a-ac97-8ca4744b019f','966f5720-3081-4697-9691-c19b86ffa569','4417b129-fab3-4503-82dd-740f8e774bff',NULL,'Rename with transfer UUID',1,'Failed',NULL,'2012-10-02 00:25:06'),('db6d3830-9eb4-4996-8f3a-18f4f998e07f','ad38cdea-d1da-4d06-a7e5-6f75da85a718','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Verify SIP compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('db9177f5-41d2-4894-be1a-a7547ed6b63a','24fb04f6-95c1-4244-8f3d-65061418b188','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('dba3028d-2029-4a87-9992-f6335d890528','d7a2bfbe-3f4d-45f7-87c6-f5c3c98961cd','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('dc144ff4-ad74-4a6e-ac15-b0beedcaf662','71d4f810-8fb6-45f7-9da2-f2dc07217076','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('dc9d4991-aefa-4d7e-b7b5-84e3c4336e74','dc2994f2-6de6-4c46-81f7-54676c5054aa','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process metadata directory',1,'Failed',NULL,'2013-02-13 22:03:40'),('ddc8b2ef-a7ba-4713-9425-ed18a1fa720b','ad38cdea-d1da-4d06-a7e5-6f75da85a718','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Assign file UUIDs and checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('de909a42-c5b5-46e1-9985-c031b50e9d30','2002fd7c-e238-4cca-a393-3c1c63a04915',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-02 07:25:06'),('df02cac1-f582-4a86-b7cf-da98a58e279e','f89b9e0f-8789-4292-b5d0-4a330c0205e1','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Include default SIP processingMCP.xml',1,'Failed',NULL,'2012-10-02 00:25:06'),('df1cc271-ff77-4f86-b4f3-afc01856db1f','accc69f9-5b99-4565-92b5-114c7727d9e9','cf71e6ff-7740-4bdb-a6a9-f392d678c6e1',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('df957421-6bba-4ad7-8580-0fc04a54efd4','4b7e128d-193d-4b7a-8c46-b37842bac047','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Generate METS.xml document',1,'Failed',NULL,'2012-10-02 00:25:06'),('e219ed78-2eda-4263-8c0f-0c7f6a86c33e','63866950-cb04-4fe2-9b1d-9d5f1d22fc86','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('e2c0dae9-3295-4a98-b3ff-664ab2dc0cda','cac32b11-820c-4d17-8c7f-4e71fc0be68a','7e65c627-c11d-4aad-beed-65ceb7053fe8',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('e399bd60-202d-42df-9760-bd14497b5034','a73b3690-ac75-4030-bb03-0c07576b649b','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-12-04 00:47:58'),('e3a6d178-fa65-4086-a4aa-6533e8f12d51','d61bb906-feff-4d6f-9e6c-a3f077f46b21','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Rename SIP directory with SIP UUID',1,'Failed',NULL,'2012-10-02 00:25:06'),('e3efab02-1860-42dd-a46c-25601251b930','e485f0f4-7d44-45c6-a0d2-bba4b2abd0d0',NULL,NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('e4b0c713-988a-4606-82ea-4b565936d9a7','ba0d0244-1526-4a99-ab65-43bfcd704e70','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process metadata directory',1,'Failed',NULL,'2013-02-13 22:03:40'),('e4e19c32-16cc-4a7f-a64d-a1f180bdb164','09fae382-37ac-45bb-9b53-d1608a44742c','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('e64d26f4-3330-4d0b-bffe-81edb0dbe93d','feac0c04-3511-4e91-9403-5c569cff7bcc','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-11-30 19:55:48'),('e76aec15-5dfa-4b14-9405-735863e3a6fa','ded09ddd-2deb-4d62-bfe3-84703f60c522','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-01-03 02:10:38'),('e888269d-460a-4cdf-9bc7-241c92734402','fb55b404-90f5-45b6-a47c-ccfbd0de2401','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('e950cd98-574b-4e57-9ef8-c2231e1ce451','7fd4e564-bed2-42c7-a186-7ae615381516','5c0d8661-1c49-4023-8a67-4991365d70fb',NULL,'Normalize',1,'Failed',NULL,'2013-11-15 00:31:31'),('ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c','dde8c13d-330e-458b-9d53-0937370695fa','438dc1cf-9813-44b5-a0a3-58e09ae73b8a',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('eb52299b-9ae6-4a1f-831e-c7eee0de829f','aa2e26b3-539e-4071-b54c-bcb89650d2d2','d27fd07e-d3ed-4767-96a5-44a2251c6d0a',NULL,'Complete transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('ee438694-815f-4b74-97e1-8e7dde2cc6d5','c1bd4921-c446-4ff9-bb34-fcd155b8132a','c168f1ee-5d56-4188-8521-09f0c5475133',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('ef6332ee-a890-4e1b-88de-986efc4269fb','4b07d97a-04c1-45ce-9d9b-36bc29054223','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Rename with transfer UUID',1,'Failed',NULL,'2012-10-02 00:25:06'),('ef8bd3f3-22f5-4283-bfd6-d458a2d18f22','2d9483ef-7dbb-4e7e-a9c6-76ed4de52da9','39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('f025f58c-d48c-4ba1-8904-a56d2a67b42f','e18e0c3a-dffb-42d2-9bfa-ea6c61328e28',NULL,NULL,'Failed compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('f052432c-d4e7-4379-8d86-f2a08f0ae509','ad38cdea-d1da-4d06-a7e5-6f75da85a718','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('f060d17f-2376-4c0b-a346-b486446e46ce','0cbfd02e-94bc-4f0d-8e56-f7af6379c3ca','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process metadata directory',1,'Failed',NULL,'2013-02-13 22:03:40'),('f09847c2-ee51-429a-9478-a860477f6b8d','97545cb5-3397-4934-9bc5-143b774e4fa7','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Identify file format',1,'Failed',NULL,'2013-11-07 22:51:42'),('f0f64c7e-30fa-47c1-9877-43955680c0d0','b5970cbb-1af7-4f8c-b41d-a0febd482da4','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('f12ece2c-fb7e-44de-ba87-7e3c5b6feb74','d7f13903-55a0-4a1c-87fa-9b75b14dccb4','6fe4678a-b3fb-4144-a8a3-7386eb87247d',NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('f1bfce12-b637-443f-85f8-b6450ca01a13','57ef1f9f-3a1a-4cdc-90fd-39b024524618','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Verify transfer checksums',1,'Failed',NULL,'2012-10-02 00:25:06'),('f1e286f9-4ec7-4e19-820c-dae7b8ea7d09','a493f430-d905-4f68-a742-f4393a43e694','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process metadata directory',1,'Failed',NULL,'2013-02-13 22:03:37'),('f2a019ea-0601-419c-a475-1b96a927a2fb','06b45b5d-d06b-49a8-8f15-e9458fbae842','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Verify transfer compliance',1,'Failed',NULL,'2013-11-07 22:51:43'),('f2a1faaf-7322-4d9c-aff9-f809e7a6a6a2','ea331cfb-d4f2-40c0-98b5-34d21ee6ad3e',NULL,NULL,'Reject DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('f2a6f2a5-2f92-47da-b63b-30326625f6ae','596a7fd5-a86b-489c-a9c0-3aa64b836cec','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('f30b23d4-c8de-453d-9b92-50b86e21d3d5','fe354b27-dbb2-4454-9c1c-340d85e67b78','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('f3a39155-d655-4336-8227-f8c88e4b7669','41e84764-e3a0-4aac-94e9-adbe996b087f','e950cd98-574b-4e57-9ef8-c2231e1ce451',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('f3a58cbb-20a8-4c6d-9ae4-1a5f02c1a28e','bf0835be-4c76-4508-a5a7-cdc4c9dae217',NULL,NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('f3be1ee1-8881-465d-80a6-a6f093d40ec2','ef0bb0cf-28d5-4687-a13d-2377341371b5','c379e58b-d458-46d6-a9ab-7493f685a388',NULL,'Remove cache files',1,'Failed',NULL,'2012-10-02 00:25:06'),('f3efc52e-22e1-4337-b8ed-b38dac0f9f77','c87ec738-b679-4d8e-8324-73038ccf0dfd','b063c4ce-ada1-4e72-a137-800f1c10905c',NULL,'Normalize',1,'Failed',NULL,'2013-11-07 22:51:35'),('f4dea20e-f3fe-4a37-b20f-0e70a7bc960e','85a2ec9b-5a80-497b-af60-04926c0bf183',NULL,NULL,'Normalize',1,'Failed',NULL,'2012-10-24 02:41:24'),('f574b2a0-6e0b-4c74-ac5b-a73ddb9593a0','b24525cd-e68d-4afd-b6ec-46192bbc117b','47dd6ea6-1ee7-4462-8b84-3fc4c1eeeb7f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('f63970a2-dc63-4ab4-80a6-9bfd72e3cf5a','e476ac7e-d3e8-43fa-bb51-5a9cf42b2713','a58bd669-79af-4999-8654-951f638d4457',NULL,'Normalize',1,'Failed',NULL,'2012-10-23 19:41:25'),('f6bcc82a-d629-4a78-8643-bf6e3cb39fe6','df1c53e4-1b69-441e-bdc9-6d08c3b47c9b',NULL,NULL,'Approve transfer',1,'Failed',NULL,'2012-10-02 00:25:06'),('f6fdd1a7-f0c5-4631-b5d3-19421155bd7a','21f8f2b6-d285-490a-9276-bfa87a0a4fb9','db9177f5-41d2-4894-be1a-a7547ed6b63a',NULL,'Normalize',1,'Failed',NULL,'2012-10-02 00:25:06'),('f7323418-9987-46ce-aac5-1fe0913c753a','fedffebc-7292-4b94-b402-84628c4254de','9304d028-8387-4ab5-9539-0aab9ac5bdb1',NULL,'Upload DIP',1,'Failed',NULL,'2012-10-02 00:25:06'),('f7488721-c936-42af-a767-2f0b39564a86','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'TRIM transfer',1,'Failed',NULL,'2012-11-30 19:55:48'),('f8319d49-f1e3-45dd-a404-66165c59dec7','df51d25b-6a63-4e7a-b164-77b929dd2f31','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Include default Transfer processingMCP.xml',1,'Failed',NULL,'2012-10-02 00:25:06'),('f8be53cd-6ca2-4770-8619-8a8101a809b9','7c02a87b-7113-4851-97cd-2cf9d3fc0010','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('f92dabe5-9dd5-495e-a996-f8eb9ef90f48','3ecab4fe-1d29-4b21-9b08-fdc715055799','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Scan for viruses',1,'Failed',NULL,'2012-10-02 00:25:06'),('f95a3ac5-47bc-4df9-a49c-d47abd1e05f3','ad38cdea-d1da-4d06-a7e5-6f75da85a718','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Verify transfer compliance',1,'Failed',NULL,'2012-10-02 00:25:06'),('fa5b0c43-ed7b-4c7e-95a8-4f9ec7181260','33c0dea0-da6c-4b8f-8038-6e95844eea95','cccc2da4-e9b8-43a0-9ca2-7383eff0fac9',NULL,'Prepare AIP',1,'Failed',NULL,'2013-01-11 00:50:39'),('faaea8eb-5872-4428-b609-9dd870cf5ceb','8ef75179-a3f1-4911-9f05-c84e8756fc67','7d728c39-395f-4892-8193-92f086c0546f',NULL,'Process submission documentation',1,'Failed',NULL,'2012-10-02 00:25:06'),('fbc3857b-bb02-425b-89ce-2d6a39eaa542','93e01ed2-8d69-4a56-b686-3cf507931885','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',NULL,'Quarantine',1,'Failed',NULL,'2012-10-02 00:25:06'),('fdfac6e5-86c0-4c81-895c-19a9edadedef','a3c27d23-dbdf-47af-bf66-4238aa1a508f','7c95b242-1ce5-4210-b7d4-fdbb6c0aa5dd',NULL,'Rename with transfer UUID',1,'Failed',NULL,'2012-10-02 00:25:06');
/*!40000 ALTER TABLE `MicroServiceChainLinks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MicroServiceChainLinksExitCodes`
--

DROP TABLE IF EXISTS `MicroServiceChainLinksExitCodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MicroServiceChainLinksExitCodes` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `microServiceChainLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `exitCode` int(11) DEFAULT '0',
  `nextMicroServiceChainLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `playSound` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `exitMessage` varchar(50) COLLATE utf8_unicode_ci DEFAULT 'Completed successfully',
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `MicroServiceChainLinksExitCodes` (`pk`),
  KEY `microServiceChainLink` (`microServiceChainLink`),
  KEY `nextMicroServiceChainLink` (`nextMicroServiceChainLink`),
  KEY `playSound` (`playSound`),
  CONSTRAINT `MicroServiceChainLinksExitCodes_ibfk_1` FOREIGN KEY (`microServiceChainLink`) REFERENCES `MicroServiceChainLinks` (`pk`),
  CONSTRAINT `MicroServiceChainLinksExitCodes_ibfk_2` FOREIGN KEY (`nextMicroServiceChainLink`) REFERENCES `MicroServiceChainLinks` (`pk`),
  CONSTRAINT `MicroServiceChainLinksExitCodes_ibfk_3` FOREIGN KEY (`playSound`) REFERENCES `Sounds` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MicroServiceChainLinksExitCodes`
--

LOCK TABLES `MicroServiceChainLinksExitCodes` WRITE;
/*!40000 ALTER TABLE `MicroServiceChainLinksExitCodes` DISABLE KEYS */;
INSERT INTO `MicroServiceChainLinksExitCodes` VALUES ('006c46bb-e833-47e8-8c86-e9c542d20d5e','c4898520-448c-40fc-8eb3-0603b6aacfb7',0,'192315ea-a1bf-44cf-8cb4-0b3edd1522a6',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('00bde88b-b4da-44f3-b0a6-2b96276931ce','f30b23d4-c8de-453d-9b92-50b86e21d3d5',0,'a2173b55-abff-4d8f-97b9-79cc2e0a64fa',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('00c7c131-5849-4bd6-a245-3edae7448bff','8ce130d4-3f7e-46ec-868a-505cf9033d96',0,'ef8bd3f3-22f5-4283-bfd6-d458a2d18f22',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('01dd8a04-d56f-4cdb-a24e-038804208660','651236d2-d77f-4ca7-bfe9-6332e96608ff',0,'e3efab02-1860-42dd-a46c-25601251b930',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('021d0483-272c-43a2-9854-f4998913f5d1','25b8ddff-4074-4803-a0dc-bbb3acd48a97',0,'dc144ff4-ad74-4a6e-ac15-b0beedcaf662',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('023547cb-a1a2-40d0-b21f-9527117593a0','7c6a0b72-f37b-4512-87f3-267644de6f80',0,'df957421-6bba-4ad7-8580-0fc04a54efd4',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('029e7f42-4c35-4df0-b081-bd623fc6d6a7','abd6d60c-d50f-4660-a189-ac1b34fafe85',0,'561bbb52-d95c-4004-b0d3-739c0a65f406',NULL,'Completed successfully',NULL,'2013-04-05 23:08:30'),('042bda05-ab8b-4ad2-b281-e0c2a9490f15','d46f6af8-bc4e-4369-a808-c0fedb439fef',0,NULL,NULL,'Completed successfully',NULL,'2013-04-05 23:08:30'),('04412437-d888-4802-9a78-6de4c00a0dfd','f3a39155-d655-4336-8227-f8c88e4b7669',0,'e950cd98-574b-4e57-9ef8-c2231e1ce451',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('0783a1ab-f70e-437b-8bec-cd1f2135ba2a','48703fad-dc44-4c8e-8f47-933df3ef6179',0,'d5a2ef60-a757-483c-a71a-ccbffe6b80da',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('07aea7e1-5132-4da2-b400-21d812eeda61','a329d39b-4711-4231-b54e-b5958934dccb',0,'d1b27e9e-73c8-4954-832c-36bd1e00c802',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('0823e0c7-ab6f-4088-bb09-4cbca4666008','f2a6f2a5-2f92-47da-b63b-30326625f6ae',0,NULL,NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('082b1079-debf-4f31-83d1-9fd4d26e8868','10c40e41-fb10-48b5-9d01-336cd958afe8',0,'91ca6f1f-feb5-485d-99d2-25eed195e330',NULL,'Completed successfully',NULL,'2013-01-03 02:10:38'),('086f8a6d-ba46-4857-aaae-0fe28854231a','f8be53cd-6ca2-4770-8619-8a8101a809b9',0,'5158c618-6160-41d6-bbbe-ddf34b5b06bc',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('09df1a22-13e6-49b9-bd3f-b55187da11c4','6fe4678a-b3fb-4144-a8a3-7386eb87247d',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('0a1a232b-23a6-4a84-a2af-76baadc87139','25b5dc50-d42d-4ee2-91fc-5dcc3eef30a7',0,'1c0f5926-fd76-4571-a706-aa6564555199',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('0a871be4-26fe-4b44-826b-65440e57595d','2fd123ea-196f-4c9c-95c0-117aa65ed9c6',0,'d0dfbd93-d2d0-44db-9945-94fd8de8a1d4',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('0ab37975-f67f-4a06-b973-8cb841b6015e','20129b22-8f28-429b-a3f2-0648090fa305',0,'e64d26f4-3330-4d0b-bffe-81edb0dbe93d',NULL,'Completed successfully',NULL,'2012-12-06 18:58:24'),('0b110f26-934c-4a2d-8857-88467983c510','47c83e01-7556-4c13-881f-282c6d9c7d6a',0,'4103a5b0-e473-4198-8ff7-aaa6fec34749',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('0b553c62-f7e3-48e1-b3cd-6180d36a13ea','a132193a-2e79-4221-a092-c51839d566fb',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('0bc58fa0-5d3c-4b86-9c1c-bb2a1ee18b0e','746b1f47-2dad-427b-8915-8b0cb7acccd8',0,'7c44c454-e3cc-43d4-abe0-885f93d693c6',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('1238736d-5b0c-4298-b8b7-d48baf69428e','333532b9-b7c2-4478-9415-28a3056d58df',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('1462359e-72c8-467f-b08a-02e4e3dfede1','52269473-5325-4a11-b38a-c4aafcbd8f54',0,'28a9f8a8-0006-4828-96d5-892e6e279f72',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('14680e13-e9b0-4c3a-86c0-44cb0100eb21','78b7adff-861d-4450-b6dd-3fabe96a849e',0,'ab0d3815-a9a3-43e1-9203-23a40c00c551',NULL,'Completed successfully',NULL,'2013-01-03 02:10:39'),('1638b707-aac3-41df-a219-660734b81368','3ba518ab-fc47-4cba-9b5c-79629adac10b',0,'3e25bda6-5314-4bb4-aa1e-90900dce887d',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('1667d4a5-65b5-4c4b-a2bd-c273c0bf913a','01c651cb-c174-4ba4-b985-1d87a44d6754',0,'d55b42c8-c7c5-4a40-b626-d248d2bd883f',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('170d410a-5813-43a3-8706-a25a2f6e1d22','70669a5b-01e4-4ea0-ac70-10292f87da05',0,'208d441b-6938-44f9-b54a-bd73f05bc764',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('18db3a8a-ee5f-47c2-b5a7-7d223c3023c0','4edfe7e4-82ff-4c0a-ba5f-29f1ee14e17a',0,'2a62f025-83ec-4f23-adb4-11d5da7ad8c2',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('19e989cc-3ac2-4aa4-98a3-716284c8e310','9619706c-385a-472c-8144-fd5885c21532',0,'4ac461f9-ee69-4e03-924f-60ac0e8a4b7f',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('1c3c10d5-83cc-4b0a-9e90-a420f467432f','b320ce81-9982-408a-9502-097d0daa48fa',0,'5f213529-ced4-49b0-9e30-be4e0c9b81d5',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('1c6d4666-822e-4d31-870b-9aa8730fb7d8','5c0d8661-1c49-4023-8a67-4991365d70fb',0,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('1c9942e6-3b32-479e-956c-6d287d7f246f','0c96c798-9ace-4c05-b3cf-243cdad796b7',0,'25b8ddff-4074-4803-a0dc-bbb3acd48a97',NULL,'Completed successfully',NULL,'2012-11-20 21:29:24'),('1cd00b46-8bb1-4179-8ace-ad09081731b4','45063ad6-f374-4215-a2c4-ac47be4ce2cd',0,'87e7659c-d5de-4541-a09c-6deec966a0c0',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('1ce8c9af-bdea-4a6d-ac6e-710205e9dbfb','1c0f5926-fd76-4571-a706-aa6564555199',0,'82c0eca0-d9b6-4004-9d77-ded9286a9ac7',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('1cfaebb6-10ad-458f-a14d-4f035ee3a918','0e06d968-4b5b-4084-aab4-053a2a8d1679',0,'38c591d4-b7ee-4bc0-b993-c592bf15d97d',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('1f877d65-66c5-49da-bf51-2f1757b59c90','2522d680-c7d9-4d06-8b11-a28d8bd8a71f',0,'1cb7e228-6e94-4c93-bf70-430af99b9264',NULL,'Completed successfully',NULL,'2013-11-07 22:51:42'),('2017d80c-b36e-4cc5-9851-a2de64c22220','0e379b19-771e-4d90-a7e5-1583e4893c56',0,'1c2550f1-3fc0-45d8-8bc4-4c06d720283b',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('21a92e57-bc78-4c62-872d-fb166294132a','95616c10-a79f-48ca-a352-234cc91eaf08',0,'01b30826-bfc4-4e07-8ca2-4263debad642',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('22da2170-54a7-43a7-8573-5a7b998722fb','39e58573-2dbc-4939-bce0-96b2f55dae28',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('2484fb84-887f-4546-ae06-5ad7c444af36','5f213529-ced4-49b0-9e30-be4e0c9b81d5',0,'3f543585-fa4f-4099-9153-dd6d53572f5c',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('24d78b3a-d2be-4d0e-8fd1-6a1a9e44b0d9','478512a6-10e4-410a-847d-ce1e25d8d31c',0,'25b8ddff-4074-4803-a0dc-bbb3acd48a97',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('27333f0b-7463-4533-8129-9f9cd88ad0c0','561bbb52-d95c-4004-b0d3-739c0a65f406',0,'d46f6af8-bc4e-4369-a808-c0fedb439fef',NULL,'Completed successfully',NULL,'2013-04-19 22:39:27'),('27fb34b1-fe92-44dc-b5db-df52b60947e3','36609513-6502-4aca-886a-6c4ae03a9f05',0,'db6d3830-9eb4-4996-8f3a-18f4f998e07f',NULL,'Completed successfully',NULL,'2013-04-19 22:39:27'),('2858403b-895f-4ea3-b7b7-388de75fbb39','002716a1-ae29-4f36-98ab-0d97192669c4',0,NULL,NULL,'Completed successfully',NULL,'2013-11-07 22:51:34'),('291fe250-1fa9-4386-a555-375d0333c225','8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc',0,'eb52299b-9ae6-4a1f-831e-c7eee0de829f',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('2a41dd56-1d56-49d9-86f5-2d6d301377e3','58fcd2fd-bcdf-4e49-ad99-7e24cc8c3ba5',0,'e4e19c32-16cc-4a7f-a64d-a1f180bdb164',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('2a478b90-5f0c-45c0-91fe-099e8389096c','c73acd63-19c9-4ca8-912c-311107d0454e',0,'a58bd669-79af-4999-8654-951f638d4457',NULL,'Completed successfully',NULL,'2012-10-23 19:41:25'),('2a73a50f-86d8-40d0-8f49-64bac6b561ea','e3a6d178-fa65-4086-a4aa-6533e8f12d51',0,'df02cac1-f582-4a86-b7cf-da98a58e279e',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('2b1224e4-8c2a-4043-9d77-f0be8e4cde70','173d310c-8e40-4669-9a69-6d4c8ffd0396',0,'4edfe7e4-82ff-4c0a-ba5f-29f1ee14e17a',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('2b881bce-d73f-4710-8060-3f1226654710','76d87f57-9718-4f68-82e6-91174674c49c',0,'a536965b-e501-42aa-95eb-0656775be6f2',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('2c4004db-5816-4bd2-b37c-a89dee2c4fe7','01b30826-bfc4-4e07-8ca2-4263debad642',0,'22ded604-6cc0-444b-b320-f96afb15d581',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('2d71c993-c2dc-4f9c-b8ea-6bc1a3fdbbe1','3229e01f-adf3-4294-85f7-4acb01b3fbcf',0,'154dd501-a344-45a9-97e3-b30093da35f5',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('2f9305b2-30a5-4193-99c9-5e27251830b9','b6c9de5a-4a9f-41e1-a524-360bdca39893',0,'a6e97805-a420-41af-b708-2a56de5b47a6',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('2fc642bf-1950-46de-a45c-93aa3bcd78f2','2adf60a0-ecd7-441a-b82f-f77c6a3964c3',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('30d5cb9f-6d0e-40d3-9d64-1632f98770fc','f63970a2-dc63-4ab4-80a6-9bfd72e3cf5a',0,'a58bd669-79af-4999-8654-951f638d4457',NULL,'Completed successfully',NULL,'2012-10-23 19:41:25'),('30ebe1b6-d263-4322-805f-f66ae0e8d535','a6e97805-a420-41af-b708-2a56de5b47a6',0,'39e58573-2dbc-4939-bce0-96b2f55dae28',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('32cae09e-0262-46b8-ba76-eb6cf6be1272','823b0d76-9f3c-410d-83ab-f3c2cdd9ab22',0,'e3a6d178-fa65-4086-a4aa-6533e8f12d51',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('32d6ea79-0e00-4103-8d39-ddbaaafe0c3e','214f1004-2748-4bed-a38d-48fe500c41b9',0,'0fc3c795-dc68-4aa0-86fc-cbd6af3302fa',NULL,'Completed successfully',NULL,'2012-12-12 21:25:31'),('340da49e-d01f-4870-a8c4-ee8a3c827a0f','ee438694-815f-4b74-97e1-8e7dde2cc6d5',0,'c168f1ee-5d56-4188-8521-09f0c5475133',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('341c6bfe-7e42-40e7-a995-5af4590dea3b','22c0f074-07b1-445f-9e8b-bf75ac7f0b48',0,'d3c75c96-f8c7-4674-af46-5bcce7b05f87',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('345fc8d9-f44d-41d7-a439-57067cc04c10','c5ecb5a9-d697-4188-844f-9a756d8734fa',0,'aaa929e4-5c35-447e-816a-033a66b9b90b',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('350f74af-d7f5-4b08-b99e-902aff95e3da','03ee1136-f6ad-4184-8dcb-34872f843e14',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('357a0bff-fe7a-40e1-85a7-bbc17232bf2a','c379e58b-d458-46d6-a9ab-7493f685a388',0,'a46e95fe-4a11-4d3c-9b76-c5d8ea0b094d',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('35c0d321-ee6d-450b-996c-434176770a95','39ac9205-cb08-47b1-8bc3-d3375e37d9eb',0,'bf6873f4-90b8-4393-9057-7f14f4687d72',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('35d72d20-e271-4874-881f-a920cfa1c5e2','cddde867-4cf9-4248-ac31-f7052fae053f',0,'77a7fa46-92b9-418e-aa88-fbedd4114c9f',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('36167520-cb63-4137-a4c8-a208f0d08e17','f3be1ee1-8881-465d-80a6-a6f093d40ec2',0,'c379e58b-d458-46d6-a9ab-7493f685a388',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('36cb4f22-2ede-4b70-8947-c97458261235','f7323418-9987-46ce-aac5-1fe0913c753a',0,'9304d028-8387-4ab5-9539-0aab9ac5bdb1',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('39c100c4-4007-415c-b1b6-b23ac54236d1','bf6873f4-90b8-4393-9057-7f14f4687d72',0,'2f83c458-244f-47e5-a302-ce463163354e',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('3a3bd3d6-a9a0-4155-b361-3dceb876c99d','b4567e89-9fea-4256-99f5-a88987026488',0,'045c43ae-d6cf-44f7-97d6-c8a602748565',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('3a6947d3-d3a6-4bfa-9b01-de62209367e1','d7681789-5f98-49bb-85d4-c01b34dac5b9',0,'b063c4ce-ada1-4e72-a137-800f1c10905c',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('3e7aba06-c98a-4c12-bcad-e4e849ecb14c','5158c618-6160-41d6-bbbe-ddf34b5b06bc',0,'f09847c2-ee51-429a-9478-a860477f6b8d',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('3f0bcb8d-3c64-4b2d-ac2d-596a52735c34','d27fd07e-d3ed-4767-96a5-44a2251c6d0a',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('3f70336e-c50e-44d7-875d-d099d0dae373','045c43ae-d6cf-44f7-97d6-c8a602748565',0,'50b67418-cb8d-434d-acc9-4a8324e7fdd2',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('40733530-5ad8-40ac-b5d4-8f56af04c264','31abe664-745e-4fef-a669-ff41514e0083',0,'09b85517-e5f5-415b-a950-1a60ee285242',NULL,'Completed successfully',NULL,'2013-01-10 22:49:49'),('41020480-1078-4106-94d9-964ab1af6bd2','b063c4ce-ada1-4e72-a137-800f1c10905c',0,'83484326-7be7-4f9f-b252-94553cd42370',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('42353ec8-76cb-477f-841c-4adfc8432d78','b3d11842-0090-420a-8919-52d7039d50e6',179,'bdfecadc-8219-4109-885c-cfb9ef53ebc3',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('4322b48f-e7a9-4a9f-a8c0-bf7aac4b9289','b04e9232-2aea-49fc-9560-27349c8eba4e',0,NULL,NULL,'Completed successfully',NULL,'2012-12-06 17:43:25'),('460aae60-19df-4388-841b-d9d26dd5b3a0','ef8bd3f3-22f5-4283-bfd6-d458a2d18f22',0,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('4653d10a-4d8d-11e3-9842-94de802aa978','8ce130d4-3f7e-46ec-868a-505cf9033d96',1,'ef8bd3f3-22f5-4283-bfd6-d458a2d18f22',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653d280-4d8d-11e3-9842-94de802aa978','5c0d8661-1c49-4023-8a67-4991365d70fb',1,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653d507-4d8d-11e3-9842-94de802aa978','ef8bd3f3-22f5-4283-bfd6-d458a2d18f22',1,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653d5de-4d8d-11e3-9842-94de802aa978','f6fdd1a7-f0c5-4631-b5d3-19421155bd7a',1,'db9177f5-41d2-4894-be1a-a7547ed6b63a',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653d69e-4d8d-11e3-9842-94de802aa978','09b85517-e5f5-415b-a950-1a60ee285242',1,'dba3028d-2029-4a87-9992-f6335d890528',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653d778-4d8d-11e3-9842-94de802aa978','26cf64e2-21b5-4935-a52b-71695870f1f2',1,'bf6873f4-90b8-4393-9057-7f14f4687d72',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653d835-4d8d-11e3-9842-94de802aa978','8adb23cc-dee3-44da-8356-fa6ce849e4d6',1,'d77ccaa0-3a3d-46ff-877f-4edf1a8179e2',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653d8dd-4d8d-11e3-9842-94de802aa978','440ef381-8fe8-4b6e-9198-270ee5653454',1,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653d98a-4d8d-11e3-9842-94de802aa978','bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0',1,'440ef381-8fe8-4b6e-9198-270ee5653454',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653da34-4d8d-11e3-9842-94de802aa978','8ce378a5-1418-4184-bf02-328a06e1d3be',1,'83257841-594d-4a0e-a4a1-1e9269c30f3d',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653dadb-4d8d-11e3-9842-94de802aa978','d77ccaa0-3a3d-46ff-877f-4edf1a8179e2',1,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653db8c-4d8d-11e3-9842-94de802aa978','092b47db-6f77-4072-aed3-eb248ab69e9c',1,'bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653dce1-4d8d-11e3-9842-94de802aa978','180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21',1,'8ce378a5-1418-4184-bf02-328a06e1d3be',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653dd99-4d8d-11e3-9842-94de802aa978','0a6558cf-cf5f-4646-977e-7d6b4fde47e8',1,'055de204-6229-4200-87f7-e3c29f095017',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4653de50-4d8d-11e3-9842-94de802aa978','e950cd98-574b-4e57-9ef8-c2231e1ce451',1,'5c0d8661-1c49-4023-8a67-4991365d70fb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('466198c8-4d8d-11e3-9842-94de802aa978','8ce130d4-3f7e-46ec-868a-505cf9033d96',2,'ef8bd3f3-22f5-4283-bfd6-d458a2d18f22',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('46619bb1-4d8d-11e3-9842-94de802aa978','5c0d8661-1c49-4023-8a67-4991365d70fb',2,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('46619d14-4d8d-11e3-9842-94de802aa978','ef8bd3f3-22f5-4283-bfd6-d458a2d18f22',2,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('46619e34-4d8d-11e3-9842-94de802aa978','f6fdd1a7-f0c5-4631-b5d3-19421155bd7a',2,'db9177f5-41d2-4894-be1a-a7547ed6b63a',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('46619efb-4d8d-11e3-9842-94de802aa978','09b85517-e5f5-415b-a950-1a60ee285242',2,'dba3028d-2029-4a87-9992-f6335d890528',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('46619fc6-4d8d-11e3-9842-94de802aa978','26cf64e2-21b5-4935-a52b-71695870f1f2',2,'bf6873f4-90b8-4393-9057-7f14f4687d72',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4661a09b-4d8d-11e3-9842-94de802aa978','8adb23cc-dee3-44da-8356-fa6ce849e4d6',2,'d77ccaa0-3a3d-46ff-877f-4edf1a8179e2',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4661a162-4d8d-11e3-9842-94de802aa978','440ef381-8fe8-4b6e-9198-270ee5653454',2,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4661a228-4d8d-11e3-9842-94de802aa978','bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0',2,'440ef381-8fe8-4b6e-9198-270ee5653454',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4661a33f-4d8d-11e3-9842-94de802aa978','8ce378a5-1418-4184-bf02-328a06e1d3be',2,'83257841-594d-4a0e-a4a1-1e9269c30f3d',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4661a403-4d8d-11e3-9842-94de802aa978','d77ccaa0-3a3d-46ff-877f-4edf1a8179e2',2,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4661a4c2-4d8d-11e3-9842-94de802aa978','092b47db-6f77-4072-aed3-eb248ab69e9c',2,'bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4661a7c3-4d8d-11e3-9842-94de802aa978','180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21',2,'8ce378a5-1418-4184-bf02-328a06e1d3be',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4661a88c-4d8d-11e3-9842-94de802aa978','0a6558cf-cf5f-4646-977e-7d6b4fde47e8',2,'055de204-6229-4200-87f7-e3c29f095017',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('4661c886-4d8d-11e3-9842-94de802aa978','e950cd98-574b-4e57-9ef8-c2231e1ce451',2,'5c0d8661-1c49-4023-8a67-4991365d70fb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('478ab718-faa4-43c3-8b4e-31678052a46f','288b739d-40a1-4454-971b-812127a5e03d',0,'154dd501-a344-45a9-97e3-b30093da35f5',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('48812a6e-4c7b-4fde-9ea6-50cced027b6e','61a8de9c-7b25-4f0f-b218-ad4dde261eed',0,'3ba518ab-fc47-4cba-9b5c-79629adac10b',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('49609998-33b5-4257-89e9-5d049c17159c','88affaa2-13c5-4efb-a860-b182bd46c2c6',0,'f060d17f-2376-4c0b-a346-b486446e46ce',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('4ad9fa2a-3c87-4cd6-8a0b-3a27ec7efbab','1c2550f1-3fc0-45d8-8bc4-4c06d720283b',0,'2584b25c-8d98-44b7-beca-2b3ea2ea2505',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('4bfba45a-6808-4b31-a8bf-cbf34c66111a','032cdc54-0b9b-4caf-86e8-10d63efbaec0',179,'b04e9232-2aea-49fc-9560-27349c8eba4e',NULL,'Completed successfully',NULL,'2012-12-06 17:43:33'),('4d475f2c-1c11-4915-a231-bce2f02fdb9b','ab0d3815-a9a3-43e1-9203-23a40c00c551',0,NULL,NULL,'Completed successfully',NULL,'2013-01-03 02:10:38'),('4d703bf8-12ce-4fe7-9ddc-4dac274d8424','ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0',0,'65240550-d745-4afe-848f-2bf5910457c9',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('4de0e894-8eda-49eb-a915-124b4f6c3608','dc9d4991-aefa-4d7e-b7b5-84e3c4336e74',0,'b6b0fe37-aa26-40bd-8be8-d3acebf3ccf8',NULL,'Completed successfully',NULL,'2013-02-13 22:03:40'),('4f4b2fd0-fc20-4572-ac49-c18be1eefe15','83257841-594d-4a0e-a4a1-1e9269c30f3d',0,'dba3028d-2029-4a87-9992-f6335d890528',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('4ffb1b47-b240-4fcc-8012-afb2a3149750','d3c75c96-f8c7-4674-af46-5bcce7b05f87',0,'da2d650e-8ce3-4b9a-ac97-8ca4744b019f',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('5035f15f-90a9-4beb-9251-c24ec3e530d7','4417b129-fab3-4503-82dd-740f8e774bff',0,'fdfac6e5-86c0-4c81-895c-19a9edadedef',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('516512ee-0aca-4d4f-b79f-eec82ea063d7','6ee25a55-7c08-4c9a-a114-c200a37146c4',0,'61a8de9c-7b25-4f0f-b218-ad4dde261eed',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('51f9783a-fe1c-47aa-afd3-600296ee8ff5','c1339015-e15b-4303-8f37-a2516669ac4e',0,'478512a6-10e4-410a-847d-ce1e25d8d31c',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('550df3a0-5cbe-4009-9be7-8d86b53c3f68','e399bd60-202d-42df-9760-bd14497b5034',0,'3409b898-e532-49d3-98ff-a2a1f9d988fa',NULL,'Completed successfully',NULL,'2012-12-04 00:47:58'),('55413eac-d358-45f1-b54e-595a6489adcf','df1cc271-ff77-4f86-b4f3-afc01856db1f',0,'cf71e6ff-7740-4bdb-a6a9-f392d678c6e1',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('557ab052-a7a7-4eff-9869-e3f55d5d505e','d0c463c2-da4c-4a70-accb-c4ce96ac5194',0,'ef6332ee-a890-4e1b-88de-986efc4269fb',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('55c70f4f-a05f-4903-9f62-fe5daa282ba7','f6fdd1a7-f0c5-4631-b5d3-19421155bd7a',0,'db9177f5-41d2-4894-be1a-a7547ed6b63a',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('55dd25a7-944a-4a99-8b94-a508d28d0b38','c3269a0a-91db-44e8-96d0-9c748cf80177',0,NULL,NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('57bb6687-c187-4fba-af99-956119ca7672','48199d23-afd0-4b9b-b8a3-cd80c7d45e7c',0,'1798e1d4-ec91-4299-a767-d10c32155d19',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('5858d1d8-9900-4e65-bf61-2a5ff648998e','f12ece2c-fb7e-44de-ba87-7e3c5b6feb74',0,'6fe4678a-b3fb-4144-a8a3-7386eb87247d',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('59489199-c348-4f12-82c7-f26afab99301','dba3028d-2029-4a87-9992-f6335d890528',0,'c2e6600d-cd26-42ed-bed5-95d41c06e37b',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('5a9bdbce-2887-4817-90b6-144c16f50a26','56da7758-913a-4cd2-a815-be140ed09357',0,'8ce130d4-3f7e-46ec-868a-505cf9033d96',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('5b2542c8-2088-4541-8bf9-a750eacb4ac5','bd382151-afd0-41bf-bb7a-b39aef728a32',0,'1b1a4565-b501-407b-b40f-2f20889423f1',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('5bb7a0a6-44f8-4042-be96-a33200eeaa49','ac85a1dc-272b-46ac-bb3e-5bf3f8e56348',0,'0e06d968-4b5b-4084-aab4-053a2a8d1679',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('5c0f905e-40c8-4cdb-af87-d8635ada9f07','26bf24c9-9139-4923-bf99-aa8648b1692b',0,'f2a019ea-0601-419c-a475-1b96a927a2fb',NULL,'Completed successfully',NULL,'2012-11-06 01:07:49'),('5cd0e0ee-75a1-419f-817c-4edd6adce857','e76aec15-5dfa-4b14-9405-735863e3a6fa',0,'10c40e41-fb10-48b5-9d01-336cd958afe8',NULL,'Completed successfully',NULL,'2013-01-03 02:10:38'),('5d1e6692-a0fc-438d-8448-82490a874da4','f052432c-d4e7-4379-8d86-f2a08f0ae509',0,'3229e01f-adf3-4294-85f7-4acb01b3fbcf',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('5e481248-543b-463d-b0a4-eee87c79e71f','dc144ff4-ad74-4a6e-ac15-b0beedcaf662',0,'370aca94-65ab-4f2a-9d7d-294a62c8b7ba',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('5ec10388-20a3-4e54-9e0a-45186242317b','50b67418-cb8d-434d-acc9-4a8324e7fdd2',0,'ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('5fae3555-f2bd-4e36-aebf-32a5c11e2f1e','11033dbd-e4d4-4dd6-8bcf-48c424e222e3',0,'1ba589db-88d1-48cf-bb1a-a5f9d2b17378',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('6027ccf7-879b-45ad-b6df-e4486d6560ff','16415d2f-5642-496d-a46d-00028ef6eb0a',0,NULL,NULL,'Completed successfully',NULL,'2012-12-04 21:29:48'),('604d4f55-f8a5-4c57-852d-579477a22bf1','d0dfbd93-d2d0-44db-9945-94fd8de8a1d4',0,'8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('60ae5742-9a6d-4a0b-93df-ae367fddafb8','e888269d-460a-4cdf-9bc7-241c92734402',0,'faaea8eb-5872-4428-b609-9dd870cf5ceb',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('62430e2d-3240-43aa-9af7-4ec9c8236576','7c95b242-1ce5-4210-b7d4-fdbb6c0aa5dd',0,'f8319d49-f1e3-45dd-a404-66165c59dec7',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('6243c80d-8db3-45a2-bc29-ca5d039f0de5','5e4f7467-8637-49b2-a584-bae83dabf762',0,'f2a6f2a5-2f92-47da-b63b-30326625f6ae',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('62619dde-d34b-4648-962a-3888badd5b56','f1bfce12-b637-443f-85f8-b6450ca01a13',0,'3409b898-e532-49d3-98ff-a2a1f9d988fa',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('628711a4-75e2-452e-b8af-97cf30932a32','208d441b-6938-44f9-b54a-bd73f05bc764',0,'d1018160-aaab-4d92-adce-d518880d7c7d',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('62af9c19-2ddb-4d5b-81b0-df1be79eb96e','1b1a4565-b501-407b-b40f-2f20889423f1',0,'c4898520-448c-40fc-8eb3-0603b6aacfb7',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('63648444-106d-4f14-81f4-d89b9fe7284e','0ba9bbd9-6c21-4127-b971-12dbc43c8119',0,'e888269d-460a-4cdf-9bc7-241c92734402',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('64426665-4e8b-4814-823a-db8c9a88c8ab','7b146689-1a04-4f58-ba86-3caf2b76ddbc',0,'f3a39155-d655-4336-8227-f8c88e4b7669',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('65409432-a449-4455-8eb2-5cc28af16958','aa9ba088-0b1e-4962-a9d7-79d7a0cbea2d',0,'45063ad6-f374-4215-a2c4-ac47be4ce2cd',NULL,'Completed successfully',NULL,'2012-11-06 01:14:17'),('654b4527-9e55-4792-930c-94aed94b3639','15a2df8a-7b45-4c11-b6fa-884c9b7e5c67',0,'1cd3b36a-5252-4a69-9b1c-3b36829288ab',NULL,'Completed successfully',NULL,'2013-02-19 00:52:53'),('6618b464-6c18-4db4-b4f3-5e00c23081bf','14a0678f-9c2a-4995-a6bd-5acd141eeef1',0,'055de204-6229-4200-87f7-e3c29f095017',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('662164ca-9872-49f7-8a4b-bd306b01fca2','424ee8f1-6cdd-4960-8641-ed82361d3ad7',0,'47c83e01-7556-4c13-881f-282c6d9c7d6a',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('666b8986-b3ae-4397-8fad-1f52c6395f62','5b7a48e1-32ed-43f9-8ffa-e374010fcf76',0,'0e1a8a6b-abcc-4ed6-b4fb-cbccfdc23ef5',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('6740b87f-6d30-4f43-8848-1371fe9b08c5','d1b27e9e-73c8-4954-832c-36bd1e00c802',0,NULL,NULL,'Completed successfully',NULL,'2013-11-07 22:51:42'),('674f222a-4911-4005-9c45-e3a54ac3df78','7e65c627-c11d-4aad-beed-65ceb7053fe8',0,'67a91b4b-a5af-4b54-a836-705e6cf4eeb9',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('691782ba-080f-4e46-a945-ab3f3576b7dc','e3efab02-1860-42dd-a46c-25601251b930',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('691a64b4-7208-42c6-bc9f-db0a05961c18','91ca6f1f-feb5-485d-99d2-25eed195e330',0,'ab0d3815-a9a3-43e1-9203-23a40c00c551',NULL,'Completed successfully',NULL,'2013-01-03 02:10:38'),('6a52ad30-95b1-4a9a-9746-6c16a37d4595','faaea8eb-5872-4428-b609-9dd870cf5ceb',0,'4ef35d72-9494-431a-8cdb-8527b42664c7',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('6b2786d7-60dc-4feb-94ec-b84f82a6e05d','4b75ca30-2eaf-431b-bffa-d737c8a0bf37',0,'66c9c178-2224-41c6-9c0b-dcb60ff57b1a',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('6c381156-7012-4a3c-86f8-e7e262380011','6b931965-d5f6-4611-a536-39d5901f8f70',0,'0a6558cf-cf5f-4646-977e-7d6b4fde47e8',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('6cb712b2-0961-4e93-91e5-9ea5f8ac8b65','4df4cc06-3b03-4c6f-b5c4-bec12a97dc90',0,'5e4f7467-8637-49b2-a584-bae83dabf762',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('6d4d9afb-7bb6-4527-9c8c-4cd9adcdedcf','09b85517-e5f5-415b-a950-1a60ee285242',0,'dba3028d-2029-4a87-9992-f6335d890528',NULL,'Completed successfully',NULL,'2013-01-10 22:49:49'),('6d87f2f2-9d5a-4216-8dbf-6201a9ee8cca','e4e19c32-16cc-4a7f-a64d-a1f180bdb164',179,'83d5e887-6f7c-48b0-bd81-e3f00a9da772',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('6e06fd5e-3892-4e79-b64f-069876bd95a1','60b0e812-ebbe-487e-810f-56b1b6fdd819',100,'31fc3f66-34e9-478f-8d1b-c29cd0012360',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('6e9003bf-6314-4f80-a9d3-7f64c00e7be8','377f8ebb-7989-4a68-9361-658079ff8138',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('6f084d8e-4b3e-4d51-a251-1c31847b65dc','65916156-41a5-4ed2-9472-7dca11e6bc08',0,'055de204-6229-4200-87f7-e3c29f095017',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('6f9575c3-4b84-45bf-920d-b8115e4806f4','5d6a103c-9a5d-4010-83a8-6f4c61eb1478',0,'74665638-5d8f-43f3-b7c9-98c4c8889766',NULL,'Completed successfully',NULL,'2012-10-24 00:40:06'),('6fe4c525-f337-408a-abcc-1caf2d3ee003','bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 07:25:07'),('6ff56b9a-2e0d-4117-a6ee-0ba51e6da708','0e41c244-6c3e-46b9-a554-65e66e5c9324',0,'95616c10-a79f-48ca-a352-234cc91eaf08',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('70d285e1-0548-4f84-bc8a-687e06a220b0','0b92a510-a290-44a8-86d8-6b7139be29df',0,'f6fdd1a7-f0c5-4631-b5d3-19421155bd7a',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('71a09b45-3f64-4618-af51-6a960ae16754','2dd53959-8106-457d-a385-fee57fc93aa9',0,'83484326-7be7-4f9f-b252-94553cd42370',NULL,'Completed successfully',NULL,'2013-11-07 22:51:42'),('72cdeeb3-4dfd-41c9-a0cb-e105ba22bf4f','88807d68-062e-4d1a-a2d5-2d198c88d8ca',0,'ee438694-815f-4b74-97e1-8e7dde2cc6d5',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('730c63c4-7b81-4710-a4d0-0efe49c14708','b15c0ba6-e247-4512-8b56-860fd2b6299d',0,NULL,NULL,'Completed successfully',NULL,'2012-10-24 17:04:11'),('734283b4-527c-4d72-a8b1-f879e64df034','303a65f6-a16f-4a06-807b-cb3425a30201',0,'1b1a4565-b501-407b-b40f-2f20889423f1',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('7386614c-6b85-4fc2-9aec-1b7a8d4adb8a','67b44f8f-bc97-4cb3-b6dd-09dba3c99d30',0,'5d6a103c-9a5d-4010-83a8-6f4c61eb1478',NULL,'Completed successfully',NULL,'2012-10-24 00:40:07'),('7458e131-3beb-40cb-9880-32dec49f1592','f060d17f-2376-4c0b-a346-b486446e46ce',0,'e4b0c713-988a-4606-82ea-4b565936d9a7',NULL,'Completed successfully',NULL,'2013-02-13 22:03:40'),('75a6bee7-49ec-459a-9fc4-4cd0ab0b22bf','055de204-6229-4200-87f7-e3c29f095017',0,'befaf1ef-a595-4a32-b083-56eac51082b0',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('767d6a50-5a17-436c-84f9-68c5991c9a57','635ba89d-0ad6-4fc9-acc3-e6069dffdcd5',0,'a2173b55-abff-4d8f-97b9-79cc2e0a64fa',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('78e44cfa-d6c9-4f74-861b-4a0f9bb57dcb','c8f7bf7b-d903-42ec-bfdf-74d357ac4230',0,'a329d39b-4711-4231-b54e-b5958934dccb',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('78fc9675-6c21-4dc6-9181-9d2885726112','ddc8b2ef-a7ba-4713-9425-ed18a1fa720b',0,'52269473-5325-4a11-b38a-c4aafcbd8f54',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('7963e4e9-ccca-486e-94f5-df9d141554b3','78b7adff-861d-4450-b6dd-3fabe96a849e',179,'a1b65fe3-9358-479b-93b9-68f2b5e71b2b',NULL,'Completed successfully',NULL,'2013-01-03 02:10:39'),('7977788d-4da0-4977-b60c-c3f91a95bd95','45f01e11-47c7-45a3-a99b-48677eb321a5',0,'f12ece2c-fb7e-44de-ba87-7e3c5b6feb74',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('7a49c825-aeeb-4609-a3ba-2c2979888591','c103b2fb-9a6b-4b68-8112-b70597a6cd14',0,'60b0e812-ebbe-487e-810f-56b1b6fdd819',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('7aecfcc6-d9af-4049-b56b-74eb4b70c9f1','26cf64e2-21b5-4935-a52b-71695870f1f2',0,'bf6873f4-90b8-4393-9057-7f14f4687d72',NULL,'Completed successfully',NULL,'2013-01-10 22:49:49'),('7b5b7206-f812-4e60-a35a-bb20246fcc3d','befaf1ef-a595-4a32-b083-56eac51082b0',0,'9619706c-385a-472c-8144-fd5885c21532',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('7c61af02-852b-4619-bcd6-962b7c2c37ae','d55b42c8-c7c5-4a40-b626-d248d2bd883f',0,'0915f727-0bc3-47c8-b9b2-25dc2ecef2bb',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('7c6cef61-5d18-4069-bc48-00a636965903','4430077a-92c5-4d86-b0f8-0d31bdb731fb',0,'f8be53cd-6ca2-4770-8619-8a8101a809b9',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('7d0a2e68-7f29-40ab-a29d-0eeadacda21b','df957421-6bba-4ad7-8580-0fc04a54efd4',0,'b2552a90-e674-4a40-a482-687c046407d3',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('7d6b5e10-6cd2-4315-88d7-0afad4957d75','f025f58c-d48c-4ba1-8904-a56d2a67b42f',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('7deb2533-ae68-4ffa-9217-85d5bb4bfd62','49cbcc4d-067b-4cd5-b52e-faf50857b35a',0,'b320ce81-9982-408a-9502-097d0daa48fa',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('7f2d5239-b464-4837-8e01-0fc43e31395d','60b0e812-ebbe-487e-810f-56b1b6fdd819',0,'7d728c39-395f-4892-8193-92f086c0546f',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('800259c7-f6d2-4ac6-af69-07985f23efec','e64d26f4-3330-4d0b-bffe-81edb0dbe93d',0,'d2035da2-dfe1-4a56-8524-84d5732fd3a3',NULL,'Completed successfully',NULL,'2012-11-30 19:55:48'),('8065a544-5eb6-4868-88b5-f352b4e3f822','6b39088b-683e-48bd-ab89-9dab47f4e9e0',0,'35c8763a-0430-46be-8198-9ecb23f895c8',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('82c773f3-28af-4bcd-bab8-186ef528a6c9','21d6d597-b876-4b3f-ab85-f97356f10507',0,'c8f7bf7b-d903-42ec-bfdf-74d357ac4230',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('83c7602b-ad10-4b34-935f-d0fa225ce9b8','8adb23cc-dee3-44da-8356-fa6ce849e4d6',0,'d77ccaa0-3a3d-46ff-877f-4edf1a8179e2',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('8609a2ef-9da2-4803-ad4f-605bfff10795','31fc3f66-34e9-478f-8d1b-c29cd0012360',0,'58fcd2fd-bcdf-4e49-ad99-7e24cc8c3ba5',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('86bba355-218d-4eef-b6ef-145d17ddbbff','bbfbecde-370c-4e26-8087-cfa751e72e6a',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('883345d7-9bb6-455f-b546-0fbe27c08048','46dcf7b1-3750-4f49-a9be-a4bf076e304f',0,'df1cc271-ff77-4f86-b4f3-afc01856db1f',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('88a36d00-af47-4845-8bcf-a72529ae78f8','3c526a07-c3b8-4e53-801b-7f3d0c4857a5',0,'c77fee8c-7c4e-4871-a72e-94d499994869',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('88ccca76-c4d0-4172-b722-0c0ecb3d7d46','83d5e887-6f7c-48b0-bd81-e3f00a9da772',0,'29dece8e-55a4-4f2c-b4c2-365ab6376ceb',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('88e39b88-e57b-4cb5-96e4-dd48cb9e3a6f','d1018160-aaab-4d92-adce-d518880d7c7d',0,'b3d11842-0090-420a-8919-52d7039d50e6',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('8a526305-0805-4680-8dd8-3f7dd3da7854','8de9fe10-932f-4151-88b0-b50cf271e156',0,'9e3dd445-551d-42d1-89ba-fe6dff7c6ee6',NULL,'Completed successfully',NULL,'2012-10-24 00:40:07'),('8aa5fa19-cd87-4abf-b1ee-84f23f145be8','f3efc52e-22e1-4337-b8ed-b38dac0f9f77',0,'cf26b361-dd5f-4b62-a493-6ee02728bd5f',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('8b8a4bc0-277c-4d45-acc0-d02f7a34e31a','3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('8bec6c39-8b98-4e2c-9a91-f7a9c8130f2e','66c9c178-2224-41c6-9c0b-dcb60ff57b1a',0,'2714cd07-b99f-40e3-9ae8-c97281d0d429',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('8c346844-b95d-4ed5-8fc3-694c34844de9','22ded604-6cc0-444b-b320-f96afb15d581',0,'bd382151-afd0-41bf-bb7a-b39aef728a32',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('8c9618b1-3cf2-411e-a5ef-bb4c23470c84','0e1a8a6b-abcc-4ed6-b4fb-cbccfdc23ef5',0,'26bf24c9-9139-4923-bf99-aa8648b1692b',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('8e572576-4ad9-4a8b-8d18-80b2af8d1d4e','eb52299b-9ae6-4a1f-831e-c7eee0de829f',0,'d27fd07e-d3ed-4767-96a5-44a2251c6d0a',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('8e8166c3-aca3-4eea-aa66-1522117f0b97','c4e109d6-38ee-4c92-b83d-bc4d360f6f2e',0,'0b5ad647-5092-41ce-9fe5-1cc376d0bc3f',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('8f2feee8-9c73-4ee1-bdaf-29c43bffba25','45f4a7e3-87cf-4fb4-b4f9-e36ad8c853b1',0,'288b739d-40a1-4454-971b-812127a5e03d',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('8f5f0648-1051-44cd-80a1-d83e21f67d42','828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('8f795343-1ebb-46f5-9cb4-03442c5bc14e','8f639582-8881-4a8b-8574-d2f86dc4db3d',0,'39a128e3-c35d-40b7-9363-87f75091e1ff',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('8f95edbc-02d4-4a0e-8904-d5c027c9969b','2584b25c-8d98-44b7-beca-2b3ea2ea2505',0,'a329d39b-4711-4231-b54e-b5958934dccb',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('8fd30c27-7125-4b9f-8e8d-d2bdd41f3525','3e25bda6-5314-4bb4-aa1e-90900dce887d',0,'002716a1-ae29-4f36-98ab-0d97192669c4',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('90c61585-bd9c-4c7c-81ea-693039b1a4c4','7d43afab-4d3e-4733-a3f2-84eb772e9e57',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('9159eb2a-e720-4bf0-bafb-ed5bd5b9db7b','5cf308fd-a6dc-4033-bda1-61689bb55ce2',0,'88d2120a-4d19-4b47-922f-7438be1f52a2',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('919909a4-b66f-4bca-af3d-fc8ec6f94047','8bc92801-4308-4e3b-885b-1a89fdcd3014',0,'f1e286f9-4ec7-4e19-820c-dae7b8ea7d09',NULL,'Completed successfully',NULL,'2013-02-13 22:03:39'),('9367abb6-a9ce-4ed6-88e0-b3370d1f0003','0d7f5dc2-b9af-43bf-b698-10fdcc5b014d',0,NULL,NULL,'Completed successfully',NULL,'2013-04-18 20:38:36'),('938e6215-77f4-4ebc-abdd-ed511ebc5357','c168f1ee-5d56-4188-8521-09f0c5475133',0,'e4b0c713-988a-4606-82ea-4b565936d9a7',NULL,'Completed successfully',NULL,'2013-02-13 22:03:41'),('942ba7f8-d58a-439f-97cc-10964f6c2f13','46e19522-9a71-48f1-9ccd-09cabfba3f38',0,'3409b898-e532-49d3-98ff-a2a1f9d988fa',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('96f3718e-bccd-4cc1-ad23-2996345fc553','4ac461f9-ee69-4e03-924f-60ac0e8a4b7f',0,'0ba9bbd9-6c21-4127-b971-12dbc43c8119',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('97dd0591-5588-4cd4-9da8-fec60f2369c0','b2552a90-e674-4a40-a482-687c046407d3',0,'21d6d597-b876-4b3f-ab85-f97356f10507',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('98aa3486-eb3d-4273-9c42-9fc0542b3334','3467d003-1603-49e3-b085-e58aa693afed',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('992e8dce-80e3-4721-8f25-9e6334fae8c5','2e7f83f9-495a-44b3-b0cf-bff66f021a4d',0,'bbfbecde-370c-4e26-8087-cfa751e72e6a',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('9b010021-a969-4a16-98c2-0db1ecd5d6d9','8ba83807-2832-4e41-843c-2e55ad10ea0b',0,'5d6a103c-9a5d-4010-83a8-6f4c61eb1478',NULL,'Completed successfully',NULL,'2012-10-24 00:40:07'),('9cdd2a70-61a3-4590-8ccd-26dde4290be4','df02cac1-f582-4a86-b7cf-da98a58e279e',0,'f3be1ee1-8881-465d-80a6-a6f093d40ec2',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('9d7c1a9c-85d3-407c-9be2-044885bc064a','65240550-d745-4afe-848f-2bf5910457c9',0,'3ba518ab-fc47-4cba-9b5c-79629adac10b',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('9dd9d972-d4ef-4368-8a2f-eb77ae4f4f90','f8319d49-f1e3-45dd-a404-66165c59dec7',0,'4b75ca30-2eaf-431b-bffa-d737c8a0bf37',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('9e7cc8ee-4732-4dfa-86c4-cdb8b9c710da','7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1',0,'bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1',NULL,'Completed successfully',NULL,'2012-10-02 07:25:07'),('9f6bc15e-31fc-4682-baf5-a780288eba2c','20515483-25ed-4133-b23e-5bb14cab8e22',0,'48703fad-dc44-4c8e-8f47-933df3ef6179',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('9fc959c0-d635-44d0-8f1b-168e843b33cc','b20ff203-1472-40db-b879-0e59d17de867',0,'7b146689-1a04-4f58-ba86-3caf2b76ddbc',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('a085c6ce-4af0-4ac3-9755-93b4945bd71d','888a5bdc-9928-44f0-9fb7-91bc5f1e155b',0,'214f1004-2748-4bed-a38d-48fe500c41b9',NULL,'Completed successfully',NULL,'2012-12-12 21:25:31'),('a0f33c59-081b-4427-b430-43b811cf0594','b6b0fe37-aa26-40bd-8be8-d3acebf3ccf8',0,'b21018df-f67d-469a-9ceb-ac92ac68654e',NULL,'Completed successfully',NULL,'2013-02-13 22:03:40'),('a38d1d45-42e7-47ea-9a83-01a139f28d59','5fbc344c-19c8-48be-a753-02dac987428c',0,'746b1f47-2dad-427b-8915-8b0cb7acccd8',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('a5e44b09-e884-4364-8793-7d81b4a4c29b','ef6332ee-a890-4e1b-88de-986efc4269fb',0,'0c96c798-9ace-4c05-b3cf-243cdad796b7',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('a9569ef7-fbba-4f1a-9230-83a8bb73c166','9304d028-8387-4ab5-9539-0aab9ac5bdb1',0,'45f01e11-47c7-45a3-a99b-48677eb321a5',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('a9eb16bf-74e9-468d-b3c5-3ee9e7aa6453','fdfac6e5-86c0-4c81-895c-19a9edadedef',0,'7c95b242-1ce5-4210-b7d4-fdbb6c0aa5dd',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('aaf01618-5e54-4d28-8dcd-8904f912e552','cf71e6ff-7740-4bdb-a6a9-f392d678c6e1',0,'2adf60a0-ecd7-441a-b82f-f77c6a3964c3',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('ab61e4b6-1167-461f-921e-ebcb5126ff89','7a024896-c4f7-4808-a240-44c87c762bc5',0,'2dd53959-8106-457d-a385-fee57fc93aa9',NULL,'Completed successfully',NULL,'2013-11-07 22:51:42'),('ad09d973-5c5d-44e9-84a2-a7dbb27dd23d','2714cd07-b99f-40e3-9ae8-c97281d0d429',0,'7c6a0b72-f37b-4512-87f3-267644de6f80',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('ae13dd4f-81d6-44d5-94c8-0c19aa6c6cf8','b3d11842-0090-420a-8919-52d7039d50e6',0,'e3a6d178-fa65-4086-a4aa-6533e8f12d51',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('affffa5f-33b2-43cc-84e0-f7f378c9600e','29dece8e-55a4-4f2c-b4c2-365ab6376ceb',0,'635ba89d-0ad6-4fc9-acc3-e6069dffdcd5',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('b060a877-9a59-450c-8da0-f32b97b1a516','3f543585-fa4f-4099-9153-dd6d53572f5c',0,'20515483-25ed-4133-b23e-5bb14cab8e22',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('b06d8cfe-7cc0-46d0-bc53-93f0068cf9cf','2f83c458-244f-47e5-a302-ce463163354e',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('b4293a9c-71c6-4dbb-a49c-1fcfc506b1ee','8dc0284a-45f4-486e-a78d-7af3e5b8d621',0,'6b931965-d5f6-4611-a536-39d5901f8f70',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('b5157984-6f63-4903-a582-ff1f104e6009','440ef381-8fe8-4b6e-9198-270ee5653454',0,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('b61ce1c0-30f3-4871-85a2-dcf14e0f659c','cb48ef2a-3394-4936-af1f-557b39620efa',0,'888a5bdc-9928-44f0-9fb7-91bc5f1e155b',NULL,'Completed successfully',NULL,'2012-11-30 19:55:48'),('b741a8b8-5c79-4748-80e0-6ec88236043b','cf26b361-dd5f-4b62-a493-6ee02728bd5f',0,'b063c4ce-ada1-4e72-a137-800f1c10905c',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('b87ee978-0f02-4852-af21-4511a43010e6','bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0',0,'440ef381-8fe8-4b6e-9198-270ee5653454',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('bb452573-3323-45cc-8835-ca5ba682a379','c425258a-cf54-44f9-b39f-cf14c7966a41',0,'8adb23cc-dee3-44da-8356-fa6ce849e4d6',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('bb45ac92-22fd-44e7-9c6a-7d653edd1496','8ce378a5-1418-4184-bf02-328a06e1d3be',0,'83257841-594d-4a0e-a4a1-1e9269c30f3d',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('bbc7cbfd-c3aa-4625-8782-a461615137ed','f1e286f9-4ec7-4e19-820c-dae7b8ea7d09',0,NULL,NULL,'Completed successfully',NULL,'2013-02-13 22:03:37'),('bce1ab01-7acd-466a-8ed5-a0d2efaad960','f7488721-c936-42af-a767-2f0b39564a86',0,'2483c25a-ade8-4566-a259-c6c37350d0d6',NULL,'Completed successfully',NULL,'2012-12-04 20:13:10'),('bd03ec7a-7d3f-4562-b50f-02ce4f56e344','2307b24a-a019-4b5b-a520-a6fff270a852',0,'b443ba1a-a0b6-4f7c-aeb2-65bd83de5e8b',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('be2d2436-1764-46ba-a341-8ad74d282056','01292b28-9588-4a85-953b-d92b29faf4d0',0,'b063c4ce-ada1-4e72-a137-800f1c10905c',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('bfb7fc07-ab7b-11e2-bace-08002742f837','bfade79c-ab7b-11e2-bace-08002742f837',0,'0d7f5dc2-b9af-43bf-b698-10fdcc5b014d',NULL,'Completed successfully',NULL,'2013-04-22 18:37:56'),('bfd11ca1-57db-4340-89bb-7e25b0386a64','154dd501-a344-45a9-97e3-b30093da35f5',0,'3c526a07-c3b8-4e53-801b-7f3d0c4857a5',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c1dd1c2c-a18a-4716-a525-3d650cb5529a','7c44c454-e3cc-43d4-abe0-885f93d693c6',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c1f6f15d-2ce9-43fd-841c-1fd916f9fd2e','e4e19c32-16cc-4a7f-a64d-a1f180bdb164',0,'29dece8e-55a4-4f2c-b4c2-365ab6376ceb',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('c2c7eb9e-d523-40ab-9cf2-d83f72d8977f','378ae4fc-7b62-40af-b448-a1ab47ac2c0c',0,'ad011cc2-b0eb-4f51-96bb-400149a2ea11',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c2ccb9f8-c7d3-4876-a29c-3f15c3663451','87e7659c-d5de-4541-a09c-6deec966a0c0',0,'6bd4d385-c490-4c42-a195-dace8697891c',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c35e05aa-5bb0-454f-8ff3-66ffc625f7ef','67b44f8f-bc97-4cb3-b6dd-09dba3c99d30',179,'9e3dd445-551d-42d1-89ba-fe6dff7c6ee6',NULL,'Completed successfully',NULL,'2012-10-24 00:40:07'),('c4060d14-6cfe-4e06-9c8a-17c380a9895d','3409b898-e532-49d3-98ff-a2a1f9d988fa',0,'9071c352-aed5-444c-ac3f-b6c52dfb65ac',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c496fdf3-1d60-4adc-9af7-d3ef8b88fc3f','9e4e39be-0dad-41bc-bee0-35cb71e693df',0,'209400c1-5619-4acc-b091-b9d9c8fbb1c0',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c4c0538a-56fd-4c8e-96dd-c58b713be284','f2a1faaf-7322-4d9c-aff9-f809e7a6a6a2',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c4c7ff3c-3eef-42e3-a68d-f11ca3e7c6dd','c77fee8c-7c4e-4871-a72e-94d499994869',0,'f0f64c7e-30fa-47c1-9877-43955680c0d0',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c648c562-a9a2-499e-ac5b-055488d842dc','77a7fa46-92b9-418e-aa88-fbedd4114c9f',0,'f574b2a0-6e0b-4c74-ac5b-a73ddb9593a0',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c66b290b-3c3b-4122-86f6-d8953db77f70','f574b2a0-6e0b-4c74-ac5b-a73ddb9593a0',0,'47dd6ea6-1ee7-4462-8b84-3fc4c1eeeb7f',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c6e80559-2eda-484d-9f5e-bd365b11278f','9e3dd445-551d-42d1-89ba-fe6dff7c6ee6',0,'e219ed78-2eda-4263-8c0f-0c7f6a86c33e',NULL,'Completed successfully',NULL,'2012-10-24 00:40:07'),('c8225885-4554-4181-b006-13048f99eb5c','1798e1d4-ec91-4299-a767-d10c32155d19',0,'c425258a-cf54-44f9-b39f-cf14c7966a41',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c84e7df7-2259-418d-a5f0-37108d63ac13','6327fdf9-9673-42a8-ace5-cccad005818b',0,'7a134af0-b285-4a9f-8acf-f6947b7ed072',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c91c108d-3491-440b-97c7-b71bfcb2ebec','a1b65fe3-9358-479b-93b9-68f2b5e71b2b',0,'9e9b522a-77ab-4c17-ab08-5a4256f49d59',NULL,'Completed successfully',NULL,'2013-01-03 02:10:39'),('c9422b26-d2bc-4c03-a173-809d12971d27','67a91b4b-a5af-4b54-a836-705e6cf4eeb9',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('c97b8ab4-069e-4b37-8ccf-f27480ba8d6e','4103a5b0-e473-4198-8ff7-aaa6fec34749',0,'092b47db-6f77-4072-aed3-eb248ab69e9c',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('cb53d708-4e54-4b93-a2b5-3c323cd9750f','cccc2da4-e9b8-43a0-9ca2-7383eff0fac9',0,'378ae4fc-7b62-40af-b448-a1ab47ac2c0c',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('cb61ce7b-4ba0-483e-8dfa-5c30af4927db','a2173b55-abff-4d8f-97b9-79cc2e0a64fa',0,NULL,NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('cc349cf1-7e9d-476e-9669-d5fdacea81b4','ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c',0,'438dc1cf-9813-44b5-a0a3-58e09ae73b8a',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('cd98e02d-19ae-408e-8199-4000d2a5dfee','61c316a6-0a50-4f65-8767-1f44b1eeb6dd',0,'377f8ebb-7989-4a68-9361-658079ff8138',NULL,'Completed successfully',NULL,'2013-01-08 02:12:00'),('cdbd5aee-2ff5-463e-bdb2-b18d48d392bb','35c8763a-0430-46be-8198-9ecb23f895c8',0,'180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('ce4ca1af-4a4b-4dbb-a8ef-4a52da95b7b9','4ef35d72-9494-431a-8cdb-8527b42664c7',0,'76d87f57-9718-4f68-82e6-91174674c49c',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('cfd3ad31-70e2-4b7f-9643-fff6e6ab1f91','f0f64c7e-30fa-47c1-9877-43955680c0d0',0,'46e19522-9a71-48f1-9ccd-09cabfba3f38',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('d12fdeb8-f8dd-4ba6-8a72-80f1ec406b3e','663a11f6-91cb-4fef-9aa7-2594b3752e4c',0,'a132193a-2e79-4221-a092-c51839d566fb',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('d1b46b7e-57cd-4120-97d6-50f8e385f56e','77c722ea-5a8f-48c0-ae82-c66a3fa8ca77',0,'c103b2fb-9a6b-4b68-8112-b70597a6cd14',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('d235e950-1d4a-4180-b22c-e74b929e4c86','70f41678-baa5-46e6-a71c-4b6b4d99f4a6',0,'8dc0284a-45f4-486e-a78d-7af3e5b8d621',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('d2c5ab7b-ced1-45cd-a7da-98ab30a31259','192315ea-a1bf-44cf-8cb4-0b3edd1522a6',0,'2fd123ea-196f-4c9c-95c0-117aa65ed9c6',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('d37c9a69-a757-4a7d-9f48-9299b8eb5cfa','89071669-3bb6-4e03-90a3-3c8b20c7f6fe',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('d4076b34-0b38-4c00-b35b-74ef6cfade97','d77ccaa0-3a3d-46ff-877f-4edf1a8179e2',0,'39ac9205-cb08-47b1-8bc3-d3375e37d9eb',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('d4c81458-05b5-434d-a972-46ae43417213','092b47db-6f77-4072-aed3-eb248ab69e9c',0,'bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('d5690bcf-1c0f-44a1-846e-e63cea2b9087','28a9f8a8-0006-4828-96d5-892e6e279f72',0,'5e4bd4e8-d158-4c2a-be89-51e3e9bd4a06',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('d5838814-8874-4fe1-b375-2e044cdf05c2','2d751fc6-dc9d-4c52-b0d9-a4454cefb359',0,'b063c4ce-ada1-4e72-a137-800f1c10905c',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('d60a37f1-3422-46ee-bfc2-2d55b282c98b','b443ba1a-a0b6-4f7c-aeb2-65bd83de5e8b',0,'0f0c1f33-29f2-49ae-b413-3e043da5df61',NULL,'Completed successfully',NULL,'2013-01-03 02:10:40'),('d6914e3c-4d4a-4b0d-9d26-eeb340ac027b','f2a019ea-0601-419c-a475-1b96a927a2fb',0,'aa9ba088-0b1e-4962-a9d7-79d7a0cbea2d',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('d69a5920-5c3b-46ff-bdcd-e836dfa7c954','d7e6404a-a186-4806-a130-7e6d27179a15',0,'f92dabe5-9dd5-495e-a996-f8eb9ef90f48',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('d73a6c9a-0d51-4bef-980a-3769199f40e7','0745a713-c7dc-451d-87c1-ec3dc28568b8',0,'f7323418-9987-46ce-aac5-1fe0913c753a',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('d7c24320-1152-4808-96ea-81cfdd0617ed','7d728c39-395f-4892-8193-92f086c0546f',0,'828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c',NULL,'Completed successfully',NULL,'2013-01-08 02:12:00'),('d81c236d-6a0c-4bf1-a1b1-4ece6763e890','1b737a9b-b4c0-4230-aa92-1e88067534b9',0,'20129b22-8f28-429b-a3f2-0648090fa305',NULL,'Completed successfully',NULL,'2012-12-06 18:58:24'),('da1d8295-6914-4839-b1dd-6dd33ab6a41c','1cd3b36a-5252-4a69-9b1c-3b36829288ab',0,'67b44f8f-bc97-4cb3-b6dd-09dba3c99d30',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('da54863b-44c0-4ea2-9561-34105ed5208e','e2c0dae9-3295-4a98-b3ff-664ab2dc0cda',0,'7e65c627-c11d-4aad-beed-65ceb7053fe8',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('dad05633-987d-4672-9b7c-1341cecbf59c','bdfecadc-8219-4109-885c-cfb9ef53ebc3',0,'823b0d76-9f3c-410d-83ab-f3c2cdd9ab22',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('dad445c0-0b8e-466c-9fe0-537002fd8852','a536965b-e501-42aa-95eb-0656775be6f2',0,'88affaa2-13c5-4efb-a860-b182bd46c2c6',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('db159412-71fa-4d94-aea6-c173e82fd7c2','a46e95fe-4a11-4d3c-9b76-c5d8ea0b094d',0,'15a2df8a-7b45-4c11-b6fa-884c9b7e5c67',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('dc3c6084-74eb-4dc9-b3bd-6c89c8538d8a','88d2120a-4d19-4b47-922f-7438be1f52a2',0,'89071669-3bb6-4e03-90a3-3c8b20c7f6fe',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('dc99bcd5-e3c3-4763-9b37-3bff5f92f5e9','3868c8b8-977d-4162-a319-dc487de20f11',0,'f7488721-c936-42af-a767-2f0b39564a86',NULL,'Completed successfully',NULL,'2012-11-30 19:55:48'),('dcf156a2-2ee4-4673-99de-4689f281dc43','da2d650e-8ce3-4b9a-ac97-8ca4744b019f',0,'4417b129-fab3-4503-82dd-740f8e774bff',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('dd9e0f88-9e96-4d8b-a9ae-e0cee1dc5365','db6d3830-9eb4-4996-8f3a-18f4f998e07f',0,'70669a5b-01e4-4ea0-ac70-10292f87da05',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('de6d3970-c27e-4be0-929f-07bca37db7cc','f95a3ac5-47bc-4df9-a49c-d47abd1e05f3',0,'b4567e89-9fea-4256-99f5-a88987026488',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('e0199503-2b98-47a6-89d9-3a1a91d042c3','82c0eca0-d9b6-4004-9d77-ded9286a9ac7',0,'d5a2ef60-a757-483c-a71a-ccbffe6b80da',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('e0248782-a96c-4fa3-8a02-3157c976f4e1','ad011cc2-b0eb-4f51-96bb-400149a2ea11',0,'6ee25a55-7c08-4c9a-a114-c200a37146c4',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('e05ae8d7-89ee-46bf-9308-f2cdaa0957f7','e219ed78-2eda-4263-8c0f-0c7f6a86c33e',0,'7d43afab-4d3e-4733-a3f2-84eb772e9e57',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('e090fea3-2e44-4dd9-b17d-73c4d2088e0c','9e9b522a-77ab-4c17-ab08-5a4256f49d59',0,'e76aec15-5dfa-4b14-9405-735863e3a6fa',NULL,'Completed successfully',NULL,'2013-01-03 02:10:39'),('e0935e25-62dc-43c1-b4d3-bb3c1f8f04f9','75fb5d67-5efa-4232-b00b-d85236de0d3f',0,'ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0',NULL,'Completed successfully',NULL,'2013-02-08 22:21:21'),('e0d9e83b-89e1-4711-89e4-14dbe15bea4c','370aca94-65ab-4f2a-9d7d-294a62c8b7ba',0,'f1bfce12-b637-443f-85f8-b6450ca01a13',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('e132d3e2-6dcd-4c81-b6f3-7a0ea04193c0','aaa929e4-5c35-447e-816a-033a66b9b90b',0,'303a65f6-a16f-4a06-807b-cb3425a30201',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('e28ed9a4-f176-482e-a360-7893995080bc','2483c25a-ade8-4566-a259-c6c37350d0d6',0,'1b737a9b-b4c0-4230-aa92-1e88067534b9',NULL,'Completed successfully',NULL,'2012-12-04 20:13:09'),('e5b32c5b-6165-4158-ac85-573f627c5a8f','9071c352-aed5-444c-ac3f-b6c52dfb65ac',0,'03ee1136-f6ad-4184-8dcb-34872f843e14',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('e70eb6eb-0ced-481b-9872-231fd0005ad8','6bd4d385-c490-4c42-a195-dace8697891c',0,'209400c1-5619-4acc-b091-b9d9c8fbb1c0',NULL,'Completed successfully',NULL,'2012-11-20 22:55:53'),('e84b0a8d-7fcc-497e-969d-5046a3b24681','438dc1cf-9813-44b5-a0a3-58e09ae73b8a',0,'d0c463c2-da4c-4a70-accb-c4ce96ac5194',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('e8c31963-29fe-4812-846e-3d18327db4b4','180ae3d0-aa6c-4ed4-ab94-d0a2121e7f21',0,'8ce378a5-1418-4184-bf02-328a06e1d3be',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('e9a2f2c6-fd4b-4766-8794-a96d69256e2b','01fd7a29-deb9-4dd1-8e28-1c48fc1ac41b',0,'ac85a1dc-272b-46ac-bb3e-5bf3f8e56348',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('e9bd8aee-74a8-4a55-bd7a-062ea4bc321b','2872d007-6146-4359-b554-6e9fe7a8eca6',0,'e2c0dae9-3295-4a98-b3ff-664ab2dc0cda',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('ea5b8e14-519e-473b-818c-e62879559816','d2035da2-dfe1-4a56-8524-84d5732fd3a3',0,'cb48ef2a-3394-4936-af1f-557b39620efa',NULL,'Completed successfully',NULL,'2012-11-30 19:55:48'),('ea78b5c7-0bf3-46a2-a08d-faeaeeeed363','47dd6ea6-1ee7-4462-8b84-3fc4c1eeeb7f',0,'173d310c-8e40-4669-9a69-6d4c8ffd0396',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('eb5c83b1-1f60-4f77-85af-ee8cccf01924','a58bd669-79af-4999-8654-951f638d4457',0,NULL,NULL,'Completed successfully',NULL,'2013-11-07 22:51:42'),('ebaa0741-cf37-406f-8769-e2f9b00d0935','a72afc44-fa28-4de7-b35f-c79b9f01aa5c',0,'25b8ddff-4074-4803-a0dc-bbb3acd48a97',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('ec42faf9-8f99-47c0-b29d-c9bdc580ef5b','1c7726a4-9165-4809-986a-bf4477c719ca',0,'26cf64e2-21b5-4935-a52b-71695870f1f2',NULL,'Completed successfully',NULL,'2013-01-10 22:49:50'),('ece1558b-2b29-41aa-abe2-732510d4f47f','38c591d4-b7ee-4bc0-b993-c592bf15d97d',0,'f92dabe5-9dd5-495e-a996-f8eb9ef90f48',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('ece55bab-4377-4ac8-b021-59c88dceea34','0b5ad647-5092-41ce-9fe5-1cc376d0bc3f',0,'0f0c1f33-29f2-49ae-b413-3e043da5df61',NULL,'Completed successfully',NULL,'2013-01-03 02:10:39'),('edcb6a1c-3122-4de3-80a8-b5cbae330aad','0f0c1f33-29f2-49ae-b413-3e043da5df61',0,'745340f5-5741-408e-be92-34c596c00209',NULL,'Completed successfully',NULL,'2013-01-03 02:10:39'),('ef56e6a6-5280-4227-9799-9c1d2d7c0919','f09847c2-ee51-429a-9478-a860477f6b8d',0,'c3269a0a-91db-44e8-96d0-9c748cf80177',NULL,'Completed successfully',NULL,'2013-11-07 22:51:42'),('effb457a-885d-411e-a542-9f37e30007fc','db9177f5-41d2-4894-be1a-a7547ed6b63a',0,'cddde867-4cf9-4248-ac31-f7052fae053f',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f01f4b3e-a8a8-4ec8-b373-a1cb7d307590','39a128e3-c35d-40b7-9363-87f75091e1ff',0,'3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f0ba8289-b40f-4279-a968-7496f837c9f9','1cb7e228-6e94-4c93-bf70-430af99b9264',0,'c5ecb5a9-d697-4188-844f-9a756d8734fa',NULL,'Completed successfully',NULL,'2013-11-07 22:51:43'),('f11414be-45ae-4f17-bf8e-76a9dd784d39','1ba589db-88d1-48cf-bb1a-a5f9d2b17378',0,'33d7ac55-291c-43ae-bb42-f599ef428325',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f139c451-a7d8-467d-811f-9ee556d7f1d2','209400c1-5619-4acc-b091-b9d9c8fbb1c0',0,'ddc8b2ef-a7ba-4713-9425-ed18a1fa720b',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f2857a15-9c0a-49df-92ee-a95678940f15','c2e6600d-cd26-42ed-bed5-95d41c06e37b',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f34b9825-9a86-49bd-939c-050c25e62c49','33d7ac55-291c-43ae-bb42-f599ef428325',0,'576f1f43-a130-4c15-abeb-c272ec458d33',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f4d92639-af82-476d-84cd-508afd167fcf','576f1f43-a130-4c15-abeb-c272ec458d33',0,'88807d68-062e-4d1a-a2d5-2d198c88d8ca',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f52ffb80-3ecd-4db0-9110-d6568cfd3e10','745340f5-5741-408e-be92-34c596c00209',0,'78b7adff-861d-4450-b6dd-3fabe96a849e',NULL,'Completed successfully',NULL,'2013-01-03 02:10:39'),('f5644951-ecaa-42bc-9286-ed4ee220b58f','0915f727-0bc3-47c8-b9b2-25dc2ecef2bb',0,'5fbc344c-19c8-48be-a753-02dac987428c',NULL,'Completed successfully',NULL,'2013-11-07 22:51:35'),('f61a8be3-8574-49a9-9af5-cb3a01ed6ab5','7a134af0-b285-4a9f-8acf-f6947b7ed072',0,'56da7758-913a-4cd2-a815-be140ed09357',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f6f2c768-f322-4ad5-a64a-96746dbe4afa','0fc3c795-dc68-4aa0-86fc-cbd6af3302fa',0,'e399bd60-202d-42df-9760-bd14497b5034',NULL,'Completed successfully',NULL,'2012-12-04 00:47:58'),('f77ea984-9a0e-4214-a7f4-9e33a3157837','032cdc54-0b9b-4caf-86e8-10d63efbaec0',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f797ae30-2018-40bd-bbff-7a947058ee7b','01d64f58-8295-4b7b-9cab-8f1b153a504f',0,'01c651cb-c174-4ba4-b985-1d87a44d6754',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f98ca91f-8650-4f5c-9acb-21c0fdb5ac0a','74665638-5d8f-43f3-b7c9-98c4c8889766',0,'7d43afab-4d3e-4733-a3f2-84eb772e9e57',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('f9d57a68-a7be-41ee-ad9f-b761fac65b1c','d5a2ef60-a757-483c-a71a-ccbffe6b80da',0,NULL,NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('fa5b0c43-ed7b-4c7e-95a8-4f9ec7181260','fa5b0c43-ed7b-4c7e-95a8-4f9ec7181260',0,'cccc2da4-e9b8-43a0-9ca2-7383eff0fac9',NULL,'Completed successfully',NULL,'2013-01-11 00:50:39'),('fb0ecf23-a32e-4874-96dc-1175ee86b159','0a6558cf-cf5f-4646-977e-7d6b4fde47e8',0,'055de204-6229-4200-87f7-e3c29f095017',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('fc879152-2c5f-44ec-aea8-10594cec0281','f92dabe5-9dd5-495e-a996-f8eb9ef90f48',0,'2584b25c-8d98-44b7-beca-2b3ea2ea2505',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('fd465136-38f3-47b8-80dd-f02d5fa9888a','b21018df-f67d-469a-9ceb-ac92ac68654e',0,'8bc92801-4308-4e3b-885b-1a89fdcd3014',NULL,'Completed successfully',NULL,'2013-02-13 22:03:39'),('fe188831-76b3-4487-8712-5d727a50e8ce','2a62f025-83ec-4f23-adb4-11d5da7ad8c2',0,'11033dbd-e4d4-4dd6-8bcf-48c424e222e3',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07'),('fe27318c-9ee1-470f-a9ce-0f8103cc78a5','e950cd98-574b-4e57-9ef8-c2231e1ce451',0,'5c0d8661-1c49-4023-8a67-4991365d70fb',NULL,'Completed successfully',NULL,'2013-11-15 00:31:31'),('ff97354f-9fdd-4c85-8a33-cb9e96b48229','e4b0c713-988a-4606-82ea-4b565936d9a7',0,'dc9d4991-aefa-4d7e-b7b5-84e3c4336e74',NULL,'Completed successfully',NULL,'2013-02-13 22:03:40'),('fff06898-16ff-40a5-ba41-90652f65eb9c','5e4bd4e8-d158-4c2a-be89-51e3e9bd4a06',0,'b6c9de5a-4a9f-41e1-a524-360bdca39893',NULL,'Completed successfully',NULL,'2012-10-02 00:25:07');
/*!40000 ALTER TABLE `MicroServiceChainLinksExitCodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MicroServiceChains`
--

DROP TABLE IF EXISTS `MicroServiceChains`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MicroServiceChains` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `startingLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` longtext COLLATE utf8_unicode_ci,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `MicroServiceChains` (`pk`),
  KEY `startingLink` (`startingLink`),
  CONSTRAINT `MicroServiceChains_ibfk_1` FOREIGN KEY (`startingLink`) REFERENCES `MicroServiceChainLinks` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MicroServiceChains`
--

LOCK TABLES `MicroServiceChains` WRITE;
/*!40000 ALTER TABLE `MicroServiceChains` DISABLE KEYS */;
INSERT INTO `MicroServiceChains` VALUES ('040feba9-4039-48b3-bf7d-a5a5e5f4ce85','cf26b361-dd5f-4b62-a493-6ee02728bd5f','FITS - JHOVE',NULL,'2013-11-07 22:51:35'),('082fa7d6-68e1-431c-9216-899aec92cfa7','5cf308fd-a6dc-4033-bda1-61689bb55ce2','Attempt restructure for compliance',NULL,'2012-10-02 00:25:08'),('09949bda-5332-482a-ae47-5373bd372174','5bddbb67-76b4-4bcb-9b85-a0d9337e7042','mediainfo',NULL,'2012-10-24 02:41:24'),('0ea3a6f9-ff37-4f32-ac01-eec5393f008a','7a024896-c4f7-4808-a240-44c87c762bc5','Pre-normalize identify file format',NULL,'2013-11-07 22:51:42'),('0fe9842f-9519-4067-a691-8a363132ae24','651236d2-d77f-4ca7-bfe9-6332e96608ff','Upload DIP to Atom',NULL,'2012-10-02 00:25:08'),('12aaa737-4abd-45ea-a442-8f9f2666fa98','d7681789-5f98-49bb-85d4-c01b34dac5b9','FITS - ffident',NULL,'2013-11-07 22:51:35'),('167dc382-4ab1-4051-8e22-e7f1c1bf3e6f','f052432c-d4e7-4379-8d86-f2a08f0ae509','Approve transfer',NULL,'2012-10-02 00:25:08'),('169a5448-c756-4705-a920-737de6b8d595','3467d003-1603-49e3-b085-e58aa693afed','Reject',NULL,'2012-10-02 00:25:08'),('191914db-119e-4b91-8422-c77805ad8249','89071669-3bb6-4e03-90a3-3c8b20c7f6fe','Move transfer back to activeTransfers directory',NULL,'2012-10-02 00:25:08'),('1ab4abd7-5f28-430b-8ea8-3ba531043521','48199d23-afd0-4b9b-b8a3-cd80c7d45e7c','Normalize for preservation',NULL,'2012-10-02 00:25:08'),('1b04ec43-055c-43b7-9543-bd03c6a778ba','333532b9-b7c2-4478-9415-28a3056d58df','Reject transfer',NULL,'2012-10-02 00:25:08'),('1ca0211c-05f9-4805-9119-d066e0bd1960','48bfc7e1-75ed-44eb-a65c-0701c022d934','Create DIP ?',NULL,'2012-10-02 00:25:08'),('1cb2ef0e-afe8-45b5-8d8f-a1e120f06605','5b7a48e1-32ed-43f9-8ffa-e374010fcf76','Approve transfer',NULL,'2012-10-02 00:25:08'),('1e0df175-d56d-450d-8bee-7df1dc7ae815','c4e109d6-38ee-4c92-b83d-bc4d360f6f2e','Approve',NULL,'2013-01-03 02:10:39'),('2256d500-a26e-438d-803d-3ffe17b8caf0','2307b24a-a019-4b5b-a520-a6fff270a852','Approve',NULL,'2013-01-03 02:10:40'),('252ceb42-cc61-4833-a048-97fc0bda4759','0e379b19-771e-4d90-a7e5-1583e4893c56','Skip quarantine',NULL,'2012-10-02 00:25:08'),('260ef4ea-f87d-4acf-830d-d0de41e6d2af','77c722ea-5a8f-48c0-ae82-c66a3fa8ca77','Create DIP from AIP',NULL,'2013-11-07 22:51:35'),('27cf6ca9-11b4-41ac-9014-f8018bcbad5e','01d64f58-8295-4b7b-9cab-8f1b153a504f','Compress AIP',NULL,'2013-11-07 22:51:34'),('2884ed7c-8c4c-4fa9-a6eb-e27bcaf9ab92','c1339015-e15b-4303-8f37-a2516669ac4e','Backup transfer',NULL,'2012-10-02 00:25:08'),('28a4322d-b8a5-4bae-b2dd-71cc9ff99e73','92879a29-45bf-4f0b-ac43-e64474f0f2f9','uploadDIP',NULL,'2012-10-02 00:25:08'),('2ba94783-d073-4372-9bd1-8316ada02635','2872d007-6146-4359-b554-6e9fe7a8eca6','Quarantine',NULL,'2012-10-02 00:25:08'),('2eae85d6-da2f-4f1c-8c33-3810b55e23aa','36609513-6502-4aca-886a-6c4ae03a9f05','SIP Creation complete',NULL,'2012-10-02 00:25:08'),('32dfa5f0-5964-4aa4-8132-9abb5b539644','01292b28-9588-4a85-953b-d92b29faf4d0','FITS - DROID',NULL,'2013-11-07 22:51:35'),('333643b7-122a-4019-8bef-996443f3ecc5','4430077a-92c5-4d86-b0f8-0d31bdb731fb','Unquarantine',NULL,'2012-10-02 00:25:08'),('39682d0c-8d81-4fdd-8e10-85114b9eb2dd','de909a42-c5b5-46e1-9985-c031b50e9d30','approveNormalization',NULL,'2012-10-02 07:25:08'),('4171636c-e013-4ecc-ae45-60b5458c208b','998044bb-6260-452f-a742-cfb19e80125b','Transfers In progress',NULL,'2012-10-02 00:25:08'),('433f4e6b-1ef4-49f8-b1e4-49693791a806','bfade79c-ab7b-11e2-bace-08002742f837','Reject AIP',NULL,'2012-10-02 00:25:08'),('45811f43-40d2-4efa-9c1d-876417834b7f','35c8763a-0430-46be-8198-9ecb23f895c8','manual normalization',NULL,'2012-10-02 00:25:08'),('498795c7-06f2-4f3f-95bf-57f1b35964ad','032cdc54-0b9b-4caf-86e8-10d63efbaec0','Check transfer directory for objects',NULL,'2012-10-02 00:25:08'),('503d240c-c5a0-4bd5-a5f2-e3e44bd0018a','b3c5e343-5940-4aad-8a9f-fb0eccbfb3a3','Select file id type - without existing fits/fileIDbyExt',NULL,'2013-11-07 22:51:35'),('522d85ae-298c-42ff-ab6c-bb5bf795c1ca','2d751fc6-dc9d-4c52-b0d9-a4454cefb359','FITS - file utility',NULL,'2013-11-07 22:51:35'),('526eded3-2280-4f10-ac86-eff6c464cc81','0745a713-c7dc-451d-87c1-ec3dc28568b8','Upload DIP to CONTENTdm',NULL,'2012-10-02 00:25:08'),('55fa7084-3b64-48ca-be64-08949227f85d','b963a646-0569-43c4-89a2-e3b814c5c08e','DSpace Transfers In progress',NULL,'2012-10-02 00:25:08'),('612e3609-ce9a-4df6-a9a3-63d634d2d934','6b39088b-683e-48bd-ab89-9dab47f4e9e0','Normalize for preservation',NULL,'2012-10-02 00:25:08'),('61cfa825-120e-4b17-83e6-51a42b67d969','8f639582-8881-4a8b-8574-d2f86dc4db3d','Create single SIP and continue processing',NULL,'2012-10-02 00:25:08'),('6953950b-c101-4f4c-a0c3-0cd0684afe5e','f95a3ac5-47bc-4df9-a49c-d47abd1e05f3','Approve transfer',NULL,'2012-10-02 00:25:08'),('69f4a4b9-93e2-481c-99a0-fa92d68c3ebd','01fd7a29-deb9-4dd1-8e28-1c48fc1ac41b','SIP Creation complete',NULL,'2012-10-02 00:25:08'),('6f0f35fb-6831-4842-9512-4a263700a29b','2d32235c-02d4-4686-88a6-96f4d6c7b1c3','storeAIP',NULL,'2012-10-02 00:25:08'),('7030f152-398a-470b-b045-f5dfa9013671','55de1490-f3a0-4e1e-a25b-38b75f4f05e3','quarantineSIP ?',NULL,'2012-10-02 00:25:08'),('7065d256-2f47-4b7d-baec-2c4699626121','abd6d60c-d50f-4660-a189-ac1b34fafe85','Send to backlog',NULL,'2013-04-05 23:08:30'),('816f28cd-6af1-4d26-97f3-e61645eb881b','f6bcc82a-d629-4a78-8643-bf6e3cb39fe6','baggitDirectory Transfers In progress',NULL,'2012-10-02 00:25:08'),('89cb80dd-0636-464f-930d-57b61e3928b2','0b92a510-a290-44a8-86d8-6b7139be29df','Do not normalize',NULL,'2012-10-02 00:25:08'),('94f764ad-805a-4d4e-8a2b-a6f2515b30c7','8db10a7b-924f-4561-87b4-cb6078c65aab','TRIM Ingest',NULL,'2012-11-30 19:55:49'),('9634868c-b183-4d65-8587-2f53f7ff5a0a',NULL,'Create SIP(s) manually',NULL,'2012-10-02 00:25:08'),('97ea7702-e4d5-48bc-b4b5-d15d897806ab','46dcf7b1-3750-4f49-a9be-a4bf076e304f','Quarantine',NULL,'2012-10-02 00:25:08'),('9918b64c-b898-407b-bce4-a65aa3c11b89','9520386f-bb6d-4fb9-a6b6-5845ef39375f','createDIPFromAIP-wdChain',NULL,'2013-11-07 22:51:35'),('9efab23c-31dc-4cbd-a39d-bb1665460cbe','49cbcc4d-067b-4cd5-b52e-faf50857b35a','Store AIP',NULL,'2012-10-02 00:25:08'),('a2e19764-b373-4093-b0dd-11d61580f180','ab69c494-23b7-4f50-acff-2e00cf7bffda','SIP Creation',NULL,'2012-10-02 00:25:08'),('a6ed697e-6189-4b4e-9f80-29209abc7937','3467d003-1603-49e3-b085-e58aa693afed','Reject SIP',NULL,'2012-10-02 00:25:08'),('a7f8f67f-401f-4665-b7b3-35496fd5017c','a72afc44-fa28-4de7-b35f-c79b9f01aa5c','Do not backup transfer',NULL,'2012-10-02 00:25:08'),('ad37288a-162c-4562-8532-eb4050964c73','fbc3857b-bb02-425b-89ce-2d6a39eaa542','Unquarantine',NULL,'2012-10-02 00:25:08'),('b0e0bf75-6b7e-44b6-a0d0-189eea7605dd','15402367-2d3f-475e-b251-55532347a3c2','baggitZippedFile Transfers In progress',NULL,'2012-10-02 00:25:08'),('b3b90ab1-39e2-4dea-84a7-34e4c3a13415','d05eaa5e-344b-4daa-b78b-c9f27c76499d','Select file id type - without existing fits/fileIDbyExt',NULL,'2013-11-07 22:51:35'),('b93cecd4-71f2-4e28-bc39-d32fd62c5a94','424ee8f1-6cdd-4960-8641-ed82361d3ad7','Normalize for preservation and access',NULL,'2012-12-04 22:56:32'),('b96411f1-bbf4-425a-adcf-8e7bfac2b85b','f3efc52e-22e1-4337-b8ed-b38dac0f9f77','FITS - summary',NULL,'2013-11-07 22:51:35'),('bd94cc9b-7990-45a2-a255-a1b70936f9f2','f09847c2-ee51-429a-9478-a860477f6b8d','Identify file format',NULL,'2013-11-07 22:51:42'),('c34bd22a-d077-4180-bf58-01db35bdb644','31abe664-745e-4fef-a669-ff41514e0083','Normalize manually',NULL,'2013-01-05 01:09:13'),('c622426e-190e-437b-aa1a-4be9c9a7680d','01fd7a29-deb9-4dd1-8e28-1c48fc1ac41b','Unquarantine',NULL,'2012-10-02 00:25:08'),('c75ef451-2040-4511-95ac-3baa0f019b48','45f4a7e3-87cf-4fb4-b4f9-e36ad8c853b1','Approve transfer',NULL,'2012-10-02 00:25:08'),('cbe9b4a3-e4e6-4a32-8d7c-3adfc409cb6f','b15c0ba6-e247-4512-8b56-860fd2b6299d','Redo',NULL,'2012-10-24 17:04:11'),('cc38912d-6520-44e1-92ff-76bb4881a55e','a98ba456-3dcd-4f45-804c-a40220ddc6cb','Failed compliance',NULL,'2012-10-02 00:25:08'),('cc884b80-3e89-4e0c-bc65-b73019fc0089','39ac9205-cb08-47b1-8bc3-d3375e37d9eb','manual normalization',NULL,'2012-10-02 00:25:08'),('d381cf76-9313-415f-98a1-55c91e4d78e0','22c0f074-07b1-445f-9e8b-bf75ac7f0b48','Approve transfer',NULL,'2012-10-02 00:25:08'),('d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e','d7e6404a-a186-4806-a130-7e6d27179a15','Skip quarantine',NULL,'2012-10-02 00:25:08'),('d4ff46d4-5c57-408c-943b-fed63c1a9d75','4430077a-92c5-4d86-b0f8-0d31bdb731fb','SIP Creation complete',NULL,'2012-10-02 00:25:08'),('d7cf171e-82e8-4bbb-bc33-de6b8b256202','150dcb45-46c3-4529-b35f-b0a8a5a553e9','approveNormalization',NULL,'2012-10-02 00:25:08'),('e4a59e3e-3dba-4eb5-9cf1-c1fb3ae61fa9','3868c8b8-977d-4162-a319-dc487de20f11','Approve transfer',NULL,'2012-11-30 19:55:48'),('e5bc60f8-4e64-4363-bf01-bef67154cfed','1c7726a4-9165-4809-986a-bf4477c719ca','Normalize manually',NULL,'2013-01-05 01:09:13'),('e600b56d-1a43-4031-9d7c-f64f123e5662','b20ff203-1472-40db-b879-0e59d17de867','Normalize service files for access',NULL,'2012-10-02 00:25:08'),('e8544c5e-9cbb-4b8f-a68b-6d9b4d7f7362','70f41678-baa5-46e6-a71c-4b6b4d99f4a6','Do not normalize',NULL,'2012-10-02 00:25:08'),('eea54915-2a85-49b7-a370-b1a250dd29ce','f2a1faaf-7322-4d9c-aff9-f809e7a6a6a2','Reject DIP',NULL,'2012-10-02 00:25:08'),('f11409ad-cf3c-4e7f-b0d5-4be32d98229b','7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1','Upload DIP to Archivists Toolkit',NULL,'2013-03-26 03:25:01'),('fb7a326e-1e50-4b48-91b9-4917ff8d0ae8','6327fdf9-9673-42a8-ace5-cccad005818b','Normalize for access',NULL,'2012-10-02 00:25:08'),('fefdcee4-dd84-4b55-836f-99ef880ecdb6','db6d3830-9eb4-4996-8f3a-18f4f998e07f','Automatic SIP Creation complete',NULL,'2013-08-22 23:25:08'),('fffd5342-2337-463f-857a-b2c8c3778c6d','0c94e6b5-4714-4bec-82c8-e187e0c04d77','Transfers In progress',NULL,'2012-10-02 00:25:08');
/*!40000 ALTER TABLE `MicroServiceChains` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MicroServiceChoiceReplacementDic`
--

DROP TABLE IF EXISTS `MicroServiceChoiceReplacementDic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MicroServiceChoiceReplacementDic` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `choiceAvailableAtLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` longtext COLLATE utf8_unicode_ci,
  `replacementDic` longtext COLLATE utf8_unicode_ci,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `MicroServiceChoiceReplacementDic` (`pk`),
  KEY `choiceAvailableAtLink` (`choiceAvailableAtLink`),
  CONSTRAINT `MicroServiceChoiceReplacementDic_ibfk_1` FOREIGN KEY (`choiceAvailableAtLink`) REFERENCES `MicroServiceChainLinks` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MicroServiceChoiceReplacementDic`
--

LOCK TABLES `MicroServiceChoiceReplacementDic` WRITE;
/*!40000 ALTER TABLE `MicroServiceChoiceReplacementDic` DISABLE KEYS */;
INSERT INTO `MicroServiceChoiceReplacementDic` VALUES ('1f77af0a-2f7a-468f-af8c-653a9e61ca4f','f09847c2-ee51-429a-9478-a860477f6b8d','Skip File Identification','{\"%IDCommand%\":\"None\"}',NULL,'2013-11-07 22:51:42'),('3c1faec7-7e1e-4cdd-b3bd-e2f05f4baa9b','7a024896-c4f7-4808-a240-44c87c762bc5','Use existing data','{\"%IDCommand%\":\"None\"}',NULL,'2013-11-07 22:51:42'),('414da421-b83f-4648-895f-a34840e3c3f5','01c651cb-c174-4ba4-b985-1d87a44d6754','5 - normal compression mode','{\"%AIPCompressionLevel%\":\"5\"}',NULL,'2012-10-02 00:25:08'),('4e31f579-68bd-4be1-a10e-ec5411897121','01c651cb-c174-4ba4-b985-1d87a44d6754','7 - maximum compression','{\"%AIPCompressionLevel%\":\"7\"}',NULL,'2012-10-02 00:25:08'),('5395d1ea-a892-4029-b5a8-5264a17bbade','7b1f1ed8-6c92-46b9-bab6-3a37ffb665f1','Archivists Toolkit Config','{\"%host%\":\"localhost\", \"%port%\":\"3306\", \"%dbname%\":\"atk01\", \"%dbuser%\":\"ATUser\", \"%dbpass%\":\"\", \"%atuser%\":\"atkuser\", \"%restrictions%\":\"premis\", \"%object_type%\":\"\", \"%ead_actuate%\":\"onRequest\", \"%ead_show%\":\"new\", \"%use_statement%\":\"Image-Service\",\"%uri_prefix%\":\"http:www.example.com/\", \"%access_conditions%\":\"\", \"%use_conditions%\":\"\"}',NULL,'2013-03-23 03:25:00'),('6d52fd24-8c06-4c8e-997a-e427ba0acc36','01c651cb-c174-4ba4-b985-1d87a44d6754','9 - ultra compression','{\"%AIPCompressionLevel%\":\"9\"}',NULL,'2012-10-02 00:25:08'),('6ecbb1f7-61b6-467b-b2d5-b373e3222d45','45f01e11-47c7-45a3-a99b-48677eb321a5','Project client','{\"%ContentdmIngestFormat%\":\"projectclient\"}',NULL,'2012-10-02 00:25:08'),('85b2243e-ff97-4ca8-80e8-3c6b0842b360','01c651cb-c174-4ba4-b985-1d87a44d6754','3 - fast compression mode','{\"%AIPCompressionLevel%\":\"3\"}',NULL,'2012-10-02 00:25:08'),('9475447c-9889-430c-9477-6287a9574c5b','01d64f58-8295-4b7b-9cab-8f1b153a504f','7z using bzip2','{\"%AIPCompressionAlgorithm%\":\"7z-bzip2\"}',NULL,'2012-10-02 00:25:08'),('c001db23-200c-4195-9c4a-65f206f817f2','0745a713-c7dc-451d-87c1-ec3dc28568b8','contentdm.example.com','{\"%ContentdmServer%\":\"111.222.333.444:81\", \"%ContentdmUser%\":\"usernamebar\", \"%ContentdmGroup%\":\"456\"}',NULL,'2012-10-02 00:25:08'),('c1f4b3e4-64c2-425f-b0d0-86a5ad2c3eab','45f01e11-47c7-45a3-a99b-48677eb321a5','Direct upload','{\"%ContentdmIngestFormat%\":\"directupload\"}',NULL,'2012-10-02 00:25:08'),('c96353b9-0d55-46cf-baa0-d7c3e180dd43','01d64f58-8295-4b7b-9cab-8f1b153a504f','7z using lzma','{\"%AIPCompressionAlgorithm%\":\"7z-lzma\"}',NULL,'2012-10-02 00:25:08'),('ce62eec6-0a49-489f-ac4b-c7b8c93086fd','0745a713-c7dc-451d-87c1-ec3dc28568b8','localhost','{\"%ContentdmServer%\":\"localhost\", \"%ContentdmUser%\":\"usernamefoo\", \"%ContentdmGroup%\":\"123\"}',NULL,'2012-10-02 00:25:08'),('ecfad581-b007-4612-a0e0-fcc551f4057f','01c651cb-c174-4ba4-b985-1d87a44d6754','1 - fastest mode','{\"%AIPCompressionLevel%\":\"1\"}',NULL,'2012-10-02 00:25:08'),('f61b00a1-ef2e-4dc4-9391-111c6f42b9a7','01d64f58-8295-4b7b-9cab-8f1b153a504f','Parallel bzip2','{\"%AIPCompressionAlgorithm%\":\"pbzip2-\"}',NULL,'2013-08-20 00:25:08');
/*!40000 ALTER TABLE `MicroServiceChoiceReplacementDic` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Notifications`
--

DROP TABLE IF EXISTS `Notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Notifications` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `message` longtext COLLATE utf8_unicode_ci,
  `created` int(11) DEFAULT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Notifications`
--

LOCK TABLES `Notifications` WRITE;
/*!40000 ALTER TABLE `Notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `Notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `PDI_by_unit`
--

DROP TABLE IF EXISTS `PDI_by_unit`;
/*!50001 DROP VIEW IF EXISTS `PDI_by_unit`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `PDI_by_unit` (
  `SIP_OR_TRANSFER_UUID` tinyint NOT NULL,
  `unitType` tinyint NOT NULL,
  `Total time processing` tinyint NOT NULL,
  `Number_of_tasks` tinyint NOT NULL,
  `Average time per task` tinyint NOT NULL,
  `total file size` tinyint NOT NULL,
  `number of files` tinyint NOT NULL,
  `count( DISTINCT  FilesByUnit.fileUUID)` tinyint NOT NULL,
  `average file size KB` tinyint NOT NULL,
  `average file size MB` tinyint NOT NULL,
  `time per task per MB` tinyint NOT NULL,
  `currentLocation` tinyint NOT NULL,
  `currentPath` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `Reports`
--

DROP TABLE IF EXISTS `Reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Reports` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `unitType` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `unitName` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `unitIdentifier` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `content` longtext COLLATE utf8_unicode_ci,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Reports`
--

LOCK TABLES `Reports` WRITE;
/*!40000 ALTER TABLE `Reports` DISABLE KEYS */;
/*!40000 ALTER TABLE `Reports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatement`
--

DROP TABLE IF EXISTS `RightsStatement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatement` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `metadataAppliesToType` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `metadataAppliesToidentifier` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `rightsStatementIdentifierType` longtext COLLATE utf8_unicode_ci NOT NULL,
  `rightsStatementIdentifierValue` longtext COLLATE utf8_unicode_ci NOT NULL,
  `fkAgent` int(10) unsigned NOT NULL DEFAULT '0',
  `rightsBasis` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkAgent` (`fkAgent`),
  KEY `metadataAppliesToType` (`metadataAppliesToType`),
  CONSTRAINT `RightsStatement_ibfk_1` FOREIGN KEY (`metadataAppliesToType`) REFERENCES `MetadataAppliesToTypes` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatement`
--

LOCK TABLES `RightsStatement` WRITE;
/*!40000 ALTER TABLE `RightsStatement` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementCopyright`
--

DROP TABLE IF EXISTS `RightsStatementCopyright`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementCopyright` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatement` int(10) unsigned DEFAULT NULL,
  `copyrightStatus` longtext COLLATE utf8_unicode_ci NOT NULL,
  `copyrightJurisdiction` longtext COLLATE utf8_unicode_ci NOT NULL,
  `copyrightStatusDeterminationDate` longtext COLLATE utf8_unicode_ci NOT NULL,
  `copyrightApplicableStartDate` longtext COLLATE utf8_unicode_ci NOT NULL,
  `copyrightApplicableEndDate` longtext COLLATE utf8_unicode_ci NOT NULL,
  `copyrightApplicableEndDateOpen` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatement` (`fkRightsStatement`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementCopyright`
--

LOCK TABLES `RightsStatementCopyright` WRITE;
/*!40000 ALTER TABLE `RightsStatementCopyright` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementCopyright` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementCopyrightDocumentationIdentifier`
--

DROP TABLE IF EXISTS `RightsStatementCopyrightDocumentationIdentifier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementCopyrightDocumentationIdentifier` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatementCopyrightInformation` int(10) unsigned DEFAULT NULL,
  `copyrightDocumentationIdentifierType` longtext COLLATE utf8_unicode_ci NOT NULL,
  `copyrightDocumentationIdentifierValue` longtext COLLATE utf8_unicode_ci NOT NULL,
  `copyrightDocumentationIdentifierRole` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatementCopyrightInformation` (`fkRightsStatementCopyrightInformation`),
  CONSTRAINT `RightsStatementCopyrightDocumentationIdentifier_ibfk_1` FOREIGN KEY (`fkRightsStatementCopyrightInformation`) REFERENCES `RightsStatementCopyright` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementCopyrightDocumentationIdentifier`
--

LOCK TABLES `RightsStatementCopyrightDocumentationIdentifier` WRITE;
/*!40000 ALTER TABLE `RightsStatementCopyrightDocumentationIdentifier` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementCopyrightDocumentationIdentifier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementCopyrightNote`
--

DROP TABLE IF EXISTS `RightsStatementCopyrightNote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementCopyrightNote` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatementCopyrightInformation` int(10) unsigned DEFAULT NULL,
  `copyrightNote` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatementCopyrightInformation` (`fkRightsStatementCopyrightInformation`),
  CONSTRAINT `RightsStatementCopyrightNote_ibfk_1` FOREIGN KEY (`fkRightsStatementCopyrightInformation`) REFERENCES `RightsStatementCopyright` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementCopyrightNote`
--

LOCK TABLES `RightsStatementCopyrightNote` WRITE;
/*!40000 ALTER TABLE `RightsStatementCopyrightNote` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementCopyrightNote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementLicense`
--

DROP TABLE IF EXISTS `RightsStatementLicense`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementLicense` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatement` int(10) unsigned DEFAULT NULL,
  `licenseTerms` longtext COLLATE utf8_unicode_ci,
  `licenseApplicableStartDate` longtext COLLATE utf8_unicode_ci NOT NULL,
  `licenseApplicableEndDate` longtext COLLATE utf8_unicode_ci NOT NULL,
  `licenseApplicableEndDateOpen` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatement` (`fkRightsStatement`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementLicense`
--

LOCK TABLES `RightsStatementLicense` WRITE;
/*!40000 ALTER TABLE `RightsStatementLicense` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementLicense` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementLicenseDocumentationIdentifier`
--

DROP TABLE IF EXISTS `RightsStatementLicenseDocumentationIdentifier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementLicenseDocumentationIdentifier` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatementLicense` int(10) unsigned DEFAULT NULL,
  `licenseDocumentationIdentifierType` longtext COLLATE utf8_unicode_ci NOT NULL,
  `licenseDocumentationIdentifierValue` longtext COLLATE utf8_unicode_ci NOT NULL,
  `licenseDocumentationIdentifierRole` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatementLicense` (`fkRightsStatementLicense`),
  CONSTRAINT `RightsStatementLicenseDocumentationIdentifier_ibfk_1` FOREIGN KEY (`fkRightsStatementLicense`) REFERENCES `RightsStatementLicense` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementLicenseDocumentationIdentifier`
--

LOCK TABLES `RightsStatementLicenseDocumentationIdentifier` WRITE;
/*!40000 ALTER TABLE `RightsStatementLicenseDocumentationIdentifier` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementLicenseDocumentationIdentifier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementLicenseNote`
--

DROP TABLE IF EXISTS `RightsStatementLicenseNote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementLicenseNote` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatementLicense` int(10) unsigned DEFAULT NULL,
  `licenseNote` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatementLicense` (`fkRightsStatementLicense`),
  CONSTRAINT `RightsStatementLicenseNote_ibfk_1` FOREIGN KEY (`fkRightsStatementLicense`) REFERENCES `RightsStatementLicense` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementLicenseNote`
--

LOCK TABLES `RightsStatementLicenseNote` WRITE;
/*!40000 ALTER TABLE `RightsStatementLicenseNote` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementLicenseNote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementLinkingAgentIdentifier`
--

DROP TABLE IF EXISTS `RightsStatementLinkingAgentIdentifier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementLinkingAgentIdentifier` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatement` int(10) unsigned DEFAULT NULL,
  `linkingAgentIdentifierType` longtext COLLATE utf8_unicode_ci NOT NULL,
  `linkingAgentIdentifierValue` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatement` (`fkRightsStatement`),
  CONSTRAINT `RightsStatementLinkingAgentIdentifier_ibfk_1` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementLinkingAgentIdentifier`
--

LOCK TABLES `RightsStatementLinkingAgentIdentifier` WRITE;
/*!40000 ALTER TABLE `RightsStatementLinkingAgentIdentifier` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementLinkingAgentIdentifier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementOtherRightsDocumentationIdentifier`
--

DROP TABLE IF EXISTS `RightsStatementOtherRightsDocumentationIdentifier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementOtherRightsDocumentationIdentifier` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatementOtherRightsInformation` int(10) unsigned DEFAULT NULL,
  `otherRightsDocumentationIdentifierType` longtext COLLATE utf8_unicode_ci NOT NULL,
  `otherRightsDocumentationIdentifierValue` longtext COLLATE utf8_unicode_ci NOT NULL,
  `otherRightsDocumentationIdentifierRole` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatementOtherRightsInformation` (`fkRightsStatementOtherRightsInformation`),
  CONSTRAINT `RightsStatementOtherRightsDocumentationIdentifier_ibfk_1` FOREIGN KEY (`fkRightsStatementOtherRightsInformation`) REFERENCES `RightsStatementOtherRightsInformation` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementOtherRightsDocumentationIdentifier`
--

LOCK TABLES `RightsStatementOtherRightsDocumentationIdentifier` WRITE;
/*!40000 ALTER TABLE `RightsStatementOtherRightsDocumentationIdentifier` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementOtherRightsDocumentationIdentifier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementOtherRightsInformation`
--

DROP TABLE IF EXISTS `RightsStatementOtherRightsInformation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementOtherRightsInformation` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatement` int(10) unsigned DEFAULT NULL,
  `otherRightsBasis` longtext COLLATE utf8_unicode_ci NOT NULL,
  `otherRightsApplicableStartDate` longtext COLLATE utf8_unicode_ci NOT NULL,
  `otherRightsApplicableEndDate` longtext COLLATE utf8_unicode_ci NOT NULL,
  `otherRightsApplicableEndDateOpen` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatement` (`fkRightsStatement`),
  CONSTRAINT `RightsStatementOtherRightsInformation_ibfk_1` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementOtherRightsInformation`
--

LOCK TABLES `RightsStatementOtherRightsInformation` WRITE;
/*!40000 ALTER TABLE `RightsStatementOtherRightsInformation` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementOtherRightsInformation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementOtherRightsNote`
--

DROP TABLE IF EXISTS `RightsStatementOtherRightsNote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementOtherRightsNote` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatementOtherRightsInformation` int(10) unsigned DEFAULT NULL,
  `otherRightsNote` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatementOtherRightsInformation` (`fkRightsStatementOtherRightsInformation`),
  CONSTRAINT `RightsStatementOtherRightsNote_ibfk_1` FOREIGN KEY (`fkRightsStatementOtherRightsInformation`) REFERENCES `RightsStatementOtherRightsInformation` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementOtherRightsNote`
--

LOCK TABLES `RightsStatementOtherRightsNote` WRITE;
/*!40000 ALTER TABLE `RightsStatementOtherRightsNote` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementOtherRightsNote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementRightsGranted`
--

DROP TABLE IF EXISTS `RightsStatementRightsGranted`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementRightsGranted` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatement` int(10) unsigned DEFAULT NULL,
  `act` longtext COLLATE utf8_unicode_ci NOT NULL,
  `startDate` longtext COLLATE utf8_unicode_ci NOT NULL,
  `endDate` longtext COLLATE utf8_unicode_ci,
  `endDateOpen` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatement` (`fkRightsStatement`),
  CONSTRAINT `RightsStatementRightsGranted_ibfk_1` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementRightsGranted`
--

LOCK TABLES `RightsStatementRightsGranted` WRITE;
/*!40000 ALTER TABLE `RightsStatementRightsGranted` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementRightsGranted` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementRightsGrantedNote`
--

DROP TABLE IF EXISTS `RightsStatementRightsGrantedNote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementRightsGrantedNote` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatementRightsGranted` int(10) unsigned DEFAULT NULL,
  `rightsGrantedNote` longtext COLLATE utf8_unicode_ci,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatementRightsGranted` (`fkRightsStatementRightsGranted`),
  CONSTRAINT `RightsStatementRightsGrantedNote_ibfk_1` FOREIGN KEY (`fkRightsStatementRightsGranted`) REFERENCES `RightsStatementRightsGranted` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementRightsGrantedNote`
--

LOCK TABLES `RightsStatementRightsGrantedNote` WRITE;
/*!40000 ALTER TABLE `RightsStatementRightsGrantedNote` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementRightsGrantedNote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementRightsGrantedRestriction`
--

DROP TABLE IF EXISTS `RightsStatementRightsGrantedRestriction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementRightsGrantedRestriction` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatementRightsGranted` int(10) unsigned DEFAULT NULL,
  `restriction` longtext COLLATE utf8_unicode_ci,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatementRightsGranted` (`fkRightsStatementRightsGranted`),
  CONSTRAINT `RightsStatementRightsGrantedRestriction_ibfk_1` FOREIGN KEY (`fkRightsStatementRightsGranted`) REFERENCES `RightsStatementRightsGranted` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementRightsGrantedRestriction`
--

LOCK TABLES `RightsStatementRightsGrantedRestriction` WRITE;
/*!40000 ALTER TABLE `RightsStatementRightsGrantedRestriction` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementRightsGrantedRestriction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementStatuteDocumentationIdentifier`
--

DROP TABLE IF EXISTS `RightsStatementStatuteDocumentationIdentifier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementStatuteDocumentationIdentifier` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatementStatuteInformation` int(10) unsigned DEFAULT NULL,
  `statuteDocumentationIdentifierType` longtext COLLATE utf8_unicode_ci NOT NULL,
  `statuteDocumentationIdentifierValue` longtext COLLATE utf8_unicode_ci NOT NULL,
  `statuteDocumentationIdentifierRole` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatementStatuteInformation` (`fkRightsStatementStatuteInformation`),
  CONSTRAINT `RightsStatementStatuteDocumentationIdentifier_ibfk_1` FOREIGN KEY (`fkRightsStatementStatuteInformation`) REFERENCES `RightsStatementStatuteInformation` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementStatuteDocumentationIdentifier`
--

LOCK TABLES `RightsStatementStatuteDocumentationIdentifier` WRITE;
/*!40000 ALTER TABLE `RightsStatementStatuteDocumentationIdentifier` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementStatuteDocumentationIdentifier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementStatuteInformation`
--

DROP TABLE IF EXISTS `RightsStatementStatuteInformation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementStatuteInformation` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatement` int(10) unsigned DEFAULT NULL,
  `statuteJurisdiction` longtext COLLATE utf8_unicode_ci NOT NULL,
  `statuteCitation` longtext COLLATE utf8_unicode_ci NOT NULL,
  `statuteInformationDeterminationDate` longtext COLLATE utf8_unicode_ci,
  `statuteApplicableStartDate` longtext COLLATE utf8_unicode_ci NOT NULL,
  `statuteApplicableEndDate` longtext COLLATE utf8_unicode_ci NOT NULL,
  `statuteApplicableEndDateOpen` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatement` (`fkRightsStatement`),
  CONSTRAINT `RightsStatementStatuteInformation_ibfk_1` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementStatuteInformation`
--

LOCK TABLES `RightsStatementStatuteInformation` WRITE;
/*!40000 ALTER TABLE `RightsStatementStatuteInformation` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementStatuteInformation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RightsStatementStatuteInformationNote`
--

DROP TABLE IF EXISTS `RightsStatementStatuteInformationNote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementStatuteInformationNote` (
  `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fkRightsStatementStatuteInformation` int(10) unsigned DEFAULT NULL,
  `statuteNote` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `fkRightsStatementStatuteInformation` (`fkRightsStatementStatuteInformation`),
  CONSTRAINT `RightsStatementStatuteInformationNote_ibfk_1` FOREIGN KEY (`fkRightsStatementStatuteInformation`) REFERENCES `RightsStatementStatuteInformation` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RightsStatementStatuteInformationNote`
--

LOCK TABLES `RightsStatementStatuteInformationNote` WRITE;
/*!40000 ALTER TABLE `RightsStatementStatuteInformationNote` DISABLE KEYS */;
/*!40000 ALTER TABLE `RightsStatementStatuteInformationNote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SIPs`
--

DROP TABLE IF EXISTS `SIPs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SIPs` (
  `sipUUID` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `createdTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `currentPath` longtext COLLATE utf8_unicode_ci,
  `magicLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `magicLinkExitMessage` varchar(50) COLLATE utf8_unicode_ci DEFAULT 'Completed successfully',
  `hidden` tinyint(1) NOT NULL DEFAULT '0',
  `aipFilename` text COLLATE utf8_unicode_ci,
  PRIMARY KEY (`sipUUID`),
  KEY `magicLink` (`magicLink`),
  CONSTRAINT `SIPs_ibfk_1` FOREIGN KEY (`magicLink`) REFERENCES `MicroServiceChainLinks` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SIPs`
--

LOCK TABLES `SIPs` WRITE;
/*!40000 ALTER TABLE `SIPs` DISABLE KEYS */;
/*!40000 ALTER TABLE `SIPs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Sounds`
--

DROP TABLE IF EXISTS `Sounds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Sounds` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `description` longtext COLLATE utf8_unicode_ci,
  `fileLocation` longtext COLLATE utf8_unicode_ci,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `Sounds` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Sounds`
--

LOCK TABLES `Sounds` WRITE;
/*!40000 ALTER TABLE `Sounds` DISABLE KEYS */;
INSERT INTO `Sounds` VALUES ('1a23e63b-0d5c-4573-8eef-d51e502b75b4','Error','/usr/share/sounds/KDE-Im-Error-On-Connection.ogg',NULL,'2012-10-02 00:25:09'),('f3998ac8-c5ba-4ff9-9fa4-8fa4ddc25b1c','Alert','/usr/share/sounds/KDE-Im-Irc-Event.ogg',NULL,'2012-10-02 00:25:09'),('fa7625a4-572c-467c-b9ad-6ee3e4b58776','Requires approval','/usr/share/sounds/KDE-Sys-List-End.ogg',NULL,'2012-10-02 00:25:09');
/*!40000 ALTER TABLE `Sounds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `StandardTasksConfigs`
--

DROP TABLE IF EXISTS `StandardTasksConfigs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `StandardTasksConfigs` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `filterFileEnd` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `filterFileStart` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `filterSubDir` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `requiresOutputLock` tinyint(1) DEFAULT NULL,
  `standardOutputFile` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL,
  `standardErrorFile` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL,
  `execute` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL,
  `arguments` longtext COLLATE utf8_unicode_ci,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `StandardTasksConfigs` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `StandardTasksConfigs`
--

LOCK TABLES `StandardTasksConfigs` WRITE;
/*!40000 ALTER TABLE `StandardTasksConfigs` DISABLE KEYS */;
INSERT INTO `StandardTasksConfigs` VALUES ('02fd0952-4c9c-4da6-9ea3-a1409c87963d',NULL,NULL,'objects/attachments',0,'%SIPLogsDirectory%fileFormatIdentification.log','%SIPLogsDirectory%fileFormatIdentification.log','identifyFileFormat_v0.0','%IDCommand% %relativeLocation% %fileUUID%',NULL,'2013-11-07 22:51:43'),('037feb3c-f4d1-44dd-842e-c681793094df',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%processingDirectory%.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('045f84de-2669-4dbc-a31b-43a4954d0481',NULL,NULL,NULL,0,NULL,NULL,'bagit_v0.0','create \"%SIPDirectory%%SIPName%-%SIPUUID%\" \"%SIPLogsDirectory%\" \"%SIPObjectsDirectory%\" \"%SIPDirectory%METS.%SIPUUID%.xml\" \"%SIPDirectory%thumbnails/\" --writer filesystem --payloadmanifestalgorithm \"sha512\"',NULL,'2012-10-02 00:25:01'),('0aec05d4-7222-4c28-89f4-043d20a812cc',NULL,NULL,NULL,0,NULL,NULL,'createMETS_v2.0','--amdSec --baseDirectoryPath \"%SIPDirectory%\" --baseDirectoryPathString \"SIPDirectory\" --fileGroupIdentifier \"%SIPUUID%\" --fileGroupType \"sipUUID\" --xmlFile \"%SIPDirectory%METS.%SIPUUID%.xml\"',NULL,'2012-10-02 00:25:01'),('0b1177e8-8541-4293-a238-1783c793a7b1',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%processingDirectory%%SIPName%-%SIPUUID%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('0b17b446-11d4-45a8-9d0c-4297b8c8887c',NULL,NULL,NULL,0,NULL,NULL,'setFilePermission_v0.0','700 -R \"%relativeLocation%\"',NULL,'2012-10-02 00:25:01'),('0bdecdc8-f5ef-48dd-8a89-f937d2b3f2f9',NULL,NULL,'objects/manualNormalization/preservation',0,NULL,NULL,'updateSizeAndChecksum_v0.0','--filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\"',NULL,'2013-01-03 02:10:38'),('0c6990d8-ce1f-4093-803b-5ca6256119ca',NULL,NULL,NULL,0,NULL,'%SIPDirectory%SIPnameCleanup.log','sanitizeSIPName_v0.0','\"%relativeLocation%\" \"%SIPUUID%\" \"%date%\" \"%sharedPath%\" \"%unitType%\"',NULL,'2012-10-02 00:25:01'),('11e6fcbe-3d7b-41cc-bfac-14dee9172b51',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%rejectedDirectory%.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('13d2adfc-8cb8-4206-bf70-04f031436ca2',NULL,NULL,NULL,0,NULL,NULL,'getContentdmCollectionList_v0.0','\"%ContentdmServer%\"',NULL,'2012-10-02 00:25:01'),('14780202-4aab-43f4-94ed-3bf9a040d055',NULL,NULL,NULL,0,NULL,NULL,'elasticSearchIndex_v0.0','\"%SIPDirectory%\" \"%SIPUUID%\"',NULL,'2013-11-07 22:51:35'),('16ce41d9-7bfa-4167-bca8-49fe358f53ba',NULL,NULL,NULL,0,NULL,NULL,'backlogUpdatingTransferFileIndex_v0.0','\"%SIPUUID%\" \"%SIPName%\" \"%SIPDirectory%\"',NULL,'2013-04-05 23:08:30'),('179373e8-a6b4-4274-a245-ca3f4b105396',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/workFlowDecisions/selectFormatIDToolIngest/.\"  \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2013-11-07 22:51:42'),('179c8ce5-2b83-4ae2-9653-971e868fe183',NULL,NULL,NULL,0,NULL,NULL,'assignFileUUIDs_v0.0','--transferUUID \"%SIPUUID%\" --sipDirectory \"%SIPDirectory%\" --filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\"',NULL,'2012-10-02 00:25:01'),('1aaa6e10-7907-4dea-a92a-dd0931eff226',NULL,NULL,NULL,0,NULL,NULL,'checkForSubmissionDocumenation_v0.0','\"%SIPDirectory%metadata/submissionDocumentation\"',NULL,'2012-10-02 00:25:01'),('1e5e8ee2-8b93-4e8c-bb9c-0cb40d2728dd',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/system/autoRestructureForCompliance/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('1fb68647-9db0-49ef-b6b7-3f775646ffbe',NULL,NULL,NULL,0,NULL,NULL,'createDirectory_v0.0','-m 770 \"%SIPDirectory%DIP/\" \"%SIPDirectory%DIP/objects/\"',NULL,'2012-10-02 00:25:01'),('20915fc5-594f-46d8-aa23-bfa45b622d17',NULL,NULL,NULL,0,NULL,NULL,'copy_v0.0','\"%SIPDirectory%METS.%SIPUUID%.xml\" \"%SIPDirectory%DIP/METS.%SIPUUID%.xml\"',NULL,'2012-10-02 00:25:01'),('24272436-39b0-44f1-a0d6-c4bdca93ce88',NULL,NULL,'objects',0,NULL,NULL,'extractMaildirAttachments_v0.0','\"%SIPDirectory%\" \"%SIPUUID%\" \"%date%\"',NULL,'2012-10-02 00:25:01'),('26309e7d-6435-4700-9171-131005f29cbb',NULL,NULL,'objects/',0,NULL,NULL,'normalize_v1.0','thumbnail \"%fileUUID%\" \"%relativeLocation%\" \"%SIPDirectory%\" \"%SIPUUID%\" \"%taskUUID%\" \"service\"',NULL,'2013-11-15 00:31:31'),('27dfc012-7cf4-449c-b0f0-bdd252c6f6e9',NULL,NULL,'objects',0,NULL,NULL,'createEvent_v0.0','--eventType \"unquarantine\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --eventDateTime \"%jobCreatedDate%\"',NULL,'2012-10-02 00:25:01'),('2808a160-82df-40a8-a6ca-330151584968',NULL,NULL,NULL,0,NULL,NULL,'restructureBagAIPToSIP_v0.0','\"%SIPDirectory%\"',NULL,'2013-11-07 22:51:35'),('2843eba9-a9cf-462a-9cfc-f24ff35a22c0',NULL,NULL,'objects/manualNormalization/',0,NULL,NULL,'manualNormalizationIdentifyFilesIncluded_v0.0','\"%fileUUID%\"',NULL,'2013-02-19 00:52:52'),('290b358c-cfff-488c-a0b7-fffce037b2c5',NULL,NULL,NULL,0,NULL,NULL,'checkForServiceDirectory_v0.0','--SIPDirectory \"%SIPDirectory%\" --serviceDirectory \"objects/service/\" --objectsDirectory \"objects/\" --SIPUUID \"%SIPUUID%\" --date \"%date%\"',NULL,'2012-10-02 00:25:01'),('2936f695-190e-49e9-b7c6-6d1610f6b6de',NULL,NULL,'objects/attachments',0,NULL,NULL,'FITS_v0.0','\"%relativeLocation%\" \"%SIPLogsDirectory%fileMeta/%fileUUID%.xml\" \"%date%\" \"%taskUUID%\" \"%fileUUID%\" \"%fileGrpUse%\"',NULL,'2012-10-02 00:25:01'),('2ad612bc-1993-407e-9d66-a8ab9c1ebbd5',NULL,NULL,'objects',1,'%SIPLogsDirectory%FileUUIDs.log','%SIPLogsDirectory%FileUUIDsError.log','assignFileUUIDs_v0.0','--transferUUID \"%SIPUUID%\" --sipDirectory \"%SIPDirectory%\" --filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\"',NULL,'2012-10-02 00:25:01'),('2c9fd8e4-a4f9-4aa6-b443-de8a9a49e396',NULL,NULL,NULL,0,NULL,NULL,'elasticSearchIndex_v0.0','\"%SIPDirectory%\" \"%SIPUUID%\"',NULL,'2012-10-02 00:25:01'),('2e9fb50f-2275-4253-87e5-47d2faf1031e',NULL,NULL,NULL,0,NULL,NULL,'copyTransfersMetadataAndLogs_v0.0','--sipDirectory \"%SIPDirectory%\" --sipUUID \"%SIPUUID%\" --sharedPath \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('2f2a9b2b-bcdb-406b-a842-898d4bed02be',NULL,NULL,NULL,0,NULL,NULL,'move_v0.0','\"%SIPDirectory%metadata/submissionDocumentation\" \"%SIPDirectory%objects/submissionDocumentation\"',NULL,'2012-10-02 00:25:01'),('2f851d03-722f-4c49-8369-64f11542af89',NULL,NULL,NULL,0,NULL,NULL,'loadLabelsFromCSV_v0.0','\"%SIPUUID%\" \"%SIPDirectory%metadata/file_labels.csv\"',NULL,'2012-10-02 00:25:01'),('2fdb8408-8bbb-45d1-846b-5e28bf220d5c',NULL,NULL,'objects/submissionDocumentation',1,NULL,'%SIPLogsDirectory%clamAVScan.txt','archivematicaClamscan_v0.0','\"%fileUUID%\" \"%relativeLocation%\" \"%date%\" \"%taskUUID%\"',NULL,'2012-10-02 00:25:01'),('302be9f9-af3f-45da-9305-02706d81b742',NULL,NULL,NULL,0,NULL,NULL,'move_v0.0','\"%SIPDirectory%\" \"%watchDirectoryPath%uploadedDIPs/.\"',NULL,'2012-10-02 00:25:01'),('30ea6854-cf7a-42d4-b1e8-3c4ca0b82b7d',NULL,NULL,'objects',0,NULL,NULL,'createEvent_v0.0','--eventType \"quarantine\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --eventDateTime \"%jobCreatedDate%\"',NULL,'2012-10-02 00:25:01'),('329fd50d-42fd-44e3-940e-7dc45d1a7727',NULL,NULL,NULL,0,NULL,NULL,'setFilePermission_v0.0',' -R 750 \"%relativeLocation%\"',NULL,'2012-10-02 00:25:01'),('339f300d-62d1-4a46-97c2-57244f54d32e',NULL,NULL,'objects/service',0,NULL,NULL,'normalize_v1.0','access \"%fileUUID%\" \"%relativeLocation%\" \"%SIPDirectory%\" \"%SIPUUID%\" \"%taskUUID%\" \"service\"',NULL,'2013-11-15 00:31:31'),('33e7f3af-e414-484f-8468-1db09cb4258b',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/workFlowDecisions/selectFileIDTool/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2013-11-07 22:51:35'),('34966164-9800-4ae1-91eb-0a0c608d72d5',NULL,NULL,'objects/metadata',1,'%SIPLogsDirectory%FileUUIDs.log','%SIPLogsDirectory%FileUUIDsError.log','assignFileUUIDs_v0.0','--sipUUID \"%SIPUUID%\" --sipDirectory \"%SIPDirectory%\" --filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\" --use \"metadata\"',NULL,'2013-02-13 22:03:40'),('352fc88d-4228-4bc8-9c15-508683dabc58',NULL,NULL,NULL,0,NULL,NULL,'retryNormalizeRemoveNormalized_v0.0','--SIPDirectory \"%SIPDirectory%\" --SIPUUID \"%SIPUUID%\" --preservation --thumbnails',NULL,'2012-10-24 18:18:24'),('353f326a-c599-4e66-8e1c-6262316e3729',NULL,NULL,NULL,0,NULL,NULL,'archivematicaSetTransferType_v0.0','\"%SIPUUID%\" \"TRIM\"',NULL,'2012-11-30 19:55:48'),('3565ac77-780e-43d8-87c8-8a6bf04aab40',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/approveNormalization/preservationAndAccess/.\" \"%SIPUUID%\" \"%sharedPath%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('35ef1f2d-0124-422f-a84a-5e1d756b6bf2',NULL,NULL,NULL,0,NULL,NULL,'copy_v0.0','\"%sharedPath%sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml\" \"%SIPDirectory%processingMCP.xml\" -n',NULL,'2012-10-02 00:25:01'),('36ad6300-5a2c-491b-867b-c202541749e8',NULL,NULL,NULL,0,NULL,NULL,'archivematicaSetTransferType_v0.0','\"%SIPUUID%\" \"Standard\"',NULL,'2012-10-02 00:25:01'),('36cc5356-6db1-4f3e-8155-1f92f958d2a4',NULL,NULL,'objects/metadata',1,'%SIPLogsDirectory%extraction.log','%SIPLogsDirectory%extraction.log','transcoderExtractPackages_v0.0','\"%relativeLocation%\" \"%SIPObjectsDirectory%\" \"%SIPLogsDirectory%\" \"%date%\" \"%taskUUID%\" \"%fileUUID%\"',NULL,'2013-02-13 22:03:39'),('3843f87a-12c4-4526-904a-d900572c6483',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/SIPCreation/SIPsUnderConstruction/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('39f8d4bf-2078-4415-b600-ce2865585aca',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%watchDirectoryPath%quarantined/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('3b889d1d-bfe1-467f-8373-2c9366127093',NULL,NULL,NULL,0,NULL,NULL,'trimVerifyChecksums_v0.0','\"%SIPUUID%\" \"%SIPName%\" \"%SIPDirectory%\" \"%date%\"',NULL,'2012-12-06 14:56:58'),('3c256437-6435-4307-9757-fbac5c07541c',NULL,NULL,'objects/',0,NULL,NULL,'normalize_v1.0','access \"%fileUUID%\" \"%relativeLocation%\" \"%SIPDirectory%\" \"%SIPUUID%\" \"%taskUUID%\" \"original\"',NULL,'2013-11-15 00:31:31'),('3e8f5b9e-b3a6-4782-a944-749de6ae234d',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/workFlowDecisions/selectFormatIDToolTransfer/.\"  \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2013-11-07 22:51:42'),('40bf5b85-7cfd-47b0-9fbc-aed6c2cde8be',NULL,NULL,NULL,0,NULL,NULL,'elasticSearchAIPIndex_v0.0','\"%SIPDirectory%\" \"%SIPUUID%\" \"%SIPName%\"',NULL,'2012-10-02 00:25:01'),('42aed4a4-8e2b-49f3-ba03-1a45c8baf52c',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%rejectedDirectory%.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('4306315c-1f75-4eaf-8752-f08f67f9ada4',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/activeTransfers/standardTransfer/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('45df6fd4-9200-4ec7-bd31-ba0338c07806',NULL,NULL,'objects',0,NULL,NULL,'updateSizeAndChecksum_v0.0','--filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\"',NULL,'2012-10-02 00:25:01'),('45f11547-0df9-4856-b95a-3b1ff0c658bd',NULL,NULL,NULL,0,NULL,NULL,'createPointerFile_v0.0','%SIPUUID% %SIPName% %AIPCompressionAlgorithm% %SIPDirectory% %AIPFilename%',NULL,'2013-11-07 22:51:35'),('463e5d1c-d680-47fa-a27a-7efd4f702355',NULL,NULL,'objects',0,NULL,NULL,'createEvent_v0.0','--eventType \"removal from backlog\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --eventDateTime \"%jobCreatedDate%\"',NULL,'2013-04-19 22:39:27'),('464a0a66-571b-4e6d-ba3a-4d182551a20f',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%processingDirectory%.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('46883944-8561-44d0-ac50-e1c3fd9aeb59',NULL,NULL,'objects/',0,NULL,NULL,'archivematicaFido_v0.0','--fileUUID \"%fileUUID%\" --SIPUUID \"%SIPUUID%\" --filePath \"%relativeLocation%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\" --fileGrpUse \"%fileGrpUse%\"',NULL,'2013-11-07 22:51:35'),('49b803e3-8342-4098-bb3f-434e1eb5cfa8',NULL,NULL,'objects',1,'%SIPLogsDirectory%removeUnneededFiles.log','%SIPLogsDirectory%removeUnneededFiles.log','removeUnneededFiles_v0.0','\"%relativeLocation%\" \"%fileUUID%\" \"%SIPLogsDirectory%\" \"%date%\" \"%taskUUID%\"',NULL,'2012-10-02 00:25:01'),('4b816807-10a7-447a-b42f-f34c8b8b3b76',NULL,NULL,'objects/submissionDocumentation',0,NULL,NULL,'FITS_v0.0','\"%relativeLocation%\" \"%SIPLogsDirectory%fileMeta/%fileUUID%.xml\" \"%date%\" \"%taskUUID%\" \"%fileUUID%\" \"%fileGrpUse%\"',NULL,'2012-10-02 00:25:01'),('4c25f856-6639-42b5-9120-3ac166dce932',NULL,NULL,NULL,0,NULL,NULL,'assignFauxFileUUIDs_v0.0','\"%SIPUUID%\" \"%SIPDirectory%\" \"%date%\"',NULL,'2013-11-07 22:51:35'),('4cfac870-24ec-4a80-8bcb-7a38fd02e048',NULL,NULL,NULL,0,NULL,NULL,'createSIPsfromTRIMTransferContainers_v0.0','\"%SIPObjectsDirectory%\" \"%SIPName%\" \"%SIPUUID%\" \"%processingDirectory%\" \"%sharedPath%watchedDirectories/system/autoProcessSIP/\" \"%sharedPath%\"',NULL,'2012-12-04 21:29:48'),('4dc2b1d2-acbb-47e7-88ca-570281f3236f',NULL,NULL,NULL,0,NULL,NULL,'compressAIP_v0.0','%AIPCompressionAlgorithm% %AIPCompressionLevel% %SIPDirectory% %SIPName% %SIPUUID%',NULL,'2012-10-02 00:25:01'),('4f400b71-37be-49d0-8da3-125abac2bfd0',NULL,NULL,'objects/',0,NULL,NULL,'verifyPREMISChecksums_v0.0','--fileUUID \"%fileUUID%\" --filePath \"%relativeLocation%\" --date \"%date%\" --eventIdentifierUUID \"%taskUUID%\"',NULL,'2012-10-02 00:25:01'),('4f47371b-a69b-4a8a-87b5-01e7eb1628c3',NULL,NULL,'objects/manualNormalization/preservation',0,NULL,NULL,'assignFileUUIDs_v0.0','--sipUUID \"%SIPUUID%\" --sipDirectory \"%SIPDirectory%\" --filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\" --use \"preservation\"',NULL,'2013-01-03 02:10:38'),('4f7e2ed6-44b9-49a7-a1b7-bbfe58eadea8',NULL,NULL,NULL,0,NULL,NULL,'move_v0.0','\"%SIPDirectory%\" \"%rejectedDirectory%.\"',NULL,'2012-10-02 00:25:01'),('51eab45d-6a24-4080-a1be-1e5c9405ce25',NULL,NULL,'objects',0,NULL,NULL,'FITS_v0.0','\"%relativeLocation%\" \"%SIPLogsDirectory%fileMeta/%fileUUID%.xml\" \"%date%\" \"%taskUUID%\" \"%fileUUID%\" \"%fileGrpUse%\"',NULL,'2012-10-02 00:25:01'),('5341d647-dc75-4f00-8e02-cef59c9862e5',NULL,NULL,NULL,0,NULL,NULL,'createDirectory_v0.0','-m 770 \"%SIPDirectory%DIP/\" \"%SIPDirectory%DIP/objects/\"',NULL,'2012-10-02 00:25:01'),('5401961e-773d-41fe-8d62-8c1262f6156b',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%failed/.\" \"%SIPUUID%\" \"%sharedPath%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('55eec242-68fa-4a1b-a3cd-458c087a017b',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/workFlowDecisions/selectNormalizationPath/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2013-11-07 22:51:35'),('57d42245-79e2-4c2d-8ed3-b596cce416db',NULL,NULL,'objects',1,'%SIPLogsDirectory%FileUUIDs.log','%SIPLogsDirectory%FileUUIDsError.log','assignFileUUIDs_v0.0','--transferUUID \"%SIPUUID%\" --sipDirectory \"%SIPDirectory%\" --filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\"',NULL,'2012-10-02 00:25:01'),('58b192eb-0507-4a83-ae5a-f5e260634c2a',NULL,NULL,'objects/metadata',0,'%SIPLogsDirectory%filenameCleanup.log','%SIPLogsDirectory%filenameCleanup.log','sanitizeObjectNames_v0.0','\"%SIPDirectory%objects/metadata/\" \"%SIPUUID%\" \"%date%\" \"%taskUUID%\" \"SIPDirectory\" \"sipUUID\" \"%SIPDirectory%\"',NULL,'2013-02-13 22:03:39'),('5f5ca409-8009-4732-a47c-1a35c72abefc',NULL,NULL,'DIP/objects',0,NULL,NULL,'renameDIPFauxToOrigUUIDs_v0.0','\"%SIPUUID%\" \"%relativeLocation%\"',NULL,'2013-11-07 22:51:35'),('614b1d56-9078-4cb0-80cc-1ea87b9fbbe8',NULL,NULL,'objects/submissionDocumentation',1,'%SIPLogsDirectory%FileUUIDs.log','%SIPLogsDirectory%FileUUIDsError.log','assignFileUUIDs_v0.0','--sipUUID \"%SIPUUID%\" --sipDirectory \"%SIPDirectory%\" --filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\" --use \"submissionDocumentation\"',NULL,'2012-10-02 00:25:01'),('6157fe87-26ff-49da-9899-d9036b21c4b0',NULL,NULL,NULL,0,NULL,NULL,'setDirectoryPermissionsForAppraisal_v0.0','\"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('62f21582-3925-47f6-b17e-90f46323b0d1',NULL,NULL,'objects/service',0,NULL,NULL,'normalize_v1.0','thumbnail \"%fileUUID%\" \"%relativeLocation%\" \"%SIPDirectory%\" \"%SIPUUID%\" \"%taskUUID%\" \"service\"',NULL,'2013-11-15 00:31:31'),('65321292-b17c-4671-bfa6-da43a9d5c367',NULL,NULL,NULL,0,NULL,NULL,'move_v0.0','\"%SIPDirectory%\" \"%watchDirectoryPath%uploadedDIPs/.\"',NULL,'2012-10-02 00:25:01'),('6733ebdd-5c5f-4168-81a5-fe9a2fbc10c9',NULL,NULL,'objects',0,NULL,NULL,'createEvent_v0.0','--eventType \"placement in backlog\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --eventDateTime \"%jobCreatedDate%\"',NULL,'2013-04-19 22:39:27'),('68b1456e-9a59-48d8-96ef-92bc20fd7cab',NULL,NULL,'objects/manualNormalization/access',0,NULL,NULL,'manualNormalizationMoveAccessFilesToDIP_v0.0','--sipUUID \"%SIPUUID%\" --sipDirectory \"%SIPDirectory%\" --filePath \"%relativeLocation%\"',NULL,'2013-01-03 23:01:21'),('6abefa8d-387d-4f23-9978-bea7e6657a57',NULL,NULL,NULL,0,NULL,NULL,'copy_v0.0','-R \"%SIPDirectory%thumbnails\" \"%SIPDirectory%DIP/.\"',NULL,'2012-10-02 00:25:01'),('6c261f8f-17ce-4b58-86c2-ac3bfb0d2850',NULL,NULL,NULL,0,NULL,NULL,'archivematicaSetTransferType_v0.0','\"%SIPUUID%\" \"Dspace\"',NULL,'2012-10-02 00:25:01'),('6c50d546-b0a4-4900-90ac-b4bcca802368',NULL,NULL,NULL,0,NULL,NULL,'removeHiddenFilesAndDirectories_v0.0','\"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('6dccf7b3-4282-46f9-a805-1297c6ea482b',NULL,NULL,'objects/',0,NULL,NULL,'normalize_v1.0','access \"%fileUUID%\" \"%relativeLocation%\" \"%SIPDirectory%\" \"%SIPUUID%\" \"%taskUUID%\" \"service\"',NULL,'2013-11-15 00:31:31'),('7316e6ed-1c1a-4bf6-a570-aead6b544e41',NULL,NULL,'objects/metadata',1,NULL,'%SIPLogsDirectory%clamAVScan.txt','archivematicaClamscan_v0.0','\"%fileUUID%\" \"%relativeLocation%\" \"%date%\" \"%taskUUID%\"',NULL,'2013-02-13 22:03:39'),('73b71a30-1a26-4a07-8aa8-4dfb6e66a321',NULL,NULL,NULL,0,NULL,NULL,'createMETS_v0.0','--sipUUID \"%SIPUUID%\" --basePath \"%SIPDirectory%\" --xmlFile \"%SIPDirectory%\"metadata/submissionDocumentation/METS.xml --basePathString \"transferDirectory\" --fileGroupIdentifier \"transferUUID\"',NULL,'2012-10-02 00:25:01'),('744000f8-8688-4080-9225-5547cd3f77cc',NULL,NULL,NULL,0,NULL,NULL,'createSIPfromTransferObjects_v0.0','\"%SIPObjectsDirectory%\" \"%SIPName%\" \"%SIPUUID%\" \"%processingDirectory%\" \"%sharedPath%watchedDirectories/system/autoProcessSIP/\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('7478e34b-da4b-479b-ad2e-5a3d4473364f',NULL,NULL,'objects/',0,NULL,NULL,'normalize_v1.0','preservation \"%fileUUID%\" \"%relativeLocation%\" \"%SIPDirectory%\" \"%SIPUUID%\" \"%taskUUID%\" \"original\"',NULL,'2013-11-15 00:31:31'),('748eef17-84d3-4b84-9439-6756f0fc697d',NULL,NULL,NULL,0,NULL,NULL,'trimVerifyManifest_v0.0','\"%SIPUUID%\" \"%SIPName%\" \"%SIPDirectory%\" \"%date%\"',NULL,'2012-12-06 14:56:58'),('761f00af-3d9a-4cb4-b7f1-259fccedb802',NULL,NULL,NULL,0,NULL,NULL,'createMETS_v0.0','--sipUUID \"%SIPUUID%\" --basePath \"%SIPDirectory%\" --xmlFile \"%SIPDirectory%\"metadata/submissionDocumentation/METS.xml --basePathString \"transferDirectory\" --fileGroupIdentifier \"transferUUID\"',NULL,'2012-10-02 00:25:01'),('77ea8809-bc90-4e9d-a144-ad6d5ec59de9',NULL,NULL,NULL,0,NULL,NULL,'checkTransferDirectoryForObjects_v0.0','\"%SIPObjectsDirectory%\"',NULL,'2012-10-02 00:25:01'),('79f3c95a-c1f1-463b-ab23-972ad859e136',NULL,NULL,'objects/manualNormalization/preservation',0,NULL,NULL,'FITS_v0.0','\"%relativeLocation%\" \"%SIPLogsDirectory%fileMeta/%fileUUID%.xml\" \"%date%\" \"%taskUUID%\" \"%fileUUID%\" \"%fileGrpUse%\"',NULL,'2013-01-03 02:10:38'),('7b455fc5-b201-4233-ba1c-e05be059b279',NULL,NULL,NULL,0,NULL,NULL,'archivematicaSetTransferType_v0.0','\"%SIPUUID%\" \"Maildir\"',NULL,'2012-10-02 00:25:01'),('7df9e91b-282f-457f-b91a-ad6135f4337d',NULL,NULL,NULL,0,NULL,NULL,'storeAIP_v0.0','\"%AIPsStore%\" \"%SIPDirectory%%AIPFilename%\" \"%SIPUUID%\" \"%SIPName%\"',NULL,'2012-10-02 00:25:01'),('7e47b56f-f9bc-4a10-9f63-1b165354d5f4',NULL,NULL,NULL,0,NULL,NULL,'verifyMD5_v0.0','\"%relativeLocation%\"  \"%checksumsNoExtention%\" \"%date%\" \"%taskUUID%\" \"%SIPUUID%\"',NULL,'2012-10-02 00:25:01'),('805d7c5d-5ca9-4e66-9223-767eef79e0bd',NULL,NULL,NULL,0,NULL,NULL,'remove_v0.0','-R \"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('80759ad1-c79a-4c3b-b255-735c28a50f9e',NULL,NULL,'objects',0,'%SIPLogsDirectory%filenameCleanup.log','%SIPLogsDirectory%filenameCleanup.log','sanitizeObjectNames_v0.0','\"%SIPObjectsDirectory%\" \"%SIPUUID%\" \"%date%\" \"%taskUUID%\" \"transferDirectory\" \"transferUUID\" \"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('807603e2-9914-46e0-9be4-73d4c073d2e8',NULL,NULL,NULL,NULL,NULL,NULL,'emailFailReport_v0.0','--unitType \"%unitType%\" --unitIdentifier \"%SIPUUID%\" --unitName \"%SIPName%\" --date \"%date%\" --server \"localhost\"',NULL,'2013-01-08 02:11:59'),('80c4a6ed-abe4-4e02-8de8-55a50f559dab',NULL,NULL,NULL,0,NULL,NULL,'verifySIPCompliance_v0.0','\"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('81f36881-9e54-4c75-a5b2-838cfb2ca228',NULL,NULL,NULL,0,NULL,NULL,'indexAIP_v0.0','\"%SIPUUID%\" \"%SIPName%\" \"%SIPDirectory%%AIPFilename%\"',NULL,'2013-11-07 22:51:35'),('8516867e-b223-41af-8069-d42b08d32e99',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%completed/transfers/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2013-11-07 22:51:43'),('85419d3b-a0bf-402c-aa69-f5770a79904b',NULL,NULL,'objects/submissionDocumentation',1,'%SIPLogsDirectory%extraction.log','%SIPLogsDirectory%extraction.log','transcoderExtractPackages_v0.0','\"%relativeLocation%\" \"%SIPObjectsDirectory%\" \"%SIPLogsDirectory%\" \"%date%\" \"%taskUUID%\" \"%fileUUID%\"',NULL,'2012-10-02 00:25:01'),('857fb861-8aa1-45c0-95f5-c5af66764142',NULL,NULL,NULL,0,NULL,NULL,'getAipStorageLocations_v0.0','',NULL,'2013-11-07 22:51:35'),('862c0ce2-82e3-4336-bd20-d8bcb2d0fa6c',NULL,NULL,NULL,0,NULL,NULL,'restructureForCompliance_v0.0','\"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('867f326b-66d1-498d-87e9-b6bcacf45abd',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/storeAIP/.\" \"%SIPUUID%\" \"%sharedPath%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('87fb2e00-03b9-4890-a4d4-0e28f27e32c2',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/approveNormalization/preservation/.\" \"%SIPUUID%\" \"%sharedPath%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('8971383b-5c38-4818-975f-e539bd993eb8',NULL,NULL,NULL,0,NULL,NULL,'manualNormalizationRemoveMNDirectories_v0.0','\"%SIPDirectory%\"',NULL,'2013-01-11 00:50:39'),('89b4d447-1cfc-4bbf-beaa-fb6477b00f70',NULL,NULL,'objects/attachments',0,'%SIPLogsDirectory%filenameCleanup.log','%SIPLogsDirectory%filenameCleanup.log','sanitizeObjectNames_v0.0','\"%SIPObjectsDirectory%attachments/\" \"%SIPUUID%\" \"%date%\" \"%taskUUID%\" \"transferDirectory\" \"transferUUID\" \"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('8c50f6ab-7fa4-449e-bea8-483999568d85',NULL,NULL,NULL,0,NULL,NULL,'checkForAccessDirectory_v0.0','--SIPDirectory \"%SIPDirectory%\" --accessDirectory \"objects/access/\" --objectsDirectory \"objects/\" --DIPDirectory \"DIP\" --SIPUUID \"%SIPUUID%\" --date \"%date%\"',NULL,'2012-10-02 00:25:01'),('8fad772e-7d2e-4cdd-89e6-7976152b6696',NULL,NULL,NULL,0,NULL,NULL,'extractContents_v0.0','\"%SIPUUID%\" \"%transferDirectory%\" \"%date%\" \"%taskUUID%\"',NULL,'2013-11-07 22:51:43'),('8fe4a2c3-d43c-41e4-aeb9-18e8f57c9ccf',NULL,NULL,'objects/',0,NULL,NULL,'normalize_v1.0','thumbnail \"%fileUUID%\" \"%relativeLocation%\" \"%SIPDirectory%\" \"%SIPUUID%\" \"%taskUUID%\" \"original\"',NULL,'2013-11-15 00:31:31'),('94d0c52f-7594-4f59-9de5-b827d8d2a7f3',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%watchDirectoryPath%quarantined/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('9c3680a5-91cb-413f-af4e-d39c3346f8db',NULL,NULL,'objects',0,'%SIPLogsDirectory%fileFormatIdentification.log','%SIPLogsDirectory%fileFormatIdentification.log','identifyFileFormat_v0.0','%IDCommand% %relativeLocation% %fileUUID%',NULL,'2013-11-07 22:51:42'),('9c94b1d7-0563-4be9-9d64-058d0d1a03f4',NULL,NULL,NULL,0,NULL,NULL,'createDirectory_v0.0','-m 770 \"%SIPDirectory%thumbnails/\"',NULL,'2012-10-02 00:25:01'),('9e1b0378-5d4e-4f7f-9934-23f6c7475906',NULL,NULL,NULL,0,NULL,'%SIPDirectory%SIPnameCleanup.log','sanitizeSIPName_v0.0','\"%relativeLocation%\" \"%SIPUUID%\" \"%date%\" \"%sharedPath%\" \"%unitType%\"',NULL,'2012-10-02 00:25:01'),('9e302b2b-e28d-4a61-9be7-b94e16929560',NULL,NULL,NULL,0,NULL,NULL,'copy_v0.0','\"%SIPDirectory%\" \"%sharedPath%transferBackups/.\" -R --preserve',NULL,'2012-10-02 00:25:01'),('9e32257f-161e-430e-9412-07ce7f8db8ab',NULL,NULL,'objects/',0,NULL,NULL,'archivematicaTika_v0.0','--fileUUID \"%fileUUID%\" --SIPUUID \"%SIPUUID%\" --filePath \"%relativeLocation%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\" --fileGrpUse \"%fileGrpUse%\"',NULL,'2013-11-07 22:51:35'),('9e6d6445-ccc6-427a-9407-a126699f98b4',NULL,NULL,NULL,1,NULL,NULL,'extractBagTransfer_v0.0','\"%SIPDirectory%\" \"%SIPUUID%\" \"%processingDirectory%\"  %sharedPath%',NULL,'2012-10-02 00:25:01'),('9ea66f4e-150b-4911-b68d-29fd5d372d2c','mets.xml',NULL,'objects',0,NULL,NULL,'identifyDspaceFiles_v0.0','\"%relativeLocation%\" \"%SIPDirectory%\" \"%SIPUUID%\"',NULL,'2012-10-02 00:25:01'),('9f25a366-f7a4-4b59-b219-2d5f259a1be9',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%www/AIPsStore/transferBacklog/originals/.\" \"%SIPUUID%\" \"%sharedPath%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2013-04-05 23:08:30'),('9f473616-9094-45b0-aa3c-41d81a204d3b',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%processingDirectory%%SIPName%-%SIPUUID%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('a32fc538-efd1-4be0-95a9-5ee40cbc70fd',NULL,NULL,'objects/',0,'%SIPLogsDirectory%removedFilesWithNoPremisMetadata.log','%SIPLogsDirectory%removedFilesWithNoPremisMetadata.log','removeFilesWithoutPresmisMetadata_v0.0','--fileUUID \"%fileUUID%\" --inputFile \"%relativeLocation%\" --sipDirectory \"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('a51af5c7-0ed4-41c2-9142-fc9e43e83960',NULL,NULL,NULL,0,NULL,NULL,'generateDIPFromAIPGenerateDIP_v0.0','\"%SIPUUID%\" \"%SIPDirectory%\" \"%date%\"',NULL,'2013-11-07 22:51:35'),('a540bd68-27fa-47c3-9fc3-bd297999478d',NULL,NULL,NULL,0,NULL,NULL,'createDirectory_v0.0','-m 770 \"%SIPDirectory%DIP/\" \"%SIPDirectory%DIP/objects/\"',NULL,'2012-10-02 00:25:01'),('a56a116c-167b-45c5-b634-253696270a12',NULL,NULL,NULL,0,NULL,NULL,'copy_v0.0','\"%sharedPath%sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml\" \"%SIPDirectory%processingMCP.xml\" -n',NULL,'2012-10-02 00:25:01'),('a5bb8df6-a8f0-4279-ac6d-873ec5cf37cd','mets.xml',NULL,'objects',1,'%SIPLogsDirectory%verifyChecksumsInFileSecOfDSpaceMETSFiles.log','%SIPLogsDirectory%verifyChecksumsInFileSecOfDSpaceMETSFiles.log','verifyChecksumsInFileSecOfDspaceMETSFiles_v0.0','\"%relativeLocation%\" \"%date%\" \"%taskUUID%\"',NULL,'2012-10-02 00:25:01'),('a650921e-b754-4e61-9713-1457cf52e77d',NULL,NULL,NULL,0,NULL,NULL,'upload-archivistsToolkit_v0.0','--host=%host% --port=%port% --dbname=%dbname% --dbuser=%dbuser% --dbpass=%dbpass% --atuser=%atuser% --dip_location=%SIPDirectory% --dip_name=%SIPName% --dip_uuid=%SIPUUID% --restrictions=%restrictions% --object_type=%object_type% --ead_actuate=%ead_actuate% --ead_show=%ead_show% --use_statement=%use_statement% --uri_prefix=%uri_prefix% --access_conditions=%access_conditions% --use_conditions=%use_conditions%',NULL,'2013-03-23 04:42:00'),('ac562701-7672-4e1d-a318-b986b7c9007c',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/SIPCreation/completedTransfers/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('ad65bf76-3491-4c3d-afb0-acc94ff28bee',NULL,NULL,'objects/submissionDocumentation',0,'%SIPLogsDirectory%filenameCleanup.log','%SIPLogsDirectory%filenameCleanup.log','sanitizeObjectNames_v0.0','\"%SIPDirectory%objects/submissionDocumentation/\" \"%SIPUUID%\" \"%date%\" \"%taskUUID%\" \"SIPDirectory\" \"sipUUID\" \"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('adde688c-eb79-4036-a3b8-49aacc6a1b36',NULL,NULL,'objects/manualNormalization/preservation',0,NULL,NULL,'manualNormalizationCreateMetadataAndRestructure_v0.0','\"%SIPUUID%\" \"%SIPName%\" \"%SIPDirectory%\" \"%fileUUID%\" \"%relativeLocation%\" \"%date%\"',NULL,'2013-01-04 23:20:01'),('ae090b70-0234-40ea-bc11-4be27370515f',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%watchDirectoryPath%workFlowDecisions/compressionAIPDecisions/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2013-11-07 22:51:34'),('ae6b87d8-59c8-4ffa-b417-ce93ab472e74',NULL,NULL,NULL,0,NULL,NULL,'verifyAIP_v0.0','\"%SIPUUID%\" \"%SIPDirectory%%AIPFilename%\"',NULL,'2013-11-07 22:51:35'),('b0aa4fd2-a837-4cb8-964d-7f905326aa85',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/activeTransfers/Dspace/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('b3c14f6c-bc91-4349-9e8f-c02f7dac27b3',NULL,NULL,NULL,0,NULL,NULL,'copyTransferSubmissionDocumentation_v0.0','\"%SIPUUID%\" \"%SIPDirectory%metadata/submissionDocumentation\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('b3fed349-54c4-4142-8d86-925b3a9f4365',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%processingDirectory%%SIPName%-%SIPUUID%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('ba937c55-6148-4f45-a9ad-9697c0cf11ed',NULL,NULL,NULL,0,NULL,NULL,'setFilePermission_v0.0','775 \"%SIPDirectory%%AIPFilename%\"',NULL,'2012-10-02 00:25:01'),('bc7d263a-3798-4e5e-8098-8e273fd5890b',NULL,NULL,NULL,0,NULL,NULL,'createMETS_v0.0','--sipUUID \"%SIPUUID%\" --basePath \"%SIPDirectory%\" --xmlFile \"%SIPDirectory%\"metadata/submissionDocumentation/METS.xml --basePathString \"transferDirectory\" --fileGroupIdentifier \"transferUUID\"',NULL,'2012-10-02 00:25:01'),('bfaf4e65-ab7b-11e2-bace-08002742f837',NULL,NULL,NULL,0,NULL,NULL,'removeAIPFilesFromIndex_v0.0','%SIPUUID%',NULL,'2013-04-22 18:37:55'),('c06ecc19-8f75-4ccf-a549-22fde3972f28',NULL,NULL,NULL,0,NULL,NULL,'updateSizeAndChecksum_v0.0','--filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\"',NULL,'2012-10-02 00:25:01'),('c0ae5130-0c17-4fc1-91c7-aa36265a21d5',NULL,NULL,NULL,0,NULL,NULL,'isMaildirAIP_v0.0','\"%SIPDirectory%\"',NULL,'2013-11-07 22:51:35'),('c15de53e-a5b2-41a1-9eee-1a7b4dd5447a',NULL,NULL,NULL,0,NULL,NULL,'retryNormalizeRemoveNormalized_v0.0','--SIPDirectory \"%SIPDirectory%\" --SIPUUID \"%SIPUUID%\" --preservation --thumbnails --access',NULL,'2012-10-24 18:18:52'),('c3625e5b-2c8d-47d9-9f66-c37111d39a07',NULL,NULL,NULL,0,NULL,NULL,'restructureForCompliance_v0.0','\"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('c64b1064-c856-4758-9891-152c7eabde7f',NULL,NULL,NULL,0,NULL,NULL,'verifyMD5_v0.0','\"%relativeLocation%\"  \"%checksumsNoExtention%\" \"%date%\" \"%taskUUID%\" \"%SIPUUID%\"',NULL,'2012-10-02 00:25:01'),('c79f55f7-637c-4d32-a6fa-1d193e87c5fc',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%failed/.\" \"%SIPUUID%\" \"%sharedPath%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('c7e6b467-445e-4142-a837-5b50184238fc',NULL,NULL,'objects/',0,NULL,NULL,'archivematicaMediaInfo_v0.0','--fileUUID \"%fileUUID%\" --SIPUUID \"%SIPUUID%\" --filePath \"%relativeLocation%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\" --fileGrpUse \"%fileGrpUse%\"',NULL,'2013-11-07 22:51:34'),('c8f93c3d-b078-428d-bd53-1b5789cde598',NULL,NULL,'objects/submissionDocumentation',0,NULL,NULL,'updateSizeAndChecksum_v0.0','--filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\"',NULL,'2012-10-02 00:25:01'),('ccbaa53f-a486-4564-9b1a-a1b7bd5b1239',NULL,NULL,NULL,0,NULL,NULL,'trimCreateRightsEntries_v0.0','\"%SIPUUID%\" \"%SIPName%\" \"%SIPDirectory%\" \"%date%\"',NULL,'2012-12-12 21:30:55'),('ce13677c-8ad4-4af0-92c8-ae8763f5094d',NULL,NULL,NULL,1,NULL,NULL,'move_v0.0','\"%SIPDirectory%metadata\" \"%SIPDirectory%objects/metadata\"',NULL,'2013-02-13 22:03:40'),('cf23dd75-d273-4c4e-8394-17622adf9bd6',NULL,NULL,NULL,0,NULL,NULL,'verifyTransferCompliance_v0.0','\"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('d079b090-bc81-4fc6-a9c5-a267ad5f69a9',NULL,NULL,NULL,0,NULL,NULL,'createDirectory_v0.0','-m 770 \"%SIPDirectory%thumbnails/\"',NULL,'2012-10-02 00:25:01'),('d12b6b59-1f1c-47c2-b1a3-2bf898740eae',NULL,NULL,NULL,0,NULL,NULL,'remove_v0.0','-R \"%SIPDirectory%%SIPName%-%SIPUUID%\" \"%SIPDirectory%METS.%SIPUUID%.xml\" \"%SIPLogsDirectory%\" \"%SIPObjectsDirectory%\" \"%SIPDirectory%thumbnails/\"',NULL,'2012-10-02 00:25:01'),('db753cdd-c556-4f4b-aa09-e55eb637244d',NULL,NULL,NULL,0,NULL,NULL,'restructureForComplianceMaildir_v0.0','\"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('dca1bdba-5086-4423-be6b-8c660f8537ac',NULL,NULL,'objects',0,'%SIPLogsDirectory%extraction.log','%SIPLogsDirectory%extraction.log','transcoderExtractPackages_v0.0','\"%relativeLocation%\" \"%SIPDirectory%\" \"%SIPUUID%\" \"%date%\" \"%taskUUID%\" \"%fileUUID%\"',NULL,'2012-10-02 00:25:01'),('de58249f-9594-439d-8bea-536ce59d70a3',NULL,NULL,NULL,0,NULL,'%SIPLogsDirectory%clamAVScan.txt','archivematicaClamscan_v0.0','\"%fileUUID%\" \"%relativeLocation%\" \"%date%\" \"%taskUUID%\"',NULL,'2012-10-02 00:25:01'),('df526440-c08e-49f9-9b9e-c9aa3adedc72',NULL,NULL,NULL,0,NULL,NULL,'moveSIP_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/workFlowDecisions/createDip/.\" \"%SIPUUID%\" \"%sharedPath%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('df65573b-70b7-4cd4-b825-d5d5d8dd016d',NULL,NULL,NULL,0,NULL,NULL,'verifyMD5_v0.0','\"%relativeLocation%\"  \"%checksumsNoExtention%\" \"%date%\" \"%taskUUID%\" \"%SIPUUID%\"',NULL,'2012-10-02 00:25:01'),('e377b543-d9b8-47a9-8297-4f95ca7600b3',NULL,NULL,'objects/metadata',0,NULL,NULL,'updateSizeAndChecksum_v0.0','--filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\"',NULL,'2013-02-13 22:03:40'),('e3c09c46-6d05-4369-8c12-b5af6657c8f7',NULL,NULL,NULL,0,NULL,NULL,'trimRestructureForCompliance_v0.0','\"%SIPUUID%\" \"%SIPName%\" \"%SIPDirectory%\"',NULL,'2012-11-30 19:55:46'),('e469dc77-5712-4ef1-b053-06f3cd3c34be',NULL,NULL,NULL,0,NULL,NULL,'upload-contentDM_v0.0','--uuid=\"%SIPName%-%SIPUUID%\" --collection \"%ContentdmCollection%\" --server \"%ContentdmServer%\" --username \"%ContentdmUser%\" --group \"%ContentdmGroup%\" --outputDir \"%watchDirectoryPath%uploadedDIPs\"',NULL,'2012-10-02 00:25:01'),('e7d2a9ac-b5c5-4b5c-9e57-a3c4e98035e6',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/workFlowDecisions/quarantineTransfer/.\" \"%SIPUUID%\" \"%sharedPath%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-11-20 23:05:52'),('e884b0db-8e51-4ea6-87f9-0420ee9ddf8f',NULL,NULL,NULL,1,NULL,NULL,'verifyAndRestructureTransferBag_v0.0','\"%SIPDirectory%\" \"%SIPUUID%\"',NULL,'2012-10-02 00:25:01'),('e887c51e-afb9-48b1-b416-502a2357e621',NULL,NULL,NULL,0,NULL,NULL,'copy_v0.0','\"%sharedPath%sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml\" \"%SIPDirectory%processingMCP.xml\" -n',NULL,'2012-10-02 00:25:01'),('e8fb137c-d499-45a8-a4aa-a884d81b9f3d',NULL,NULL,NULL,0,NULL,NULL,'%ContentdmCollection%',NULL,NULL,'2012-10-02 00:25:01'),('e8fc5fd0-fd55-4eb6-9170-92615fc9c344',NULL,NULL,'objects/manualNormalization/preservation',0,NULL,NULL,'manualNormalizationCheckForManualNormalizationDirectory_v0.0','\"%SIPUUID%\" \"%SIPName%\" \"%SIPDirectory%\"',NULL,'2013-01-03 02:10:39'),('ebab9878-f42e-4451-a24a-ec709889a858',NULL,NULL,NULL,0,NULL,NULL,'%AIPsStore%',NULL,NULL,'2013-11-07 22:51:35'),('ec54a7cb-690f-4dd6-ad2b-979ae9f8d25a',NULL,NULL,'objects',0,NULL,NULL,'updateSizeAndChecksum_v0.0','--filePath \"%relativeLocation%\" --fileUUID \"%fileUUID%\" --eventIdentifierUUID \"%taskUUID%\" --date \"%date%\"',NULL,'2012-10-02 00:25:01'),('ec688528-d492-4de3-a176-b777734153b1',NULL,NULL,NULL,0,NULL,NULL,'setMaildirFileGrpUseAndFileIDs_v0.0','\"%SIPUUID%\" \"%SIPDirectory%\"',NULL,'2013-11-07 22:51:35'),('ed8c70b7-1456-461c-981b-6b9c84896263',NULL,NULL,NULL,0,NULL,NULL,'move_v0.0','\"%SIPDirectory%DIP\" \"%sharedPath%watchedDirectories/uploadDIP/%SIPDirectoryBasename%\"',NULL,'2012-10-02 00:25:01'),('ee80b69b-6128-4e31-9db4-ef90aa677c87',NULL,NULL,NULL,0,NULL,NULL,'upload-qubit_v0.0','--url=\"http://localhost/ica-atom/index.php\" \\\r\n--email=\"demo@example.com\" \\\r\n--password=\"demo\" \\\r\n--uuid=\"%SIPUUID%\" \\\r\n--rsync-target=\"/tmp\"',NULL,'2012-10-02 00:25:01'),('f368a36d-2b27-4f08-b662-2828a96d189a',NULL,NULL,NULL,0,NULL,NULL,'sanitizeObjectNames_v0.0','\"%SIPObjectsDirectory%\" \"%SIPUUID%\" \"%date%\" \"%taskUUID%\" \"transferDirectory\" \"transferUUID\" \"%SIPDirectory%\"',NULL,'2013-11-07 22:51:43'),('f46bbd28-d533-4933-9b5c-4a5d32927ff3',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/workFlowDecisions/quarantineTransfer/.\" \"%SIPUUID%\" \"%sharedPath%\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-11-20 23:05:52'),('f593ea48-4c4a-47ee-9187-a9cbdd3165bc',NULL,NULL,NULL,0,NULL,NULL,'moveTransfer_v0.0','\"%SIPDirectory%\" \"%sharedPath%watchedDirectories/SIPCreation/completedTransfers/.\" \"%SIPUUID%\" \"%sharedPath%\"',NULL,'2012-10-02 00:25:01'),('f798426b-fbe9-4fd3-9180-8df776384b14','mets.xml',NULL,'objects',0,NULL,NULL,'identifyDspaceMETSFiles_v0.0','\"%fileUUID%\"',NULL,'2012-10-02 00:25:01'),('f8af7e00-0ae4-47ab-9d22-92395ff053fc',NULL,NULL,NULL,0,NULL,'%SIPDirectory%SIPnameCleanup.log','sanitizeSIPName_v0.0','\"%relativeLocation%\" \"%SIPUUID%\" \"%date%\" \"%sharedPath%\" \"%unitType%\"',NULL,'2012-10-02 00:25:01'),('f9f7793c-5a70-4ffd-9727-159c1070e4f5',NULL,NULL,NULL,0,NULL,NULL,'restructureDIPForContentDMUpload_v0.0','--uuid=\"%SIPName%-%SIPUUID%\" --dipDir \"%SIPDirectory%\" --collection \"%ContentdmCollection%\" --server \"%ContentdmServer%\" --ingestFormat \"%ContentdmIngestFormat%\" --outputDir \"%watchDirectoryPath%uploadedDIPs\"',NULL,'2012-10-02 00:25:01'),('fa903131-1d84-4d2b-b498-67a48bc44fc8',NULL,NULL,NULL,0,NULL,NULL,'archivematicaVerifyMets_v0.0','\"%SIPDirectory%\"',NULL,'2012-10-02 00:25:01'),('feec6329-c21a-48b6-b142-cd3c810e846f',NULL,NULL,NULL,0,NULL,NULL,'determineAIPVersionKeyExitCode_v0.0','\"%SIPUUID%\" \"%SIPDirectory%\"',NULL,'2013-11-07 22:51:35');
/*!40000 ALTER TABLE `StandardTasksConfigs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SubGroups`
--

DROP TABLE IF EXISTS `SubGroups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SubGroups` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `parentGroupID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `childGroupID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `enabled` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`pk`),
  KEY `childGroupID` (`childGroupID`),
  KEY `parentGroupID` (`parentGroupID`),
  CONSTRAINT `SubGroups_ibfk_1` FOREIGN KEY (`childGroupID`) REFERENCES `Groups` (`pk`),
  CONSTRAINT `SubGroups_ibfk_2` FOREIGN KEY (`parentGroupID`) REFERENCES `Groups` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SubGroups`
--

LOCK TABLES `SubGroups` WRITE;
/*!40000 ALTER TABLE `SubGroups` DISABLE KEYS */;
/*!40000 ALTER TABLE `SubGroups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TaskTypes`
--

DROP TABLE IF EXISTS `TaskTypes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TaskTypes` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `description` longtext COLLATE utf8_unicode_ci,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `TaskTypes` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TaskTypes`
--

LOCK TABLES `TaskTypes` WRITE;
/*!40000 ALTER TABLE `TaskTypes` DISABLE KEYS */;
INSERT INTO `TaskTypes` VALUES ('01b748fe-2e9d-44e4-ae5d-113f74c9a0ba','Get user choice from microservice generated list',NULL,'2012-10-02 00:25:10'),('3590f73d-5eb0-44a0-91a6-5b2db6655889','assign magic link',NULL,'2012-10-02 00:25:10'),('36b2e239-4a57-4aa5-8ebc-7a29139baca6','one instance',NULL,'2012-10-02 00:25:10'),('61fb3874-8ef6-49d3-8a2d-3cb66e86a30c','get user choice to proceed with',NULL,'2012-10-02 00:25:10'),('6f0b612c-867f-4dfd-8e43-5b35b7f882d7','linkTaskManagerSetUnitVariable',NULL,'2012-10-22 17:05:07'),('6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9','goto magic link',NULL,'2012-10-02 00:25:10'),('9c84b047-9a6d-463f-9836-eafa49743b84','get replacement dic from user choice',NULL,'2012-10-02 00:25:10'),('a19bfd9f-9989-4648-9351-013a10b382ed','Get microservice generated list in stdOut',NULL,'2012-10-02 00:25:10'),('a6b1c323-7d36-428e-846a-e7e819423577','for each file',NULL,'2012-10-02 00:25:10'),('c42184a3-1a7f-4c4d-b380-15d8d97fdd11','linkTaskManagerUnitVariableLinkPull',NULL,'2012-10-22 17:03:13');
/*!40000 ALTER TABLE `TaskTypes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Tasks`
--

DROP TABLE IF EXISTS `Tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tasks` (
  `taskUUID` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `jobUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `createdTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fileUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `fileName` longtext COLLATE utf8_unicode_ci,
  `exec` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL,
  `arguments` varchar(1000) COLLATE utf8_unicode_ci DEFAULT NULL,
  `startTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `client` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `endTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `stdOut` longtext COLLATE utf8_unicode_ci,
  `stdError` longtext COLLATE utf8_unicode_ci,
  `exitCode` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`taskUUID`),
  KEY `jobUUID` (`jobUUID`),
  CONSTRAINT `Tasks_ibfk_1` FOREIGN KEY (`jobUUID`) REFERENCES `Jobs` (`jobUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Tasks`
--

LOCK TABLES `Tasks` WRITE;
/*!40000 ALTER TABLE `Tasks` DISABLE KEYS */;
/*!40000 ALTER TABLE `Tasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TasksConfigs`
--

DROP TABLE IF EXISTS `TasksConfigs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TasksConfigs` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `taskType` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `taskTypePKReference` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` longtext COLLATE utf8_unicode_ci,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `TasksConfigs` (`pk`),
  KEY `taskType` (`taskType`),
  CONSTRAINT `TasksConfigs_ibfk_1` FOREIGN KEY (`taskType`) REFERENCES `TaskTypes` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TasksConfigs`
--

LOCK TABLES `TasksConfigs` WRITE;
/*!40000 ALTER TABLE `TasksConfigs` DISABLE KEYS */;
INSERT INTO `TasksConfigs` VALUES ('008e5b38-b19c-48af-896f-349aaf5eba9f','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','be6dda53-ef28-42dd-8452-e11734d57a91','Set SIP to normalize with MediaInfo file identification.',NULL,'2012-10-23 19:41:24'),('032347f1-c0fb-4c6c-96ba-886ac8ac636c','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ec688528-d492-4de3-a176-b777734153b1','Set file group use and fileIDs for maildir AIP',NULL,'2013-11-07 22:51:35'),('04806cbd-d146-46e9-b3b6-1bd664636057','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','202e00f4-595e-41fb-9a96-b8ec8c76318e','Set SIP to normalize with file extension file identification.',NULL,'2012-10-23 19:41:23'),('04c7e0fb-ec4e-4637-a7b7-41601d5523bd','36b2e239-4a57-4aa5-8ebc-7a29139baca6','0c6990d8-ce1f-4093-803b-5ca6256119ca','Sanitize SIP name',NULL,'2012-10-02 00:25:11'),('06334a2c-82ed-477b-af0b-9c9f3dcade99','9c84b047-9a6d-463f-9836-eafa49743b84',NULL,'Select upload type (Project Client or direct upload)',NULL,'2012-10-02 00:25:11'),('06b45b5d-d06b-49a8-8f15-e9458fbae842','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','ed98984f-69c5-45de-8a32-2c9ecf65e83f','Set specialized processing link',NULL,'2013-11-07 22:51:43'),('0732af8f-d60b-43e0-8f75-8e89039a05a8','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','9329d1d8-03f9-4c5e-81ec-7010552d0a3e','Set SIP to normalize with FITS-file utility file identification.',NULL,'2012-10-23 19:41:23'),('07bf7432-fd9b-456e-9d17-5b387087723a','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Approve TRIM transfer',NULL,'2012-11-30 19:55:48'),('07f6f419-d51f-4c69-bca6-a395adecbee0','6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9',NULL,'Find type to process as',NULL,'2012-10-02 00:25:11'),('09f73737-f7ca-4ea2-9676-d369f390e650','36b2e239-4a57-4aa5-8ebc-7a29139baca6','8fad772e-7d2e-4cdd-89e6-7976152b6696','Extract contents from compressed archives',NULL,'2013-11-07 22:51:43'),('09fae382-37ac-45bb-9b53-d1608a44742c','36b2e239-4a57-4aa5-8ebc-7a29139baca6','c0ae5130-0c17-4fc1-91c7-aa36265a21d5','Is maildir AIP',NULL,'2013-11-07 22:51:35'),('0a521e24-b376-4a9c-9cd6-ce41e187179a','a6b1c323-7d36-428e-846a-e7e819423577','adde688c-eb79-4036-a3b8-49aacc6a1b36','Relate manual normalized preservation files to the original files',NULL,'2013-01-03 02:10:38'),('0ae50158-a6e2-4663-a684-61d9a8384789','36b2e239-4a57-4aa5-8ebc-7a29139baca6','4306315c-1f75-4eaf-8752-f08f67f9ada4','Move transfer back to activeTransfers directory.',NULL,'2012-10-02 00:25:11'),('0b90715c-50bc-4cb7-a390-771a7cc8180f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','e3c09c46-6d05-4369-8c12-b5af6657c8f7','Restructure TRIM for compliance',NULL,'2012-11-30 19:55:47'),('0bb3f551-1418-4b99-8094-05a43fcd9537','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','65263ec0-f3ff-4fd5-9cd3-cf6f51ef92c7','Set files to identify',NULL,'2013-11-07 22:51:43'),('0c1664f2-dfcb-46d9-bd9e-5b604baef788','a6b1c323-7d36-428e-846a-e7e819423577','a5bb8df6-a8f0-4279-ac6d-873ec5cf37cd','Verify checksums in fileSec of DSpace METS files',NULL,'2012-10-02 00:25:11'),('0cbfd02e-94bc-4f0d-8e56-f7af6379c3ca','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','6b4600f2-6df6-42cb-b611-32938b46a9cf','Set resume link after processing metadata directory',NULL,'2013-02-13 22:03:40'),('0d7f2532-0402-449e-ab86-eb0cb84f3fe9','a6b1c323-7d36-428e-846a-e7e819423577','a32fc538-efd1-4be0-95a9-5ee40cbc70fd','Remove files without linking information (failed normalization artifacts etc.)',NULL,'2012-10-02 00:25:11'),('108f7f4c-72f2-4ddb-910a-24f173d64fa7','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Attempt restructure for compliance?',NULL,'2012-10-02 00:25:11'),('134a1a94-22f0-4e67-be17-23a4c7178105','36b2e239-4a57-4aa5-8ebc-7a29139baca6','81f36881-9e54-4c75-a5b2-838cfb2ca228','Index AIP',NULL,'2013-11-07 22:51:35'),('135dd73d-845a-412b-b17e-23941a3d9f78','36b2e239-4a57-4aa5-8ebc-7a29139baca6','2808a160-82df-40a8-a6ca-330151584968','Restructure from bag AIP to SIP directory format',NULL,'2013-11-07 22:51:35'),('13aaa76e-41db-4bff-8519-1f9ba8ca794f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','0b1177e8-8541-4293-a238-1783c793a7b1','Rename with transfer UUID',NULL,'2012-10-02 00:25:11'),('1423da1c-e9f8-479c-9949-4238c59899ac','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Workflow decision - create transfer backup',NULL,'2012-10-02 00:25:11'),('143b4734-9c33-4f6e-9af0-2dc09cf9017a','36b2e239-4a57-4aa5-8ebc-7a29139baca6','8c50f6ab-7fa4-449e-bea8-483999568d85','Check for Access directory',NULL,'2012-10-02 00:25:11'),('167be10a-135f-4d59-8647-79c0a2f55ec0','6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9',NULL,'Find type to process as',NULL,'2012-10-02 00:25:11'),('16b8cc42-68b6-4751-b497-3e3a64101bbb','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Upload DIP',NULL,'2012-10-02 00:25:11'),('16eaacad-e180-4be1-a13c-35ab070808a7','36b2e239-4a57-4aa5-8ebc-7a29139baca6','f8af7e00-0ae4-47ab-9d22-92395ff053fc','Sanitize Transfer name',NULL,'2012-10-02 00:25:11'),('18030155-ee1d-47d1-85d0-8744e6657491','a6b1c323-7d36-428e-846a-e7e819423577','85419d3b-a0bf-402c-aa69-f5770a79904b','Extract packages in submission documentation',NULL,'2012-10-02 00:25:11'),('18dceb0a-dfb1-4b18-81a7-c6c5c578c5f1','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ae090b70-0234-40ea-bc11-4be27370515f','Move to compressionAIPDecisions directory',NULL,'2013-11-07 22:51:34'),('1a6bdb05-f66b-4708-935e-75b819637dd2','a6b1c323-7d36-428e-846a-e7e819423577','a32fc538-efd1-4be0-95a9-5ee40cbc70fd','Remove files without linking information (failed normalization artifacts etc.)',NULL,'2012-10-02 00:25:11'),('1b8b596f-b6ee-440f-b59c-5e8b39a2b46d','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Approve standard transfer',NULL,'2012-10-02 00:25:11'),('1c7de28f-8f18-41c7-b03a-19f900d38f34','a6b1c323-7d36-428e-846a-e7e819423577','ec54a7cb-690f-4dd6-ad2b-979ae9f8d25a','Assign checksums and file sizes to objects',NULL,'2012-10-02 00:25:11'),('1cd60a70-f78e-4625-9381-3863ff819f33','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Select format identification tool',NULL,'2013-11-07 22:51:35'),('1df8d388-fdc9-4c37-a639-bd8b6f4a87c7','36b2e239-4a57-4aa5-8ebc-7a29139baca6','8516867e-b223-41af-8069-d42b08d32e99','Move to completed transfers directory',NULL,'2013-11-07 22:51:43'),('1e02e82a-2055-4f37-af3a-7dc606f9fd97','a6b1c323-7d36-428e-846a-e7e819423577','a32fc538-efd1-4be0-95a9-5ee40cbc70fd','Remove files without linking information (failed normalization artifacts etc.)',NULL,'2012-10-02 00:25:11'),('1e516ea6-6814-4292-9ea9-552ebfaa0d23','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','f130c16d-d419-4063-8c8b-2e4c3ad138bb','Set SIP to normalize with FIDO file identification.',NULL,'2012-10-23 19:41:23'),('2002fd7c-e238-4cca-a393-3c1c63a04915','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Approve normalization',NULL,'2012-10-02 07:25:11'),('21f8f2b6-d285-490a-9276-bfa87a0a4fb9','a6b1c323-7d36-428e-846a-e7e819423577','26309e7d-6435-4700-9171-131005f29cbb','Normalize for thumbnails',NULL,'2013-11-15 00:31:31'),('235c3727-b138-4e62-9265-c8f07761a5fa','3590f73d-5eb0-44a0-91a6-5b2db6655889','ae38e88c-3a61-4029-a7b4-af8f06b4265f','Grant normalization options for no pre-existing DIP',NULL,'2012-10-02 00:25:11'),('23650e92-092d-4ace-adcc-c627c41b127e','36b2e239-4a57-4aa5-8ebc-7a29139baca6','0aec05d4-7222-4c28-89f4-043d20a812cc','Generate METS.xml document',NULL,'2012-10-02 00:25:11'),('23ad16a5-49fe-409d-98d9-f5a8de333f81','36b2e239-4a57-4aa5-8ebc-7a29139baca6','73b71a30-1a26-4a07-8aa8-4dfb6e66a321','Generate METS.xml document',NULL,'2012-10-02 00:25:11'),('243b67e9-4d0b-4c38-8fa4-0fa3df8a5b86','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Approve zipped bagit transfer',NULL,'2012-10-02 00:25:11'),('246c34b0-b785-485f-971b-0ed9f82e1ae3','a6b1c323-7d36-428e-846a-e7e819423577','339f300d-62d1-4a46-97c2-57244f54d32e','Normalize service files for access',NULL,'2013-11-15 00:31:31'),('24deba11-c719-4c64-a53c-e08c85663c40','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','95fb93a5-ef63-4ceb-8572-c0ddf88ef3ea','Set resume link - postApproveNormalizationLink',NULL,'2013-11-07 22:51:35'),('24f82c1a-5de7-4b2a-8ac2-68a48edf252f','01b748fe-2e9d-44e4-ae5d-113f74c9a0ba','e8fb137c-d499-45a8-a4aa-a884d81b9f3d','Select destination collection',NULL,'2012-10-02 00:25:11'),('24fb04f6-95c1-4244-8f3d-65061418b188','a6b1c323-7d36-428e-846a-e7e819423577','a32fc538-efd1-4be0-95a9-5ee40cbc70fd','Remove files without linking information (failed normalization artifacts etc.)',NULL,'2012-10-02 00:25:11'),('256e18ca-1bcd-4b14-b3d5-4efbad5663fc','36b2e239-4a57-4aa5-8ebc-7a29139baca6','353f326a-c599-4e66-8e1c-6262316e3729','Set transfer type: TRIM',NULL,'2012-11-30 19:55:48'),('26ec68d5-8d33-4fe2-bc11-f06d80fb23e0','c42184a3-1a7f-4c4d-b380-15d8d97fdd11','003b52a6-f80a-409c-95f9-82dd770aa132','Resume after normalization file identification tool selected.',NULL,'2012-10-23 19:41:22'),('2865c5e7-55c4-44d4-ab6f-144f209ad48f','a6b1c323-7d36-428e-846a-e7e819423577','614b1d56-9078-4cb0-80cc-1ea87b9fbbe8','Assign file UUIDs to submission documentation',NULL,'2012-10-02 00:25:11'),('29937fd7-b482-4180-8037-1b57d71e903c','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','ba7bafe6-7241-4ffe-a0b8-97ca3c68eac1','Set resume link - returnFromManualNormalized',NULL,'2013-11-07 22:51:35'),('2ba3c9f4-2c1b-44b9-a9bf-90f460a28dd0','a6b1c323-7d36-428e-846a-e7e819423577','dca1bdba-5086-4423-be6b-8c660f8537ac','Extract packages',NULL,'2012-10-02 00:25:11'),('2bfd7cef-dcf8-4587-8043-2c69c612a6e3','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Normalize',NULL,'2012-10-02 00:25:11'),('2d0b36bb-5c82-4ee5-b54c-f3e146ce370b','36b2e239-4a57-4aa5-8ebc-7a29139baca6','87fb2e00-03b9-4890-a4d4-0e28f27e32c2','Move to approve normalization directory',NULL,'2012-10-02 00:25:11'),('2d9483ef-7dbb-4e7e-a9c6-76ed4de52da9','a6b1c323-7d36-428e-846a-e7e819423577','3c256437-6435-4307-9757-fbac5c07541c','Normalize for access',NULL,'2013-11-15 00:31:31'),('2e3c3f0f-069e-4ca1-b71b-93f4880a39b5','36b2e239-4a57-4aa5-8ebc-7a29139baca6','0b17b446-11d4-45a8-9d0c-4297b8c8887c','Set quarantine permissions on transfer',NULL,'2012-10-02 00:25:11'),('2f6947ee-5d92-416a-bade-b1079767e641','9c84b047-9a6d-463f-9836-eafa49743b84',NULL,'Select compression level',NULL,'2012-10-02 00:25:11'),('2ffa6679-ede5-47a0-a427-8faf0649a078','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9e1b0378-5d4e-4f7f-9934-23f6c7475906','Sanitize Transfer name',NULL,'2012-10-02 00:25:11'),('30e72f4d-0999-44a1-a7ef-c8d07b179d54','36b2e239-4a57-4aa5-8ebc-7a29139baca6','1aaa6e10-7907-4dea-a92a-dd0931eff226','Check for submission documentation',NULL,'2012-10-02 00:25:11'),('31707047-5d61-4b9f-ba58-1353d6c38e0c','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','fc9f30bf-7f6e-4e62-9f99-689c8dc2e4ec','Set resume link after handling any manual normalized files',NULL,'2013-01-03 02:10:40'),('32b2600c-6907-4cb2-b18a-3986f0842219','36b2e239-4a57-4aa5-8ebc-7a29139baca6','807603e2-9914-46e0-9be4-73d4c073d2e8','Email fail report',NULL,'2013-01-08 02:11:59'),('33c0dea0-da6c-4b8f-8038-6e95844eea95','36b2e239-4a57-4aa5-8ebc-7a29139baca6','8971383b-5c38-4818-975f-e539bd993eb8','Remove empty manual normalization directories',NULL,'2013-01-11 00:50:39'),('3649f0f4-2174-44af-aef9-31ebeddeb73b','c42184a3-1a7f-4c4d-b380-15d8d97fdd11','49d853a9-646d-4e9f-b825-d1bcc3ba77f0','Check for specialized processing',NULL,'2013-11-07 22:51:43'),('38324d67-8358-4679-902d-c20dcdfd548b','6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9',NULL,'Find options to normalize as',NULL,'2012-10-02 00:25:11'),('3875546f-9137-4c8f-9fcc-ed112eaa6414','3590f73d-5eb0-44a0-91a6-5b2db6655889','c691548f-0131-4bd5-864c-364b1f7feb7f','Designate to process as a standard transfer',NULL,'2012-10-02 00:25:11'),('38cea9c4-d75c-48f9-ba88-8052e9d3aa61','36b2e239-4a57-4aa5-8ebc-7a29139baca6','3e8f5b9e-b3a6-4782-a944-749de6ae234d','Move to select file ID tool',NULL,'2013-11-07 22:51:42'),('39ac9ff8-d312-4033-a2c6-44219471abda','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ac562701-7672-4e1d-a318-b986b7c9007c','Move to SIP creation directory for completed transfers',NULL,'2012-10-02 00:25:11'),('3ad0db9a-f57d-4664-ad34-947404dddd04','36b2e239-4a57-4aa5-8ebc-7a29139baca6','94d0c52f-7594-4f59-9de5-b827d8d2a7f3','Move to quarantine',NULL,'2012-10-02 00:25:11'),('3ae4931e-886e-4e0a-9a85-9b047c9983ac','36b2e239-4a57-4aa5-8ebc-7a29139baca6','862c0ce2-82e3-4336-bd20-d8bcb2d0fa6c','Attempt restructure for compliance',NULL,'2012-10-02 00:25:11'),('3c002fb6-a511-461e-ad16-0d2c46649374','a6b1c323-7d36-428e-846a-e7e819423577','de58249f-9594-439d-8bea-536ce59d70a3','Scan for viruses',NULL,'2012-10-02 00:25:11'),('3c04068f-20b8-4cbc-8166-c61faacb6628','36b2e239-4a57-4aa5-8ebc-7a29139baca6','329fd50d-42fd-44e3-940e-7dc45d1a7727','Set unquarantined file permissions on Transfer',NULL,'2012-10-02 00:25:11'),('3dbdc8cc-510c-4aa4-ab29-6645b84864ba','36b2e239-4a57-4aa5-8ebc-7a29139baca6','2f2a9b2b-bcdb-406b-a842-898d4bed02be','Move submission documentation into objects directory',NULL,'2012-10-02 00:25:11'),('3df5643c-2556-412f-a7ac-e2df95722dae','36b2e239-4a57-4aa5-8ebc-7a29139baca6','761f00af-3d9a-4cb4-b7f1-259fccedb802','Generate METS.xml document',NULL,'2012-10-02 00:25:11'),('3e70f50d-5056-413e-a3d1-7b4b13d2b821','36b2e239-4a57-4aa5-8ebc-7a29139baca6','e7d2a9ac-b5c5-4b5c-9e57-a3c4e98035e6','Move to workFlowDecisions-quarantineSIP directory',NULL,'2012-10-02 00:25:11'),('3ecab4fe-1d29-4b21-9b08-fdc715055799','a6b1c323-7d36-428e-846a-e7e819423577','de58249f-9594-439d-8bea-536ce59d70a3','Scan for viruses',NULL,'2012-10-02 00:25:11'),('3f3ab7ae-766e-4405-a05a-5ee9aea5042f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','c0ae5130-0c17-4fc1-91c7-aa36265a21d5','Check if SIP is from Maildir Transfer',NULL,'2013-11-07 22:51:43'),('3f8ccc75-8109-4171-b5c4-062189745a37','a6b1c323-7d36-428e-846a-e7e819423577','4b816807-10a7-447a-b42f-f34c8b8b3b76','Characterize and extract metadata on submission documentation',NULL,'2012-10-02 00:25:11'),('41e84764-e3a0-4aac-94e9-adbe996b087f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9c94b1d7-0563-4be9-9d64-058d0d1a03f4','Create thumbnails directory',NULL,'2012-10-02 00:25:11'),('445d6579-ee40-47d0-af6c-e2f6799f450d','a6b1c323-7d36-428e-846a-e7e819423577','2936f695-190e-49e9-b7c6-6d1610f6b6de','Characterize and extract metadata for attachments',NULL,'2012-10-02 00:25:11'),('449530ec-cd94-4d8c-aae0-3b7cd2e2d5f9','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','771dd17a-02d1-403b-a761-c70cc9cc1d1a','Set resume link after processing metadata directory',NULL,'2013-02-13 22:03:40'),('450794b5-db3e-4557-8ab8-1abd77786429','a6b1c323-7d36-428e-846a-e7e819423577','57d42245-79e2-4c2d-8ed3-b596cce416db','Assign file UUIDs to objects',NULL,'2012-10-02 00:25:11'),('4554c5f9-52f9-440c-bc69-0f7be3651949','a6b1c323-7d36-428e-846a-e7e819423577','463e5d1c-d680-47fa-a27a-7efd4f702355','Create removal from backlog PREMIS events',NULL,'2013-04-19 22:39:27'),('4745d0bb-910c-4c0d-8b81-82d7bfca7819','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','76eaa4d2-fd4f-4741-b68c-df5b96ba81d1','Set remove preservation and access normalized files to renormalize link.',NULL,'2012-10-24 00:40:06'),('4773c7e4-df8b-4928-acdd-1e9a3235b4b1','36b2e239-4a57-4aa5-8ebc-7a29139baca6','3565ac77-780e-43d8-87c8-8a6bf04aab40','Move to approve normalization directory',NULL,'2012-10-02 00:25:11'),('483d0fc9-8f89-4699-b90b-7be250bab743','a6b1c323-7d36-428e-846a-e7e819423577','a32fc538-efd1-4be0-95a9-5ee40cbc70fd','Remove files without linking information (failed normalization artifacts etc.)',NULL,'2012-10-02 00:25:11'),('48929c19-c0c7-41b2-8bd0-552b22e2d86f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','36ad6300-5a2c-491b-867b-c202541749e8','Set transfer type: Standard',NULL,'2012-10-02 00:25:11'),('4ad0eecf-aa6e-4e3c-afe4-7e230cc671b2','c42184a3-1a7f-4c4d-b380-15d8d97fdd11','65af383e-2153-4117-a2f9-bbe83358e54b','Load finished with manual normalized link',NULL,'2013-01-03 02:10:38'),('4b07d97a-04c1-45ce-9d9b-36bc29054223','36b2e239-4a57-4aa5-8ebc-7a29139baca6','0b1177e8-8541-4293-a238-1783c793a7b1','Rename with transfer UUID',NULL,'2012-10-02 00:25:11'),('4b7e128d-193d-4b7a-8c46-b37842bac047','36b2e239-4a57-4aa5-8ebc-7a29139baca6','bc7d263a-3798-4e5e-8098-8e273fd5890b','Generate METS.xml document',NULL,'2012-10-02 00:25:11'),('4d2ed238-1b35-43fb-9753-fcac0ede8da4','a6b1c323-7d36-428e-846a-e7e819423577','5f5ca409-8009-4732-a47c-1a35c72abefc','Rename DIP files with original UUIDs',NULL,'2013-11-07 22:51:35'),('4d56a90c-8d9f-498c-8331-cf469fcb3147','9c84b047-9a6d-463f-9836-eafa49743b84','','Choose Config for Archivists Toolkit DIP Upload',NULL,'2013-03-26 03:25:01'),('502a8bc4-88b1-41b0-8821-f8afd984036e','36b2e239-4a57-4aa5-8ebc-7a29139baca6','867f326b-66d1-498d-87e9-b6bcacf45abd','Move to the store AIP approval directory',NULL,'2012-10-02 00:25:11'),('5044f7ec-96f9-4bf1-8540-671e543c2411','36b2e239-4a57-4aa5-8ebc-7a29139baca6','fa903131-1d84-4d2b-b498-67a48bc44fc8','Verify mets_structmap.xml compliance',NULL,'2012-10-02 00:25:11'),('5092ff10-097b-4bac-a4d8-9b4766aaf40d','c42184a3-1a7f-4c4d-b380-15d8d97fdd11','7477907c-79ec-4d48-93ae-9e0cbbfd2b65','Load post approve normalization link',NULL,'2013-11-07 22:51:35'),('51e31d21-3e92-4c9f-8fec-740f559285f2','a6b1c323-7d36-428e-846a-e7e819423577','7478e34b-da4b-479b-ad2e-5a3d4473364f','Normalize for preservation',NULL,'2013-11-15 00:31:31'),('525db1a2-d494-4764-a900-7ff89d67c384','36b2e239-4a57-4aa5-8ebc-7a29139baca6','805d7c5d-5ca9-4e66-9223-767eef79e0bd','Remove the processing directory',NULL,'2012-10-02 00:25:11'),('528c8fe3-265f-45dd-b5c0-1a4ac0e15954','36b2e239-4a57-4aa5-8ebc-7a29139baca6','c64b1064-c856-4758-9891-152c7eabde7f','Verify metadata directory checksums',NULL,'2012-10-02 00:25:11'),('52d646df-fd66-4157-b8aa-32786fef9481','36b2e239-4a57-4aa5-8ebc-7a29139baca6','df65573b-70b7-4cd4-b825-d5d5d8dd016d','Verify metadata directory checksums',NULL,'2012-10-02 00:25:11'),('530b3b90-b97a-4aaf-836f-3a889ad1d7d2','a6b1c323-7d36-428e-846a-e7e819423577','4b816807-10a7-447a-b42f-f34c8b8b3b76','Characterize and extract metadata on submission documentation',NULL,'2012-10-02 00:25:11'),('547f95f6-3fcd-45e1-98b6-a8a7d9097373','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9c94b1d7-0563-4be9-9d64-058d0d1a03f4','Create thumbnails directory',NULL,'2012-10-02 00:25:11'),('549181ed-febe-487a-a036-ed6fdfa10a86','36b2e239-4a57-4aa5-8ebc-7a29139baca6','6c50d546-b0a4-4900-90ac-b4bcca802368','Remove hidden files and directories',NULL,'2012-10-02 00:25:11'),('54a05ec3-a34f-4404-96ec-36b527445da9','36b2e239-4a57-4aa5-8ebc-7a29139baca6','b0aa4fd2-a837-4cb8-964d-7f905326aa85','Failed compliance. See output in dashboard. Transfer moved back to activeTransfers.',NULL,'2012-10-02 00:25:11'),('55f0e6fa-834c-44f1-89f3-c912e79cea7d','36b2e239-4a57-4aa5-8ebc-7a29139baca6','d12b6b59-1f1c-47c2-b1a3-2bf898740eae','Removed bagged files',NULL,'2012-10-02 00:25:11'),('56aef696-b752-42de-9c6d-0a436bcc6870','36b2e239-4a57-4aa5-8ebc-7a29139baca6','33e7f3af-e414-484f-8468-1db09cb4258b','Move to select and run file id tool',NULL,'2013-11-07 22:51:35'),('57bd2747-181e-4f06-b969-dc012c592982','36b2e239-4a57-4aa5-8ebc-7a29139baca6','f368a36d-2b27-4f08-b662-2828a96d189a','Sanitize extracted objects\' file and directory names',NULL,'2013-11-07 22:51:43'),('57ef1f9f-3a1a-4cdc-90fd-39b024524618','36b2e239-4a57-4aa5-8ebc-7a29139baca6','7e47b56f-f9bc-4a10-9f63-1b165354d5f4','Verify metadata directory checksums',NULL,'2012-10-02 00:25:11'),('582883b9-9338-4e73-8873-371b666038fe','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','42e656d6-4816-417f-b45e-92dadd0dfde5','Set SIP to normalize with Tika file identification.',NULL,'2012-10-23 19:41:24'),('58a83299-c854-49bb-9b16-bf97813edd8e','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Normalize',NULL,'2012-10-02 00:25:11'),('58cddaf1-3273-4c18-9455-f341b199edf0','a6b1c323-7d36-428e-846a-e7e819423577','dca1bdba-5086-4423-be6b-8c660f8537ac','Extract packages',NULL,'2012-10-02 00:25:11'),('596a7fd5-a86b-489c-a9c0-3aa64b836cec','36b2e239-4a57-4aa5-8ebc-7a29139baca6','55eec242-68fa-4a1b-a3cd-458c087a017b','Move to select normalization path.',NULL,'2013-11-07 22:51:35'),('59ebdcec-eacc-4daf-978a-1b0d8652cd0c','36b2e239-4a57-4aa5-8ebc-7a29139baca6','5401961e-773d-41fe-8d62-8c1262f6156b','Move to the failed directory',NULL,'2012-10-02 00:25:11'),('5a3d244e-c7a1-4cd9-b1a8-2890bf1f254c','36b2e239-4a57-4aa5-8ebc-7a29139baca6','290b358c-cfff-488c-a0b7-fffce037b2c5','Check for Service directory',NULL,'2012-10-02 00:25:11'),('5a9fbb03-2434-4034-b20f-bcc6f971a8e5','36b2e239-4a57-4aa5-8ebc-7a29139baca6','4c25f856-6639-42b5-9120-3ac166dce932','Assign file UUIDs',NULL,'2013-11-07 22:51:35'),('5bd51fcb-6a68-4c5f-b99e-4fc36f51c40c','a6b1c323-7d36-428e-846a-e7e819423577','e377b543-d9b8-47a9-8297-4f95ca7600b3','Assign checksums and file sizes to metadata ',NULL,'2013-02-13 22:03:40'),('5c831a10-5d75-44ca-9741-06fdfc72052a','36b2e239-4a57-4aa5-8ebc-7a29139baca6','5341d647-dc75-4f00-8e02-cef59c9862e5','Create DIP directory',NULL,'2012-10-02 00:25:11'),('5f1b9002-3f89-4f9a-b960-92ac5466ef81','a6b1c323-7d36-428e-846a-e7e819423577','c7e6b467-445e-4142-a837-5b50184238fc','Identify file formats with MediaInfo',NULL,'2013-11-07 22:51:34'),('602e9b26-5839-4940-b230-0264bb873fe7','a6b1c323-7d36-428e-846a-e7e819423577','2843eba9-a9cf-462a-9cfc-f24ff35a22c0','Identify manually normalized files',NULL,'2013-02-19 00:52:52'),('62ba16c8-4a3f-4199-a48e-d557a90728e2','a6b1c323-7d36-428e-846a-e7e819423577','27dfc012-7cf4-449c-b0f0-bdd252c6f6e9','Create unquarantine PREMIS events',NULL,'2012-10-02 00:25:11'),('63866950-cb04-4fe2-9b1d-9d5f1d22fc86','3590f73d-5eb0-44a0-91a6-5b2db6655889','ce2491ee-3d68-45a2-bb14-fd0b304c9891','Grant normalization options for pre-existing DIP',NULL,'2012-10-02 00:25:11'),('63f265b3-57f5-4f14-90f5-cf0179dc366e','a6b1c323-7d36-428e-846a-e7e819423577','c8f93c3d-b078-428d-bd53-1b5789cde598','Assign checksums and file sizes to submissionDocumentation',NULL,'2012-10-02 00:25:11'),('6405c283-9eed-410d-92b1-ce7d938ef080','a6b1c323-7d36-428e-846a-e7e819423577','c06ecc19-8f75-4ccf-a549-22fde3972f28','Assign checksums and file sizes to objects',NULL,'2012-10-02 00:25:11'),('64a859be-f362-45d1-b9b4-4e15091f686f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9e6d6445-ccc6-427a-9407-a126699f98b4','Extract zipped bag transfer',NULL,'2012-10-02 00:25:11'),('674e21f3-1c50-4185-8e5d-70b1ed4a7f3a','a6b1c323-7d36-428e-846a-e7e819423577','614b1d56-9078-4cb0-80cc-1ea87b9fbbe8','Assign file UUIDs to submission documentation',NULL,'2012-10-02 00:25:11'),('68920df3-66aa-44fc-b221-710dbe97680a','a6b1c323-7d36-428e-846a-e7e819423577','79f3c95a-c1f1-463b-ab23-972ad859e136','Run FITS on manual normalized preservation files',NULL,'2013-01-03 02:10:38'),('6a930177-66db-49d3-b95d-10c28ee47562','36b2e239-4a57-4aa5-8ebc-7a29139baca6','748eef17-84d3-4b84-9439-6756f0fc697d','Verify TRIM manifest',NULL,'2012-11-30 19:55:47'),('6af5d804-de90-4c5b-bdba-e15a89e1a3db','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9e302b2b-e28d-4a61-9be7-b94e16929560','Create transfer backup (sharedDirectory/transferBackups)',NULL,'2012-10-02 00:25:11'),('6ed7ec07-5df1-470b-9a2e-a934cba8af26','36b2e239-4a57-4aa5-8ebc-7a29139baca6','b3fed349-54c4-4142-8d86-925b3a9f4365','Rename with transfer UUID',NULL,'2012-10-02 00:25:11'),('6f5d5518-1ed4-49b8-9cd5-497d112c97e4','36b2e239-4a57-4aa5-8ebc-7a29139baca6','3b889d1d-bfe1-467f-8373-2c9366127093','Verify TRIM checksums',NULL,'2012-11-30 19:55:47'),('7058a655-82f3-455c-9245-ad8e87e77a4f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ee80b69b-6128-4e31-9db4-ef90aa677c87','Upload DIP',NULL,'2012-10-02 00:25:11'),('714d3957-3e7d-4b70-b72e-6fef90c0da21','a6b1c323-7d36-428e-846a-e7e819423577','85419d3b-a0bf-402c-aa69-f5770a79904b','Extract packages in submission documentation',NULL,'2012-10-02 00:25:11'),('71d4f810-8fb6-45f7-9da2-f2dc07217076','a6b1c323-7d36-428e-846a-e7e819423577','2ad612bc-1993-407e-9d66-a8ab9c1ebbd5','Assign file UUIDs to objects',NULL,'2012-10-02 00:25:11'),('72dce7bc-054c-4d2d-8971-a480cb894bdc','36b2e239-4a57-4aa5-8ebc-7a29139baca6','d079b090-bc81-4fc6-a9c5-a267ad5f69a9','Create thumbnails directory',NULL,'2012-10-02 00:25:11'),('73ad6c9d-8ea1-4667-ae7d-229656a49237','36b2e239-4a57-4aa5-8ebc-7a29139baca6','744000f8-8688-4080-9225-5547cd3f77cc','Create SIP from transfer objects',NULL,'2012-10-02 00:25:11'),('73e12d44-ec3d-41a9-b138-80ec7e31ede5','36b2e239-4a57-4aa5-8ebc-7a29139baca6','2f2a9b2b-bcdb-406b-a842-898d4bed02be','Move submission documentation into objects directory',NULL,'2012-10-02 00:25:11'),('74146fe4-365d-4f14-9aae-21eafa7d8393','36b2e239-4a57-4aa5-8ebc-7a29139baca6','464a0a66-571b-4e6d-ba3a-4d182551a20f','Move to processing directory',NULL,'2012-10-02 00:25:11'),('757b5f8b-0fdf-4c5c-9cff-569d63a2d209','36b2e239-4a57-4aa5-8ebc-7a29139baca6','fa903131-1d84-4d2b-b498-67a48bc44fc8','Verify mets_structmap.xml compliance',NULL,'2012-10-02 00:25:11'),('75e00332-24a3-4076-aed1-e3dc44379227','a19bfd9f-9989-4648-9351-013a10b382ed','857fb861-8aa1-45c0-95f5-c5af66764142','Retrieve AIP Storage Locations',NULL,'2013-11-07 22:51:35'),('76135f22-6dba-417f-9833-89ecbe9a3d99','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','face6ee9-42d5-46ff-be1b-a645594b2da8','Set SIP to normalize with FITS-JHOVE file identification.',NULL,'2012-10-23 19:41:23'),('76729a40-dfa1-4c1a-adbf-01fb362324f5','36b2e239-4a57-4aa5-8ebc-7a29139baca6','0b1177e8-8541-4293-a238-1783c793a7b1','Rename with transfer UUID',NULL,'2012-10-02 00:25:11'),('7872599e-ebfc-472b-bb11-524ff728679f','3590f73d-5eb0-44a0-91a6-5b2db6655889','f1357379-0118-4f51-aa49-37aeb702b760','Designate to process as a DSpace transfer',NULL,'2012-10-02 00:25:11'),('7a96f085-924b-483e-bc63-440323bce587','c42184a3-1a7f-4c4d-b380-15d8d97fdd11','97ddf0be-7b07-48b1-82f6-6a3b49edde2b','Determine which files to identify',NULL,'2013-11-07 22:51:43'),('7b07859b-015e-4a17-8bbf-0d46f910d687','36b2e239-4a57-4aa5-8ebc-7a29139baca6','58b192eb-0507-4a83-ae5a-f5e260634c2a','Sanitize file and directory names in metadata',NULL,'2013-02-13 22:03:39'),('7beb3689-02a7-4f56-a6d1-9c9399f06842','36b2e239-4a57-4aa5-8ebc-7a29139baca6','2f851d03-722f-4c49-8369-64f11542af89','Load labels from metadata/file_labels.csv',NULL,'2012-10-02 00:25:11'),('7c02a87b-7113-4851-97cd-2cf9d3fc0010','36b2e239-4a57-4aa5-8ebc-7a29139baca6','037feb3c-f4d1-44dd-842e-c681793094df','Move to processing directory',NULL,'2012-10-02 00:25:11'),('7f786b5c-c003-4ef1-97c2-c2269a04e89a','a6b1c323-7d36-428e-846a-e7e819423577','46883944-8561-44d0-ac50-e1c3fd9aeb59','Identify file formats with FIDO',NULL,'2013-11-07 22:51:35'),('7fd4e564-bed2-42c7-a186-7ae615381516','a6b1c323-7d36-428e-846a-e7e819423577','62f21582-3925-47f6-b17e-90f46323b0d1','Normalize service files for thumbnails',NULL,'2013-11-15 00:31:31'),('80ebef4c-0dd1-45eb-b993-1db56a077db8','36b2e239-4a57-4aa5-8ebc-7a29139baca6','6c261f8f-17ce-4b58-86c2-ac3bfb0d2850','Set transfer type: DSpace',NULL,'2012-10-02 00:25:11'),('81d64862-a4f6-4e3f-b32e-47268d9eb9a3','a6b1c323-7d36-428e-846a-e7e819423577','f798426b-fbe9-4fd3-9180-8df776384b14','Identify DSpace mets files',NULL,'2012-10-02 00:25:11'),('851d679e-44db-485a-9b0e-2dfbdf80c791','3590f73d-5eb0-44a0-91a6-5b2db6655889','1c460578-e696-4378-a5d1-63ee77dd18bc','Designate to process as a standard transfer when unquarantined',NULL,'2012-10-02 00:25:11'),('8558d885-d6c2-4d74-af46-20da45487ae7','a6b1c323-7d36-428e-846a-e7e819423577','9c3680a5-91cb-413f-af4e-d39c3346f8db','Identify file format',NULL,'2013-11-07 22:51:42'),('85a2ec9b-5a80-497b-af60-04926c0bf183','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Select format identification tool',NULL,'2012-10-24 00:45:13'),('8850aeff-8553-4ff1-ab31-99b5392a458b','a6b1c323-7d36-428e-846a-e7e819423577','7316e6ed-1c1a-4bf6-a570-aead6b544e41','Scan for viruses in metadata',NULL,'2013-02-13 22:03:39'),('8a291152-729c-42f2-ab2e-c53b9f357799','9c84b047-9a6d-463f-9836-eafa49743b84',NULL,'Select compression algorithm',NULL,'2012-10-02 00:25:11'),('8b846431-5da9-4743-906d-2cdc4e777f8f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','179373e8-a6b4-4274-a245-ca3f4b105396','Move to select file ID tool',NULL,'2013-11-07 22:51:42'),('8cda5b7a-fb44-4a61-a865-6ad01af5a150','36b2e239-4a57-4aa5-8ebc-7a29139baca6','77ea8809-bc90-4e9d-a144-ad6d5ec59de9','Check transfer directory for objects',NULL,'2012-10-02 00:25:11'),('8ef75179-a3f1-4911-9f05-c84e8756fc67','a6b1c323-7d36-428e-846a-e7e819423577','2fdb8408-8bbb-45d1-846b-5e28bf220d5c','Scan for viruses in submission documentation',NULL,'2012-10-02 00:25:11'),('8fa944df-1baf-4f89-8106-af013b5078f4','6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9',NULL,'Find branch to continue processing',NULL,'2012-10-02 00:25:11'),('90e0993d-23d4-4d0c-8b7d-73717b58f20e','36b2e239-4a57-4aa5-8ebc-7a29139baca6','6abefa8d-387d-4f23-9978-bea7e6657a57','Copy thumbnails to DIP directory',NULL,'2012-10-02 00:25:11'),('92a7b76c-7c5c-41b3-8657-ba4cdd9a8176','36b2e239-4a57-4aa5-8ebc-7a29139baca6','fa903131-1d84-4d2b-b498-67a48bc44fc8','Verify mets_structmap.xml compliance',NULL,'2012-10-02 00:25:11'),('9371ba25-b600-485d-b2d8-cef2f39c35ed','36b2e239-4a57-4aa5-8ebc-7a29139baca6','4cfac870-24ec-4a80-8bcb-7a38fd02e048','Create SIPs from TRIM transfer containers',NULL,'2012-12-04 21:29:48'),('93e01ed2-8d69-4a56-b686-3cf507931885','6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9',NULL,'Find type to remove from quarantine as',NULL,'2012-10-02 00:25:11'),('9413e636-1209-40b0-a735-74ec785ea14a','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Normalize',NULL,'2013-11-07 22:51:35'),('94942d82-8b87-4be3-a338-158f893573cd','9c84b047-9a6d-463f-9836-eafa49743b84',NULL,'Select target CONTENTdm server',NULL,'2012-10-02 00:25:11'),('94da9e56-46aa-4215-bcd8-062fed887a36','a6b1c323-7d36-428e-846a-e7e819423577','4f400b71-37be-49d0-8da3-125abac2bfd0','Verify checksums generated on ingest',NULL,'2012-10-02 00:25:11'),('95d2ddff-a5e5-49cd-b4da-a5dd6fd3d2eb','36b2e239-4a57-4aa5-8ebc-7a29139baca6','a51af5c7-0ed4-41c2-9142-fc9e43e83960','Generate DIP',NULL,'2013-11-07 22:51:35'),('95d9f32a-466b-4754-9553-12eb43527c63','a6b1c323-7d36-428e-846a-e7e819423577','a32fc538-efd1-4be0-95a9-5ee40cbc70fd','Remove files without linking information (failed normalization artifacts etc.)',NULL,'2012-10-02 00:25:11'),('9649186d-e5bd-4765-b285-3b0d8e83b105','a6b1c323-7d36-428e-846a-e7e819423577','6733ebdd-5c5f-4168-81a5-fe9a2fbc10c9','Create placement in backlog PREMIS events',NULL,'2013-04-19 22:39:27'),('966f5720-3081-4697-9691-c19b86ffa569','36b2e239-4a57-4aa5-8ebc-7a29139baca6','7b455fc5-b201-4233-ba1c-e05be059b279','Set transfer type: Maildir',NULL,'2012-10-02 00:25:11'),('96a4bdad-a602-4007-ba37-6a2c47e77366','36b2e239-4a57-4aa5-8ebc-7a29139baca6','2f851d03-722f-4c49-8369-64f11542af89','Load labels from metadata/file_labels.csv',NULL,'2012-10-02 00:25:11'),('97545cb5-3397-4934-9bc5-143b774e4fa7','9c84b047-9a6d-463f-9836-eafa49743b84',NULL,'Select file format identification command',NULL,'2013-11-07 22:51:42'),('97cc7629-c580-44db-8a41-68b6b2f23be4','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','b5808a0f-e842-4820-837a-832d18398ebb','Set remove preservation normalized files to renormalize link.',NULL,'2012-10-24 00:40:07'),('99324102-ebe8-415d-b5d8-b299ab2f4703','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','f226ecea-ae91-42d5-b039-39a1125b1c30','Set files to normalize',NULL,'2013-11-07 22:51:43'),('99712faf-6cd0-48d1-9c66-35a2033057cf','36b2e239-4a57-4aa5-8ebc-7a29139baca6','c79f55f7-637c-4d32-a6fa-1d193e87c5fc','Move to the failed directory',NULL,'2012-10-02 00:25:11'),('9a0f8eac-6a9d-4b85-8049-74954fbd6594','a6b1c323-7d36-428e-846a-e7e819423577','de58249f-9594-439d-8bea-536ce59d70a3','Scan for viruses',NULL,'2012-10-02 00:25:11'),('9a70cc32-2b0e-4763-a168-b81485fac366','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ed8c70b7-1456-461c-981b-6b9c84896263','Generate DIP',NULL,'2012-10-02 00:25:11'),('9dd95035-e11b-4438-a6c6-a03df302933c','36b2e239-4a57-4aa5-8ebc-7a29139baca6','80759ad1-c79a-4c3b-b255-735c28a50f9e','Sanitize object\'s file and directory names',NULL,'2012-10-02 00:25:11'),('a0aecc16-3f78-4579-b6d4-a10df1f89a41','36b2e239-4a57-4aa5-8ebc-7a29139baca6','329fd50d-42fd-44e3-940e-7dc45d1a7727','Set unquarantined file permissions on Transfer',NULL,'2012-10-02 00:25:11'),('a20c5353-9e23-4b5d-bb34-09f2efe1e54d','36b2e239-4a57-4aa5-8ebc-7a29139baca6','45f11547-0df9-4856-b95a-3b1ff0c658bd','Create AIP Pointer File',NULL,'2013-11-07 22:51:35'),('a2e93146-a3ff-4e6c-ae3d-76ce49ca5e1b','3590f73d-5eb0-44a0-91a6-5b2db6655889','5dffcd9c-472d-44e0-ae4d-a30705cf80cd','Designate to process as a standard transfer',NULL,'2012-10-02 00:25:11'),('a3c27d23-dbdf-47af-bf66-4238aa1a508f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','db753cdd-c556-4f4b-aa09-e55eb637244d','Attempt restructure for compliance',NULL,'2012-10-02 00:25:11'),('a493f430-d905-4f68-a742-f4393a43e694','c42184a3-1a7f-4c4d-b380-15d8d97fdd11','49c816cd-b443-498f-9369-9274d060ddd3','Load finished with metadata processing link',NULL,'2013-02-13 22:03:37'),('a66737a0-c912-470f-9edf-983c7be0951f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','b3c14f6c-bc91-4349-9e8f-c02f7dac27b3','Copy transfer submission documentation',NULL,'2012-10-02 00:25:11'),('a71f40ec-77b2-4f13-91b6-da3d4a67a284','36b2e239-4a57-4aa5-8ebc-7a29139baca6','a56a116c-167b-45c5-b634-253696270a12','Include default Transfer processingMCP.xml',NULL,'2012-10-02 00:25:11'),('a73b3690-ac75-4030-bb03-0c07576b649b','36b2e239-4a57-4aa5-8ebc-7a29139baca6','a56a116c-167b-45c5-b634-253696270a12','Include default Transfer processingMCP.xml',NULL,'2012-10-02 00:25:11'),('a75ee667-3a1c-4950-9194-e07d0e6bf545','a6b1c323-7d36-428e-846a-e7e819423577','02fd0952-4c9c-4da6-9ea3-a1409c87963d','Identify file format of attachments',NULL,'2013-11-07 22:51:43'),('a8489361-b731-4d4a-861d-f4da1767665f','a6b1c323-7d36-428e-846a-e7e819423577','8fe4a2c3-d43c-41e4-aeb9-18e8f57c9ccf','Normalize for thumbnails',NULL,'2013-11-15 00:31:31'),('aa2e26b3-539e-4071-b54c-bcb89650d2d2','36b2e239-4a57-4aa5-8ebc-7a29139baca6','2c9fd8e4-a4f9-4aa6-b443-de8a9a49e396','Index transfer contents',NULL,'2012-10-02 00:25:11'),('abeaa79e-668b-4de0-b8cb-70f8ab8056b6','a6b1c323-7d36-428e-846a-e7e819423577','c8f93c3d-b078-428d-bd53-1b5789cde598','Assign checksums and file sizes to submissionDocumentation',NULL,'2012-10-02 00:25:11'),('ac99ec32-7732-4cfe-9cac-579af16f6734','36b2e239-4a57-4aa5-8ebc-7a29139baca6','2e9fb50f-2275-4253-87e5-47d2faf1031e','Copy transfers metadata and logs',NULL,'2012-10-02 00:25:11'),('accc69f9-5b99-4565-92b5-114c7727d9e9','a6b1c323-7d36-428e-846a-e7e819423577','30ea6854-cf7a-42d4-b1e8-3c4ca0b82b7d','Create quarantine PREMIS events',NULL,'2012-10-02 00:25:11'),('acd5e136-11ed-46fe-bf67-dc108f115d6b','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9c94b1d7-0563-4be9-9d64-058d0d1a03f4','Create thumbnails directory',NULL,'2012-10-02 00:25:11'),('acf7bd62-1587-4bff-b640-5b34b7196386','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Approve maildir transfer',NULL,'2012-10-02 00:25:11'),('ad1f1ae6-658f-4281-abc2-fe2f6c5d5e8e','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Remove from quarantine',NULL,'2012-10-02 00:25:11'),('ad38cdea-d1da-4d06-a7e5-6f75da85a718','36b2e239-4a57-4aa5-8ebc-7a29139baca6','6157fe87-26ff-49da-9899-d9036b21c4b0','Set file permissions',NULL,'2012-10-02 00:25:11'),('b24525cd-e68d-4afd-b6ec-46192bbc117b','36b2e239-4a57-4aa5-8ebc-7a29139baca6','b3c14f6c-bc91-4349-9e8f-c02f7dac27b3','Copy transfer submission documentation',NULL,'2012-10-02 00:25:11'),('b3875772-0f3b-4b03-b602-5304ded86397','36b2e239-4a57-4aa5-8ebc-7a29139baca6','cf23dd75-d273-4c4e-8394-17622adf9bd6','Verify transfer compliance',NULL,'2012-10-02 00:25:11'),('b3b86729-470f-4301-8861-d62574966747','36b2e239-4a57-4aa5-8ebc-7a29139baca6','d079b090-bc81-4fc6-a9c5-a267ad5f69a9','Create thumbnails directory',NULL,'2012-10-02 00:25:11'),('b57b3564-e271-4226-a5f9-2c7cf1661a83','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ae6b87d8-59c8-4ffa-b417-ce93ab472e74','Verify AIP',NULL,'2013-11-07 22:51:35'),('b5970cbb-1af7-4f8c-b41d-a0febd482da4','36b2e239-4a57-4aa5-8ebc-7a29139baca6','e884b0db-8e51-4ea6-87f9-0420ee9ddf8f','Verify bag, and restructure for compliance',NULL,'2012-10-02 00:25:11'),('b5e6340f-07f3-4ed1-aada-7a7f049b19b9','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','6c02936d-552a-415e-b3c1-6d681b01d1c6','Set SIP to normalize with FITS-ffident file identification.',NULL,'2012-10-23 19:41:23'),('b6167c79-1770-4519-829c-fa01718756f4','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9e302b2b-e28d-4a61-9be7-b94e16929560','Create transfer backup (sharedDirectory/transferBackups)',NULL,'2012-10-02 00:25:11'),('b8403044-12a3-4b63-8399-772b9adace15','a6b1c323-7d36-428e-846a-e7e819423577','51eab45d-6a24-4080-a1be-1e5c9405ce25','Characterize and extract metadata on objects',NULL,'2012-10-02 00:25:11'),('b8c10f19-40c9-44c8-8b9f-6fab668513f5','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','4093954b-5e44-4fe9-9a47-14c82158a00d','Set SIP to normalize with FITS-Droid file identification.',NULL,'2012-10-23 19:41:22'),('ba0d0244-1526-4a99-ab65-43bfcd704e70','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ce13677c-8ad4-4af0-92c8-ae8763f5094d','Move metadata to objects directory',NULL,'2013-02-13 22:03:40'),('bacb088a-66ef-4590-b855-69f21dfdf87a','36b2e239-4a57-4aa5-8ebc-7a29139baca6','352fc88d-4228-4bc8-9c15-508683dabc58','Remove preservation normalized files to renormalize.',NULL,'2012-10-24 00:40:07'),('bafe0ba3-420a-44f2-bb15-7509ef5c498c','36b2e239-4a57-4aa5-8ebc-7a29139baca6','4dc2b1d2-acbb-47e7-88ca-570281f3236f','Compress AIP',NULL,'2012-10-02 00:25:11'),('bcff2873-f006-442e-9628-5eadbb8d0db7','36b2e239-4a57-4aa5-8ebc-7a29139baca6','a650921e-b754-4e61-9713-1457cf52e77d','Upload to Archivists Toolkit',NULL,'2013-03-26 03:25:01'),('bd9769ba-4182-4dd4-ba85-cff24ea8733e','a6b1c323-7d36-428e-846a-e7e819423577','ec54a7cb-690f-4dd6-ad2b-979ae9f8d25a','Assign checksums and file sizes to objects',NULL,'2012-10-02 00:25:11'),('be4e3ee6-9be3-465f-93f0-77a4ccdfd1db','36b2e239-4a57-4aa5-8ebc-7a29139baca6','11e6fcbe-3d7b-41cc-bfac-14dee9172b51','Move to the rejected directory',NULL,'2012-10-02 00:25:11'),('bec683fa-f006-48a4-b298-d33b3b681cb2','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Store AIP',NULL,'2012-10-02 00:25:11'),('bf0835be-4c76-4508-a5a7-cdc4c9dae217','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Remove from quarantine',NULL,'2012-10-02 00:25:11'),('bf5a1f0c-1b3e-4196-b51f-f6d509091346','a6b1c323-7d36-428e-846a-e7e819423577','45df6fd4-9200-4ec7-bd31-ba0338c07806','Assign checksums and file sizes to objects',NULL,'2012-10-02 00:25:11'),('bf71562c-bc87-4fd0-baa6-1d85ff751ea2','36b2e239-4a57-4aa5-8ebc-7a29139baca6','7df9e91b-282f-457f-b91a-ad6135f4337d','Store the AIP',NULL,'2012-10-02 00:25:11'),('bf9b2fb7-43bd-4c3e-9dd0-7b6f43e6cb48','c42184a3-1a7f-4c4d-b380-15d8d97fdd11','11aef684-f2c7-494e-9763-277344e139bf','Load options to create SIPs',NULL,'2012-12-06 17:43:25'),('bfb30b76-ab7b-11e2-bace-08002742f837','36b2e239-4a57-4aa5-8ebc-7a29139baca6','bfaf4e65-ab7b-11e2-bace-08002742f837','Remove indexed AIP files',NULL,'2013-04-22 18:37:56'),('c075014f-4051-441a-b16b-3083d5c264c5','36b2e239-4a57-4aa5-8ebc-7a29139baca6','045f84de-2669-4dbc-a31b-43a4954d0481','Prepare AIP',NULL,'2012-10-02 00:25:11'),('c1bd4921-c446-4ff9-bb34-fcd155b8132a','36b2e239-4a57-4aa5-8ebc-7a29139baca6','2e9fb50f-2275-4253-87e5-47d2faf1031e','Copy transfers metadata and logs',NULL,'2012-10-02 00:25:11'),('c2c7edcc-0e65-4df7-812f-a2ee5b5d52b6','36b2e239-4a57-4aa5-8ebc-7a29139baca6','89b4d447-1cfc-4bbf-beaa-fb6477b00f70','Sanitize extracted objects\' file and directory names',NULL,'2013-11-07 22:51:43'),('c307d6bd-cb81-46a1-89f1-bb02a43e0a3a','a6b1c323-7d36-428e-846a-e7e819423577','68b1456e-9a59-48d8-96ef-92bc20fd7cab','Move access files to DIP',NULL,'2013-01-03 02:10:39'),('c310a18a-1659-45d0-845e-06eb3321512f','36b2e239-4a57-4aa5-8ebc-7a29139baca6','1fb68647-9db0-49ef-b6b7-3f775646ffbe','Create DIP directory',NULL,'2012-10-02 00:25:11'),('c3e3f03d-c104-48c3-8c64-4290459965f4','36b2e239-4a57-4aa5-8ebc-7a29139baca6','a540bd68-27fa-47c3-9fc3-bd297999478d','Create DIP directory',NULL,'2012-10-02 00:25:11'),('c409f2b0-bcb7-49ad-a048-a217811ca9b6','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Approve SIP Creation',NULL,'2012-10-02 00:25:11'),('c450501a-251f-4de7-acde-91c47cf62e36','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Create DIP from AIP',NULL,'2013-11-07 22:51:35'),('c4b2e8ce-fe02-45d4-9b0f-b163bffcc05f','c42184a3-1a7f-4c4d-b380-15d8d97fdd11','e076e08f-5f14-4fc3-93d0-1e80ca727f34','Load post approve normalization link',NULL,'2013-11-07 22:51:35'),('c52736fa-2bc5-4142-a111-8b13751ed067','36b2e239-4a57-4aa5-8ebc-7a29139baca6','0aec05d4-7222-4c28-89f4-043d20a812cc','Generate METS.xml document',NULL,'2012-10-02 00:25:11'),('c5d7e646-01b1-4d4a-9e38-b89d97e77e33','36b2e239-4a57-4aa5-8ebc-7a29139baca6','e469dc77-5712-4ef1-b053-06f3cd3c34be','Upload DIP to CONTENTdm',NULL,'2012-10-02 00:25:11'),('c5e80ef1-aa90-45b2-beb4-c42652acf3e7','36b2e239-4a57-4aa5-8ebc-7a29139baca6','df526440-c08e-49f9-9b9e-c9aa3adedc72','Move to workFlowDecisions-createDip directory',NULL,'2012-10-02 00:25:11'),('c6f9f99a-0b60-438f-9a8d-35d4989db2bb','3590f73d-5eb0-44a0-91a6-5b2db6655889','5057b0ce-a7f9-48c4-a7e9-65a7d88bb4ca','Designate to process as a standard transfer',NULL,'2012-10-02 00:25:11'),('c74dfa47-9a6d-4a12-bffe-bf610ab75db9','36b2e239-4a57-4aa5-8ebc-7a29139baca6','24272436-39b0-44f1-a0d6-c4bdca93ce88','Extract attachments',NULL,'2012-10-02 00:25:11'),('c87ec738-b679-4d8e-8324-73038ccf0dfd','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','471ff5ad-1fd3-4540-9245-360cc8c9b389','Set SIP to normalize with FITS-FITS file identification.',NULL,'2012-10-23 19:41:24'),('caaa29bc-a2b6-487b-abff-c3031a0e147a','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','5035632e-7879-4ece-bf43-2fc253026ff5','Set resume link after handling any manual normalized files',NULL,'2013-01-03 02:10:39'),('cac32b11-820c-4d17-8c7f-4e71fc0be68a','a6b1c323-7d36-428e-846a-e7e819423577','30ea6854-cf7a-42d4-b1e8-3c4ca0b82b7d','Create quarantine PREMIS events',NULL,'2012-10-02 00:25:11'),('cd53e17c-1dd1-4e78-9086-e6e013a64536','36b2e239-4a57-4aa5-8ebc-7a29139baca6','feec6329-c21a-48b6-b142-cd3c810e846f','Determin processing path for this AIP version.',NULL,'2013-11-07 22:51:35'),('ce48a9f5-4513-49e2-83db-52b01234705b','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','c26b2859-7a96-462f-880a-0cd8d1b0ac32','Set re-normalize link',NULL,'2013-11-07 22:51:35'),('ce52ace2-68fc-4bfb-8444-f32ec8c01783','c42184a3-1a7f-4c4d-b380-15d8d97fdd11','e56e168e-d339-45b4-bc2a-a3eb24390f0f','Determine what to remove to re-normalize.',NULL,'2012-10-24 17:04:11'),('ce57ffbc-abd9-43dc-a09b-e888397488f2','36b2e239-4a57-4aa5-8ebc-7a29139baca6','e8fc5fd0-fd55-4eb6-9170-92615fc9c344','Check for manual normalized files',NULL,'2013-01-03 02:10:39'),('cfc7f6be-3984-4727-a71a-02ce27bef791','36b2e239-4a57-4aa5-8ebc-7a29139baca6','a56a116c-167b-45c5-b634-253696270a12','Include default Transfer processingMCP.xml',NULL,'2012-10-02 00:25:11'),('d1004e1d-f938-4c68-ba70-0e0ae508cbbe','36b2e239-4a57-4aa5-8ebc-7a29139baca6','1e5e8ee2-8b93-4e8c-bb9c-0cb40d2728dd','Failed compliance.',NULL,'2012-10-02 00:25:11'),('d49684b1-badd-4802-b54e-06eb6b329140','36b2e239-4a57-4aa5-8ebc-7a29139baca6','20915fc5-594f-46d8-aa23-bfa45b622d17','Copy METS to DIP directory',NULL,'2012-10-02 00:25:11'),('d61bb906-feff-4d6f-9e6c-a3f077f46b21','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9f473616-9094-45b0-aa3c-41d81a204d3b','Rename SIP directory with SIP UUID',NULL,'2012-10-02 00:25:11'),('d6a0dec1-63e7-4c7c-b4c0-e68f0afcedd3','36b2e239-4a57-4aa5-8ebc-7a29139baca6','16ce41d9-7bfa-4167-bca8-49fe358f53ba','Updating transfer file index',NULL,'2013-04-05 23:08:30'),('d7542890-281f-4cdb-a64c-4b6bdd88c4b8','36b2e239-4a57-4aa5-8ebc-7a29139baca6','40bf5b85-7cfd-47b0-9fbc-aed6c2cde8be','Index AIP contents',NULL,'2012-10-02 00:25:11'),('d7a2bfbe-3f4d-45f7-87c6-f5c3c98961cd','a6b1c323-7d36-428e-846a-e7e819423577','a32fc538-efd1-4be0-95a9-5ee40cbc70fd','Remove files without linking information (failed normalization artifacts etc.)',NULL,'2012-10-02 00:25:11'),('d7f13903-55a0-4a1c-87fa-9b75b14dccb4','36b2e239-4a57-4aa5-8ebc-7a29139baca6','f9f7793c-5a70-4ffd-9727-159c1070e4f5','Restructure DIP for CONTENTdm upload',NULL,'2012-10-02 00:25:11'),('da756a4e-9d8b-4992-a219-2a7fd1edf2bb','36b2e239-4a57-4aa5-8ebc-7a29139baca6','89b4d447-1cfc-4bbf-beaa-fb6477b00f70','Sanitize object\'s file and directory names',NULL,'2012-10-02 00:25:11'),('dc2994f2-6de6-4c46-81f7-54676c5054aa','a6b1c323-7d36-428e-846a-e7e819423577','34966164-9800-4ae1-91eb-0a0c608d72d5','Assign file UUIDs to metadata',NULL,'2013-02-13 22:03:40'),('ddcd9c7d-6615-4524-bb5d-ae7c1b6acbbb','a6b1c323-7d36-428e-846a-e7e819423577','6dccf7b3-4282-46f9-a805-1297c6ea482b','Normalize for access',NULL,'2013-11-15 00:31:31'),('dde51fc1-af7d-4923-ad6a-06e670447a2a','36b2e239-4a57-4aa5-8ebc-7a29139baca6','0b17b446-11d4-45a8-9d0c-4297b8c8887c','Set quarantine permissions on transfer',NULL,'2012-10-02 00:25:11'),('dde8c13d-330e-458b-9d53-0937370695fa','36b2e239-4a57-4aa5-8ebc-7a29139baca6','c3625e5b-2c8d-47d9-9f66-c37111d39a07','Attempt restructure for compliance',NULL,'2012-10-02 00:25:11'),('de195451-989e-48fe-ad0c-3ff2265b3410','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Workflow decision - send transfer to quarantine',NULL,'2012-10-02 00:25:11'),('ded09ddd-2deb-4d62-bfe3-84703f60c522','a6b1c323-7d36-428e-846a-e7e819423577','0bdecdc8-f5ef-48dd-8a89-f937d2b3f2f9','Assign checksums to manual normalized preservation files',NULL,'2013-01-03 02:10:38'),('dee46f53-8afb-4aec-820e-d495bcbeaf20','a6b1c323-7d36-428e-846a-e7e819423577','27dfc012-7cf4-449c-b0f0-bdd252c6f6e9','Create unquarantine PREMIS events',NULL,'2012-10-02 00:25:11'),('df1c53e4-1b69-441e-bdc9-6d08c3b47c9b','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Approve bagit transfer',NULL,'2012-10-02 00:25:11'),('df51d25b-6a63-4e7a-b164-77b929dd2f31','36b2e239-4a57-4aa5-8ebc-7a29139baca6','35ef1f2d-0124-422f-a84a-5e1d756b6bf2','Include default Transfer processingMCP.xml',NULL,'2012-10-02 00:25:11'),('e0b25af2-1ce4-4ed3-b14f-87843fbd4c93','36b2e239-4a57-4aa5-8ebc-7a29139baca6','14780202-4aab-43f4-94ed-3bf9a040d055','Index transfer contents',NULL,'2013-11-07 22:51:35'),('e18e0c3a-dffb-42d2-9bfa-ea6c61328e28','36b2e239-4a57-4aa5-8ebc-7a29139baca6','3843f87a-12c4-4526-904a-d900572c6483','Failed compliance. See output in dashboard. SIP moved back to SIPsUnderConstruction',NULL,'2012-10-02 00:25:11'),('e20ea90b-fa16-4576-8647-199ecde0d511','36b2e239-4a57-4aa5-8ebc-7a29139baca6','42aed4a4-8e2b-49f3-ba03-1a45c8baf52c','Move to the rejected directory',NULL,'2012-10-02 00:25:11'),('e211ae41-bf9d-4f34-8b58-9a0dcc0bebe2','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Approve normalization',NULL,'2012-10-02 00:25:11'),('e476ac7e-d3e8-43fa-bb51-5a9cf42b2713','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','1871a1a5-1937-4c4d-ab05-3b0c04a0bca1','Set resume link after tool selected.',NULL,'2012-10-23 19:41:25'),('e485f0f4-7d44-45c6-a0d2-bba4b2abd0d0','36b2e239-4a57-4aa5-8ebc-7a29139baca6','302be9f9-af3f-45da-9305-02706d81b742','Move to the uploadedDIPs directory',NULL,'2012-10-02 00:25:11'),('e601b1e3-a957-487f-8cbe-54160070574d','a6b1c323-7d36-428e-846a-e7e819423577','2ad612bc-1993-407e-9d66-a8ab9c1ebbd5','Assign file UUIDs to objects',NULL,'2012-10-02 00:25:11'),('e62e4b85-e3f1-4550-8e40-3939e6497e92','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','f85bbe03-8aca-4211-99b7-ddb7dfb24da1','Set resume link after tool selected.',NULL,'2012-10-23 19:41:25'),('e6591da1-abfa-4bf2-abeb-cc0791ba5284','a6b1c323-7d36-428e-846a-e7e819423577','9ea66f4e-150b-4911-b68d-29fd5d372d2c','Identify DSpace text files',NULL,'2012-10-02 00:25:11'),('e82c3c69-3799-46fd-afc1-f479f960a362','36b2e239-4a57-4aa5-8ebc-7a29139baca6','80c4a6ed-abe4-4e02-8de8-55a50f559dab','Verify SIP compliance',NULL,'2012-10-02 00:25:11'),('e9f57845-4609-4e0a-a573-4b488d8a4aeb','36b2e239-4a57-4aa5-8ebc-7a29139baca6','f46bbd28-d533-4933-9b5c-4a5d32927ff3','Move to workFlowDecisions-createTransferBackup directory',NULL,'2012-10-02 00:25:11'),('ea331cfb-d4f2-40c0-98b5-34d21ee6ad3e','36b2e239-4a57-4aa5-8ebc-7a29139baca6','4f7e2ed6-44b9-49a7-a1b7-bbfe58eadea8','Move to the rejected directory',NULL,'2012-10-02 00:25:11'),('ea463bfd-5fa2-4936-b8c3-1ce3b74303cf','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9c94b1d7-0563-4be9-9d64-058d0d1a03f4','Create thumbnails directory',NULL,'2012-10-02 00:25:11'),('ea4a0dbc-9ee0-4865-a764-d78e7b501b1b','a6b1c323-7d36-428e-846a-e7e819423577','a32fc538-efd1-4be0-95a9-5ee40cbc70fd','Remove files without linking information (failed normalization artifacts etc.)',NULL,'2012-10-02 00:25:11'),('eb14ba91-20cb-4b0e-ab5d-c30bfea4dbc8','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','6adccf2b-1c91-448b-bf0f-56414ee237ac','Set TRIM options to create SIPs',NULL,'2012-12-06 19:01:04'),('ec503c22-1f4d-442f-b546-f90c9a9e5c86','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','d8e2c7b2-5452-4c26-b57a-04caafe9f95c','Set resume link',NULL,'2013-11-07 22:51:35'),('ef024cf9-1737-4161-b48a-13b4a8abddcd','a6b1c323-7d36-428e-846a-e7e819423577','4f400b71-37be-49d0-8da3-125abac2bfd0','Verify checksums generated on ingest',NULL,'2012-10-02 00:25:11'),('ef0bb0cf-28d5-4687-a13d-2377341371b5','a6b1c323-7d36-428e-846a-e7e819423577','49b803e3-8342-4098-bb3f-434e1eb5cfa8','Remove cache files',NULL,'2012-10-02 00:25:11'),('f1586bd7-f550-4588-9f45-07a212db7994','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9f25a366-f7a4-4b59-b219-2d5f259a1be9','Move transfer to backlog',NULL,'2013-04-05 23:08:30'),('f1f0409b-d4f8-419a-b625-218dc1abd335','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Create SIP(s)',NULL,'2012-10-02 00:25:11'),('f23a22b8-a3b0-440b-bf4e-fb6e8e6e6b14','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ad65bf76-3491-4c3d-afb0-acc94ff28bee','Sanitize file and directory names in submission documentation',NULL,'2012-10-02 00:25:11'),('f3567a6d-8a45-4174-b302-a629cdbfbe92','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Workflow decision - send transfer to quarantine',NULL,'2012-10-02 00:25:11'),('f452a117-a992-4447-9774-6a8130f05b30','36b2e239-4a57-4aa5-8ebc-7a29139baca6','9c94b1d7-0563-4be9-9d64-058d0d1a03f4','Create thumbnails directory',NULL,'2012-10-02 00:25:11'),('f5ca3e51-35ba-4cdd-acf5-7d4fec955e76','3590f73d-5eb0-44a0-91a6-5b2db6655889','5975a5df-41af-4e3e-8e4e-ec7aff3ae085','Designate to process as a DSpace transfer when unquarantined',NULL,'2012-10-02 00:25:11'),('f6141d04-a473-47f7-b8ac-25deac01a513','a6b1c323-7d36-428e-846a-e7e819423577','51eab45d-6a24-4080-a1be-1e5c9405ce25','Characterize and extract metadata',NULL,'2012-10-02 00:25:11'),('f661aae0-05bf-4f55-a2f6-ef0f157231bd','36b2e239-4a57-4aa5-8ebc-7a29139baca6','39f8d4bf-2078-4415-b600-ce2865585aca','Move to quarantined',NULL,'2012-10-02 00:25:11'),('f6fbbf4f-bf8d-49f2-a978-8d689380cafc','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ccbaa53f-a486-4564-9b1a-a1b7bd5b1239','Create rights to flag closed AIPS.',NULL,'2012-12-12 21:37:10'),('f872b932-90dd-4501-98c4-9fc5bac9d19a','36b2e239-4a57-4aa5-8ebc-7a29139baca6','f46bbd28-d533-4933-9b5c-4a5d32927ff3','Move to workFlowDecisions-quarantineSIP directory',NULL,'2012-10-02 00:25:11'),('f89b9e0f-8789-4292-b5d0-4a330c0205e1','36b2e239-4a57-4aa5-8ebc-7a29139baca6','e887c51e-afb9-48b1-b416-502a2357e621','Include default SIP processingMCP.xml',NULL,'2012-10-02 00:25:11'),('f8d0b7df-68e8-4214-a49d-60a91ed27029','9c84b047-9a6d-463f-9836-eafa49743b84',NULL,'Select pre-normalize file format identification command',NULL,'2013-11-07 22:51:42'),('f908bcd9-2fba-48c3-b04b-459f6ad1a4de','36b2e239-4a57-4aa5-8ebc-7a29139baca6','1aaa6e10-7907-4dea-a92a-dd0931eff226','Check for submission documentation',NULL,'2012-10-02 00:25:11'),('fa2307df-e42a-4553-aaf5-b08879b0cbf4','6f0b612c-867f-4dfd-8e43-5b35b7f882d7','42454e81-e776-44cc-ae9f-b40e7e5c7738','Set files to identify',NULL,'2013-11-07 22:51:43'),('fa3e0099-b891-43f6-a4bc-390d544fa3e9','61fb3874-8ef6-49d3-8a2d-3cb66e86a30c',NULL,'Approve DSpace transfer',NULL,'2012-10-02 00:25:11'),('fa61df3a-98a5-47e2-a5ce-281ae1c8c3c2','a6b1c323-7d36-428e-846a-e7e819423577','9e32257f-161e-430e-9412-07ce7f8db8ab','Identify file formats with Tika',NULL,'2013-11-07 22:51:35'),('faf6306b-76aa-415c-9087-16cc366ac6e7','a6b1c323-7d36-428e-846a-e7e819423577','36cc5356-6db1-4f3e-8155-1f92f958d2a4','Extract packages in metadata',NULL,'2013-02-13 22:03:39'),('fb55b404-90f5-45b6-a47c-ccfbd0de2401','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ad65bf76-3491-4c3d-afb0-acc94ff28bee','Sanitize file and directory names in submission documentation',NULL,'2012-10-02 00:25:11'),('fb64af31-8f8a-4fe5-a20d-27ee26c9dda2','01b748fe-2e9d-44e4-ae5d-113f74c9a0ba','ebab9878-f42e-4451-a24a-ec709889a858','Store AIP location',NULL,'2012-10-02 00:25:11'),('fbaadb5d-63f9-440c-a607-a4ebfb973a78','36b2e239-4a57-4aa5-8ebc-7a29139baca6','cf23dd75-d273-4c4e-8394-17622adf9bd6','Verify transfer compliance',NULL,'2012-10-02 00:25:11'),('fe354b27-dbb2-4454-9c1c-340d85e67b78','36b2e239-4a57-4aa5-8ebc-7a29139baca6','c15de53e-a5b2-41a1-9eee-1a7b4dd5447a','Remove preservation and access normalized files to renormalize.',NULL,'2012-10-24 00:40:06'),('feac0c04-3511-4e91-9403-5c569cff7bcc','a6b1c323-7d36-428e-846a-e7e819423577','179c8ce5-2b83-4ae2-9653-971e868fe183','Assign file UUIDs to objects',NULL,'2012-10-02 00:25:11'),('feb27f44-3575-4d17-8e00-43aa5dc5c3dc','36b2e239-4a57-4aa5-8ebc-7a29139baca6','ba937c55-6148-4f45-a9ad-9697c0cf11ed','Set bag file permissions',NULL,'2012-10-02 00:25:11'),('fecb3fe4-5c5c-4796-b9dc-c7d7cf33a9f3','a6b1c323-7d36-428e-846a-e7e819423577','2fdb8408-8bbb-45d1-846b-5e28bf220d5c','Scan for viruses in submission documentation',NULL,'2012-10-02 00:25:11'),('fedffebc-7292-4b94-b402-84628c4254de','a19bfd9f-9989-4648-9351-013a10b382ed','13d2adfc-8cb8-4206-bf70-04f031436ca2','Get list of collections on server',NULL,'2012-10-02 00:25:11'),('ff8f70b9-e345-4163-a784-29b432b12558','a6b1c323-7d36-428e-846a-e7e819423577','4f47371b-a69b-4a8a-87b5-01e7eb1628c3','Assign UUIDs to manual normalized preservation files',NULL,'2013-01-03 02:10:39');
/*!40000 ALTER TABLE `TasksConfigs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TasksConfigsAssignMagicLink`
--

DROP TABLE IF EXISTS `TasksConfigsAssignMagicLink`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TasksConfigsAssignMagicLink` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `execute` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `TasksConfigsAssignMagicLink` (`pk`),
  KEY `execute` (`execute`),
  CONSTRAINT `TasksConfigsAssignMagicLink_ibfk_1` FOREIGN KEY (`execute`) REFERENCES `MicroServiceChainLinks` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TasksConfigsAssignMagicLink`
--

LOCK TABLES `TasksConfigsAssignMagicLink` WRITE;
/*!40000 ALTER TABLE `TasksConfigsAssignMagicLink` DISABLE KEYS */;
INSERT INTO `TasksConfigsAssignMagicLink` VALUES ('1c460578-e696-4378-a5d1-63ee77dd18bc','f3a58cbb-20a8-4c6d-9ae4-1a5f02c1a28e',NULL,'2012-10-02 00:25:03'),('5057b0ce-a7f9-48c4-a7e9-65a7d88bb4ca','9fa0a0d1-25bb-4507-a5f7-f177d7fa920d',NULL,'2012-10-02 00:25:03'),('5975a5df-41af-4e3e-8e4e-ec7aff3ae085','19adb668-b19a-4fcb-8938-f49d7485eaf3',NULL,'2012-10-02 00:25:03'),('5dffcd9c-472d-44e0-ae4d-a30705cf80cd','755b4177-c587-41a7-8c52-015277568302',NULL,'2012-10-02 00:25:03'),('ae38e88c-3a61-4029-a7b4-af8f06b4265f','c73acd63-19c9-4ca8-912c-311107d0454e',NULL,'2012-10-23 19:41:25'),('c691548f-0131-4bd5-864c-364b1f7feb7f','5c459c1a-f998-404d-a0dd-808709510b72',NULL,'2012-10-02 00:25:03'),('ce2491ee-3d68-45a2-bb14-fd0b304c9891','f63970a2-dc63-4ab4-80a6-9bfd72e3cf5a',NULL,'2012-10-23 19:41:25'),('f1357379-0118-4f51-aa49-37aeb702b760','05f99ffd-abf2-4f5a-9ec8-f80a59967b89',NULL,'2012-10-02 00:25:03');
/*!40000 ALTER TABLE `TasksConfigsAssignMagicLink` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TasksConfigsSetUnitVariable`
--

DROP TABLE IF EXISTS `TasksConfigsSetUnitVariable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TasksConfigsSetUnitVariable` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `variable` longtext COLLATE utf8_unicode_ci,
  `variableValue` longtext COLLATE utf8_unicode_ci,
  `microServiceChainLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `createdTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`pk`),
  KEY `microServiceChainLink` (`microServiceChainLink`),
  CONSTRAINT `TasksConfigsSetUnitVariable_ibfk_1` FOREIGN KEY (`microServiceChainLink`) REFERENCES `MicroServiceChainLinks` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TasksConfigsSetUnitVariable`
--

LOCK TABLES `TasksConfigsSetUnitVariable` WRITE;
/*!40000 ALTER TABLE `TasksConfigsSetUnitVariable` DISABLE KEYS */;
INSERT INTO `TasksConfigsSetUnitVariable` VALUES ('1871a1a5-1937-4c4d-ab05-3b0c04a0bca1','resumeAfterNormalizationFileIdentificationToolSelected',NULL,'7509e7dc-1e1b-4dce-8d21-e130515fce73','2012-10-23 19:41:25','0000-00-00 00:00:00'),('202e00f4-595e-41fb-9a96-b8ec8c76318e','normalizationFileIdentificationToolIdentifierTypes','FileIDTypes.pk = \'16ae42ff-1018-4815-aac8-cceacd8d88a8\'',NULL,'2012-10-23 19:41:23','0000-00-00 00:00:00'),('4093954b-5e44-4fe9-9a47-14c82158a00d','normalizationFileIdentificationToolIdentifierTypes','FileIDTypes.pk = \'ac5d97dc-df9e-48b2-81c5-4a8b044355fa\' OR FileIDTypes.pk = \'f794555f-50ad-4fd4-9eab-67bc47c431ab\'',NULL,'2012-10-23 19:41:22','0000-00-00 00:00:00'),('42454e81-e776-44cc-ae9f-b40e7e5c7738','identifyFileFormat_v0.0','{\'filterSubDir\':\'objects/attachments\'}',NULL,'2013-11-07 22:51:43','0000-00-00 00:00:00'),('42e656d6-4816-417f-b45e-92dadd0dfde5','normalizationFileIdentificationToolIdentifierTypes','FileIDTypes.pk = \'1d8f3bb3-da8a-4ef6-bac7-b65942df83fc\'',NULL,'2012-10-23 19:41:24','0000-00-00 00:00:00'),('471ff5ad-1fd3-4540-9245-360cc8c9b389','normalizationFileIdentificationToolIdentifierTypes','FileIDTypes.pk = \'c26227f7-fca8-4d98-9d8e-cfab86a2dd0a\' OR FileIDTypes.pk = \'cff7437f-20c6-440a-b801-37c647da2cf1\'',NULL,'2012-10-23 19:41:24','0000-00-00 00:00:00'),('5035632e-7879-4ece-bf43-2fc253026ff5','returnFromManualNormalized',NULL,'77a7fa46-92b9-418e-aa88-fbedd4114c9f','2013-01-03 02:10:39','0000-00-00 00:00:00'),('65263ec0-f3ff-4fd5-9cd3-cf6f51ef92c7','fileIDcommand-transfer',NULL,'0e41c244-6c3e-46b9-a554-65e66e5c9324','2013-11-07 22:51:43','0000-00-00 00:00:00'),('6adccf2b-1c91-448b-bf0f-56414ee237ac','loadOptionsToCreateSIP',NULL,'16415d2f-5642-496d-a46d-00028ef6eb0a','2012-12-06 18:58:24','0000-00-00 00:00:00'),('6b4600f2-6df6-42cb-b611-32938b46a9cf','returnFromMetadataProcessing',NULL,'fa5b0c43-ed7b-4c7e-95a8-4f9ec7181260','2013-02-13 22:03:40','0000-00-00 00:00:00'),('6c02936d-552a-415e-b3c1-6d681b01d1c6','normalizationFileIdentificationToolIdentifierTypes','FileIDTypes.pk = \'8e39a076-d359-4c60-b6f4-38f7ae6adcdf\'',NULL,'2012-10-23 19:41:23','0000-00-00 00:00:00'),('76eaa4d2-fd4f-4741-b68c-df5b96ba81d1','reNormalize',NULL,'8ba83807-2832-4e41-843c-2e55ad10ea0b','2012-10-24 00:40:06','0000-00-00 00:00:00'),('771dd17a-02d1-403b-a761-c70cc9cc1d1a','returnFromMetadataProcessing',NULL,'75fb5d67-5efa-4232-b00b-d85236de0d3f','2013-02-13 22:03:40','0000-00-00 00:00:00'),('9329d1d8-03f9-4c5e-81ec-7010552d0a3e','normalizationFileIdentificationToolIdentifierTypes','FileIDTypes.pk = \'076cce1b-9b46-4343-a193-11c2662c9e02\' OR FileIDTypes.pk = \'237d393f-aba2-44ae-b61c-76232d383883\'',NULL,'2012-10-23 19:41:23','0000-00-00 00:00:00'),('95fb93a5-ef63-4ceb-8572-c0ddf88ef3ea','postApproveNormalizationLink',NULL,'0f0c1f33-29f2-49ae-b413-3e043da5df61','2013-11-07 22:51:35','0000-00-00 00:00:00'),('b5808a0f-e842-4820-837a-832d18398ebb','reNormalize',NULL,'8de9fe10-932f-4151-88b0-b50cf271e156','2012-10-24 00:40:07','0000-00-00 00:00:00'),('ba7bafe6-7241-4ffe-a0b8-97ca3c68eac1','returnFromManualNormalized',NULL,'25b5dc50-d42d-4ee2-91fc-5dcc3eef30a7','2013-11-07 22:51:35','0000-00-00 00:00:00'),('be6dda53-ef28-42dd-8452-e11734d57a91','normalizationFileIdentificationToolIdentifierTypes','FileIDTypes.pk = \'9ffdc6e8-f25a-4e5b-aaca-02769c4e7b7f\' ',NULL,'2012-10-23 19:41:23','0000-00-00 00:00:00'),('c26b2859-7a96-462f-880a-0cd8d1b0ac32','reNormalize',NULL,'f30b23d4-c8de-453d-9b92-50b86e21d3d5','2013-11-07 22:51:35','0000-00-00 00:00:00'),('d8e2c7b2-5452-4c26-b57a-04caafe9f95c','resumeAfterNormalizationFileIdentificationToolSelected',NULL,'4df4cc06-3b03-4c6f-b5c4-bec12a97dc90','2013-11-07 22:51:35','0000-00-00 00:00:00'),('ed98984f-69c5-45de-8a32-2c9ecf65e83f','postExtractSpecializedProcessing',NULL,'2fd123ea-196f-4c9c-95c0-117aa65ed9c6','2013-11-07 22:51:43','0000-00-00 00:00:00'),('f130c16d-d419-4063-8c8b-2e4c3ad138bb','normalizationFileIdentificationToolIdentifierTypes','FileIDTypes.pk = \'afdbee13-eec5-4182-8c6c-f5638ee290f3\'',NULL,'2012-10-23 19:41:23','0000-00-00 00:00:00'),('f226ecea-ae91-42d5-b039-39a1125b1c30','normalize_v1.0','{\'filterSubDir\':\'objects/attachments\'}',NULL,'2013-11-07 22:51:43','0000-00-00 00:00:00'),('f85bbe03-8aca-4211-99b7-ddb7dfb24da1','resumeAfterNormalizationFileIdentificationToolSelected',NULL,'cb8e5706-e73f-472f-ad9b-d1236af8095f','2012-10-23 19:41:25','0000-00-00 00:00:00'),('face6ee9-42d5-46ff-be1b-a645594b2da8','normalizationFileIdentificationToolIdentifierTypes','FileIDTypes.pk = \'b0bcccfb-04bc-4daa-a13c-77c23c2bda85\' OR FileIDTypes.pk = \'dc551ed2-9d2f-4c8a-acce-760fb740af48\'',NULL,'2012-10-23 19:41:23','0000-00-00 00:00:00'),('fc9f30bf-7f6e-4e62-9f99-689c8dc2e4ec','returnFromManualNormalized',NULL,'055de204-6229-4200-87f7-e3c29f095017','2013-01-03 02:10:40','0000-00-00 00:00:00');
/*!40000 ALTER TABLE `TasksConfigsSetUnitVariable` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TasksConfigsUnitVariableLinkPull`
--

DROP TABLE IF EXISTS `TasksConfigsUnitVariableLinkPull`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TasksConfigsUnitVariableLinkPull` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `variable` longtext COLLATE utf8_unicode_ci,
  `variableValue` longtext COLLATE utf8_unicode_ci,
  `defaultMicroServiceChainLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `createdTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`pk`),
  KEY `defaultMicroServiceChainLink` (`defaultMicroServiceChainLink`),
  CONSTRAINT `TasksConfigsUnitVariableLinkPull_ibfk_1` FOREIGN KEY (`defaultMicroServiceChainLink`) REFERENCES `MicroServiceChainLinks` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TasksConfigsUnitVariableLinkPull`
--

LOCK TABLES `TasksConfigsUnitVariableLinkPull` WRITE;
/*!40000 ALTER TABLE `TasksConfigsUnitVariableLinkPull` DISABLE KEYS */;
INSERT INTO `TasksConfigsUnitVariableLinkPull` VALUES ('003b52a6-f80a-409c-95f9-82dd770aa132','resumeAfterNormalizationFileIdentificationToolSelected',NULL,NULL,'2012-10-23 19:41:22','0000-00-00 00:00:00'),('11aef684-f2c7-494e-9763-277344e139bf','loadOptionsToCreateSIP',NULL,'bb194013-597c-4e4a-8493-b36d190f8717','2012-12-06 17:43:25','0000-00-00 00:00:00'),('49c816cd-b443-498f-9369-9274d060ddd3','returnFromMetadataProcessing',NULL,NULL,'2013-02-13 22:03:37','0000-00-00 00:00:00'),('49d853a9-646d-4e9f-b825-d1bcc3ba77f0','postExtractSpecializedProcessing',NULL,'eb52299b-9ae6-4a1f-831e-c7eee0de829f','2013-11-07 22:51:43','0000-00-00 00:00:00'),('65af383e-2153-4117-a2f9-bbe83358e54b','returnFromManualNormalized',NULL,NULL,'2013-01-03 02:10:38','0000-00-00 00:00:00'),('7477907c-79ec-4d48-93ae-9e0cbbfd2b65','postApproveNormalizationLink','','b443ba1a-a0b6-4f7c-aeb2-65bd83de5e8b','2013-11-07 22:51:35','0000-00-00 00:00:00'),('97ddf0be-7b07-48b1-82f6-6a3b49edde2b','fileIDcommand-transfer',NULL,'2522d680-c7d9-4d06-8b11-a28d8bd8a71f','2013-11-07 22:51:43','0000-00-00 00:00:00'),('e076e08f-5f14-4fc3-93d0-1e80ca727f34','postApproveNormalizationLink','','0b5ad647-5092-41ce-9fe5-1cc376d0bc3f','2013-11-07 22:51:35','0000-00-00 00:00:00'),('e56e168e-d339-45b4-bc2a-a3eb24390f0f','reNormalize',NULL,NULL,'2012-10-24 17:04:11','0000-00-00 00:00:00');
/*!40000 ALTER TABLE `TasksConfigsUnitVariableLinkPull` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Transfers`
--

DROP TABLE IF EXISTS `Transfers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Transfers` (
  `transferUUID` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `currentLocation` longtext COLLATE utf8_unicode_ci,
  `magicLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `magicLinkExitMessage` varchar(50) COLLATE utf8_unicode_ci DEFAULT 'Completed successfully',
  `type` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `accessionID` longtext COLLATE utf8_unicode_ci,
  `sourceOfAcquisition` longtext COLLATE utf8_unicode_ci,
  `typeOfTransfer` longtext COLLATE utf8_unicode_ci,
  `description` longtext COLLATE utf8_unicode_ci,
  `notes` longtext COLLATE utf8_unicode_ci,
  `hidden` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`transferUUID`),
  KEY `magicLink` (`magicLink`),
  CONSTRAINT `Transfers_ibfk_1` FOREIGN KEY (`magicLink`) REFERENCES `MicroServiceChainLinks` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Transfers`
--

LOCK TABLES `Transfers` WRITE;
/*!40000 ALTER TABLE `Transfers` DISABLE KEYS */;
/*!40000 ALTER TABLE `Transfers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UnitVariables`
--

DROP TABLE IF EXISTS `UnitVariables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `UnitVariables` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `unitType` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `unitUUID` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `variable` longtext COLLATE utf8_unicode_ci,
  `variableValue` longtext COLLATE utf8_unicode_ci,
  `microServiceChainLink` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `createdTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`pk`),
  KEY `microServiceChainLink` (`microServiceChainLink`),
  CONSTRAINT `UnitVariables_ibfk_1` FOREIGN KEY (`microServiceChainLink`) REFERENCES `MicroServiceChainLinks` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UnitVariables`
--

LOCK TABLES `UnitVariables` WRITE;
/*!40000 ALTER TABLE `UnitVariables` DISABLE KEYS */;
/*!40000 ALTER TABLE `UnitVariables` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `WatchedDirectories`
--

DROP TABLE IF EXISTS `WatchedDirectories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `WatchedDirectories` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `watchedDirectoryPath` longtext COLLATE utf8_unicode_ci,
  `chain` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `onlyActOnDirectories` tinyint(1) DEFAULT '1',
  `expectedType` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `WatchedDirectories` (`pk`),
  KEY `chain` (`chain`),
  KEY `expectedType` (`expectedType`),
  CONSTRAINT `WatchedDirectories_ibfk_1` FOREIGN KEY (`chain`) REFERENCES `MicroServiceChains` (`pk`),
  CONSTRAINT `WatchedDirectories_ibfk_2` FOREIGN KEY (`expectedType`) REFERENCES `WatchedDirectoriesExpectedTypes` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `WatchedDirectories`
--

LOCK TABLES `WatchedDirectories` WRITE;
/*!40000 ALTER TABLE `WatchedDirectories` DISABLE KEYS */;
INSERT INTO `WatchedDirectories` VALUES ('11a4f280-9b43-45a0-9ebd-ec7a115ccc62','%watchDirectoryPath%workFlowDecisions/selectFormatIDToolTransfer/','bd94cc9b-7990-45a2-a255-a1b70936f9f2',1,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2013-11-07 22:51:42'),('1caf28cd-95d5-437b-ac07-2171feb9e645','%watchDirectoryPath%activeTransfers/maildir','4171636c-e013-4ecc-ae45-60b5458c208b',1,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2012-10-02 00:25:12'),('1f49b5a3-58e9-4dfa-b3c8-45010a957146','%watchDirectoryPath%storeAIP/','6f0f35fb-6831-4842-9512-4a263700a29b',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2012-10-02 00:25:12'),('20e551b3-d8b9-47c9-b9cb-2c7b701fbca7','%watchDirectoryPath%activeTransfers/TRIM/','94f764ad-805a-4d4e-8a2b-a6f2515b30c7',1,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2012-11-30 19:55:49'),('2d9e4ca0-2d20-4c65-82cb-8ca23901fd5b','%watchDirectoryPath%approveNormalization/preservationAndAccess/','d7cf171e-82e8-4bbb-bc33-de6b8b256202',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2012-10-02 00:25:12'),('3132e312-aee3-46c1-a71d-eed431d7b563','%watchDirectoryPath%quarantined/','ad37288a-162c-4562-8532-eb4050964c73',1,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2012-10-02 00:25:12'),('31807189-05e5-4d5f-b31f-fa445c1b039a','%watchDirectoryPath%uploadDIP/','28a4322d-b8a5-4bae-b2dd-71cc9ff99e73',1,'907cbebd-78f5-4f79-a441-feac0ea119f7',NULL,'2012-10-02 00:25:12'),('4e3f8390-896d-4a46-9a20-6865c45bb8da','%watchDirectoryPath%system/autoRestructureForCompliance/','cc38912d-6520-44e1-92ff-76bb4881a55e',1,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2012-10-02 00:25:12'),('50c378ed-6a88-4988-bf21-abe1ea3e0115','%watchDirectoryPath%workFlowDecisions/selectFormatIDToolIngest/','0ea3a6f9-ff37-4f32-ac01-eec5393f008a',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2013-11-07 22:51:42'),('6b3f9acb-6567-408e-a0cf-5e02abf535c2','%watchDirectoryPath%SIPCreation/completedTransfers/','498795c7-06f2-4f3f-95bf-57f1b35964ad',1,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2012-10-02 00:25:12'),('77ac4a58-8b4f-4519-ad0a-1a35dedb47b4','%watchDirectoryPath%system/createDIPFromAIP/','9918b64c-b898-407b-bce4-a65aa3c11b89',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2013-11-07 22:51:35'),('88d93fa1-2cf2-4a47-b982-19721a697471','%watchDirectoryPath%workFlowDecisions/quarantineTransfer','7030f152-398a-470b-b045-f5dfa9013671',1,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2012-11-20 22:31:11'),('88f9c08e-ebc3-4334-9126-79d0489e8f39','%watchDirectoryPath%system/autoProcessSIP','fefdcee4-dd84-4b55-836f-99ef880ecdb6',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2012-10-02 00:25:12'),('94df8566-7337-48f1-b3f9-abcc9e52fa4a','%watchDirectoryPath%activeTransfers/baggitZippedDirectory','b0e0bf75-6b7e-44b6-a0d0-189eea7605dd',0,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2012-10-02 00:25:12'),('a68ef52c-0d44-4eeb-9c82-5bd9b253e7b6','%watchDirectoryPath%activeTransfers/standardTransfer','fffd5342-2337-463f-857a-b2c8c3778c6d',1,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2012-10-02 00:25:12'),('a9c1fb41-244c-410d-bef6-51cb48d975e2','%watchDirectoryPath%workFlowDecisions/selectNormalizationPath/','503d240c-c5a0-4bd5-a5f2-e3e44bd0018a',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2013-11-07 22:51:35'),('b33b9116-ea82-435c-8d1c-9b2d6d5331b5','%watchDirectoryPath%workFlowDecisions/createDip/','1ca0211c-05f9-4805-9119-d066e0bd1960',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2012-10-02 00:25:12'),('cb790b11-227a-4e9b-9a7f-e0db198036a4','%watchDirectoryPath%workFlowDecisions/selectFileIDTool/','b3b90ab1-39e2-4dea-84a7-34e4c3a13415',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2013-11-07 22:51:35'),('d1d46afd-8e1d-4c72-ae25-e2cea4cb8fa6','%watchDirectoryPath%activeTransfers/baggitDirectory','816f28cd-6af1-4d26-97f3-e61645eb881b',1,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2012-10-02 00:25:12'),('d91f3c5b-7936-4cf9-a702-117ec3e7e7d3','%watchDirectoryPath%SIPCreation/SIPsUnderConstruction','a2e19764-b373-4093-b0dd-11d61580f180',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2012-10-02 00:25:12'),('dfb22984-c6eb-4c5d-939c-0df43559033e','%watchDirectoryPath%workFlowDecisions/compressionAIPDecisions/','27cf6ca9-11b4-41ac-9014-f8018bcbad5e',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2013-11-07 22:51:34'),('e3b15e28-6370-42bf-a0e1-f61e4837a2a7','%watchDirectoryPath%activeTransfers/Dspace','55fa7084-3b64-48ca-be64-08949227f85d',1,'f9a3a93b-f184-4048-8072-115ffac06b5d',NULL,'2012-10-02 00:25:12'),('fb77de49-855d-4949-bb85-553b23cdc708','%watchDirectoryPath%approveNormalization/preservation/','39682d0c-8d81-4fdd-8e10-85114b9eb2dd',1,'76e66677-40e6-41da-be15-709afb334936',NULL,'2012-10-02 00:25:12');
/*!40000 ALTER TABLE `WatchedDirectories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `WatchedDirectoriesExpectedTypes`
--

DROP TABLE IF EXISTS `WatchedDirectoriesExpectedTypes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `WatchedDirectoriesExpectedTypes` (
  `pk` varchar(36) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `description` longtext COLLATE utf8_unicode_ci,
  `replaces` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `lastModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pk`),
  KEY `WatchedDirectoriesExpectedTypes` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `WatchedDirectoriesExpectedTypes`
--

LOCK TABLES `WatchedDirectoriesExpectedTypes` WRITE;
/*!40000 ALTER TABLE `WatchedDirectoriesExpectedTypes` DISABLE KEYS */;
INSERT INTO `WatchedDirectoriesExpectedTypes` VALUES ('76e66677-40e6-41da-be15-709afb334936','SIP',NULL,'2012-10-02 00:25:12'),('907cbebd-78f5-4f79-a441-feac0ea119f7','DIP',NULL,'2012-10-02 00:25:12'),('f9a3a93b-f184-4048-8072-115ffac06b5d','Transfer',NULL,'2012-10-02 00:25:12');
/*!40000 ALTER TABLE `WatchedDirectoriesExpectedTypes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `administration_archiviststoolkitconfig`
--

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

--
-- Dumping data for table `administration_archiviststoolkitconfig`
--

LOCK TABLES `administration_archiviststoolkitconfig` WRITE;
/*!40000 ALTER TABLE `administration_archiviststoolkitconfig` DISABLE KEYS */;
/*!40000 ALTER TABLE `administration_archiviststoolkitconfig` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `permission_id_refs_id_a7792de1` (`permission_id`),
  CONSTRAINT `group_id_refs_id_3cea63fe` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `permission_id_refs_id_a7792de1` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `message` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auth_message_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_9af0b65a` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_message`
--

LOCK TABLES `auth_message` WRITE;
/*!40000 ALTER TABLE `auth_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_e4470c6e` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_728de91f` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (22,'Can add api access',8,'add_apiaccess'),(23,'Can change api access',8,'change_apiaccess'),(24,'Can delete api access',8,'delete_apiaccess'),(25,'Can add api key',9,'add_apikey'),(26,'Can change api key',9,'change_apikey'),(27,'Can delete api key',9,'delete_apikey');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `first_name` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `last_name` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `email` varchar(75) COLLATE utf8_unicode_ci NOT NULL,
  `password` varchar(128) COLLATE utf8_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `group_id_refs_id_f0ee9890` (`group_id`),
  CONSTRAINT `group_id_refs_id_f0ee9890` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `user_id_refs_id_831107f1` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `permission_id_refs_id_67e79cb` (`permission_id`),
  CONSTRAINT `permission_id_refs_id_67e79cb` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `user_id_refs_id_f2045483` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `developmentAide_choicesDisplayed`
--

DROP TABLE IF EXISTS `developmentAide_choicesDisplayed`;
/*!50001 DROP VIEW IF EXISTS `developmentAide_choicesDisplayed`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `developmentAide_choicesDisplayed` (
  `pk` tinyint NOT NULL,
  `choiceAvailableAtLink` tinyint NOT NULL,
  `chainAvailable` tinyint NOT NULL,
  `replaces` tinyint NOT NULL,
  `lastModified` tinyint NOT NULL,
  `Text` tinyint NOT NULL,
  `Choice` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `app_label` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (8,'api access','tastypie','apiaccess'),(9,'api key','tastypie','apikey');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8_unicode_ci NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_c25c2c28` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fpr_format`
--

DROP TABLE IF EXISTS `fpr_format`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_format` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `description` varchar(128) COLLATE utf8_unicode_ci NOT NULL,
  `group_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `slug` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `group_id_refs_uuid_5f6777a9` (`group_id`),
  CONSTRAINT `group_id_refs_uuid_5f6777a9` FOREIGN KEY (`group_id`) REFERENCES `fpr_formatgroup` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fpr_format`
--

LOCK TABLES `fpr_format` WRITE;
/*!40000 ALTER TABLE `fpr_format` DISABLE KEYS */;
/*!40000 ALTER TABLE `fpr_format` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fpr_formatgroup`
--

DROP TABLE IF EXISTS `fpr_formatgroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_formatgroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `description` varchar(128) COLLATE utf8_unicode_ci NOT NULL,
  `slug` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fpr_formatgroup`
--

LOCK TABLES `fpr_formatgroup` WRITE;
/*!40000 ALTER TABLE `fpr_formatgroup` DISABLE KEYS */;
/*!40000 ALTER TABLE `fpr_formatgroup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fpr_formatversion`
--

DROP TABLE IF EXISTS `fpr_formatversion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_formatversion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `replaces_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `lastmodified` datetime NOT NULL,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `format_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `version` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `pronom_id` varchar(32) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` varchar(128) COLLATE utf8_unicode_ci DEFAULT NULL,
  `access_format` tinyint(1) NOT NULL,
  `preservation_format` tinyint(1) NOT NULL,
  `slug` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `format_id_refs_uuid_f14962b4` (`format_id`),
  KEY `replaces_id_refs_uuid_4a1558fd` (`replaces_id`),
  CONSTRAINT `replaces_id_refs_uuid_4a1558fd` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_formatversion` (`uuid`),
  CONSTRAINT `format_id_refs_uuid_f14962b4` FOREIGN KEY (`format_id`) REFERENCES `fpr_format` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fpr_formatversion`
--

LOCK TABLES `fpr_formatversion` WRITE;
/*!40000 ALTER TABLE `fpr_formatversion` DISABLE KEYS */;
/*!40000 ALTER TABLE `fpr_formatversion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fpr_fpcommand`
--

DROP TABLE IF EXISTS `fpr_fpcommand`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_fpcommand` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `replaces_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `lastmodified` datetime NOT NULL,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `tool_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` varchar(256) COLLATE utf8_unicode_ci NOT NULL,
  `command` longtext COLLATE utf8_unicode_ci NOT NULL,
  `script_type` varchar(16) COLLATE utf8_unicode_ci NOT NULL,
  `output_location` longtext COLLATE utf8_unicode_ci,
  `output_format_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `command_usage` varchar(16) COLLATE utf8_unicode_ci NOT NULL,
  `verification_command_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `event_detail_command_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `output_format_id_refs_uuid_e187d88f` (`output_format_id`),
  KEY `replaces_id_refs_uuid_bd1394fd` (`replaces_id`),
  KEY `verification_command_id_refs_uuid_bd1394fd` (`verification_command_id`),
  KEY `event_detail_command_id_refs_uuid_bd1394fd` (`event_detail_command_id`),
  KEY `tool_id_refs_uuid_38b1c33` (`tool_id`),
  CONSTRAINT `tool_id_refs_uuid_38b1c33` FOREIGN KEY (`tool_id`) REFERENCES `fpr_fptool` (`uuid`),
  CONSTRAINT `event_detail_command_id_refs_uuid_bd1394fd` FOREIGN KEY (`event_detail_command_id`) REFERENCES `fpr_fpcommand` (`uuid`),
  CONSTRAINT `output_format_id_refs_uuid_e187d88f` FOREIGN KEY (`output_format_id`) REFERENCES `fpr_formatversion` (`uuid`),
  CONSTRAINT `replaces_id_refs_uuid_bd1394fd` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_fpcommand` (`uuid`),
  CONSTRAINT `verification_command_id_refs_uuid_bd1394fd` FOREIGN KEY (`verification_command_id`) REFERENCES `fpr_fpcommand` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fpr_fpcommand`
--

LOCK TABLES `fpr_fpcommand` WRITE;
/*!40000 ALTER TABLE `fpr_fpcommand` DISABLE KEYS */;
/*!40000 ALTER TABLE `fpr_fpcommand` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fpr_fprule`
--

DROP TABLE IF EXISTS `fpr_fprule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_fprule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `replaces_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `lastmodified` datetime NOT NULL,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `purpose` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `command_id` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `format_id` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `count_attempts` int(11) NOT NULL,
  `count_okay` int(11) NOT NULL,
  `count_not_okay` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `format_id_refs_uuid_365f2da7` (`format_id`),
  KEY `replaces_id_refs_uuid_50262b13` (`replaces_id`),
  KEY `command_id_refs_uuid_37ce2045` (`command_id`),
  CONSTRAINT `command_id_refs_uuid_37ce2045` FOREIGN KEY (`command_id`) REFERENCES `fpr_fpcommand` (`uuid`),
  CONSTRAINT `format_id_refs_uuid_365f2da7` FOREIGN KEY (`format_id`) REFERENCES `fpr_formatversion` (`uuid`),
  CONSTRAINT `replaces_id_refs_uuid_50262b13` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_fprule` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fpr_fprule`
--

LOCK TABLES `fpr_fprule` WRITE;
/*!40000 ALTER TABLE `fpr_fprule` DISABLE KEYS */;
/*!40000 ALTER TABLE `fpr_fprule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fpr_fptool`
--

DROP TABLE IF EXISTS `fpr_fptool`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_fptool` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `description` varchar(256) COLLATE utf8_unicode_ci NOT NULL,
  `version` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `slug` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fpr_fptool`
--

LOCK TABLES `fpr_fptool` WRITE;
/*!40000 ALTER TABLE `fpr_fptool` DISABLE KEYS */;
/*!40000 ALTER TABLE `fpr_fptool` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fpr_idcommand`
--

DROP TABLE IF EXISTS `fpr_idcommand`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_idcommand` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `replaces_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `lastmodified` datetime NOT NULL,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `description` varchar(256) COLLATE utf8_unicode_ci NOT NULL,
  `config` varchar(4) COLLATE utf8_unicode_ci NOT NULL,
  `script` longtext COLLATE utf8_unicode_ci NOT NULL,
  `script_type` varchar(16) COLLATE utf8_unicode_ci NOT NULL,
  `tool_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `replaces_id_refs_uuid_dc5c8519` (`replaces_id`),
  KEY `tool_id_refs_uuid_8b5d5f5f` (`tool_id`),
  CONSTRAINT `tool_id_refs_uuid_8b5d5f5f` FOREIGN KEY (`tool_id`) REFERENCES `fpr_idtool` (`uuid`),
  CONSTRAINT `replaces_id_refs_uuid_dc5c8519` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_idcommand` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fpr_idcommand`
--

LOCK TABLES `fpr_idcommand` WRITE;
/*!40000 ALTER TABLE `fpr_idcommand` DISABLE KEYS */;
/*!40000 ALTER TABLE `fpr_idcommand` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fpr_idrule`
--

DROP TABLE IF EXISTS `fpr_idrule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_idrule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `replaces_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `lastmodified` datetime NOT NULL,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `command_id` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `format_id` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `command_output` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `format_id_refs_uuid_419026e2` (`format_id`),
  KEY `command_id_refs_uuid_9f407367` (`command_id`),
  KEY `replaces_id_refs_uuid_a57a01f5` (`replaces_id`),
  CONSTRAINT `replaces_id_refs_uuid_a57a01f5` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_idrule` (`uuid`),
  CONSTRAINT `command_id_refs_uuid_9f407367` FOREIGN KEY (`command_id`) REFERENCES `fpr_idcommand` (`uuid`),
  CONSTRAINT `format_id_refs_uuid_419026e2` FOREIGN KEY (`format_id`) REFERENCES `fpr_formatversion` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fpr_idrule`
--

LOCK TABLES `fpr_idrule` WRITE;
/*!40000 ALTER TABLE `fpr_idrule` DISABLE KEYS */;
/*!40000 ALTER TABLE `fpr_idrule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fpr_idtool`
--

DROP TABLE IF EXISTS `fpr_idtool`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_idtool` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `description` varchar(256) COLLATE utf8_unicode_ci NOT NULL,
  `version` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `slug` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fpr_idtool`
--

LOCK TABLES `fpr_idtool` WRITE;
/*!40000 ALTER TABLE `fpr_idtool` DISABLE KEYS */;
/*!40000 ALTER TABLE `fpr_idtool` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `jobDurationsView`
--

DROP TABLE IF EXISTS `jobDurationsView`;
/*!50001 DROP VIEW IF EXISTS `jobDurationsView`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `jobDurationsView` (
  `jobUUID` tinyint NOT NULL,
  `Time_spent_processing_in_seconds` tinyint NOT NULL,
  `Time_spent_processing` tinyint NOT NULL,
  `createdTime` tinyint NOT NULL,
  `createdTimeDec` tinyint NOT NULL,
  `startTime` tinyint NOT NULL,
  `endTime` tinyint NOT NULL,
  `time_from_start_of_processing_till_end_of_processing_in_seconds` tinyint NOT NULL,
  `time_from_job_created_till_start_of_processing_in_seconds` tinyint NOT NULL,
  `time_from_job_created_till_end_of_processing_in_seconds` tinyint NOT NULL,
  `jobType` tinyint NOT NULL,
  `directory` tinyint NOT NULL,
  `SIPUUID` tinyint NOT NULL,
  `unitType` tinyint NOT NULL,
  `currentStep` tinyint NOT NULL,
  `microserviceGroup` tinyint NOT NULL,
  `MicroServiceChainLinksPK` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `lastJobsInfo`
--

DROP TABLE IF EXISTS `lastJobsInfo`;
/*!50001 DROP VIEW IF EXISTS `lastJobsInfo`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `lastJobsInfo` (
  `Completed Tasks` tinyint NOT NULL,
  `min(startTime)` tinyint NOT NULL,
  `max(endTime)` tinyint NOT NULL,
  `Job duration` tinyint NOT NULL,
  `Time Since last return` tinyint NOT NULL,
  `AVG proc time` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `lastJobsTasks`
--

DROP TABLE IF EXISTS `lastJobsTasks`;
/*!50001 DROP VIEW IF EXISTS `lastJobsTasks`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `lastJobsTasks` (
  `taskUUID` tinyint NOT NULL,
  `jobUUID` tinyint NOT NULL,
  `createdTime` tinyint NOT NULL,
  `fileUUID` tinyint NOT NULL,
  `fileName` tinyint NOT NULL,
  `exec` tinyint NOT NULL,
  `arguments` tinyint NOT NULL,
  `startTime` tinyint NOT NULL,
  `client` tinyint NOT NULL,
  `endTime` tinyint NOT NULL,
  `stdOut` tinyint NOT NULL,
  `stdError` tinyint NOT NULL,
  `exitCode` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `processingDurationInformation`
--

DROP TABLE IF EXISTS `processingDurationInformation`;
/*!50001 DROP VIEW IF EXISTS `processingDurationInformation`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `processingDurationInformation` (
  `SIP_OR_TRANSFER_UUID` tinyint NOT NULL,
  `client` tinyint NOT NULL,
  `Time_spent_in_system` tinyint NOT NULL,
  `Time_spent_processing` tinyint NOT NULL,
  `Number_of_tasks` tinyint NOT NULL,
  `currentLocation` tinyint NOT NULL,
  `currentPath` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `processingDurationInformation2`
--

DROP TABLE IF EXISTS `processingDurationInformation2`;
/*!50001 DROP VIEW IF EXISTS `processingDurationInformation2`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `processingDurationInformation2` (
  `sipUUID` tinyint NOT NULL,
  `Time_spent_in_system` tinyint NOT NULL,
  `startedTime` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `processingDurationInformationByClient`
--

DROP TABLE IF EXISTS `processingDurationInformationByClient`;
/*!50001 DROP VIEW IF EXISTS `processingDurationInformationByClient`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `processingDurationInformationByClient` (
  `SIP_OR_TRANSFER_UUID` tinyint NOT NULL,
  `client` tinyint NOT NULL,
  `Time_spent_in_system` tinyint NOT NULL,
  `Time_spent_processing` tinyint NOT NULL,
  `Number_of_tasks` tinyint NOT NULL,
  `currentLocation` tinyint NOT NULL,
  `currentPath` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `south_migrationhistory`
--

DROP TABLE IF EXISTS `south_migrationhistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `south_migrationhistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_name` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `migration` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `applied` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `south_migrationhistory`
--

LOCK TABLES `south_migrationhistory` WRITE;
/*!40000 ALTER TABLE `south_migrationhistory` DISABLE KEYS */;
/*!40000 ALTER TABLE `south_migrationhistory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `taskDurationsView`
--

DROP TABLE IF EXISTS `taskDurationsView`;
/*!50001 DROP VIEW IF EXISTS `taskDurationsView`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `taskDurationsView` (
  `taskUUID` tinyint NOT NULL,
  `Time_spent_processing_in_seconds` tinyint NOT NULL,
  `Time_spent_processing` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `tastypie_apiaccess`
--

DROP TABLE IF EXISTS `tastypie_apiaccess`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tastypie_apiaccess` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `identifier` varchar(255) NOT NULL,
  `url` varchar(255) NOT NULL,
  `request_method` varchar(10) NOT NULL,
  `accessed` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tastypie_apiaccess`
--

LOCK TABLES `tastypie_apiaccess` WRITE;
/*!40000 ALTER TABLE `tastypie_apiaccess` DISABLE KEYS */;
/*!40000 ALTER TABLE `tastypie_apiaccess` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tastypie_apikey`
--

DROP TABLE IF EXISTS `tastypie_apikey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tastypie_apikey` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `key` varchar(256) NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `tastypie_apikey_45544485` (`key`),
  CONSTRAINT `user_id_refs_id_56bfdb62` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tastypie_apikey`
--

LOCK TABLES `tastypie_apikey` WRITE;
/*!40000 ALTER TABLE `tastypie_apikey` DISABLE KEYS */;
/*!40000 ALTER TABLE `tastypie_apikey` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `transfersAndSIPs`
--

DROP TABLE IF EXISTS `transfersAndSIPs`;
/*!50001 DROP VIEW IF EXISTS `transfersAndSIPs`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `transfersAndSIPs` (
  `unitUUID` tinyint NOT NULL,
  `unitType` tinyint NOT NULL,
  `currentLocation` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `FileExtensions`
--

/*!50001 DROP TABLE IF EXISTS `FileExtensions`*/;
/*!50001 DROP VIEW IF EXISTS `FileExtensions`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `FileExtensions` AS select `Files`.`fileUUID` AS `FileUUID`,substring_index(substring_index(`Files`.`currentLocation`,'/',-(1)),'.',-(1)) AS `extension` from `Files` where (`Files`.`removedTime` = 0) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `FilesByUnit`
--

/*!50001 DROP TABLE IF EXISTS `FilesByUnit`*/;
/*!50001 DROP VIEW IF EXISTS `FilesByUnit`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `FilesByUnit` AS select `Files`.`fileUUID` AS `fileUUID`,`Files`.`originalLocation` AS `originalLocation`,`Files`.`currentLocation` AS `currentLocation`,`Files`.`sipUUID` AS `unitUUID`,'SIP' AS `unitType`,`Files`.`removedTime` AS `removedTime`,`Files`.`enteredSystem` AS `enteredSystem`,`Files`.`fileSize` AS `fileSize`,`Files`.`checksum` AS `checksum`,`Files`.`fileGrpUse` AS `fileGrpUse`,`Files`.`fileGrpUUID` AS `fileGrpUUID`,`Files`.`label` AS `label` from `Files` union all select `Files`.`fileUUID` AS `fileUUID`,`Files`.`originalLocation` AS `originalLocation`,`Files`.`currentLocation` AS `currentLocation`,`Files`.`transferUUID` AS `unitUUID`,'Transfer' AS `unitType`,`Files`.`removedTime` AS `removedTime`,`Files`.`enteredSystem` AS `enteredSystem`,`Files`.`fileSize` AS `fileSize`,`Files`.`checksum` AS `checksum`,`Files`.`fileGrpUse` AS `fileGrpUse`,`Files`.`fileGrpUUID` AS `fileGrpUUID`,`Files`.`label` AS `label` from `Files` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `PDI_by_unit`
--

/*!50001 DROP TABLE IF EXISTS `PDI_by_unit`*/;
/*!50001 DROP VIEW IF EXISTS `PDI_by_unit`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `PDI_by_unit` AS select `processingDurationInformation`.`SIP_OR_TRANSFER_UUID` AS `SIP_OR_TRANSFER_UUID`,`FilesByUnit`.`unitType` AS `unitType`,sec_to_time(sum(time_to_sec(`processingDurationInformation`.`Time_spent_processing`))) AS `Total time processing`,`processingDurationInformation`.`Number_of_tasks` AS `Number_of_tasks`,sec_to_time((sum(time_to_sec(`processingDurationInformation`.`Time_spent_processing`)) / `processingDurationInformation`.`Number_of_tasks`)) AS `Average time per task`,sum(`FilesByUnit`.`fileSize`) AS `total file size`,count(`FilesByUnit`.`fileUUID`) AS `number of files`,count(distinct `FilesByUnit`.`fileUUID`) AS `count( DISTINCT  FilesByUnit.fileUUID)`,((sum(`FilesByUnit`.`fileSize`) / count(`FilesByUnit`.`fileUUID`)) / 1000) AS `average file size KB`,((sum(`FilesByUnit`.`fileSize`) / count(`FilesByUnit`.`fileUUID`)) / 1000000) AS `average file size MB`,sec_to_time((time_to_sec(sec_to_time((sum(time_to_sec(`processingDurationInformation`.`Time_spent_processing`)) / `processingDurationInformation`.`Number_of_tasks`))) / ((sum(`FilesByUnit`.`fileSize`) / count(`FilesByUnit`.`fileUUID`)) / 1000000))) AS `time per task per MB`,`processingDurationInformation`.`currentLocation` AS `currentLocation`,`processingDurationInformation`.`currentPath` AS `currentPath` from (`processingDurationInformation` join `FilesByUnit` on((`processingDurationInformation`.`SIP_OR_TRANSFER_UUID` = `FilesByUnit`.`unitUUID`))) group by `processingDurationInformation`.`SIP_OR_TRANSFER_UUID` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `developmentAide_choicesDisplayed`
--

/*!50001 DROP TABLE IF EXISTS `developmentAide_choicesDisplayed`*/;
/*!50001 DROP VIEW IF EXISTS `developmentAide_choicesDisplayed`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `developmentAide_choicesDisplayed` AS select `MicroServiceChainChoice`.`pk` AS `pk`,`MicroServiceChainChoice`.`choiceAvailableAtLink` AS `choiceAvailableAtLink`,`MicroServiceChainChoice`.`chainAvailable` AS `chainAvailable`,`MicroServiceChainChoice`.`replaces` AS `replaces`,`MicroServiceChainChoice`.`lastModified` AS `lastModified`,`TasksConfigs`.`description` AS `Text`,`MicroServiceChains`.`description` AS `Choice` from (((`MicroServiceChainChoice` join `MicroServiceChainLinks` on((`MicroServiceChainChoice`.`choiceAvailableAtLink` = `MicroServiceChainLinks`.`pk`))) join `TasksConfigs` on((`MicroServiceChainLinks`.`currentTask` = `TasksConfigs`.`pk`))) join `MicroServiceChains` on((`MicroServiceChainChoice`.`chainAvailable` = `MicroServiceChains`.`pk`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `jobDurationsView`
--

/*!50001 DROP TABLE IF EXISTS `jobDurationsView`*/;
/*!50001 DROP VIEW IF EXISTS `jobDurationsView`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `jobDurationsView` AS select `Jobs`.`jobUUID` AS `jobUUID`,sum(`taskDurationsView`.`Time_spent_processing_in_seconds`) AS `Time_spent_processing_in_seconds`,sec_to_time(sum(`taskDurationsView`.`Time_spent_processing_in_seconds`)) AS `Time_spent_processing`,`Jobs`.`createdTime` AS `createdTime`,`Jobs`.`createdTimeDec` AS `createdTimeDec`,min(`Tasks`.`startTime`) AS `startTime`,max(`Tasks`.`endTime`) AS `endTime`,(unix_timestamp(max(`Tasks`.`endTime`)) - unix_timestamp(min(`Tasks`.`startTime`))) AS `time_from_start_of_processing_till_end_of_processing_in_seconds`,(unix_timestamp(min(`Tasks`.`startTime`)) - unix_timestamp(`Jobs`.`createdTime`)) AS `time_from_job_created_till_start_of_processing_in_seconds`,(unix_timestamp(max(`Tasks`.`endTime`)) - unix_timestamp(`Jobs`.`createdTime`)) AS `time_from_job_created_till_end_of_processing_in_seconds`,`Jobs`.`jobType` AS `jobType`,`Jobs`.`directory` AS `directory`,`Jobs`.`SIPUUID` AS `SIPUUID`,`Jobs`.`unitType` AS `unitType`,`Jobs`.`currentStep` AS `currentStep`,`Jobs`.`microserviceGroup` AS `microserviceGroup`,`Jobs`.`MicroServiceChainLinksPK` AS `MicroServiceChainLinksPK` from ((`Jobs` join `Tasks` on((`Tasks`.`jobUUID` = `Jobs`.`jobUUID`))) join `taskDurationsView` on((`Tasks`.`taskUUID` = `taskDurationsView`.`taskUUID`))) group by `Jobs`.`jobUUID` order by sum(`taskDurationsView`.`Time_spent_processing_in_seconds`) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `lastJobsInfo`
--

/*!50001 DROP TABLE IF EXISTS `lastJobsInfo`*/;
/*!50001 DROP VIEW IF EXISTS `lastJobsInfo`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `lastJobsInfo` AS select count(`lastJobsTasks`.`taskUUID`) AS `Completed Tasks`,min(`lastJobsTasks`.`startTime`) AS `min(startTime)`,max(`lastJobsTasks`.`endTime`) AS `max(endTime)`,timediff(utc_timestamp(),min(`lastJobsTasks`.`startTime`)) AS `Job duration`,timediff(utc_timestamp(),max(`lastJobsTasks`.`endTime`)) AS `Time Since last return`,cast((timediff(utc_timestamp(),min(`lastJobsTasks`.`startTime`)) / count(`lastJobsTasks`.`taskUUID`)) as time) AS `AVG proc time` from `lastJobsTasks` where (`lastJobsTasks`.`startTime` <> 0) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `lastJobsTasks`
--

/*!50001 DROP TABLE IF EXISTS `lastJobsTasks`*/;
/*!50001 DROP VIEW IF EXISTS `lastJobsTasks`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `lastJobsTasks` AS select `Tasks`.`taskUUID` AS `taskUUID`,`Tasks`.`jobUUID` AS `jobUUID`,`Tasks`.`createdTime` AS `createdTime`,`Tasks`.`fileUUID` AS `fileUUID`,`Tasks`.`fileName` AS `fileName`,`Tasks`.`exec` AS `exec`,`Tasks`.`arguments` AS `arguments`,`Tasks`.`startTime` AS `startTime`,`Tasks`.`client` AS `client`,`Tasks`.`endTime` AS `endTime`,`Tasks`.`stdOut` AS `stdOut`,`Tasks`.`stdError` AS `stdError`,`Tasks`.`exitCode` AS `exitCode` from `Tasks` where (`Tasks`.`jobUUID` = (select `Jobs`.`jobUUID` from `Jobs` order by `Jobs`.`createdTime` desc,`Jobs`.`createdTimeDec` desc limit 1)) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `processingDurationInformation`
--

/*!50001 DROP TABLE IF EXISTS `processingDurationInformation`*/;
/*!50001 DROP VIEW IF EXISTS `processingDurationInformation`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `processingDurationInformation` AS select `Jobs`.`SIPUUID` AS `SIP_OR_TRANSFER_UUID`,`Tasks`.`client` AS `client`,`Durations`.`Time_spent_in_system` AS `Time_spent_in_system`,sec_to_time(sum((unix_timestamp(`Tasks`.`endTime`) - unix_timestamp(`Tasks`.`startTime`)))) AS `Time_spent_processing`,count(`Tasks`.`taskUUID`) AS `Number_of_tasks`,`Transfers`.`currentLocation` AS `currentLocation`,`SIPs`.`currentPath` AS `currentPath` from ((((`Tasks` join `Jobs` on((`Tasks`.`jobUUID` = `Jobs`.`jobUUID`))) left join `processingDurationInformation2` `Durations` on((`Jobs`.`SIPUUID` = `Durations`.`sipUUID`))) left join `Transfers` on((`Jobs`.`SIPUUID` = `Transfers`.`transferUUID`))) left join `SIPs` on((`Jobs`.`SIPUUID` = `SIPs`.`sipUUID`))) where ((`Tasks`.`endTime` <> 0) and (`Tasks`.`startTime` <> 0)) group by `Jobs`.`SIPUUID` order by `Durations`.`startedTime`,`Jobs`.`SIPUUID` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `processingDurationInformation2`
--

/*!50001 DROP TABLE IF EXISTS `processingDurationInformation2`*/;
/*!50001 DROP VIEW IF EXISTS `processingDurationInformation2`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `processingDurationInformation2` AS select `Jobs`.`SIPUUID` AS `sipUUID`,sec_to_time((max(unix_timestamp(`d`.`endTime`)) - min(unix_timestamp(`d`.`startTime`)))) AS `Time_spent_in_system`,min(unix_timestamp(`d`.`startTime`)) AS `startedTime` from (`Tasks` `d` join `Jobs` on((`d`.`jobUUID` = `Jobs`.`jobUUID`))) where ((`d`.`endTime` <> 0) and (`d`.`startTime` <> 0)) group by `Jobs`.`SIPUUID` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `processingDurationInformationByClient`
--

/*!50001 DROP TABLE IF EXISTS `processingDurationInformationByClient`*/;
/*!50001 DROP VIEW IF EXISTS `processingDurationInformationByClient`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `processingDurationInformationByClient` AS select `Jobs`.`SIPUUID` AS `SIP_OR_TRANSFER_UUID`,`Tasks`.`client` AS `client`,`Durations`.`Time_spent_in_system` AS `Time_spent_in_system`,sec_to_time(sum((unix_timestamp(`Tasks`.`endTime`) - unix_timestamp(`Tasks`.`startTime`)))) AS `Time_spent_processing`,count(`Tasks`.`taskUUID`) AS `Number_of_tasks`,`Transfers`.`currentLocation` AS `currentLocation`,`SIPs`.`currentPath` AS `currentPath` from ((((`Tasks` join `Jobs` on((`Tasks`.`jobUUID` = `Jobs`.`jobUUID`))) left join `processingDurationInformation2` `Durations` on((`Jobs`.`SIPUUID` = `Durations`.`sipUUID`))) left join `Transfers` on((`Jobs`.`SIPUUID` = `Transfers`.`transferUUID`))) left join `SIPs` on((`Jobs`.`SIPUUID` = `SIPs`.`sipUUID`))) where ((`Tasks`.`endTime` <> 0) and (`Tasks`.`startTime` <> 0)) group by `Tasks`.`client`,`Jobs`.`SIPUUID` order by `Durations`.`startedTime`,`Jobs`.`SIPUUID` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `taskDurationsView`
--

/*!50001 DROP TABLE IF EXISTS `taskDurationsView`*/;
/*!50001 DROP VIEW IF EXISTS `taskDurationsView`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `taskDurationsView` AS select `Tasks`.`taskUUID` AS `taskUUID`,(unix_timestamp(`Tasks`.`endTime`) - unix_timestamp(`Tasks`.`startTime`)) AS `Time_spent_processing_in_seconds`,sec_to_time((unix_timestamp(`Tasks`.`endTime`) - unix_timestamp(`Tasks`.`startTime`))) AS `Time_spent_processing` from `Tasks` order by (unix_timestamp(`Tasks`.`endTime`) - unix_timestamp(`Tasks`.`startTime`)) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `transfersAndSIPs`
--

/*!50001 DROP TABLE IF EXISTS `transfersAndSIPs`*/;
/*!50001 DROP VIEW IF EXISTS `transfersAndSIPs`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `transfersAndSIPs` AS select `SIPs`.`sipUUID` AS `unitUUID`,'SIP' AS `unitType`,`SIPs`.`currentPath` AS `currentLocation` from `SIPs` union all select `Transfers`.`transferUUID` AS `unitUUID`,'Transfer' AS `unitType`,`Transfers`.`currentLocation` AS `currentLocation` from `Transfers` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-11-14 16:39:10
