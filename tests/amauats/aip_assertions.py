from pathlib import Path
from typing import Any

import metsrw
from api_helpers import METS_NSMAP
from api_helpers import extract_document_text
from lxml import etree
from models import TransferRun

PREMIS_EVENT_TYPES = {
    "file format identification": "format identification",
    "ingestion": "ingestion",
    "message digest calculation": "message digest calculation",
    "reingestion": "reingestion",
    "validation": "validation",
    "virus scanning": "virus check",
}
MC_EVENT_DETAIL_PREFIX = 'program="MediaConch"'
MC_IMPLEMENTATION_CHECK_PREFIX = "MediaConch implementation check result:"
MC_POLICY_CHECK_PREFIX = "MediaConch policy check result"


def _require_aip_artifacts(
    transfer_run: TransferRun, *, reingested: bool = False
) -> None:
    if reingested:
        if (
            transfer_run.reingest_extracted_aip_dir is None
            or transfer_run.reingest_aip_mets_location is None
        ):
            raise AssertionError(
                "Reingested AIP has not been downloaded and extracted yet"
            )
        return
    if transfer_run.extracted_aip_dir is None or transfer_run.aip_mets_location is None:
        raise AssertionError("AIP has not been downloaded and extracted yet")


def _current_extracted_aip_dir(transfer_run: TransferRun) -> Path:
    if transfer_run.reingest_extracted_aip_dir is not None:
        extracted_aip_dir = transfer_run.reingest_extracted_aip_dir
        return Path(extracted_aip_dir)
    _require_aip_artifacts(transfer_run)
    assert transfer_run.extracted_aip_dir is not None
    extracted_aip_dir = transfer_run.extracted_aip_dir
    return Path(extracted_aip_dir)


def _current_aip_mets_location(transfer_run: TransferRun) -> Path:
    if transfer_run.reingest_aip_mets_location is not None:
        aip_mets_location = transfer_run.reingest_aip_mets_location
        return Path(aip_mets_location)
    _require_aip_artifacts(transfer_run)
    assert transfer_run.aip_mets_location is not None
    aip_mets_location = transfer_run.aip_mets_location
    return Path(aip_mets_location)


def _current_sip_uuid(transfer_run: TransferRun) -> str:
    if transfer_run.reingest_uuid is not None:
        return str(transfer_run.reingest_uuid)
    assert transfer_run.sip_uuid is not None
    return str(transfer_run.sip_uuid)


def _parse_mets_tree(
    transfer_run: TransferRun, *, reingested: bool = False
) -> etree._ElementTree:
    if reingested:
        _require_aip_artifacts(transfer_run, reingested=True)
        assert transfer_run.reingest_aip_mets_location is not None
        return etree.parse(str(transfer_run.reingest_aip_mets_location))
    return etree.parse(str(_current_aip_mets_location(transfer_run)))


def _load_mets_document(
    transfer_run: TransferRun, *, reingested: bool = False
) -> metsrw.METSDocument:
    if reingested:
        _require_aip_artifacts(transfer_run, reingested=True)
        assert transfer_run.reingest_aip_mets_location is not None
        return metsrw.METSDocument.fromfile(
            str(transfer_run.reingest_aip_mets_location)
        )
    return metsrw.METSDocument.fromfile(str(_current_aip_mets_location(transfer_run)))


def get_filesec_files(
    tree: etree._ElementTree,
    use: str | None = None,
) -> list[etree._Element]:
    use_query = ""
    if use:
        use_query = f'="{use}"'
    return list(
        tree.findall(
            f"mets:fileSec/mets:fileGrp[@USE{use_query}]/mets:file",
            METS_NSMAP,
        )
    )


def get_premis_events_by_type(entry: metsrw.FSEntry, event_type: str) -> list[Any]:
    events: list[Any] = list(entry.get_premis_events())
    return [event for event in events if getattr(event, "type", None) == event_type]


def _iter_validation_events(transfer_run: TransferRun) -> list[Any]:
    mets = _load_mets_document(transfer_run)
    events: list[Any] = []
    for entry in mets.all_files():
        events.extend(get_premis_events_by_type(entry, "validation"))
    return events


def assert_all_mediaconch_validation_events_have_outcome(
    transfer_run: TransferRun,
    *,
    outcome_detail_prefix: str,
    expected_outcome: str,
) -> None:
    matched_events = [
        event
        for event in _iter_validation_events(transfer_run)
        if isinstance(getattr(event, "detail", None), str)
        and isinstance(getattr(event, "event_outcome_detail_note", None), str)
        and event.detail.startswith(MC_EVENT_DETAIL_PREFIX)
        and event.event_outcome_detail_note.startswith(outcome_detail_prefix)
    ]
    assert matched_events
    for event in matched_events:
        assert event.outcome == expected_outcome


def assert_normalization_report_column_values(
    report_rows: list[dict[str, Any]],
    *,
    column: str,
    expected_value: str,
) -> None:
    assert report_rows
    for row in report_rows:
        if row.get("file_format") == "None":
            continue
        assert row.get(column) == expected_value


def get_transfer_dir_from_structmap(
    tree: etree._ElementTree,
    transfer_run: TransferRun,
    *,
    reingested: bool = False,
) -> etree._Element:
    struct_map = tree.find('mets:structMap[@TYPE="physical"]', namespaces=METS_NSMAP)
    assert struct_map is not None
    if reingested:
        transfer_suffix = _current_sip_uuid(transfer_run)
    else:
        assert transfer_run.sip_uuid is not None
        transfer_suffix = transfer_run.sip_uuid
    transfer_dir = struct_map.find(
        f'mets:div[@LABEL="{transfer_run.transfer_name}-{transfer_suffix}"][@TYPE="Directory"]',
        namespaces=METS_NSMAP,
    )
    assert transfer_dir is not None
    return transfer_dir


def get_submission_docs_from_structmap(
    tree: etree._ElementTree, transfer_run: TransferRun
) -> list[etree._Element]:
    transfer_dir = get_transfer_dir_from_structmap(tree, transfer_run)
    return list(
        transfer_dir.findall(
            'mets:div[@LABEL="objects"]/mets:div[@LABEL="submissionDocumentation"]//mets:div[@TYPE="Item"]',
            namespaces=METS_NSMAP,
        )
    )


def get_path_before_filename_change(
    entry: metsrw.FSEntry, transfer_contains_objects_dir: bool = False
) -> str:
    filename_change_events = get_premis_events_by_type(entry, "filename change")
    result: str
    if not filename_change_events:
        result = str(entry.path)
    else:
        event = filename_change_events[0]
        note = getattr(event, "event_outcome_detail_note", None)
        assert isinstance(note, str)
        parsed_note: dict[str, str] = dict(
            _parse_note_pair(pair) for pair in note.split(";")
        )
        result = parsed_note["Original name"][19:]
    if transfer_contains_objects_dir:
        return result
    return result[8:]


def _parse_note_pair(pair: str) -> tuple[str, str]:
    parsed = [value.strip(' "') for value in pair.strip().split("=", 1)]
    assert len(parsed) == 2
    return parsed[0], parsed[1]


def assert_structmap_item_path_exists(
    item: etree._Element, root_path: Path, parent_path: Path | None = None
) -> None:
    label = item.attrib.get("LABEL")
    if not label:
        return
    relative_parent = Path() if parent_path is None else parent_path
    path = root_path / relative_parent / label
    if item.attrib["TYPE"] == "Item":
        assert path.is_file()
    elif item.attrib["TYPE"] == "Directory":
        assert path.is_dir()
    else:
        raise ValueError(f'Unsupported structMap TYPE "{item.attrib["TYPE"]}"')
    for child in item:
        assert_structmap_item_path_exists(child, root_path, relative_parent / label)


def assert_mets_is_accessible_and_parseable(transfer_run: TransferRun) -> None:
    mets = _load_mets_document(transfer_run)
    assert mets.get_file(type="Directory", label="objects") is not None


def assert_mets_hdr_dates(
    transfer_run: TransferRun, *, lastmod_required: bool = False
) -> None:
    tree = _parse_mets_tree(transfer_run)
    mets_hdr_elements = tree.findall(".//mets:metsHdr", METS_NSMAP)
    assert len(mets_hdr_elements) == 1
    mets_hdr = mets_hdr_elements[0]
    assert mets_hdr.get("CREATEDATE")
    if lastmod_required:
        assert mets_hdr.get("LASTMODDATE")
    else:
        assert mets_hdr.get("LASTMODDATE") is None


def assert_dmdsec_count(transfer_run: TransferRun, expected_count: int) -> None:
    tree = _parse_mets_tree(transfer_run)
    dmdsec_elements = tree.findall(".//mets:dmdSec", METS_NSMAP)
    actual_count = len(dmdsec_elements)
    assert actual_count == expected_count, (
        f"Expected {expected_count} dmdSec element(s), got {actual_count}"
    )


def assert_expected_content_and_structure(transfer_run: TransferRun) -> None:
    root = _current_extracted_aip_dir(transfer_run)
    expected_directories = [
        Path("data/objects"),
        Path("data/logs"),
        Path("data/objects/submissionDocumentation"),
    ]
    for relative_directory in expected_directories:
        assert (root / relative_directory).is_dir()


def assert_transfer_files_are_present(transfer_run: TransferRun) -> None:
    mets = _load_mets_document(transfer_run)
    contains_objects_dir = (transfer_run.transfer_source_path / "objects").is_dir()
    original_file_paths = [
        get_path_before_filename_change(entry, contains_objects_dir)
        for entry in mets.all_files()
        if entry.use == "original"
    ]
    assert original_file_paths
    for relative_path in original_file_paths:
        assert (transfer_run.transfer_source_path / relative_path).exists()


def assert_data_directory_contains_file(
    transfer_run: TransferRun, relative_path: str, *, reingested: bool = False
) -> None:
    if reingested:
        _require_aip_artifacts(transfer_run, reingested=True)
        assert transfer_run.reingest_extracted_aip_dir is not None
        assert (transfer_run.reingest_extracted_aip_dir / relative_path).is_file()
        return
    assert (_current_extracted_aip_dir(transfer_run) / relative_path).is_file()


def assert_data_directory_contains_mets_file(transfer_run: TransferRun) -> None:
    assert _current_aip_mets_location(transfer_run).is_file()


def assert_filesec_records_all_aip_files(transfer_run: TransferRun) -> None:
    tree = _parse_mets_tree(transfer_run)
    filesec_files = get_filesec_files(tree)
    assert filesec_files
    root = _current_extracted_aip_dir(transfer_run)
    for filesec_file in filesec_files:
        flocat = filesec_file.find("mets:FLocat", namespaces=METS_NSMAP)
        assert flocat is not None
        href = flocat.attrib["{http://www.w3.org/1999/xlink}href"]
        assert (root / "data" / href).exists()


def assert_structmap_matches_physical_layout(transfer_run: TransferRun) -> None:
    tree = _parse_mets_tree(transfer_run)
    transfer_dir = get_transfer_dir_from_structmap(tree, transfer_run)
    assert len(transfer_dir)
    root_path = _current_extracted_aip_dir(transfer_run) / "data"
    for item in transfer_dir:
        assert_structmap_item_path_exists(item, root_path)


def assert_every_object_has_uuid(transfer_run: TransferRun) -> None:
    tree = _parse_mets_tree(transfer_run)
    filesec_files = get_filesec_files(tree)
    assert filesec_files
    for filesec_file in filesec_files:
        file_uuid = filesec_file.attrib["ID"].split("file-")[-1]
        amdsec_id = filesec_file.attrib["ADMID"]
        object_uuid_nodes = tree.xpath(
            "mets:amdSec[@ID=$amdsec_id]/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/"
            'premis:objectIdentifier/premis:objectIdentifierType[text()="UUID"]/../premis:objectIdentifierValue',
            namespaces=METS_NSMAP,
            amdsec_id=amdsec_id,
        )
        assert len(object_uuid_nodes) == 1
        assert object_uuid_nodes[0].text == file_uuid


def assert_every_object_has_amdsec(transfer_run: TransferRun) -> None:
    tree = _parse_mets_tree(transfer_run)
    filesec_files = get_filesec_files(tree)
    assert filesec_files
    for filesec_file in filesec_files:
        amdsec_id = filesec_file.attrib["ADMID"]
        amdsec = tree.find(f'mets:amdSec[@ID="{amdsec_id}"]', namespaces=METS_NSMAP)
        assert amdsec is not None


def assert_every_premis_event_records_expected_agents(
    transfer_run: TransferRun,
) -> None:
    tree = _parse_mets_tree(transfer_run)
    expected_agent_types = {
        "Archivematica user pk",
        "repository code",
        "preservation system",
    }
    premis_events = tree.findall(
        'mets:amdSec/mets:digiprovMD/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]/mets:xmlData/premis:event',
        namespaces=METS_NSMAP,
    )
    assert premis_events
    for event in premis_events:
        event_agents = event.findall(
            "premis:linkingAgentIdentifier", namespaces=METS_NSMAP
        )
        event_agent_types = {
            event_agent.findtext(
                "premis:linkingAgentIdentifierType", namespaces=METS_NSMAP
            )
            for event_agent in event_agents
        }
        assert event_agent_types == expected_agent_types


def assert_source_md_in_bagit_mets(
    transfer_run: TransferRun, *, reingested: bool = False
) -> None:
    tree = _parse_mets_tree(transfer_run, reingested=reingested)
    source_md_elements = tree.xpath("mets:amdSec/mets:sourceMD", namespaces=METS_NSMAP)
    assert source_md_elements
    assert len(source_md_elements) == 1
    md_wraps = source_md_elements[0].xpath("mets:mdWrap", namespaces=METS_NSMAP)
    assert md_wraps
    assert md_wraps[0].attrib["OTHERMDTYPE"] == "BagIt"
    transfer_md = md_wraps[0].xpath(
        "mets:xmlData/transfer_metadata", namespaces=METS_NSMAP
    )
    assert transfer_md
    assert len(transfer_md[0]) > 0


def assert_submission_documentation_policy_file(
    transfer_run: TransferRun,
    policy_file: str,
    *,
    should_exist: bool,
) -> None:
    root = _current_extracted_aip_dir(transfer_run)
    policy_path = (
        root / "data" / "objects" / "submissionDocumentation" / "policies" / policy_file
    )
    if should_exist:
        assert policy_path.is_file()
        return
    assert not policy_path.exists()


def _assert_mediaconch_output_directory(path: Path) -> None:
    assert path.is_dir()
    outputs = [
        item for item in path.iterdir() if item.is_file() and item.suffix == ".xml"
    ]
    assert outputs
    for output in outputs:
        tree = etree.parse(str(output))
        assert tree.getroot().tag == "{https://mediaarea.net/mediaconch}MediaConch"


def assert_transfer_logs_contain_policy_outputs(
    transfer_run: TransferRun,
    policy_file: str,
) -> None:
    root = _current_extracted_aip_dir(transfer_run)
    policy_name = Path(policy_file).stem
    output_dir = (
        root
        / "data"
        / "logs"
        / "transfers"
        / f"{transfer_run.transfer_name}-{transfer_run.transfer_uuid}"
        / "logs"
        / "policyChecks"
        / policy_name
    )
    _assert_mediaconch_output_directory(output_dir)


def assert_logs_contain_policy_outputs(
    transfer_run: TransferRun,
    policy_file: str,
) -> None:
    root = _current_extracted_aip_dir(transfer_run)
    policy_name = Path(policy_file).stem
    output_dir = root / "data" / "logs" / "policyChecks" / policy_name
    _assert_mediaconch_output_directory(output_dir)


def assert_ddi_metadata_present(transfer_run: TransferRun) -> None:
    tree = _parse_mets_tree(transfer_run)
    namespaces = dict(METS_NSMAP)
    namespaces["ddi"] = "http://www.icpsr.umich.edu/DDI"
    transfer_dir = get_transfer_dir_from_structmap(tree, transfer_run)
    objects_dir = transfer_dir.find('mets:div[@LABEL="objects"]', namespaces=METS_NSMAP)
    assert objects_dir is not None
    dmdsec_ids = objects_dir.attrib["DMDID"].strip().split(" ")
    for dmdsec_id in dmdsec_ids:
        ddi_codebook = tree.find(
            f'mets:dmdSec[@ID="{dmdsec_id}"]/mets:mdWrap/mets:xmlData/ddi:codebook',
            namespaces=namespaces,
        )
        if ddi_codebook is not None:
            return
    raise AssertionError(
        "Expected DDI metadata in one of the objects directory dmdSecs"
    )


def assert_event_count_per_original(
    transfer_run: TransferRun,
    event_type: str,
    expected_count: int,
) -> None:
    mets = _load_mets_document(
        transfer_run,
        reingested=(event_type == "reingestion"),
    )
    original_files = [entry for entry in mets.all_files() if entry.use == "original"]
    assert original_files
    mapped_event_type = PREMIS_EVENT_TYPES[event_type]
    for entry in original_files:
        events = get_premis_events_by_type(entry, mapped_event_type)
        assert len(events) == expected_count


def assert_original_files_with_event_count(
    transfer_run: TransferRun,
    event_type: str,
    expected_file_count: int,
) -> None:
    if expected_file_count == 0:
        return
    mets = _load_mets_document(transfer_run)
    original_files = [entry for entry in mets.all_files() if entry.use == "original"]
    assert original_files
    mapped_event_type = PREMIS_EVENT_TYPES[event_type]
    files_with_event = [
        entry
        for entry in original_files
        if get_premis_events_by_type(entry, mapped_event_type)
    ]
    assert len(files_with_event) == expected_file_count


def assert_current_and_superseded_techmd_per_original(
    transfer_run: TransferRun,
) -> None:
    mets = _load_mets_document(transfer_run, reingested=True)
    original_files = [entry for entry in mets.all_files() if entry.use == "original"]
    assert original_files
    for entry in original_files:
        techmds = mets.tree.findall(
            f'mets:amdSec[@ID="{entry.admids[0]}"]/mets:techMD',
            namespaces=METS_NSMAP,
        )
        techmd_statuses = sorted(techmd.attrib["STATUS"] for techmd in techmds)
        assert techmd_statuses == ["current", "superseded"]


def assert_deleted_filesec_for_renormalized_objects(transfer_run: TransferRun) -> None:
    reingest_mets = _load_mets_document(transfer_run, reingested=True)
    deleted_files = get_filesec_files(reingest_mets.tree, use="deleted")
    deleted_file_uuids = [
        deleted_file.attrib["GROUPID"][6:] for deleted_file in deleted_files
    ]
    initial_mets = _load_mets_document(transfer_run, reingested=False)
    original_files = [
        entry for entry in initial_mets.all_files() if entry.use == "original"
    ]
    assert original_files
    for entry in original_files:
        if get_premis_events_by_type(entry, "normalization"):
            assert entry.file_uuid in deleted_file_uuids


def retrieve_md_section_ids(
    tree: etree._ElementTree, section: str, md_type: str
) -> set[str]:
    md_sec_ids = set()
    for md_sec in tree.findall(section, namespaces=METS_NSMAP):
        md_sec_id = md_sec.get("ID")
        if md_sec_id is None:
            continue
        for child in md_sec:
            if child.get("MDTYPE") == md_type:
                md_sec_ids.add(md_sec_id)
    return md_sec_ids


def retrieve_rights_linking_object_identifiers(
    tree: etree._ElementTree,
) -> set[str]:
    rights_objects = tree.findall(
        "mets:amdSec/mets:rightsMD/mets:mdWrap/mets:xmlData/premis:rightsStatement/"
        "premis:linkingObjectIdentifier/premis:linkingObjectIdentifierValue",
        namespaces=METS_NSMAP,
    )
    return {identifier.text for identifier in rights_objects if identifier.text}


def assert_dc_dmdsec_count_for_object_type(
    transfer_run: TransferRun, object_type: str, expected_count: int
) -> None:
    mets = _load_mets_document(transfer_run)
    dmd_sec_ids = retrieve_md_section_ids(mets.tree, "mets:dmdSec", "DC")
    directory_ids: list[str] = []
    item_ids: list[str] = []
    for entry in mets.all_files():
        for dmd_sec in entry.dmdsecs:
            if dmd_sec.id_string not in dmd_sec_ids:
                continue
            if entry.mets_div_type == "Directory":
                directory_ids.append(dmd_sec.id_string)
            elif entry.mets_div_type == "Item" and entry.use == "original":
                item_ids.append(dmd_sec.id_string)
    if object_type == "original objects":
        assert len(item_ids) == expected_count
        return
    if object_type == "directories":
        assert len(directory_ids) == expected_count
        return
    raise ValueError(f"Unsupported object type {object_type!r}")


def assert_rights_md_object_count(
    transfer_run: TransferRun, expected_count: int
) -> None:
    mets = _load_mets_document(transfer_run)
    rights_linking_ids = retrieve_rights_linking_object_identifiers(mets.tree)
    assert len(rights_linking_ids) == expected_count


def assert_premis_rights_entries_count(
    transfer_run: TransferRun, expected_count: int
) -> None:
    mets = _load_mets_document(transfer_run)
    rights_md_ids = retrieve_md_section_ids(
        mets.tree,
        "mets:amdSec/mets:rightsMD",
        "PREMIS:RIGHTS",
    )
    assert len(rights_md_ids) == expected_count


def assert_submission_document_count(
    transfer_run: TransferRun, expected_count: int
) -> None:
    tree = _parse_mets_tree(transfer_run)
    submission_docs = [
        doc
        for doc in get_submission_docs_from_structmap(tree, transfer_run)
        if doc.get("LABEL") != "METS.xml"
    ]
    assert len(submission_docs) == expected_count


def assert_reingest_metadata_directory_contains_file(
    transfer_run: TransferRun, metadata_file: str
) -> None:
    assert_data_directory_contains_file(
        transfer_run,
        f"data/objects/metadata/{metadata_file}",
        reingested=True,
    )


def assert_dip_contains_access_copy_for_each_original_object(
    transfer_run: TransferRun,
) -> None:
    assert transfer_run.extracted_dip_dir is not None
    initial_mets = _load_mets_document(transfer_run, reingested=False)
    original_file_uuids = {
        entry.file_uuid for entry in initial_mets.all_files() if entry.use == "original"
    }
    assert original_file_uuids
    dip_file_uuids = {
        entry.name[:36]
        for entry in (transfer_run.extracted_dip_dir / "objects").iterdir()
        if entry.is_file()
    }
    assert original_file_uuids == dip_file_uuids


def assert_metadata_csv_files_have_original_and_updated_dmdsecs(
    transfer_run: TransferRun,
) -> None:
    expected_statuses = ("original-superseded", "update")
    assert transfer_run.metadata_csv_files
    assert transfer_run.reingest_metadata_csv_files
    reingest_mets = _load_mets_document(transfer_run, reingested=True)
    original_filenames = {
        str(row["filename"])
        for row in transfer_run.metadata_csv_files
        if "filename" in row
    }
    rows = [
        row
        for row in transfer_run.reingest_metadata_csv_files
        if str(row.get("filename")) in original_filenames
    ]
    assert rows
    namespaces_by_url = {namespace: prefix for prefix, namespace in METS_NSMAP.items()}
    for row in rows:
        filename = str(row["filename"])
        entry = reingest_mets.get_file(path=filename)
        dmdsecs_by_status: dict[str, Any] = {}
        for expected_status in expected_statuses:
            dmdsecs = [
                dmdsec for dmdsec in entry.dmdsecs if dmdsec.status == expected_status
            ]
            assert len(dmdsecs) == 1
            dmdsecs_by_status[expected_status] = dmdsecs[0]
        for child in dmdsecs_by_status["update"].contents.document:
            q_name = etree.QName(child.tag)
            namespace = q_name.namespace
            localname = q_name.localname
            if namespace is None:
                continue
            csv_field = f"{namespaces_by_url[namespace]}.{localname}"
            row_value = row.get(csv_field)
            assert isinstance(row_value, str)
            assert row_value == child.text.strip()


def assert_source_metadata_files_have_wrapped_original_dmdsecs(
    transfer_run: TransferRun, dmdsec_status: str
) -> None:
    _assert_source_metadata_rows_have_expected_dmdsecs(
        rows=transfer_run.reingest_source_metadata_files
        if transfer_run.reingest_source_metadata_files
        else transfer_run.source_metadata_files,
        mets=_load_mets_document(transfer_run),
        expected_statuses=(dmdsec_status,),
    )


def _assert_source_metadata_rows_have_expected_dmdsecs(
    *,
    rows: list[dict[str, Any]],
    mets: metsrw.METSDocument,
    expected_statuses: tuple[str, ...],
) -> None:
    expected_mdwrap_mdtypes = ("OTHER",)
    for row in rows:
        original_filename = str(row["original_filename"])
        entry = mets.get_file(label=original_filename)
        dmdsecs_by_status: dict[str, Any] = {}
        for expected_status in expected_statuses:
            dmdsecs = [
                dmdsec
                for dmdsec in entry.dmdsecs
                if dmdsec.status == expected_status
                and dmdsec.contents.mdtype in expected_mdwrap_mdtypes
                and dmdsec.contents.othermdtype == row["type_id"]
            ]
            assert len(dmdsecs) == 1
            dmdsecs_by_status[expected_status] = dmdsecs[0]
        wrapped_text = extract_document_text(
            dmdsecs_by_status[expected_statuses[-1]].contents.document
        )
        metadata_text = extract_document_text(row["document"])
        assert wrapped_text
        assert wrapped_text == metadata_text


def assert_existing_source_metadata_files_are_superseded_and_updated(
    transfer_run: TransferRun,
) -> None:
    assert transfer_run.source_metadata_files
    assert transfer_run.reingest_source_metadata_files
    reingest_mets = _load_mets_document(transfer_run, reingested=True)
    original_filenames = {
        str(row["metadata_filename"])
        for row in transfer_run.source_metadata_files
        if row.get("metadata_filename")
    }
    rows = [
        row
        for row in transfer_run.reingest_source_metadata_files
        if str(row.get("metadata_filename")) in original_filenames
    ]
    assert rows
    for row in rows:
        entry = reingest_mets.get_file(label=str(row["original_filename"]))
        dmdsecs = [
            dmdsec
            for dmdsec in entry.dmdsecs
            if dmdsec.contents.mdtype == "OTHER"
            and dmdsec.contents.othermdtype == row["type_id"]
            and dmdsec.status in {"original-superseded", "update"}
        ]
        assert len(dmdsecs) == 2
        assert len({dmdsec.group_id for dmdsec in dmdsecs}) == 1
        update_dmdsec = next(dmdsec for dmdsec in dmdsecs if dmdsec.status == "update")
        assert extract_document_text(
            update_dmdsec.contents.document
        ) == extract_document_text(row["document"])


def assert_new_source_metadata_files_have_update_dmdsecs(
    transfer_run: TransferRun, dmdsec_status: str
) -> None:
    assert transfer_run.source_metadata_files
    assert transfer_run.reingest_source_metadata_files
    original_filenames = {
        str(row["metadata_filename"])
        for row in transfer_run.source_metadata_files
        if row.get("metadata_filename")
    }
    rows = [
        row
        for row in transfer_run.reingest_source_metadata_files
        if row.get("metadata_filename")
        and str(row["metadata_filename"]) not in original_filenames
    ]
    if not rows:
        return
    _assert_source_metadata_rows_have_expected_dmdsecs(
        rows=rows,
        mets=_load_mets_document(transfer_run, reingested=True),
        expected_statuses=(dmdsec_status,),
    )


def assert_deleted_source_metadata_files_have_deleted_dmdsecs(
    transfer_run: TransferRun, dmdsec_status: str
) -> None:
    assert transfer_run.source_metadata_files
    assert transfer_run.reingest_source_metadata_files
    original_by_type_id = {
        str(row["type_id"]): row for row in transfer_run.source_metadata_files
    }
    rows = [
        row
        for row in transfer_run.reingest_source_metadata_files
        if not row.get("metadata_filename")
        and str(row["type_id"]) in original_by_type_id
    ]
    assert rows
    reingest_mets = _load_mets_document(transfer_run, reingested=True)
    for row in rows:
        entry = reingest_mets.get_file(label=str(row["original_filename"]))
        dmdsecs = [
            dmdsec
            for dmdsec in entry.dmdsecs
            if dmdsec.status == dmdsec_status
            and dmdsec.contents.mdtype == "OTHER"
            and dmdsec.contents.othermdtype == row["type_id"]
        ]
        assert len(dmdsecs) == 1
        original_row = original_by_type_id[str(row["type_id"])]
        assert extract_document_text(
            dmdsecs[0].contents.document
        ) == extract_document_text(original_row["document"])


def get_passed_metadata_validation_events(entry: metsrw.FSEntry) -> list[Any]:
    return [
        event
        for event in get_premis_events_by_type(entry, "validation")
        if getattr(event, "parsed_event_detail", {})
        and _is_metadata_validation_event(event.parsed_event_detail)
        and event.outcome == "pass"
    ]


def _is_metadata_validation_event(event_detail: dict[str, str]) -> bool:
    return (
        set(event_detail.keys())
        == {"type", "validation-source-type", "validation-source", "program", "version"}
        and event_detail["type"] == "metadata"
    )


def assert_metadata_files_have_passed_validation_events(
    transfer_run: TransferRun,
) -> None:
    mets = _load_mets_document(transfer_run)
    rows = (
        transfer_run.reingest_source_metadata_files
        if transfer_run.reingest_source_metadata_files
        else transfer_run.source_metadata_files
    )
    for row in rows:
        metadata_filename = row.get("metadata_filename")
        if not metadata_filename:
            continue
        files = [
            entry
            for entry in mets.all_files()
            if entry.use == "metadata"
            and entry.path
            and str(entry.path).endswith(str(metadata_filename))
        ]
        if len(files) > 1:
            files = [
                entry
                for entry in files
                if entry.path == Path("objects") / "metadata" / str(metadata_filename)
            ]
        if not files:
            continue
        events = get_passed_metadata_validation_events(files[0])
        if events:
            assert len(events) == 1


def assert_structural_map_was_imported(transfer_run: TransferRun) -> None:
    assert transfer_run.extracted_aip_dir is not None
    assert transfer_run.aip_mets_location is not None
    imported_structmap_path = (
        transfer_run.extracted_aip_dir
        / "data"
        / "objects"
        / "metadata"
        / "transfers"
        / f"{transfer_run.transfer_name}-{transfer_run.transfer_uuid}"
        / "mets_structmap.xml"
    )
    assert imported_structmap_path.exists()
    mets = etree.parse(str(transfer_run.aip_mets_location))
    mets_logical_structmaps = [
        element
        for element in mets.findall(
            'mets:structMap[@TYPE="logical"]', namespaces=METS_NSMAP
        )
        if element.attrib.get("LABEL") != "Normative Directory Structure"
    ]
    assert mets_logical_structmaps
    imported_structmap_doc = etree.parse(str(imported_structmap_path))
    imported_structmap = imported_structmap_doc.find(
        'mets:structMap[@TYPE="logical"]',
        namespaces=METS_NSMAP,
    )
    assert imported_structmap is not None
    assert_equal_lxml_elements(mets_logical_structmaps[0], imported_structmap)


def assert_equal_lxml_elements(left: etree._Element, right: etree._Element) -> None:
    assert left.tag == right.tag
    assert left.text == right.text
    assert len(left) == len(right)
    left_attributes = dict(left.attrib)
    right_attributes = dict(right.attrib)
    for ignored_attribute in ("ID", "FILEID"):
        left_attributes.pop(ignored_attribute, None)
        right_attributes.pop(ignored_attribute, None)
    assert left_attributes == right_attributes
    for left_child, right_child in zip(left, right, strict=False):
        assert_equal_lxml_elements(left_child, right_child)


def assert_dspace_descriptive_metadata_sections(transfer_run: TransferRun) -> None:
    tree = _parse_mets_tree(transfer_run)
    original_files = get_filesec_files(tree, use="original")
    assert original_files
    for original_file in original_files:
        dmdsec_ids = original_file.attrib.get("DMDID", "").split()
        assert len(dmdsec_ids) == 2
        xpointer_dmdsec_id, dc_dmdsec_id = dmdsec_ids
        pointer = tree.find(
            f'//mets:dmdSec[@ID="{xpointer_dmdsec_id}"]/mets:mdRef',
            namespaces=METS_NSMAP,
        )
        assert pointer is not None
        assert pointer.attrib.get("LABEL", "").startswith("mets.xml")
        assert pointer.attrib.get("XPTR", "").startswith("xpointer(id(")
        for attr, expected_value in (
            ("MDTYPE", "OTHER"),
            ("LOCTYPE", "OTHER"),
            ("OTHERLOCTYPE", "SYSTEM"),
        ):
            assert pointer.attrib.get(attr, "") == expected_value
        identifier = tree.find(
            f'//mets:dmdSec[@ID="{dc_dmdsec_id}"]/mets:mdWrap[@MDTYPE="DC"]/mets:xmlData/dcterms:dublincore/dc:identifier',
            namespaces=METS_NSMAP,
        )
        is_part_of = tree.find(
            f'//mets:dmdSec[@ID="{dc_dmdsec_id}"]/mets:mdWrap[@MDTYPE="DC"]/mets:xmlData/dcterms:dublincore/dcterms:isPartOf',
            namespaces=METS_NSMAP,
        )
        assert identifier is not None
        assert is_part_of is not None


def assert_dspace_rights_metadata_sections(transfer_run: TransferRun) -> None:
    tree = _parse_mets_tree(transfer_run)
    original_files = get_filesec_files(tree, use="original")
    assert original_files
    for original_file in original_files:
        amdsec_ids = original_file.attrib.get("ADMID", "").split()
        assert amdsec_ids
        xpointer_amdsec_id = amdsec_ids[0]
        pointer = tree.find(
            f'//mets:amdSec[@ID="{xpointer_amdsec_id}"]/mets:rightsMD/mets:mdRef',
            namespaces=METS_NSMAP,
        )
        assert pointer is not None
        assert pointer.attrib.get("LABEL", "").startswith("mets.xml")
        assert pointer.attrib.get("XPTR", "").startswith("xpointer(id(")
        for attr, expected_value in (
            ("MDTYPE", "OTHER"),
            ("OTHERMDTYPE", "METSRIGHTS"),
            ("LOCTYPE", "OTHER"),
            ("OTHERLOCTYPE", "SYSTEM"),
        ):
            assert pointer.attrib.get(attr, "") == expected_value


def assert_filesec_is_sorted_by_file_group(transfer_run: TransferRun) -> None:
    tree = _parse_mets_tree(transfer_run)
    file_groups = tree.findall("mets:fileSec/mets:fileGrp", namespaces=METS_NSMAP)
    expected_order = [
        "original",
        "submissionDocumentation",
        "preservation",
        "service",
        "access",
        "license",
        "text/ocr",
        "metadata",
        "derivative",
    ]
    uses = [file_group.attrib.get("USE") for file_group in file_groups]
    uses_order_indexes = [expected_order.index(use) for use in uses]
    assert uses_order_indexes == sorted(uses_order_indexes)
