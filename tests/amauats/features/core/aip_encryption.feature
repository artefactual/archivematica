Feature: AIP encryption
  Archivematica users and administrators want to be able to store AIPs
  encrypted.

  Scenario: Richard wants to create a space on the Storage Service that encrypts all AIPs stored in that space
    Given there is a standard GPG-encrypted space in the storage service
    And there is a standard GPG-encrypted AIP Storage location in the storage service
    And automated processing with all decision points resolved
    And automated processing configured to Store AIP Encrypted in standard Archivematica Directory
    When a transfer is initiated on directory SampleTransfers/BagTransfer
    And the transfer has completed ingest successfully
    And the user waits for the AIP to appear in archival storage
    And the user downloads the AIP pointer file
    Then the pointer file contains a PREMIS:EVENT element for the encryption event
    And the pointer file contains a mets:transformFile element for the encryption event
    And the AIP on disk is encrypted
    When the user downloads the AIP
    Then the downloaded AIP is not encrypted

  Scenario: Richard wants to ensure that he can encrypt uncompressed AIPs
    Given there is a standard GPG-encrypted space in the storage service
    And there is a standard GPG-encrypted AIP Storage location in the storage service
    And automated processing with all decision points resolved
    And the processing config decision "Select compression algorithm" is set to "Uncompressed"
    And automated processing configured to Store AIP Encrypted in standard Archivematica Directory
    When a transfer is initiated on directory SampleTransfers/BagTransfer
    And the transfer has completed ingest successfully
    And the user waits for the AIP to appear in archival storage
    And the user queries the API until the AIP has been stored
    Then the uncompressed AIP on disk at /var/archivematica/sharedDirectory/www/AIPsStoreEncrypted/ is encrypted
    When the user downloads the AIP
    Then the downloaded uncompressed AIP is an unencrypted tarfile

  Scenario: Richard wants to ensure that a passphrase-less GPG key can be imported into the storage service
    When the user attempts to import GPG key aadams-passphraseless.key
    Then the user succeeds in importing the GPG key AAC5E07B370A2D9A

  Scenario: Richard wants to ensure that a GPG key with a passphrase cannot be imported into the storage service
    When the user attempts to import GPG key bbingo-passphrased.key
    Then the user fails to import the GPG key 0F86C799E5DEDE22 because it requires a passphrase

  Scenario: Richard wants to ensure that GPG deletion is never permitted if the key is associated to a space or if it is needed to decrypt an existing package
    Given there is a standard GPG-encrypted space in the storage service
    And there is a standard GPG-encrypted AIP Storage location in the storage service
    And automated processing with all decision points resolved
    And automated processing configured to Store AIP Encrypted in standard Archivematica Directory
    When the user creates a new GPG key and assigns it to the standard GPG-encrypted space
    And a transfer is initiated on directory SampleTransfers/BagTransfer
    And the transfer has completed ingest successfully
    And the user waits for the AIP to appear in archival storage
    And the user attempts to delete the new GPG key
    Then the user is prevented from deleting the key because it is attached to a space
    When the user assigns a different GPG key to the standard GPG-encrypted space
    And the user attempts to delete the new GPG key
    Then the user is prevented from deleting the key because it is attached to a package
    When the AIP is deleted
    And the user attempts to delete the new GPG key
    Then the user succeeds in deleting the GPG key

  Scenario: Richard wants to confirm that he can re-encrypt an encrypted AIP with a new key
    Given there is a standard GPG-encrypted space in the storage service
    And there is a standard GPG-encrypted AIP Storage location in the storage service
    And automated processing with all decision points resolved
    And the reminder to add metadata is enabled
    And automated processing configured to Store AIP Encrypted in standard Archivematica Directory
    When a transfer is initiated on directory SampleTransfers/BagTransfer
    And the transfer has completed ingest successfully
    And the user waits for the AIP to appear in archival storage
    And the user creates a new GPG key and assigns it to the standard GPG-encrypted space
    And the user performs a metadata-only re-ingest on the AIP
    And the user downloads the AIP pointer file
    Then the AIP pointer file references the fingerprint of the new GPG key
