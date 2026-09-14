Feature: Archivematica generates AIPs from different types of transfer source

  Scenario: Generate an AIP using a standard transfer workflow
    Given a "standard" transfer type located in "SampleTransfers/DemoTransferCSV"
    And the transfer has completed ingest successfully
    When the AIP is downloaded and extracted
    Then the AIP METS can be accessed and parsed by mets-reader-writer
    And in the METS file the metsHdr element has a CREATEDATE attribute but no LASTMODDATE attribute
    And in the METS file the metsHdr element has 10 dmdSec next sibling element(s)
    And the AIP conforms to expected content and structure
    And the AIP contains all files that were present in the transfer
    And the AIP contains a file called README.html in the data directory
    And the AIP contains a file called METS.xml in the data directory
    And the fileSec of the AIP METS will record every file in the objects and metadata directories of the AIP
    And the physical structMap of the AIP METS accurately reflects the physical layout of the AIP
    And every object in the AIP has been assigned a UUID in the AIP METS
    And every object in the objects and metadata directories has an amdSec
    And every PREMIS event recorded in the AIP METS records the logged-in user, the organization and the software as PREMIS agents

  Scenario: Generate an AIP using an unzipped bag transfer workflow
    Given a "unzipped bag" transfer type located in "SampleTransfers/BagTransfer"
    And the transfer has completed ingest successfully
    When the AIP is downloaded and extracted
    Then the "Approve transfer" microservice completes successfully
    And the "Verify bag, and restructure for compliance" job completes successfully
    And there is a sourceMD containing a BagIt mdWrap in the AIP METS

  Scenario: Generate an AIP using a zipped bag transfer workflow
    Given a "zipped bag" transfer type located in "SampleTransfers/BagExamples/ZippedBags/BagTransfer.zip"
    And the transfer has completed ingest successfully
    When the AIP is downloaded and extracted
    Then the "Approve transfer" microservice completes successfully
    And the "Extract zipped bag transfer" job completes successfully
    And the "Verify bag, and restructure for compliance" job completes successfully
    And there is a sourceMD containing a BagIt mdWrap in the AIP METS

  Scenario: Generate an AIP using a Dataverse workflow
    Given a "dataverse" transfer type located in "SampleTransfers/Dataverse/NDSAStaffingReport"
    And the transfer has completed ingest successfully
    When the AIP is downloaded and extracted
    Then the "Set convert Dataverse structure flag" job completes successfully
    And the "Set parse Dataverse METS flag" job completes successfully
    And the "Convert Dataverse structure" job completes successfully
    And the "Parse Dataverse METS XML" job completes successfully
    And the METS file contains a dmdSec with DDI metadata

  Scenario Outline: Generate an AIP using a Dspace transfer workflow
    Given a "dspace" transfer type located in "<sample_transfer_path>"
    And the transfer has completed ingest successfully
    When the AIP is downloaded and extracted
    Then the "Identify DSpace mets files" job completes successfully
    And the "Identify DSpace text files" job completes successfully
    And the "Verify checksums in fileSec of DSpace METS files" job completes successfully
    And the AIP METS can be accessed and parsed by mets-reader-writer
    And there are 2 DSpace-specific descriptive metadata sections for each object
    And there is a DSpace-specific rights metadata section for each object
    And the entries in the file section of the METS are sorted by file group

    Examples: sample transfers
      | sample_transfer_path                            |
      | SampleTransfers/DSpaceExport/ITEM@2429-2700.zip |
      | SampleTransfers/DSpaceExport                    |

  Scenario: Generate an AIP using a zipped directory transfer workflow
    Given a "zipfile" transfer type located in "SampleTransfers/ZippedDirectoryTransfers/DemoTransferCSV.zip"
    And the transfer has completed ingest successfully
    When the AIP is downloaded and extracted
    Then the "Approve transfer" microservice completes successfully
    And the "Extract zipped transfer" job completes successfully
    And the AIP METS can be accessed and parsed by mets-reader-writer
    And the AIP conforms to expected content and structure

  Scenario Outline: Generate an AIP with imported structural metadata
    Given a "standard" transfer type located in "<sample_transfer_path>"
    And the transfer has completed ingest successfully
    When the AIP is downloaded and extracted
    Then the AIP METS can be accessed and parsed by mets-reader-writer
    And the provided structural map will be included in the AIP METs file

    Examples: sample transfers
      | sample_transfer_path                                             |
      | SampleTransfers/StructMapTransferSamples/MinimalStructMapExample |
      | SampleTransfers/StructMapTransferSamples/ComplexStructureExample |
      | SampleTransfers/StructMapTransferSamples/SimpleBookExample       |
      | SampleTransfers/StructMapTransferSamples/SingleObjectExample     |
