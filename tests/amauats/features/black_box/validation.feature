Feature: JHOVE validation works correctly and transfers fail when they contain unvalidated files

  Scenario: Validation for a transfer fails
    Given a "standard" transfer type located in "SampleTransfers/JHOVEModulesValidation"
    When the transfer compliance is verified
    And the transfer has completed ingest successfully
    And the AIP is downloaded and extracted
    Then the "Identify file format" microservice completes successfully
    And the "Validate formats" job fails
    And 17 "Validate formats" transfer tasks were executed
    And 8 "Validate formats" transfer tasks failed
    And 9 "Validate formats" transfer tasks succeeded
    And the "Validation" microservice is executed
    And 1 AIFF file(s) failed
    And 1 AIFF file(s) succeeded
    And 1 GIF file(s) failed
    And 1 GIF file(s) succeeded
    And 1 JP2 file(s) failed
    And 1 JP2 file(s) succeeded
    And 1 JPG file(s) failed
    And 1 JPG file(s) succeeded
    And 1 PDF file(s) failed
    And 1 PDF file(s) succeeded
    And 1 TIF file(s) failed
    And 1 TIF file(s) succeeded
    And 1 WARC file(s) failed
    And 1 WARC file(s) succeeded
    And 1 WAV file(s) failed
    And 1 WAV file(s) succeeded
    And the AIP can be successfully stored
    And there are 16 original objects in the AIP METS with a validation event
