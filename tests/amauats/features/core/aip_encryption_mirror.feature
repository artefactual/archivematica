Feature: AIP encryption via mirror locations
  Archivematica users want to be able to store AIPs unencrypted with encrypted
  replicas in mirror locations.

  Scenario: Richard wants to create an AIP with an encrypted replica
    Given there is a standard GPG-encrypted space in the storage service
    And there is a standard GPG-encrypted Replicator location in the storage service
    And the default AIP Storage location has the GPG-encrypted Replicator location as its replicator
    And automated processing with all decision points resolved
    When a transfer is initiated on directory SampleTransfers/BagTransfer
    And the transfer has completed ingest successfully
    And the user waits for the AIP to appear in archival storage
    And the user searches for the AIP UUID in the Storage Service
    Then the master AIP and its replica are returned by the search
    When the user downloads the master AIP pointer file
    And the user downloads the replica AIP pointer file
    Then the master pointer file contains a(n) replication PREMIS:EVENT
    And the replica pointer file contains a(n) creation PREMIS:EVENT
    And the replica pointer file contains a(n) validation PREMIS:EVENT
    And the master pointer file contains a PREMIS:OBJECT with a derivation relationship pointing to the replica and the replication PREMIS:EVENT
    And the replica pointer file contains a mets:transformFile element for the encryption event
    And the replica pointer file contains a(n) encryption PREMIS:EVENT
    And the master AIP on disk is not encrypted
    And the replica AIP on disk is encrypted
    When the user downloads the replica AIP
    And the user downloads the master AIP
    Then the downloaded replica AIP is not encrypted
    And the master and replica AIPs are byte-for-byte identical
