Feature: Ingest policy check
  Archivists want to check that the files that are defined for access or
  preservation conform to a pre-defined policy or policies.

  Scenario Outline: Isla has access derivatives and she needs to know whether they conform to her access policy
    Given a processing configuration for policy checks on access derivatives
    And MediaConch policy file <policy_file> is present in the local etc/mediaconch-policies/ directory
    And directory <transfer_path> contains files that, when normalized, will all <do_files_conform> to <policy_file>
    When the user ensures there is an FPR command that uses policy file <policy_file>
    And the user ensures there is an FPR rule with purpose <purpose> that validates Generic MKV files against policy file <policy_file>
    And the user edits the FPR rule to transcode .mkv files to .mkv for access
    And a transfer is initiated on directory <transfer_path>
    And the user waits for the "Policy checks for access derivatives" micro-service to complete during ingest
    Then the "Policy checks for access derivatives" micro-service output is "<microservice_output>" during ingest
    And all policy check for access derivatives tasks indicate <event_outcome>
    When the user waits for the AIP to appear in archival storage
    And the user downloads the AIP
    And the user decompresses the AIP
    Then the submissionDocumentation directory of the AIP does not contain a copy of the MediaConch policy file <policy_file>

    Examples: Policy Check Outcomes
      | do_files_conform | microservice_output    | event_outcome | transfer_path                                                         | policy_file                | purpose                     |
      | conform          | Completed successfully | pass          | TestTransfers/acceptance-tests/preforma/all-conform-policy-norm-acc   | NYULib_MKVFFV1_MODIFIED.xml | Validation against a policy |
      | not conform      | Failed                 | fail          | TestTransfers/acceptance-tests/preforma/none-conform-policy-norm-acc  | NYULib_MKVFFV1_MODIFIED.xml | Validation against a policy |

  Scenario Outline: Isla has preservation derivatives and she needs to know whether they conform to her preservation policy
    Given a processing configuration for policy checks on preservation derivatives
    And MediaConch policy file <policy_file> is present in the local etc/mediaconch-policies/ directory
    And directory <transfer_path> contains files that, when normalized, will all <do_files_conform> to <policy_file>
    When the user ensures there is an FPR command that uses policy file <policy_file>
    And the user ensures there is an FPR rule with purpose <purpose> that validates Generic MKV files against policy file <policy_file>
    And a transfer is initiated on directory <transfer_path>
    And the user waits for the "Policy checks for preservation derivatives" micro-service to complete during ingest
    Then the "Policy checks for preservation derivatives" micro-service output is "<microservice_output>" during ingest
    When the user waits for the AIP to appear in archival storage
    Then all PREMIS policy-check-type validation events have eventOutcome = <event_outcome>
    And the user downloads the AIP
    And the user decompresses the AIP
    Then the submissionDocumentation directory of the AIP contains a copy of the MediaConch policy file <policy_file>
    And the logs directory of the AIP contains a MediaConch policy check output file for each policy file tested against <policy_file>

    Examples: Policy Check Outcomes
      | do_files_conform | microservice_output    | event_outcome | transfer_path                                            | policy_file                | purpose                     |
      | conform          | Completed successfully | pass          | TestTransfers/acceptance-tests/preforma/all-conform-policy   | NYULib_MKVFFV1_MODIFIED.xml | Validation against a policy |
      | not conform      | Failed                 | fail          | TestTransfers/acceptance-tests/preforma/none-conform-policy  | NYULib_MKVFFV1_MODIFIED.xml | Validation against a policy |

  Scenario Outline: Isla has manually normalized preservation derivatives and she needs to know whether they conform to her preservation policy
    Given a processing configuration for policy checks on preservation derivatives
    And MediaConch policy file <policy_file> is present in the local etc/mediaconch-policies/ directory
    And directory <transfer_path>/manualNormalization/preservation/ contains a file manually normalized for preservation that will <do_files_conform> to <policy_file>
    When the user ensures there is an FPR command that uses policy file <policy_file>
    And the user ensures there is an FPR rule with purpose <purpose> that validates Generic MKV files against policy file <policy_file>
    And a transfer is initiated on directory <transfer_path>
    And the user waits for the "Policy checks for preservation derivatives" micro-service to complete during ingest
    Then the "Policy checks for preservation derivatives" micro-service output is "<microservice_output>" during ingest
    When the user waits for the AIP to appear in archival storage
    Then all PREMIS policy-check-type validation events have eventOutcome = <event_outcome>
    And the user downloads the AIP
    And the user decompresses the AIP
    Then the submissionDocumentation directory of the AIP contains a copy of the MediaConch policy file <policy_file>
    And the logs directory of the AIP contains a MediaConch policy check output file for each policy file tested against <policy_file>

    Examples: Policy Check Outcomes
      | do_files_conform | microservice_output    | event_outcome | transfer_path                                                                            | policy_file                | purpose                     |
      | conform          | Completed successfully | pass          | TestTransfers/acceptance-tests/preforma/manually-normalized-preservation-all-conform-policy  | NYULib_MKVFFV1_MODIFIED.xml | Validation against a policy |
      | not conform      | Failed                 | fail          | TestTransfers/acceptance-tests/preforma/manually-normalized-preservation-none-conform-policy | NYULib_MKVFFV1_MODIFIED.xml | Validation against a policy |

  Scenario Outline: Isla has manually normalized access derivatives and she needs to know whether they conform to her access policy
    Given a processing configuration for policy checks on access derivatives
    And MediaConch policy file <policy_file> is present in the local etc/mediaconch-policies/ directory
    And directory <transfer_path>/manualNormalization/access/ contains a file manually normalized for access that will <do_files_conform> to <policy_file>
    When the user ensures there is an FPR command that uses policy file <policy_file>
    And the user ensures there is an FPR rule with purpose <purpose> that validates Generic MKV files against policy file <policy_file>
    And a transfer is initiated on directory <transfer_path>
    And the user waits for the "Policy checks for access derivatives" micro-service to complete during ingest
    Then policy checks for access derivatives micro-service output is <microservice_output>
    And all policy check for access derivatives tasks indicate <event_outcome>
    When the user waits for the AIP to appear in archival storage
    And the user downloads the AIP
    And the user decompresses the AIP
    Then the submissionDocumentation directory of the AIP does not contain a copy of the MediaConch policy file <policy_file>

    Examples: Policy Check Outcomes
      | do_files_conform | microservice_output    | event_outcome | transfer_path                                                                      | policy_file                | purpose                     |
      | conform          | Completed successfully | pass          | TestTransfers/acceptance-tests/preforma/manually-normalized-access-all-conform-policy  | NYULib_MKVFFV1_MODIFIED.xml | Validation against a policy |
      | not conform      | Failed                 | fail          | TestTransfers/acceptance-tests/preforma/manually-normalized-access-none-conform-policy | NYULib_MKVFFV1_MODIFIED.xml | Validation against a policy |
