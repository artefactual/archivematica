# Part 3: Prompt Preparation

## 3.1.1 Repository Context
Archivematica is a comprehensive, open-source digital preservation system designed to help institutions maintain long-term access to digital collections. It implements the Reference Model for an Open Archival Information System (OAIS), providing a suite of micro-services that automate the ingest, processing, and storage of digital objects. The intended users are primarily archivists, data managers, and librarians who need to ensure that digital files remain usable despite format obsolescence or media decay. 

The system addresses the problem domain of digital stewardship by creating Archival Information Packages (AIPs)—standardized bundles containing original data, preservation-friendly copies, and detailed metadata. Archivematica's architecture relies on a "micro-service chain" where tasks like format identification, virus scanning, and metadata generation are executed sequentially. By using open standards like METS (Metadata Encoding and Transmission Standard) and PREMIS, it ensures that preserved data is interoperable and verifiable for decades to come.

## 3.1.2 Pull Request Description
This Pull Request modifies the METS v2 generation library (`create_mets_v2.py`) to improve structural metadata linking and modernize the code. The specific technical goal is to ensure that `DMDID` attributes are populated within the `structMap` section of the METS file. The `structMap` defines the physical and logical hierarchy of the digital object, while `DMDID` serves as a pointer to the descriptive metadata (like Dublin Core or MODS) that applies to specific divisions.

Previously, these links were often missing in METS v2 output, making it difficult for external repository systems to automatically associate metadata with the correct files in the hierarchy. By populating these IDs, the PR ensures a more robust and standards-compliant AIP. Additionally, the PR replaces the deprecated `cgi.escape` function with `html.escape`. This is a necessary maintenance step as the `cgi` module's escaping functions were deprecated and eventually removed in later Python versions, potentially causing runtime errors in newer environments.

## 3.1.3 Acceptance Criteria
*   ✓ Every `<div>` element in the `structMap` must include a `DMDID` attribute if there is associated descriptive metadata for that component.
*   ✓ The value of the `DMDID` attribute must exactly match the `ID` of the corresponding descriptive metadata section (`<dmdSec>`).
*   ✓ The implementation must replace all usage of the deprecated `cgi.escape` with the standard `html.escape` library.
*   ✓ The generated XML must remain well-formed and valid according to the METS schema, even when metadata contains special XML characters.
*   ✓ Existing tests in `create_mets_v2_test.py` must pass, and new assertions must be added to verify the presence of `DMDID` in the output.

## 3.1.4 Edge Cases
*   **Elements without Metadata**: The system must ensure that `DMDID` attributes are NOT added to structural elements that do not have descriptive metadata, rather than adding an empty attribute.
*   **Special Characters in Filenames**: The escaping mechanism (`html.escape`) must be verified against filenames containing characters like `&`, `<`, and `>`, ensuring they are correctly transformed to `&amp;`, `&lt;`, and `&gt;`.
*   **Circular or Nested Metadata**: In scenarios with complex metadata relationships, the system must ensure that IDs remain unique and correctly scoped to the current structural division.

## 3.1.5 Initial Prompt
**Task: Enhance METS v2 Generation and Modernize Escaping in Archivematica**

**Context**: You are working on Archivematica, an open-source digital preservation system. The core of its output is the METS (Metadata Encoding and Transmission Standard) file, which describes the structure and metadata of preserved objects. We need to improve our METS v2 generation to better link structural components to their descriptive metadata and update deprecated library usage.

**Requirements**:
1.  **Populate DMDID in structMap**:
    *   Modify [src/archivematica/MCPClient/clientScripts/create_mets_v2.py](file:///f:/Task/archivematica/src/archivematica/MCPClient/clientScripts/create_mets_v2.py) to ensure that every `<div>` element in the `structMap` contains a `DMDID` attribute when descriptive metadata is available.
    *   This attribute must reference the `ID` of the corresponding `<dmdSec>` element.
    *   Ensure that this applies to both directory-level and file-level divisions in the structural map.

2.  **Modernize XML Escaping**:
    *   Replace all instances of `cgi.escape` with `html.escape` in [src/archivematica/MCPClient/clientScripts/create_mets_v2.py](file:///f:/Task/archivematica/src/archivematica/MCPClient/clientScripts/create_mets_v2.py).
    *   You will need to update the imports to use `import html` instead of `import cgi`.
    *   Ensure that the escaping logic correctly handles names and metadata values that contain XML reserved characters.

3.  **Testing and Validation**:
    *   Update [tests/MCPClient/test_create_mets_v2.py](file:///f:/Task/archivematica/tests/MCPClient/test_create_mets_v2.py) to verify these changes.
    *   Add a test case that generates a METS file and asserts that the `DMDID` attribute is present and correctly valued in the `structMap`.
    *   Verify that all existing tests pass after your changes.

**Reference Information**:
*   The `DMDID` attribute in METS is used to link a structural division (`div`) to descriptive metadata sections (`dmdSec`).
*   Archivematica uses `lxml` for XML generation in this module.

**Acceptance Criteria**:
*   `structMap` divisions link to `dmdSec` via `DMDID`.
*   Zero usage of the `cgi` module for escaping.
*   Valid XML output for files with special characters.
*   All unit tests pass.

"I declare that all written content in this assessment is my own work, created without the use of AI language models or automated writing tools. All technical analysis and documentation reflects my personal understanding and has been written in my own words."
