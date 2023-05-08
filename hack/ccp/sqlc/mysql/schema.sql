-- MySQL dump 10.13  Distrib 5.6.51-91.0, for Linux (x86_64)
--
-- Host: localhost    Database: MCP
-- ------------------------------------------------------
-- Server version	5.6.51-91.0

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

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Accesses` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `SIPUUID` varchar(36) NOT NULL,
  `resource` longtext NOT NULL,
  `target` longtext NOT NULL,
  `status` longtext NOT NULL,
  `statusCode` smallint(5) unsigned DEFAULT NULL,
  `exitCode` smallint(5) unsigned DEFAULT NULL,
  `createdTime` datetime(6) NOT NULL,
  `updatedTime` datetime(6) NOT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Agents`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Agents` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `agentIdentifierType` longtext,
  `agentIdentifierValue` longtext,
  `agentName` longtext,
  `agentType` longtext NOT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ArchivesSpaceDIPObjectResourcePairing`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ArchivesSpaceDIPObjectResourcePairing` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `dipUUID` varchar(50) NOT NULL,
  `fileUUID` varchar(50) NOT NULL,
  `resourceId` varchar(150) NOT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DashboardSettings`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DashboardSettings` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `value` longtext NOT NULL,
  `lastModified` datetime(6) NOT NULL,
  `scope` varchar(255) NOT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB AUTO_INCREMENT=89 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Derivations`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Derivations` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `derivedFileUUID` varchar(36) NOT NULL,
  `relatedEventUUID` varchar(36) DEFAULT NULL,
  `sourceFileUUID` varchar(36) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `Derivations_derivedFileUUID_4fa7e340_fk_Files_fileUUID` (`derivedFileUUID`),
  KEY `Derivations_relatedEventUUID_accc6f05_fk_Events_ev` (`relatedEventUUID`),
  KEY `Derivations_sourceFileUUID_ebf65ffc_fk_Files_fileUUID` (`sourceFileUUID`),
  CONSTRAINT `Derivations_derivedFileUUID_4fa7e340_fk_Files_fileUUID` FOREIGN KEY (`derivedFileUUID`) REFERENCES `Files` (`fileUUID`),
  CONSTRAINT `Derivations_relatedEventUUID_accc6f05_fk_Events_ev` FOREIGN KEY (`relatedEventUUID`) REFERENCES `Events` (`eventIdentifierUUID`),
  CONSTRAINT `Derivations_sourceFileUUID_ebf65ffc_fk_Files_fileUUID` FOREIGN KEY (`sourceFileUUID`) REFERENCES `Files` (`fileUUID`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Directories`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Directories` (
  `directoryUUID` varchar(36) NOT NULL,
  `originalLocation` longblob NOT NULL,
  `currentLocation` longblob,
  `enteredSystem` datetime(6) NOT NULL,
  `sipUUID` varchar(36) DEFAULT NULL,
  `transferUUID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`directoryUUID`),
  KEY `Directories_sipUUID_0d5c10c0_fk_SIPs_sipUUID` (`sipUUID`),
  KEY `Directories_transferUUID_5626ef17_fk_Transfers_transferUUID` (`transferUUID`),
  CONSTRAINT `Directories_sipUUID_0d5c10c0_fk_SIPs_sipUUID` FOREIGN KEY (`sipUUID`) REFERENCES `SIPs` (`sipUUID`),
  CONSTRAINT `Directories_transferUUID_5626ef17_fk_Transfers_transferUUID` FOREIGN KEY (`transferUUID`) REFERENCES `Transfers` (`transferUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Directories_identifiers`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Directories_identifiers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `directory_id` varchar(36) NOT NULL,
  `identifier_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `Directories_identifiers_directory_id_identifier_id_3245fda2_uniq` (`directory_id`,`identifier_id`),
  KEY `Directories_identifiers_identifier_id_0d71df00_fk_Identifiers_pk` (`identifier_id`),
  CONSTRAINT `Directories_identifi_directory_id_8d95c9da_fk_Directori` FOREIGN KEY (`directory_id`) REFERENCES `Directories` (`directoryUUID`),
  CONSTRAINT `Directories_identifiers_identifier_id_0d71df00_fk_Identifiers_pk` FOREIGN KEY (`identifier_id`) REFERENCES `Identifiers` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Dublincore`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Dublincore` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `metadataAppliesToidentifier` varchar(36) DEFAULT NULL,
  `title` longtext NOT NULL,
  `isPartOf` longtext NOT NULL,
  `creator` longtext NOT NULL,
  `subject` longtext NOT NULL,
  `description` longtext NOT NULL,
  `publisher` longtext NOT NULL,
  `contributor` longtext NOT NULL,
  `date` longtext NOT NULL,
  `type` longtext NOT NULL,
  `format` longtext NOT NULL,
  `identifier` longtext NOT NULL,
  `source` longtext NOT NULL,
  `relation` longtext NOT NULL,
  `language` longtext NOT NULL,
  `coverage` longtext NOT NULL,
  `rights` longtext NOT NULL,
  `metadataAppliesToType` varchar(36) NOT NULL,
  `status` varchar(8) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `Dublincore_metadataAppliesToTyp_bff534e2_fk_MetadataA` (`metadataAppliesToType`),
  CONSTRAINT `Dublincore_metadataAppliesToTyp_bff534e2_fk_MetadataA` FOREIGN KEY (`metadataAppliesToType`) REFERENCES `MetadataAppliesToTypes` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Events`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Events` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `eventIdentifierUUID` varchar(36) DEFAULT NULL,
  `eventType` longtext NOT NULL,
  `eventDateTime` datetime(6) NOT NULL,
  `eventDetail` longtext NOT NULL,
  `eventOutcome` longtext NOT NULL,
  `eventOutcomeDetailNote` longtext NOT NULL,
  `fileUUID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`pk`),
  UNIQUE KEY `eventIdentifierUUID` (`eventIdentifierUUID`),
  KEY `Events_fileUUID_4dfdc63a` (`fileUUID`),
  CONSTRAINT `Events_fileUUID_4dfdc63a_fk_Files_fileUUID` FOREIGN KEY (`fileUUID`) REFERENCES `Files` (`fileUUID`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Events_agents`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Events_agents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `event_id` int(11) NOT NULL,
  `agent_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `Events_agents_event_id_agent_id_98c0ada6_uniq` (`event_id`,`agent_id`),
  KEY `Events_agents_agent_id_44e0d65c_fk_Agents_pk` (`agent_id`),
  CONSTRAINT `Events_agents_agent_id_44e0d65c_fk_Agents_pk` FOREIGN KEY (`agent_id`) REFERENCES `Agents` (`pk`),
  CONSTRAINT `Events_agents_event_id_de9a7d30_fk_Events_pk` FOREIGN KEY (`event_id`) REFERENCES `Events` (`pk`)
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Files`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Files` (
  `fileUUID` varchar(36) NOT NULL,
  `originalLocation` longblob NOT NULL,
  `currentLocation` longblob,
  `fileGrpUse` varchar(50) NOT NULL,
  `fileGrpUUID` varchar(36) NOT NULL,
  `checksum` varchar(128) NOT NULL,
  `fileSize` bigint(20) DEFAULT NULL,
  `label` longtext NOT NULL,
  `enteredSystem` datetime(6) NOT NULL,
  `removedTime` datetime(6) DEFAULT NULL,
  `sipUUID` varchar(36) DEFAULT NULL,
  `transferUUID` varchar(36) DEFAULT NULL,
  `checksumType` varchar(36) NOT NULL,
  `modificationTime` datetime(6),
  PRIMARY KEY (`fileUUID`),
  KEY `Files_sipUUID_acd24128` (`sipUUID`),
  KEY `Files_transferUUID_53e2d862` (`transferUUID`),
  KEY `Files_sipUUID_fileGrpUse_390d13ef_idx` (`sipUUID`,`fileGrpUse`),
  KEY `Files_transfer_lvrgv3pn_idx` (`transferUUID`,`currentLocation`(767)),
  KEY `Files_transfer_bru5if1u_idx` (`transferUUID`,`originalLocation`(767)),
  KEY `Files_sip_1x6rkqbm_idx` (`sipUUID`,`currentLocation`(767)),
  KEY `Files_sip_orpn8lfh_idx` (`sipUUID`,`originalLocation`(767)),
  CONSTRAINT `Files_sipUUID_acd24128_fk_SIPs_sipUUID` FOREIGN KEY (`sipUUID`) REFERENCES `SIPs` (`sipUUID`),
  CONSTRAINT `Files_transferUUID_53e2d862_fk_Transfers_transferUUID` FOREIGN KEY (`transferUUID`) REFERENCES `Transfers` (`transferUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `FilesIDs`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FilesIDs` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `formatName` longtext NOT NULL,
  `formatVersion` longtext NOT NULL,
  `formatRegistryName` longtext NOT NULL,
  `formatRegistryKey` longtext NOT NULL,
  `fileUUID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `FilesIDs_fileUUID_3f4abbb5_fk_Files_fileUUID` (`fileUUID`),
  CONSTRAINT `FilesIDs_fileUUID_3f4abbb5_fk_Files_fileUUID` FOREIGN KEY (`fileUUID`) REFERENCES `Files` (`fileUUID`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `FilesIdentifiedIDs`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FilesIdentifiedIDs` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `fileUUID` varchar(36) NOT NULL,
  `fileID` varchar(36) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `FilesIdentifiedIDs_fileUUID_fe2d5360_fk_Files_fileUUID` (`fileUUID`),
  KEY `FilesIdentifiedIDs_fileID_93673942_fk_fpr_formatversion_uuid` (`fileID`),
  CONSTRAINT `FilesIdentifiedIDs_fileID_93673942_fk_fpr_formatversion_uuid` FOREIGN KEY (`fileID`) REFERENCES `fpr_formatversion` (`uuid`),
  CONSTRAINT `FilesIdentifiedIDs_fileUUID_fe2d5360_fk_Files_fileUUID` FOREIGN KEY (`fileUUID`) REFERENCES `Files` (`fileUUID`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Files_identifiers`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Files_identifiers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `file_id` varchar(36) NOT NULL,
  `identifier_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `Files_identifiers_file_id_identifier_id_73602c95_uniq` (`file_id`,`identifier_id`),
  KEY `Files_identifiers_identifier_id_344a1623_fk_Identifiers_pk` (`identifier_id`),
  CONSTRAINT `Files_identifiers_file_id_970f8b01_fk_Files_fileUUID` FOREIGN KEY (`file_id`) REFERENCES `Files` (`fileUUID`),
  CONSTRAINT `Files_identifiers_identifier_id_344a1623_fk_Identifiers_pk` FOREIGN KEY (`identifier_id`) REFERENCES `Identifiers` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Identifiers`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Identifiers` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `type` longtext,
  `value` longtext,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Jobs`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Jobs` (
  `jobUUID` varchar(36) NOT NULL,
  `jobType` varchar(250) NOT NULL,
  `createdTime` datetime(6) NOT NULL,
  `createdTimeDec` decimal(26,10) NOT NULL,
  `directory` longtext NOT NULL,
  `SIPUUID` varchar(36) NOT NULL,
  `unitType` varchar(50) NOT NULL,
  `currentStep` int(11) NOT NULL,
  `microserviceGroup` varchar(50) NOT NULL,
  `hidden` tinyint(1) NOT NULL,
  `subJobOf` varchar(36) NOT NULL,
  `MicroServiceChainLinksPK` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`jobUUID`),
  KEY `Jobs_SIPUUID_246989a2` (`SIPUUID`),
  KEY `Jobs_jobType_currentStep_797e7bb4_idx` (`jobType`,`currentStep`),
  KEY `Jobs_SIPUUID_currentStep_micro_2638efea_idx` (`SIPUUID`,`currentStep`,`microserviceGroup`,`MicroServiceChainLinksPK`),
  KEY `Jobs_SIPUUID_jobType_createdTime_createdTimeDec_b3e1c90a_idx` (`SIPUUID`,`jobType`,`createdTime`,`createdTimeDec`),
  KEY `Jobs_SIPUUID_createdTime_createdTimeDec_f3e10445_idx` (`SIPUUID`,`createdTime`,`createdTimeDec`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `MetadataAppliesToTypes`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MetadataAppliesToTypes` (
  `pk` varchar(36) NOT NULL,
  `description` varchar(50) NOT NULL,
  `replaces` varchar(36) DEFAULT NULL,
  `lastModified` datetime(6) NOT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Reports`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Reports` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `unitType` varchar(50) NOT NULL,
  `unitName` varchar(50) NOT NULL,
  `unitIdentifier` varchar(36) NOT NULL,
  `content` longtext NOT NULL,
  `created` datetime(6) NOT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatement`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatement` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `metadataAppliesToidentifier` varchar(36) NOT NULL,
  `rightsStatementIdentifierType` longtext NOT NULL,
  `rightsStatementIdentifierValue` longtext NOT NULL,
  `fkAgent` int(11) NOT NULL,
  `rightsBasis` varchar(64) NOT NULL,
  `metadataAppliesToType` varchar(36) NOT NULL,
  `status` varchar(8) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatement_metadataAppliesToTyp_3b36207a_fk_MetadataA` (`metadataAppliesToType`),
  CONSTRAINT `RightsStatement_metadataAppliesToTyp_3b36207a_fk_MetadataA` FOREIGN KEY (`metadataAppliesToType`) REFERENCES `MetadataAppliesToTypes` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementCopyright`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementCopyright` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `copyrightStatus` longtext NOT NULL,
  `copyrightJurisdiction` longtext NOT NULL,
  `copyrightStatusDeterminationDate` longtext,
  `copyrightApplicableStartDate` longtext,
  `copyrightApplicableEndDate` longtext,
  `copyrightApplicableEndDateOpen` tinyint(1) NOT NULL,
  `fkRightsStatement` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementCopyr_fkRightsStatement_e733e20a_fk_RightsSta` (`fkRightsStatement`),
  CONSTRAINT `RightsStatementCopyr_fkRightsStatement_e733e20a_fk_RightsSta` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementCopyrightDocumentationIdentifier`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementCopyrightDocumentationIdentifier` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `copyrightDocumentationIdentifierType` longtext NOT NULL,
  `copyrightDocumentationIdentifierValue` longtext NOT NULL,
  `copyrightDocumentationIdentifierRole` longtext,
  `fkRightsStatementCopyrightInformation` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementCopyr_fkRightsStatementCop_df6428ca_fk_RightsSta` (`fkRightsStatementCopyrightInformation`),
  CONSTRAINT `RightsStatementCopyr_fkRightsStatementCop_df6428ca_fk_RightsSta` FOREIGN KEY (`fkRightsStatementCopyrightInformation`) REFERENCES `RightsStatementCopyright` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementCopyrightNote`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementCopyrightNote` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `copyrightNote` longtext NOT NULL,
  `fkRightsStatementCopyrightInformation` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementCopyr_fkRightsStatementCop_70c3c471_fk_RightsSta` (`fkRightsStatementCopyrightInformation`),
  CONSTRAINT `RightsStatementCopyr_fkRightsStatementCop_70c3c471_fk_RightsSta` FOREIGN KEY (`fkRightsStatementCopyrightInformation`) REFERENCES `RightsStatementCopyright` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementLicense`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementLicense` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `licenseTerms` longtext,
  `licenseApplicableStartDate` longtext,
  `licenseApplicableEndDate` longtext,
  `licenseApplicableEndDateOpen` tinyint(1) NOT NULL,
  `fkRightsStatement` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementLicen_fkRightsStatement_1485f9e6_fk_RightsSta` (`fkRightsStatement`),
  CONSTRAINT `RightsStatementLicen_fkRightsStatement_1485f9e6_fk_RightsSta` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementLicenseDocumentationIdentifier`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementLicenseDocumentationIdentifier` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `licenseDocumentationIdentifierType` longtext NOT NULL,
  `licenseDocumentationIdentifierValue` longtext NOT NULL,
  `licenseDocumentationIdentifierRole` longtext,
  `fkRightsStatementLicense` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementLicen_fkRightsStatementLic_da69b228_fk_RightsSta` (`fkRightsStatementLicense`),
  CONSTRAINT `RightsStatementLicen_fkRightsStatementLic_da69b228_fk_RightsSta` FOREIGN KEY (`fkRightsStatementLicense`) REFERENCES `RightsStatementLicense` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementLicenseNote`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementLicenseNote` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `licenseNote` longtext NOT NULL,
  `fkRightsStatementLicense` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementLicen_fkRightsStatementLic_c462b397_fk_RightsSta` (`fkRightsStatementLicense`),
  CONSTRAINT `RightsStatementLicen_fkRightsStatementLic_c462b397_fk_RightsSta` FOREIGN KEY (`fkRightsStatementLicense`) REFERENCES `RightsStatementLicense` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementLinkingAgentIdentifier`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementLinkingAgentIdentifier` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `linkingAgentIdentifierType` longtext NOT NULL,
  `linkingAgentIdentifierValue` longtext NOT NULL,
  `fkRightsStatement` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementLinki_fkRightsStatement_7e98c246_fk_RightsSta` (`fkRightsStatement`),
  CONSTRAINT `RightsStatementLinki_fkRightsStatement_7e98c246_fk_RightsSta` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementOtherRightsDocumentationIdentifier`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementOtherRightsDocumentationIdentifier` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `otherRightsDocumentationIdentifierType` longtext NOT NULL,
  `otherRightsDocumentationIdentifierValue` longtext NOT NULL,
  `otherRightsDocumentationIdentifierRole` longtext,
  `fkRightsStatementOtherRightsInformation` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementOther_fkRightsStatementOth_0b14dc08_fk_RightsSta` (`fkRightsStatementOtherRightsInformation`),
  CONSTRAINT `RightsStatementOther_fkRightsStatementOth_0b14dc08_fk_RightsSta` FOREIGN KEY (`fkRightsStatementOtherRightsInformation`) REFERENCES `RightsStatementOtherRightsInformation` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementOtherRightsInformation`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementOtherRightsInformation` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `otherRightsBasis` longtext NOT NULL,
  `otherRightsApplicableStartDate` longtext,
  `otherRightsApplicableEndDate` longtext,
  `otherRightsApplicableEndDateOpen` tinyint(1) NOT NULL,
  `fkRightsStatement` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementOther_fkRightsStatement_381a36ed_fk_RightsSta` (`fkRightsStatement`),
  CONSTRAINT `RightsStatementOther_fkRightsStatement_381a36ed_fk_RightsSta` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementOtherRightsNote`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementOtherRightsNote` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `otherRightsNote` longtext NOT NULL,
  `fkRightsStatementOtherRightsInformation` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementOther_fkRightsStatementOth_397f479e_fk_RightsSta` (`fkRightsStatementOtherRightsInformation`),
  CONSTRAINT `RightsStatementOther_fkRightsStatementOth_397f479e_fk_RightsSta` FOREIGN KEY (`fkRightsStatementOtherRightsInformation`) REFERENCES `RightsStatementOtherRightsInformation` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementRightsGranted`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementRightsGranted` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `act` longtext NOT NULL,
  `startDate` longtext,
  `endDate` longtext,
  `endDateOpen` tinyint(1) NOT NULL,
  `fkRightsStatement` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementRight_fkRightsStatement_8c23435c_fk_RightsSta` (`fkRightsStatement`),
  CONSTRAINT `RightsStatementRight_fkRightsStatement_8c23435c_fk_RightsSta` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementRightsGrantedNote`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementRightsGrantedNote` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `rightsGrantedNote` longtext NOT NULL,
  `fkRightsStatementRightsGranted` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementRight_fkRightsStatementRig_4ffcc7db_fk_RightsSta` (`fkRightsStatementRightsGranted`),
  CONSTRAINT `RightsStatementRight_fkRightsStatementRig_4ffcc7db_fk_RightsSta` FOREIGN KEY (`fkRightsStatementRightsGranted`) REFERENCES `RightsStatementRightsGranted` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementRightsGrantedRestriction`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementRightsGrantedRestriction` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `restriction` longtext NOT NULL,
  `fkRightsStatementRightsGranted` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementRight_fkRightsStatementRig_03b70842_fk_RightsSta` (`fkRightsStatementRightsGranted`),
  CONSTRAINT `RightsStatementRight_fkRightsStatementRig_03b70842_fk_RightsSta` FOREIGN KEY (`fkRightsStatementRightsGranted`) REFERENCES `RightsStatementRightsGranted` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementStatuteDocumentationIdentifier`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementStatuteDocumentationIdentifier` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `statuteDocumentationIdentifierType` longtext NOT NULL,
  `statuteDocumentationIdentifierValue` longtext NOT NULL,
  `statuteDocumentationIdentifierRole` longtext,
  `fkRightsStatementStatuteInformation` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementStatu_fkRightsStatementSta_138e76a0_fk_RightsSta` (`fkRightsStatementStatuteInformation`),
  CONSTRAINT `RightsStatementStatu_fkRightsStatementSta_138e76a0_fk_RightsSta` FOREIGN KEY (`fkRightsStatementStatuteInformation`) REFERENCES `RightsStatementStatuteInformation` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementStatuteInformation`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementStatuteInformation` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `statuteJurisdiction` longtext NOT NULL,
  `statuteCitation` longtext NOT NULL,
  `statuteInformationDeterminationDate` longtext,
  `statuteApplicableStartDate` longtext,
  `statuteApplicableEndDate` longtext,
  `statuteApplicableEndDateOpen` tinyint(1) NOT NULL,
  `fkRightsStatement` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementStatu_fkRightsStatement_db62cdbd_fk_RightsSta` (`fkRightsStatement`),
  CONSTRAINT `RightsStatementStatu_fkRightsStatement_db62cdbd_fk_RightsSta` FOREIGN KEY (`fkRightsStatement`) REFERENCES `RightsStatement` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RightsStatementStatuteInformationNote`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RightsStatementStatuteInformationNote` (
  `pk` int(11) NOT NULL AUTO_INCREMENT,
  `statuteNote` longtext NOT NULL,
  `fkRightsStatementStatuteInformation` int(11) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `RightsStatementStatu_fkRightsStatementSta_1abec46b_fk_RightsSta` (`fkRightsStatementStatuteInformation`),
  CONSTRAINT `RightsStatementStatu_fkRightsStatementSta_1abec46b_fk_RightsSta` FOREIGN KEY (`fkRightsStatementStatuteInformation`) REFERENCES `RightsStatementStatuteInformation` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SIPs`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SIPs` (
  `sipUUID` varchar(36) NOT NULL,
  `createdTime` datetime(6) NOT NULL,
  `currentPath` longtext,
  `hidden` tinyint(1) NOT NULL,
  `aipFilename` longtext,
  `sipType` varchar(8) NOT NULL,
  `dirUUIDs` tinyint(1) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `status` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`sipUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SIPs_identifiers`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SIPs_identifiers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sip_id` varchar(36) NOT NULL,
  `identifier_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `SIPs_identifiers_sip_id_identifier_id_902dc346_uniq` (`sip_id`,`identifier_id`),
  KEY `SIPs_identifiers_identifier_id_f5b9f178_fk_Identifiers_pk` (`identifier_id`),
  CONSTRAINT `SIPs_identifiers_identifier_id_f5b9f178_fk_Identifiers_pk` FOREIGN KEY (`identifier_id`) REFERENCES `Identifiers` (`pk`),
  CONSTRAINT `SIPs_identifiers_sip_id_de813f60_fk_SIPs_sipUUID` FOREIGN KEY (`sip_id`) REFERENCES `SIPs` (`sipUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tasks`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tasks` (
  `taskUUID` varchar(36) NOT NULL,
  `createdTime` datetime(6) NOT NULL,
  `fileUUID` varchar(36) DEFAULT NULL,
  `fileName` longtext NOT NULL,
  `exec` varchar(250) NOT NULL,
  `arguments` varchar(1000) NOT NULL,
  `startTime` datetime(6) DEFAULT NULL,
  `endTime` datetime(6) DEFAULT NULL,
  `client` varchar(50) NOT NULL,
  `stdOut` longtext NOT NULL,
  `stdError` longtext NOT NULL,
  `exitCode` bigint(20) DEFAULT NULL,
  `jobuuid` varchar(36) NOT NULL,
  PRIMARY KEY (`taskUUID`),
  KEY `Tasks_jobuuid_458e89f7_fk_Jobs_jobUUID` (`jobuuid`),
  CONSTRAINT `Tasks_jobuuid_458e89f7_fk_Jobs_jobUUID` FOREIGN KEY (`jobuuid`) REFERENCES `Jobs` (`jobUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Taxonomies`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Taxonomies` (
  `pk` varchar(36) NOT NULL,
  `createdTime` datetime(6) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `type` varchar(50) NOT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TaxonomyTerms`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TaxonomyTerms` (
  `pk` varchar(36) NOT NULL,
  `createdTime` datetime(6) DEFAULT NULL,
  `term` varchar(255) NOT NULL,
  `taxonomyUUID` varchar(36) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `TaxonomyTerms_taxonomyUUID_abc1931b_fk_Taxonomies_pk` (`taxonomyUUID`),
  CONSTRAINT `TaxonomyTerms_taxonomyUUID_abc1931b_fk_Taxonomies_pk` FOREIGN KEY (`taxonomyUUID`) REFERENCES `Taxonomies` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TransferMetadataFieldValues`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TransferMetadataFieldValues` (
  `pk` varchar(36) NOT NULL,
  `createdTime` datetime(6) NOT NULL,
  `fieldValue` longtext NOT NULL,
  `fieldUUID` varchar(36) NOT NULL,
  `setUUID` varchar(36) NOT NULL,
  PRIMARY KEY (`pk`),
  KEY `TransferMetadataFiel_fieldUUID_eedd2f53_fk_TransferM` (`fieldUUID`),
  KEY `TransferMetadataFiel_setUUID_0de67fb6_fk_TransferM` (`setUUID`),
  CONSTRAINT `TransferMetadataFiel_fieldUUID_eedd2f53_fk_TransferM` FOREIGN KEY (`fieldUUID`) REFERENCES `TransferMetadataFields` (`pk`),
  CONSTRAINT `TransferMetadataFiel_setUUID_0de67fb6_fk_TransferM` FOREIGN KEY (`setUUID`) REFERENCES `TransferMetadataSets` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TransferMetadataFields`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TransferMetadataFields` (
  `pk` varchar(36) NOT NULL,
  `createdTime` datetime(6) DEFAULT NULL,
  `fieldLabel` varchar(50) NOT NULL,
  `fieldName` varchar(50) NOT NULL,
  `fieldType` varchar(50) NOT NULL,
  `sortOrder` int(11) NOT NULL,
  `optionTaxonomyUUID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `TransferMetadataFiel_optionTaxonomyUUID_6874decb_fk_Taxonomie` (`optionTaxonomyUUID`),
  CONSTRAINT `TransferMetadataFiel_optionTaxonomyUUID_6874decb_fk_Taxonomie` FOREIGN KEY (`optionTaxonomyUUID`) REFERENCES `Taxonomies` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TransferMetadataSets`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TransferMetadataSets` (
  `pk` varchar(36) NOT NULL,
  `createdTime` datetime(6) NOT NULL,
  `createdByUserID` int(11) NOT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Transfers`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Transfers` (
  `transferUUID` varchar(36) NOT NULL,
  `currentLocation` longtext NOT NULL,
  `type` varchar(50) NOT NULL,
  `accessionID` longtext NOT NULL,
  `sourceOfAcquisition` longtext NOT NULL,
  `typeOfTransfer` longtext NOT NULL,
  `description` longtext NOT NULL,
  `notes` longtext NOT NULL,
  `hidden` tinyint(1) NOT NULL,
  `transferMetadataSetRowUUID` varchar(36) DEFAULT NULL,
  `dirUUIDs` tinyint(1) NOT NULL,
  `access_system_id` longtext NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `status` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`transferUUID`),
  KEY `Transfers_transferMetadataSetR_77678fde_fk_TransferM` (`transferMetadataSetRowUUID`),
  CONSTRAINT `Transfers_transferMetadataSetR_77678fde_fk_TransferM` FOREIGN KEY (`transferMetadataSetRowUUID`) REFERENCES `TransferMetadataSets` (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `UnitVariables`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `UnitVariables` (
  `pk` varchar(36) NOT NULL,
  `unitType` varchar(50) DEFAULT NULL,
  `unitUUID` varchar(36) DEFAULT NULL,
  `variable` longtext,
  `variableValue` longtext,
  `createdTime` datetime(6) NOT NULL,
  `updatedTime` datetime(6) NOT NULL,
  `microServiceChainLink` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `UnitVariables_ep46xp7f_idx` (`unitUUID`,`unitType`,`variable`(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group_permissions`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_permission`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=190 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user_groups`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user_user_permissions`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_content_type`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_migrations`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=138 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_session`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fpr_format`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_format` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL,
  `description` varchar(128) NOT NULL,
  `slug` varchar(50) NOT NULL,
  `group_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `fpr_format_slug_a33dc014_uniq` (`slug`),
  KEY `fpr_format_group_id_f5cd269e_fk_fpr_formatgroup_uuid` (`group_id`),
  CONSTRAINT `fpr_format_group_id_f5cd269e_fk_fpr_formatgroup_uuid` FOREIGN KEY (`group_id`) REFERENCES `fpr_formatgroup` (`uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=1381 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fpr_formatgroup`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_formatgroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL,
  `description` varchar(128) NOT NULL,
  `slug` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `fpr_formatgroup_slug_bdc97a73_uniq` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fpr_formatversion`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_formatversion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `enabled` tinyint(1) NOT NULL,
  `lastmodified` datetime(6) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `version` varchar(10) DEFAULT NULL,
  `pronom_id` varchar(32) DEFAULT NULL,
  `description` varchar(128) DEFAULT NULL,
  `access_format` tinyint(1) NOT NULL,
  `preservation_format` tinyint(1) NOT NULL,
  `slug` varchar(50) NOT NULL,
  `format_id` varchar(36) DEFAULT NULL,
  `replaces_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `fpr_formatversion_slug_09e710e0` (`slug`),
  KEY `fpr_formatversion_format_id_17da4607_fk_fpr_format_uuid` (`format_id`),
  KEY `fpr_formatversion_replaces_id_199a1793_fk_fpr_formatversion_uuid` (`replaces_id`),
  CONSTRAINT `fpr_formatversion_format_id_17da4607_fk_fpr_format_uuid` FOREIGN KEY (`format_id`) REFERENCES `fpr_format` (`uuid`),
  CONSTRAINT `fpr_formatversion_replaces_id_199a1793_fk_fpr_formatversion_uuid` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_formatversion` (`uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=1873 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fpr_fpcommand`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_fpcommand` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `enabled` tinyint(1) NOT NULL,
  `lastmodified` datetime(6) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `description` varchar(256) NOT NULL,
  `command` longtext NOT NULL,
  `script_type` varchar(16) NOT NULL,
  `output_location` longtext,
  `command_usage` varchar(16) NOT NULL,
  `event_detail_command_id` varchar(36) DEFAULT NULL,
  `output_format_id` varchar(36) DEFAULT NULL,
  `replaces_id` varchar(36) DEFAULT NULL,
  `tool_id` varchar(36) DEFAULT NULL,
  `verification_command_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `fpr_fpcommand_event_detail_command_6f3e103b_fk_fpr_fpcom` (`event_detail_command_id`),
  KEY `fpr_fpcommand_output_format_id_77c1b87a_fk_fpr_forma` (`output_format_id`),
  KEY `fpr_fpcommand_replaces_id_16802556_fk_fpr_fpcommand_uuid` (`replaces_id`),
  KEY `fpr_fpcommand_tool_id_6985f419_fk_fpr_fptool_uuid` (`tool_id`),
  KEY `fpr_fpcommand_verification_command_3baeb09d_fk_fpr_fpcom` (`verification_command_id`),
  CONSTRAINT `fpr_fpcommand_event_detail_command_6f3e103b_fk_fpr_fpcom` FOREIGN KEY (`event_detail_command_id`) REFERENCES `fpr_fpcommand` (`uuid`),
  CONSTRAINT `fpr_fpcommand_output_format_id_77c1b87a_fk_fpr_forma` FOREIGN KEY (`output_format_id`) REFERENCES `fpr_formatversion` (`uuid`),
  CONSTRAINT `fpr_fpcommand_replaces_id_16802556_fk_fpr_fpcommand_uuid` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_fpcommand` (`uuid`),
  CONSTRAINT `fpr_fpcommand_tool_id_6985f419_fk_fpr_fptool_uuid` FOREIGN KEY (`tool_id`) REFERENCES `fpr_fptool` (`uuid`),
  CONSTRAINT `fpr_fpcommand_verification_command_3baeb09d_fk_fpr_fpcom` FOREIGN KEY (`verification_command_id`) REFERENCES `fpr_fpcommand` (`uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fpr_fprule`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_fprule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `enabled` tinyint(1) NOT NULL,
  `lastmodified` datetime(6) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `purpose` varchar(32) NOT NULL,
  `count_attempts` int(11) NOT NULL,
  `count_okay` int(11) NOT NULL,
  `count_not_okay` int(11) NOT NULL,
  `command_id` varchar(36) NOT NULL,
  `format_id` varchar(36) NOT NULL,
  `replaces_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `fpr_fprule_command_id_686fdef7_fk_fpr_fpcommand_uuid` (`command_id`),
  KEY `fpr_fprule_format_id_e153f0af_fk_fpr_formatversion_uuid` (`format_id`),
  KEY `fpr_fprule_replaces_id_02672819_fk_fpr_fprule_uuid` (`replaces_id`),
  CONSTRAINT `fpr_fprule_command_id_686fdef7_fk_fpr_fpcommand_uuid` FOREIGN KEY (`command_id`) REFERENCES `fpr_fpcommand` (`uuid`),
  CONSTRAINT `fpr_fprule_format_id_e153f0af_fk_fpr_formatversion_uuid` FOREIGN KEY (`format_id`) REFERENCES `fpr_formatversion` (`uuid`),
  CONSTRAINT `fpr_fprule_replaces_id_02672819_fk_fpr_fprule_uuid` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_fprule` (`uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=855 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fpr_fptool`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_fptool` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL,
  `description` varchar(256) NOT NULL,
  `version` varchar(64) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `slug` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `fpr_fptool_slug_75e9b73c_uniq` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fpr_idcommand`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_idcommand` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `enabled` tinyint(1) NOT NULL,
  `lastmodified` datetime(6) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `description` varchar(256) NOT NULL,
  `config` varchar(4) NOT NULL,
  `script` longtext NOT NULL,
  `script_type` varchar(16) NOT NULL,
  `replaces_id` varchar(36) DEFAULT NULL,
  `tool_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `fpr_idcommand_replaces_id_0e604275_fk_fpr_idcommand_uuid` (`replaces_id`),
  KEY `fpr_idcommand_tool_id_e1cf42a0_fk_fpr_idtool_uuid` (`tool_id`),
  CONSTRAINT `fpr_idcommand_replaces_id_0e604275_fk_fpr_idcommand_uuid` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_idcommand` (`uuid`),
  CONSTRAINT `fpr_idcommand_tool_id_e1cf42a0_fk_fpr_idtool_uuid` FOREIGN KEY (`tool_id`) REFERENCES `fpr_idtool` (`uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fpr_idrule`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_idrule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `enabled` tinyint(1) NOT NULL,
  `lastmodified` datetime(6) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `command_output` longtext NOT NULL,
  `command_id` varchar(36) NOT NULL,
  `format_id` varchar(36) NOT NULL,
  `replaces_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `fpr_idrule_command_id_796e0e32_fk_fpr_idcommand_uuid` (`command_id`),
  KEY `fpr_idrule_format_id_40d7d207_fk_fpr_formatversion_uuid` (`format_id`),
  KEY `fpr_idrule_replaces_id_720eb522_fk_fpr_idrule_uuid` (`replaces_id`),
  CONSTRAINT `fpr_idrule_command_id_796e0e32_fk_fpr_idcommand_uuid` FOREIGN KEY (`command_id`) REFERENCES `fpr_idcommand` (`uuid`),
  CONSTRAINT `fpr_idrule_format_id_40d7d207_fk_fpr_formatversion_uuid` FOREIGN KEY (`format_id`) REFERENCES `fpr_formatversion` (`uuid`),
  CONSTRAINT `fpr_idrule_replaces_id_720eb522_fk_fpr_idrule_uuid` FOREIGN KEY (`replaces_id`) REFERENCES `fpr_idrule` (`uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=961 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fpr_idtool`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fpr_idtool` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL,
  `description` varchar(256) NOT NULL,
  `version` varchar(64) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `slug` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `fpr_idtool_slug_85d0a92a_uniq` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `main_archivesspacedigitalobject`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `main_archivesspacedigitalobject` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `resourceid` varchar(150) NOT NULL,
  `label` varchar(255) NOT NULL,
  `title` longtext NOT NULL,
  `started` tinyint(1) NOT NULL,
  `remoteid` varchar(150) NOT NULL,
  `sip_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `main_archivesspacedigitalobject_sip_id_f69cfbbe_fk_SIPs_sipUUID` (`sip_id`),
  CONSTRAINT `main_archivesspacedigitalobject_sip_id_f69cfbbe_fk_SIPs_sipUUID` FOREIGN KEY (`sip_id`) REFERENCES `SIPs` (`sipUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `main_fpcommandoutput`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `main_fpcommandoutput` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content` longtext,
  `fileUUID` varchar(36) NOT NULL,
  `ruleUUID` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `main_fpcommandoutput_fileUUID_d923ff15_fk_Files_fileUUID` (`fileUUID`),
  KEY `main_fpcommandoutput_ruleUUID_9c892057_fk_fpr_fprule_uuid` (`ruleUUID`),
  CONSTRAINT `main_fpcommandoutput_fileUUID_d923ff15_fk_Files_fileUUID` FOREIGN KEY (`fileUUID`) REFERENCES `Files` (`fileUUID`),
  CONSTRAINT `main_fpcommandoutput_ruleUUID_9c892057_fk_fpr_fprule_uuid` FOREIGN KEY (`ruleUUID`) REFERENCES `fpr_fprule` (`uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `main_levelofdescription`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `main_levelofdescription` (
  `pk` varchar(36) NOT NULL,
  `name` varchar(1024) NOT NULL,
  `sortOrder` int(11) NOT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `main_siparrange`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `main_siparrange` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `original_path` longblob,
  `arrange_path` longblob NOT NULL,
  `file_uuid` varchar(36) DEFAULT NULL,
  `transfer_uuid` varchar(36) DEFAULT NULL,
  `sip_created` tinyint(1) NOT NULL,
  `aip_created` tinyint(1) NOT NULL,
  `level_of_description` varchar(2014) NOT NULL,
  `sip_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `main_siparrange_file_uuid_836271da_uniq` (`file_uuid`),
  KEY `main_siparrange_sip_id_0f3312cc_fk_SIPs_sipUUID` (`sip_id`),
  CONSTRAINT `main_siparrange_sip_id_0f3312cc_fk_SIPs_sipUUID` FOREIGN KEY (`sip_id`) REFERENCES `SIPs` (`sipUUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `main_siparrangeaccessmapping`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `main_siparrangeaccessmapping` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `arrange_path` varchar(255) NOT NULL,
  `system` varchar(255) NOT NULL,
  `identifier` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `main_userprofile`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `main_userprofile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `agent_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `system_emails` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `agent_id` (`agent_id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `main_userprofile_agent_id_1954be72_fk_Agents_pk` FOREIGN KEY (`agent_id`) REFERENCES `Agents` (`pk`),
  CONSTRAINT `main_userprofile_user_id_15c416f4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tastypie_apiaccess`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tastypie_apiaccess` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `identifier` varchar(255) NOT NULL,
  `url` varchar(255) NOT NULL,
  `request_method` varchar(10) NOT NULL,
  `accessed` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tastypie_apikey`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tastypie_apikey` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(128) NOT NULL,
  `created` datetime(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `tastypie_apikey_key_17b411bb` (`key`),
  CONSTRAINT `tastypie_apikey_user_id_8c8fa920_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-05-28  9:58:05
