Feature: AIP METS contains metadata from description and rights CSVs

  Scenario Outline: Descriptive and rights metadata are listed in the AIP METS and submission documentation is listed correctly
    Given a "standard" transfer type located in "<sample_transfer_path>"
    And the transfer has completed ingest successfully
    When the AIP is downloaded and extracted
    Then the AIP METS can be accessed and parsed by mets-reader-writer
    And there are <original_object_count> original objects in the AIP METS with a DMDSEC containing DC metadata
    And there are <directory_count> directories in the AIP METS with a DMDSEC containing DC metadata
    And there are <original_object_rights_count> objects in the AIP METS with a rightsMD section containing PREMIS:RIGHTS
    And there are <rights_entries_count> PREMIS:RIGHTS entries
    And there are <submission_documents_count> submission documents listed in the AIP METS as submission documentation

    Examples: sample transfers
      | sample_transfer_path            | original_object_count | directory_count | original_object_rights_count | rights_entries_count | submission_documents_count |
      | SampleTransfers/DemoTransferCSV | 7                     | 1               | 2                            | 8                    | 1                          |
      | SampleTransfers/CSVmultiLevel   | 4                     | 1               | 0                            | 0                    | 0                          |
      | TestTransfers/rightsTransfer    | 0                     | 0               | 2                            | 4                    | 0                          |
