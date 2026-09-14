Feature: Transfer conformance check

  Scenario Outline: Confirm that transfer-time MKV validation records the expected outcome
    Given a processing configuration for conformance checks on originals
    And directory <transfer_path> contains files that are all <file_validity> .mkv
    When a transfer is initiated on directory <transfer_path>
    And the user waits for the "Validate formats" micro-service to complete during transfer
    Then the "Validate formats" micro-service output is "<microservice_output>" during transfer
    When the transfer has completed ingest successfully
    And the AIP is downloaded and extracted
    Then all PREMIS implementation-check-type validation events have eventOutcome = <event_outcome>

    Examples:
      | file_validity | microservice_output    | event_outcome | transfer_path                                       |
      | valid         | Completed successfully | pass          | TestTransfers/acceptance-tests/preforma/all-valid   |
      | not valid     | Failed                 | fail          | TestTransfers/acceptance-tests/preforma/none-valid  |
