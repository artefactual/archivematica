Feature: Archivematica can reingest AIPs and record the reingest accurately in METS

  Scenario: Reingest without error
    Given a "standard" transfer type located in "SampleTransfers/DemoTransferCSV"
    And the transfer has completed ingest successfully
    And the AIP is downloaded and extracted
    When a "FULL" reingest is started using the "automated" processing configuration
    And the reingest is approved
    And the reingest has been processed
    Then the AIP can be successfully stored
    And there is a reingestion event for each original object in the AIP METS
    And there is a fileSec for deleted files for objects that were re-normalized
    And there is a current and a superseded techMD for each original object

  Scenario: Reingest unzipped bag transfer
    Given a "unzipped bag" transfer type located in "SampleTransfers/UnzippedBag"
    And the transfer has completed ingest successfully
    And the AIP is downloaded and extracted
    When a "FULL" reingest is started using the "automated" processing configuration
    And the reingest is approved
    And the reingest has been processed
    Then the AIP can be successfully stored
    And there is a reingestion event for each original object in the AIP METS
    And there is a fileSec for deleted files for objects that were re-normalized
    And there is a current and a superseded techMD for each original object
    And there is a sourceMD containing a BagIt mdWrap in the reingested AIP METS

  Scenario: Metadata only reingest without error
    Given a "standard" transfer type located in "SampleTransfers/DemoTransferCSV"
    And the transfer has completed ingest successfully
    And the AIP is downloaded and extracted
    And a processing configuration for metadata only reingests
    When a "METADATA" reingest is started using the "default" processing configuration
    And the "SampleTransfers/MetadataOnlyReingest/metadata.csv" metadata file is added
    And the reingest is approved
    And the reingest has been processed
    Then the AIP can be successfully stored
    And the "Reingest AIP" ingest microservice completes successfully
    And there is a reingestion event for each original object in the AIP METS
    And in the METS file the metsHdr element has a CREATEDATE attribute and a LASTMODDATE attribute
    And in the METS file the metsHdr element has 12 dmdSec next sibling element(s)
    And the "metadata.csv" file is in the reingest metadata directory
    And every file in the reingested metadata.csv file has two dmdSecs with the original and updated metadata

  Scenario: Partial reingest without error
    Given a "standard" transfer type located in "SampleTransfers/DemoTransferCSV"
    And the transfer has completed ingest successfully
    And the AIP is downloaded and extracted
    And a processing configuration for partial reingests
    When a "OBJECTS" reingest is started using the "default" processing configuration
    And the reingest is approved
    And the reingest has been processed
    Then the AIP can be successfully stored
    And the "Reingest AIP" ingest microservice completes successfully
    And there is a reingestion event for each original object in the AIP METS
    And the DIP is downloaded
    And the DIP contains access copies for each original object in the transfer

  Scenario: Multiple reingests for uncompressed AIPs
    Given a "standard" transfer type located in "SampleTransfers/DemoTransferCSV"
    And the transfer has completed ingest successfully
    And the AIP is downloaded and extracted
    And a processing configuration for metadata only reingests for uncompressed AIPs
    When a "METADATA" reingest is started using the "default" processing configuration
    And the "SampleTransfers/MetadataOnlyReingest/metadata.csv" metadata file is added
    And the reingest is approved
    And the reingest has been processed
    Then the AIP can be successfully stored
    And there is a reingestion event for each original object in the AIP METS
    Given a processing configuration for metadata only reingests for uncompressed AIPs
    When a "METADATA" reingest is started using the "default" processing configuration
    And the reingest is approved
    And the reingest has been processed
    Then the AIP can be successfully stored
    And there are 2 reingestion events for each original object in the AIP METS
