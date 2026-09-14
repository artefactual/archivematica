Feature: PREMIS events are recorded for preservation events that occur during transfer

  Scenario Outline: The minimum set of PREMIS events are recorded for a transfer
    Given a "standard" transfer type located in "<sample_transfer_path>"
    And the transfer has completed ingest successfully
    When the AIP is downloaded and extracted
    Then there is a virus scanning event for each original object in the AIP METS
    And there is a message digest calculation event for each original object in the AIP METS
    And there is a file format identification event for each original object in the AIP METS
    And there is an ingestion event for each original object in the AIP METS
    And there are <validated_objects_count> original objects in the AIP METS with a validation event

    Examples: sample transfers
      | sample_transfer_path            | validated_objects_count |
      | SampleTransfers/DemoTransferCSV | 2                       |
      | TestTransfers/badNames          | 0                       |
