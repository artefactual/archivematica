Feature: Package files included in the transfer are extracted

  Scenario: Packages are extracted successfully
    Given a "standard" transfer type located in "SampleTransfers/OfficeDocs"
    When the transfer compliance is verified
    Then the "Extract contents from compressed archives" job completes successfully
    And the "Change extracted objects' file and directory names" job completes successfully
    And the "Remove cache files" job completes successfully
    And the "Scan for viruses on extracted files" job completes successfully
    And the "Identify file format" job completes successfully
    And the "Determine if transfer still contains packages" job completes successfully

  Scenario: Packages are not extracted successfully
    Given a "standard" transfer type located in "TestTransfers/broken_package_format_types"
    When the transfer compliance is verified
    Then the "Extract contents from compressed archives" job fails
    And the "Failed transfer" microservice is executed
