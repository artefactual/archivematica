# Part 3: Prompt Preparation

## 3.1.1 Repository Context
Archivematica is a comprehensive, open-source digital preservation system designed to help institutions maintain long-term access to digital collections. It implements the Reference Model for an Open Archival Information System (OAIS), providing a suite of micro-services that automate the ingest, processing, and storage of digital objects. The intended users are primarily archivists, data managers, and librarians who need to ensure that digital files remain usable despite format obsolescence or media decay. In many large institutions, such as national libraries or university archives, the volume and variety of digital content—ranging from digitial manuscripts to legacy databases—make manual preservation impossible. Archivematica addresses this by providing a standardized, scalable framework for digital stewardship.

The system addresses the problem domain of digital stewardship by creating Archival Information Packages (AIPs)—standardized bundles containing original data, preservation-friendly copies, and detailed metadata. Archivematica's architecture relies on a "micro-service chain" where tasks like format identification, virus scanning, and metadata generation are executed sequentially. By using open standards like METS (Metadata Encoding and Transmission Standard) and PREMIS, it ensures that preserved data is interoperable and verifiable for decades to come. The goal is to produce "self-describing" packages that contain all the information necessary for a future archivist to understand and render the content, even if the original software that created the files no longer exists.

## 3.1.2 Pull Request Description
This Pull Request modifies the METS v2 generation library (`create_mets_v2.py`) to improve structural metadata linking and modernize the code. The specific technical goal is to ensure that `DMDID` attributes are populated within the `structMap` section of the METS file. The `structMap` defines the physical and logical hierarchy of the digital object, while `DMDID` serves as a pointer to the descriptive metadata (like Dublin Core or MODS) that applies to specific divisions. Without these pointers, the METS file provides the structure of the data but lacks the semantic context required for machine-driven discovery and ingestion into external repository systems.

Previously, these links were often missing in METS v2 output, especially in the normative (logical) structural map. This gap made it difficult for external repository systems to automatically associate metadata with the correct files in the hierarchy, leading to a fragmented user experience for those accessing the preserved content. By populating these IDs, the PR ensures a more robust and standards-compliant AIP that can be seamlessly integrated into modern library ecosystems. Additionally, the PR replaces the deprecated `cgi.escape` function with `html.escape`. This is a necessary maintenance step as the `cgi` module's escaping functions were deprecated in Python 3.2 and eventually removed in 3.8. This proactive migration ensures that Archivematica remains functional as المؤسسات (institutions) upgrade their underlying infrastructure to more modern Python environments, preventing potential runtime errors during the critical AIP generation phase.

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

**Context**: You are working on Archivematica, an open-source digital preservation system. The core of its output is the METS (Metadata Encoding and Transmission Standard) file, which describes the structure and metadata of preserved objects. We need to improve our METS v2 generation to better link structural components to their descriptive metadata and update deprecated library usage to ensure compatibility with modern Python environments.

**Detailed Requirements**:
1.  **Populate DMDID in structMap**:
    *   Navigate to the METS generation logic in [src/archivematica/MCPClient/clientScripts/create_mets_v2.py](file:///f:/Task/archivematica/src/archivematica/MCPClient/clientScripts/create_mets_v2.py).
    *   The goal is to ensure that every `<div>` element in the `structMap` contains a `DMDID` attribute whenever descriptive metadata is available for that specific component.
    *   The `DMDID` attribute must reference the unique `ID` of the corresponding descriptive metadata section (`<dmdSec>`).
    *   Your implementation must handle both directory-level divisions and file-level divisions. Ensure that if an element has multiple metadata records, the `DMDID` attribute contains a space-separated list of all relevant IDs.

2.  **Modernize XML Escaping**:
    *   Identify all usages of the deprecated `cgi.escape` function within the file.
    *   Replace these calls with the modern `html.escape` function from the `html` standard library module.
    *   Update the top-level imports to include `import html` and remove `import cgi` if it is no longer needed.
    *   Verify that the escaping logic correctly handles names and metadata values that contain XML reserved characters like `&`, `<`, and `>`, preventing malformed XML output.

3.  **Testing and Validation**:
    *   Modify the corresponding test file: [tests/MCPClient/test_create_mets_v2.py](file:///f:/Task/archivematica/tests/MCPClient/test_create_mets_v2.py).
    *   Add a specific test case that simulates the generation of a METS file for a SIP with descriptive metadata.
    *   Assert that the resulting XML contains a `structMap` where the `<div>` elements have the correct `DMDID` attributes.
    *   Confirm that all existing tests pass to ensure no regressions in the core METS generation logic.

**Technical Reference**:
*   Archivematica utilizes the `lxml` library for XML construction.
*   The `DMDID` is a standard METS attribute used to link structural divisions to metadata sections.
*   The migration from `cgi` to `html` is required for Python 3.8+ compatibility.

**Success Criteria**:
*   The generated METS `structMap` successfully links to `dmdSec` entries.
*   The codebase contains zero references to the deprecated `cgi` module.
*   The AIP output remains schema-compliant and well-formed.
*   The automated test suite provides 100% pass rate for the modified modules.

Please provide the implementation in a clear, modular format, ensuring all Archivematica coding standards are followed.

"I declare that all written content in this assessment is my own work, created without the use of AI language models or automated writing tools. All technical analysis and documentation reflects my personal understanding and has been written in my own words."
