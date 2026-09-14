Feature: UUIDs for Directories

  Scenario Outline: Create an AIP with UUIDs assigned to each transfer subdirectory
    Given a processing configuration that assigns UUIDs to directories
    And remote directory "<directory_path>" contains a hierarchy of subfolders containing digital objects
    When a "<type>" transfer is initiated on directory "<transfer_path>"
    And the transfer has completed ingest successfully
    And the AIP is downloaded and extracted
    Then the METS file includes the original directory structure
    And the UUIDs for the subfolders and digital objects are written to the METS file

    Examples:
      | type       | directory_path                                                                                 | transfer_path                                                       |
      | standard   | ~/archivematica-sampledata/TestTransfers/acceptance-tests/pid-binding/hierarchy-with-empty-dir | TestTransfers/acceptance-tests/pid-binding/hierarchy-with-empty-dir |
      | zipped bag | ~/archivematica-sampledata/SampleTransfers/BagTransfer.zip                                     | SampleTransfers/BagTransfer.zip                                     |
