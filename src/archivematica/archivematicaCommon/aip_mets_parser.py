import calendar
import copy
import os
import re
import time
from collections.abc import Generator
from typing import Any
from typing import Optional

from lxml import etree

from archivematica.archivematicaCommon import namespaces as ns
from archivematica.archivematicaCommon.externals import xmltodict
from archivematica.dashboard.main.models import Identifier


class AIPMETSParser:
    def __init__(self, mets_path: str) -> None:
        self.mets_path = mets_path
        self.mets = self.parse()
        self.dublincore: Optional[etree._Element] = ns.xml_find_premis(
            self.mets, "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore"
        )
        self.aic_identifier: Optional[str] = None
        self.is_part_of: Optional[str] = None
        if self.dublincore is not None:
            aip_type = ns.xml_findtext_premis(
                self.dublincore, "dc:type"
            ) or ns.xml_findtext_premis(self.dublincore, "dcterms:type")
            if aip_type == "Archival Information Collection":
                self.aic_identifier = ns.xml_findtext_premis(
                    self.dublincore, "dc:identifier"
                ) or ns.xml_findtext_premis(self.dublincore, "dcterms:identifier")
            elif aip_type == "Archival Information Package":
                self.is_part_of = ns.xml_findtext_premis(
                    self.dublincore, "dcterms:isPartOf"
                )
        self.created: int = self.get_create_date()
        self.aip_metadata: list[dict[str, Any]] = self._get_aip_metadata()
        self.file_count: int = 0

    def get_create_date(self) -> int:
        result = int(time.time())
        # Pull the create time from the METS header.
        # Old METS did not use `metsHdr`.
        mets_hdr = ns.xml_find_premis(self.mets, "mets:metsHdr")
        if mets_hdr is not None:
            mets_created_attr = mets_hdr.get("CREATEDATE")
            if mets_created_attr:
                try:
                    result = calendar.timegm(
                        time.strptime(mets_created_attr, "%Y-%m-%dT%H:%M:%S")
                    )
                except ValueError:
                    # Failed to parse METS CREATEDATE
                    pass
        return result

    def parse(self) -> etree._Element:
        tree = etree.parse(self.mets_path)
        root = tree.getroot()
        self._remove_tool_output_from_mets(root)
        return root

    def _remove_tool_output_from_mets(self, root: etree._Element) -> None:
        """Remove tool output from a METS ElementTree.

        Given an ElementTree object, removes all objectsCharacteristicsExtensions
        elements. This modifies the existing document in-place; it does not return
        a new document. This helps index METS files, which might otherwise get too
        large to be usable.
        """
        # Remove tool output nodes
        toolNodes = ns.xml_findall_premis(
            root,
            "mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectCharacteristics/premis:objectCharacteristicsExtension",
        )

        for parent in toolNodes:
            parent.clear()

        print("Removed FITS output from METS.")

    def _get_aip_metadata(self) -> list[dict[str, Any]]:
        """Get metadata about the directories in the AIP.

        Given a doc representing a METS file, look for Directory entries
        that have descriptive or administrative metadata in the physical
        structMap and return dictionaries with metadata attributes for
        each directory.
        """
        result: list[dict[str, Any]] = []
        physical_struct_map = ns.xml_find_premis(
            self.mets, 'mets:structMap[@TYPE="physical"]'
        )
        if physical_struct_map is not None:
            for directory in self._get_directories_with_metadata(physical_struct_map):
                directory_metadata = self._get_directory_metadata(directory)
                if directory_metadata:
                    result.append(directory_metadata)
        return result

    def _get_directories_with_metadata(
        self, container: etree._Element
    ) -> list[etree._Element]:
        """Return Directory entries with metadata sections.

        Check if the entry references dmdSec (descriptive) or amdSec
        (administrative) metadata sections.
        """
        result = ns.xml_xpath_premis(
            container, './/mets:div[@TYPE="Directory"][@DMDID or @ADMID]'
        )
        return result if isinstance(result, list) else []

    def _get_directory_metadata(self, directory: etree._Element) -> dict[str, Any]:
        """Get descriptive or administrive metadata for a directory.

        There are three types of metadata elements extracted:

        1. Dublin core, set through the metadata/metadata.csv file or the
        transfer/ingest metadata form in the dashboard
        2. Custom (non dublin core), set through the metadata/metadata.csv
        file
        3. Bag/disk image metadata, set through the bag-info.txt file or
        the disk image metadata form in the dashboard
        4. Custom XML metadata, set through the source-metadata.csv files
        and related XML files

        These types are parsed and combined into a single dictionary of
        metadata attributes. A marker element with the label of the
        Directory entry is added to the result.
        """
        result = {}
        elements_with_metadata = []
        dmd_id = directory.attrib.get("DMDID")
        if dmd_id:
            for dmd_sec in self._get_latest_dmd_secs(dmd_id):
                elements_with_metadata += self._get_descriptive_section_metadata(
                    dmd_sec
                )
        for ADMID in directory.attrib.get("ADMID", "").split():
            amd_sec = ns.xml_find_premis(self.mets, f'mets:amdSec[@ID="{ADMID}"]')
            if amd_sec is not None:
                # look for bag/disk image metadata
                elements_with_metadata += ns.xml_findall_premis(
                    amd_sec, "mets:sourceMD/mets:mdWrap/mets:xmlData/transfer_metadata"
                )
        if elements_with_metadata:
            # add an attribute with the relative path of the Directory entry
            elements_with_metadata.append(self._get_relative_path_element(directory))
            result = self._combine_elements(elements_with_metadata)
        return self._normalize_dict(result)

    def _get_relative_path_element(self, directory: etree._Element) -> etree._Element:
        """Build an element with the relative path of the directory."""
        TAG = "__DIRECTORY_LABEL__"
        result = etree.Element("container")
        path = etree.SubElement(result, TAG)
        path.text = directory.attrib.get("LABEL", "")
        return result

    def files(self) -> Generator[tuple[dict[str, Any], set[str]], None, None]:
        # Index all files in a fileGrup with USE='original' or USE='metadata'.
        original_files = ns.xml_findall_premis(
            self.mets, "mets:fileSec/mets:fileGrp[@USE='original']/mets:file"
        )
        metadata_files = ns.xml_findall_premis(
            self.mets, "mets:fileSec/mets:fileGrp[@USE='metadata']/mets:file"
        )
        files = original_files + metadata_files
        self.file_count = len(files)
        for file in files:
            yield self.get_aip_file_index_data(file)

    def get_aip_file_index_data(
        self, file_: etree._Element
    ) -> tuple[dict[str, Any], set[str]]:
        # Establish the structure to be indexed for each file item.
        indexData: dict[str, Any] = {
            "FILEUUID": "",
            "filePath": "",
            "fileExtension": "",
            "METS": {"dmdSec": {}, "amdSec": {}},
            "accessionid": "",
        }

        accession_ids: set[str] = set()

        # Get file UUID. If an ADMID exists, look in the amdSec for the UUID,
        # otherwise parse it out of the file ID.
        # 'Original' files have ADMIDs, 'Metadata' files do not.
        admID = file_.attrib.get("ADMID", None)
        fileUUID: Optional[str] = None
        if admID is None:
            # Parse UUID from the file ID.
            uuix_regex = r"\w{8}-?\w{4}-?\w{4}-?\w{4}-?\w{12}"
            uuids = re.findall(uuix_regex, file_.attrib["ID"])
            # Multiple UUIDs may be returned - if they are all identical,
            # use that UUID, otherwise use None.
            # To determine all UUIDs are identical, use the size of the set.
            if len(set(uuids)) == 1:
                fileUUID = uuids[0]
        else:
            amdSec = self._get_amdSec(admID)
            fileUUID = self._get_file_uuid(amdSec)
            accession_id = self._get_accession_number(amdSec)
            if accession_id is not None:
                indexData["accessionid"] = accession_id
                accession_ids.add(accession_id)

            # Index amdSec information.
            if amdSec is not None:
                xml = etree.tostring(amdSec, encoding="utf8")
                indexData["METS"]["amdSec"] = self._normalize_dict(xmltodict.parse(xml))

        indexData["FILEUUID"] = fileUUID

        file_metadata: list[dict[str, Any]] = []

        # Get the parent division for the file pointer by searching the
        # physical structural map section (structMap).
        file_id = file_.attrib.get("ID", None)
        file_pointer_division = ns.xml_find_premis(
            self.mets,
            f"mets:structMap[@TYPE='physical']//mets:fptr[@FILEID='{file_id}']/..",
        )
        if file_pointer_division is not None:
            descriptive_metadata = self._get_file_metadata(file_pointer_division)
            if descriptive_metadata:
                file_metadata.append(descriptive_metadata)
            # If the parent division has a DMDID attribute then index
            # its data from the descriptive metadata section (dmdSec).
            dmd_section_id = file_pointer_division.attrib.get("DMDID", None)
            if dmd_section_id is not None:
                # dmd_section_id can contain one id (e.g., "dmdSec_2") or
                # more than one (e.g., "dmdSec_2 dmdSec_3", when a file
                # has both DC and non-DC metadata).
                # Attempt to index only the DC dmdSec if available.
                for dmd_section_id_item in dmd_section_id.split():
                    dmd_section_info = ns.xml_find_premis(
                        self.mets,
                        f"mets:dmdSec[@ID='{dmd_section_id_item}']/mets:mdWrap[@MDTYPE='DC']/mets:xmlData",
                    )
                    if dmd_section_info is not None:
                        xml = etree.tostring(dmd_section_info, encoding="utf8")
                        data = self._normalize_dict(xmltodict.parse(xml))
                        indexData["METS"]["dmdSec"] = data
                        break

        indexData["transferMetadata"] = file_metadata

        # Get file path from FLocat and extension.
        flocat = ns.xml_find_premis(file_, "mets:FLocat")
        if flocat is not None:
            filePath = flocat.attrib["{http://www.w3.org/1999/xlink}href"]
            indexData["filePath"] = filePath
            _, fileExtension = os.path.splitext(filePath)
            if fileExtension:
                indexData["fileExtension"] = fileExtension[1:].lower()

        indexData["identifiers"] = self._get_file_identifiers(fileUUID)

        return indexData, accession_ids

    def _get_amdSec(self, admID: str) -> Optional[etree._Element]:
        """Get amdSec with given admID.

        :param admID: admID.
        :param doc: ElementTree object.
        :return: amdSec.
        """
        return ns.xml_find_premis(self.mets, f"mets:amdSec[@ID='{admID}']")

    def _get_file_uuid(self, amdSec: Optional[etree._Element]) -> Optional[str]:
        """Get UUID of a file from amdSec.

        :param amdSec: amdSec.
        :return: File UUID.
        """
        uuid = ns.xml_findtext_premis(
            amdSec,
            "mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectIdentifier/premis:objectIdentifierValue",
        )
        return uuid if isinstance(uuid, str) else None

    def _get_accession_number(self, amdSec: Optional[etree._Element]) -> Optional[str]:
        """Get accession number associated with a file from amdSec.

        Look for a <premis:event> entry within file's amdSec that has a
        <premis:eventType> of "registration". Return the text value (with leading
        "accession#" stripped out) from the <premis:eventOutcomeDetailNote>.

        If no matching <premis:event> entry is found, return None.

        :param amdSec: amdSec.
        :return: Accession number or None.
        """
        registration_detail_notes = ns.xml_xpath_premis(
            amdSec,
            ".//premis:event[premis:eventType='registration']/premis:eventOutcomeInformation/premis:eventOutcomeDetail/premis:eventOutcomeDetailNote",
        )
        if not registration_detail_notes or not isinstance(
            registration_detail_notes, list
        ):
            return None
        if not registration_detail_notes:
            return None
        element = registration_detail_notes[0]
        if not hasattr(element, "text"):
            return None
        detail_text = element.text
        if not isinstance(detail_text, str):
            return None
        ACCESSION_PREFIX = "accession#"
        return detail_text[len(ACCESSION_PREFIX) :]

    def _get_file_metadata(
        self, file_pointer_division: etree._Element
    ) -> dict[str, Any]:
        """Get descriptive metadata for a file pointer.

        There are various types of metadata elements extracted: dublin core
        and custom (non dublin core), both set through the metadata/metadata.csv
        file; and metadata added through the source-metadata.csv files and
        related XML files.

        These types are parsed and combined into a single dictionary of
        metadata attributes.
        """
        result: dict[str, Any] = {}
        elements_with_metadata: list[etree._Element] = []
        dmd_id = file_pointer_division.attrib.get("DMDID")
        if not dmd_id:
            return result
        for dmd_sec in self._get_latest_dmd_secs(dmd_id):
            elements_with_metadata += self._get_descriptive_section_metadata(dmd_sec)
        if elements_with_metadata:
            result = self._combine_elements(elements_with_metadata)
        return self._normalize_dict(result)

    def _get_latest_dmd_secs(self, dmd_id: str) -> list[etree._Element]:
        # Build a mapping of dmdSec by metadata type.
        dmd_secs: dict[str, list[etree._Element]] = {}
        for id in dmd_id.split():
            dmd_sec = ns.xml_find_premis(self.mets, f'mets:dmdSec[@ID="{id}"]')
            if not dmd_sec:
                continue
            # Use mdWrap MDTYPE and OTHERMDTYPE to generate a unique key.
            md_wrap = ns.xml_find_premis(dmd_sec, "mets:mdWrap")
            if not md_wrap:
                continue
            mdtype_key = md_wrap.attrib.get("MDTYPE")
            # Ignore PREMIS:OBJECT.
            if mdtype_key == "PREMIS:OBJECT":
                continue
            if mdtype_key is None:
                continue
            other_mdtype = md_wrap.attrib.get("OTHERMDTYPE")
            if other_mdtype:
                mdtype_key += "_" + other_mdtype
            if mdtype_key not in dmd_secs:
                dmd_secs[mdtype_key] = []
            dmd_secs[mdtype_key].append(dmd_sec)
        # Get only the latest dmdSec by type.
        final_dmd_secs: list[etree._Element] = []
        for _, secs in dmd_secs.items():
            latest_date = ""
            latest_sec: Optional[etree._Element] = None
            for sec in secs:
                date = sec.attrib.get("CREATED", "")
                if not latest_date or date > latest_date:
                    latest_date = date
                    latest_sec = sec
            # Do not add latest dmdSec if it's deleted.
            if latest_sec and latest_sec.attrib.get("STATUS", "") != "deleted":
                final_dmd_secs.append(latest_sec)
        return final_dmd_secs

    def _get_descriptive_section_metadata(
        self, dmdSec: etree._Element
    ) -> list[etree._Element]:
        """Get dublin core and custom descriptive metadata."""
        result: list[etree._Element] = []
        # look for dublincore terms in the dmdSec
        result += ns.xml_findall_premis(
            dmdSec, 'mets:mdWrap[@MDTYPE="DC"]/mets:xmlData/dcterms:dublincore'
        )
        # look for non dublincore (custom) metadata
        result += ns.xml_findall_premis(
            dmdSec, 'mets:mdWrap[@MDTYPE="OTHER"]/mets:xmlData'
        )
        return result

    def _combine_elements(self, elements: list[etree._Element]) -> dict[str, Any]:
        """Serialize all the elements as a JSON compatible string.

        Combine the elements contents into a single container and parse it
        with xmltodict.
        """
        # wrap the data from all metadata elements in a container
        container = etree.Element("container")
        for element in elements:
            for child in element:
                # add a copy to not modify the METS file in place
                container.append(copy.deepcopy(child))
        # parse the container with xmltodict ignoring element attributes
        return (
            xmltodict.parse(
                etree.tostring(container, encoding="utf8"), xml_attribs=False
            ).get("container")
            or {}
        )

    def _normalize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize dictionary from xmltodict for ES indexing.

        Because an XML element may contain text value or other elements, conversion
        to a dict can result in different value types for the same key. This causes
        problems in the Elasticsearch index as it expects consistent types. This
        function recurses a dict and appends "_dict" to the keys with a dict value.
        """
        new: dict[str, Any] = {}
        for key, value in data.items():
            dict_key = key + "_dict"
            if isinstance(value, dict):
                new[dict_key] = self._normalize_dict(value)
            elif isinstance(value, list):
                for item in value:
                    new_key = key
                    if isinstance(item, dict):
                        new_key = dict_key
                        item = self._normalize_dict(item)
                    if new_key not in new:
                        new[new_key] = []
                    new[new_key].append(item)
            else:
                new[key] = value
        return new

    def _get_file_identifiers(self, uuid: Optional[str]) -> list[str]:
        return list(
            Identifier.objects.filter(file=uuid).values_list("value", flat=True)
        )
