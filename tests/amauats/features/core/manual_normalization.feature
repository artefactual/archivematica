Feature: Archivematica recognizes manually normalized files

  Scenario Outline: Create an AIP from a transfer containing manually normalized files
    Given a processing configuration for testing manual normalization
    And transfer source <transfer_path> which contains a manually normalized file whose path is a prefix of another manually normalized file
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Normalize for preservation" micro-service to complete during ingest
    Then the "Normalize for preservation" micro-service output is "Completed successfully" during ingest
    And all preservation tasks recognize the manually normalized derivatives
    When the user waits for the "Relate manual normalized preservation files to the original files" micro-service to complete during ingest
    Then the "Relate manual normalized preservation files to the original files" micro-service output is "Completed successfully" during ingest
    And each manually normalized file is matched to an original
    When the user waits for the "Generate METS.xml document|Generate AIP METS" micro-service to complete during ingest
    Then the "Generate METS.xml document|Generate AIP METS" micro-service output is "Completed successfully" during ingest

    Examples:
      | transfer_path                                    |
      | TestTransfers/acceptance-tests/manual-normalization |
