Feature: Ingest conformance check
  Archivists need to verify that the preservation and access copies that
  Archivematica has created through normalization are in conformance with the
  mkv specification.

  Scenario Outline: Isla wants to confirm that normalization to mkv for preservation is successful
    Given a processing configuration for conformance checks on preservation derivatives
    And directory <transfer_path> contains files that will all be normalized to <file_validity> .mkv
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Validate preservation derivatives" micro-service to complete during ingest
    Then the "Validate preservation derivatives" micro-service output is "<microservice_output>" during ingest
    When the user waits for the "Approve normalization (review)" decision point to appear during ingest
    Then all preservation conformance checks in the normalization report have value <validation_result>
    When the user chooses "Yes" at decision point "Approve normalization (review)" during ingest
    And the user waits for the AIP to appear in archival storage
    Then all PREMIS implementation-check-type validation events have eventOutcome = <event_outcome>

    Examples: Normalized for Preservation File Validity Possibilities
      | file_validity | microservice_output    | validation_result | event_outcome | transfer_path                                                |
      | valid         | Completed successfully | Passed            | pass          | TestTransfers/acceptance-tests/preforma/when-normalized-all-valid |

  Scenario Outline: Isla wants to confirm that normalization to mkv for access is successful
    Given a processing configuration for conformance checks on access derivatives
    And directory <transfer_path> contains files that will all be normalized to <file_validity> .mkv
    When the user edits the FPR rule to transcode .mov files to .mkv for access
    And a transfer is initiated on directory <transfer_path>
    And the user waits for the "Validate access derivatives" micro-service to complete during ingest
    Then the "Validate access derivatives" micro-service output is "<microservice_output>" during ingest
    When the user waits for the "Approve normalization (review)" decision point to appear during ingest
    Then all access conformance checks in the normalization report have value <validation_result>

    Examples: Normalized for Access File Validity Possibilities
      | file_validity | microservice_output    | validation_result | transfer_path                                                       |
      | valid         | Completed successfully | Passed            | TestTransfers/acceptance-tests/preforma/when-normalized-access-all-valid |
