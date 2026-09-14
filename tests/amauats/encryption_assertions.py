import subprocess
import tarfile
from pathlib import Path

from api_helpers import METS_NSMAP
from lxml import etree


def _parse_pointer(pointer_path: Path) -> etree._ElementTree:
    return etree.parse(str(pointer_path))


def _first_file_element(pointer_path: Path) -> etree._Element:
    tree = _parse_pointer(pointer_path)
    file_el = tree.find("mets:fileSec/mets:fileGrp/mets:file", METS_NSMAP)
    assert file_el is not None
    return file_el


def get_pointer_aip_path(pointer_path: Path) -> Path:
    file_el = _first_file_element(pointer_path)
    flocat_el = file_el.find("mets:FLocat", METS_NSMAP)
    assert flocat_el is not None
    href = flocat_el.attrib.get("{http://www.w3.org/1999/xlink}href")
    assert isinstance(href, str) and href
    return Path(href)


def _find_premis_event(pointer_path: Path, event_type: str) -> etree._Element:
    tree = _parse_pointer(pointer_path)
    for event_el in tree.findall('.//mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', METS_NSMAP):
        event_type_el = event_el.find(
            "mets:xmlData/premis:event/premis:eventType",
            METS_NSMAP,
        )
        if (
            event_type_el is not None
            and (event_type_el.text or "").strip() == event_type
        ):
            return event_el
    raise AssertionError(
        f"Could not find PREMIS event {event_type!r} in pointer file {pointer_path}"
    )


def get_pointer_event_uuid(pointer_path: Path, event_type: str) -> str:
    event_el = _find_premis_event(pointer_path, event_type)
    value = event_el.findtext(
        "mets:xmlData/premis:event/premis:eventIdentifier/premis:eventIdentifierValue",
        namespaces=METS_NSMAP,
    )
    assert isinstance(value, str) and value.strip()
    return value.strip()


def assert_pointer_has_event(
    pointer_path: Path,
    *,
    event_type: str,
    outcome_contains: tuple[str, ...] = (),
    outcome_detail_contains: tuple[str, ...] = (),
    detail_contains: tuple[str, ...] = (),
) -> str:
    event_el = _find_premis_event(pointer_path, event_type)
    detail_text = (
        event_el.findtext(
            "mets:xmlData/premis:event/premis:eventDetailInformation/premis:eventDetail",
            namespaces=METS_NSMAP,
        )
        or ""
    ).strip()
    outcome_text = (
        event_el.findtext(
            "mets:xmlData/premis:event/premis:eventOutcomeInformation/premis:eventOutcome",
            namespaces=METS_NSMAP,
        )
        or ""
    ).strip()
    outcome_detail_text = (
        event_el.findtext(
            "mets:xmlData/premis:event/premis:eventOutcomeInformation/premis:eventOutcomeDetail/premis:eventOutcomeDetailNote",
            namespaces=METS_NSMAP,
        )
        or ""
    ).strip()
    for expected in detail_contains:
        assert expected in detail_text
    for expected in outcome_contains:
        assert expected in outcome_text
    for expected in outcome_detail_contains:
        assert expected in outcome_detail_text
    return get_pointer_event_uuid(pointer_path, event_type)


def assert_pointer_has_encryption_event(pointer_path: Path) -> str:
    return assert_pointer_has_event(
        pointer_path,
        event_type="encryption",
        detail_contains=("GPG", "version="),
        outcome_detail_contains=('Status="encryption ok"',),
    )


def assert_pointer_has_encryption_transform(
    pointer_path: Path,
    *,
    fingerprint: str | None = None,
) -> None:
    tree = _parse_pointer(pointer_path)
    file_el = tree.find("mets:fileSec/mets:fileGrp/mets:file", METS_NSMAP)
    assert file_el is not None
    decompression = file_el.find(
        'mets:transformFile[@TRANSFORMTYPE="decompression"]',
        METS_NSMAP,
    )
    assert decompression is not None
    assert decompression.get("TRANSFORMORDER") == "2"
    decryption = file_el.find(
        'mets:transformFile[@TRANSFORMTYPE="decryption"]',
        METS_NSMAP,
    )
    assert decryption is not None
    assert decryption.get("TRANSFORMORDER") == "1"
    assert decryption.get("TRANSFORMALGORITHM") == "GPG"
    if fingerprint is not None:
        assert decryption.get("TRANSFORMKEY") == fingerprint
    composition_level = tree.findtext(
        "mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/"
        "premis:objectCharacteristics/premis:compositionLevel",
        namespaces=METS_NSMAP,
    )
    assert composition_level == "2"
    inhibitor_type = tree.findtext(
        "mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/"
        "premis:objectCharacteristics/premis:inhibitors/premis:inhibitorType",
        namespaces=METS_NSMAP,
    )
    inhibitor_target = tree.findtext(
        "mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/"
        "premis:objectCharacteristics/premis:inhibitors/premis:inhibitorTarget",
        namespaces=METS_NSMAP,
    )
    assert inhibitor_type == "GPG"
    assert inhibitor_target == "All content"


def assert_pointer_derivation_relationship(
    pointer_path: Path,
    *,
    related_object_uuid: str,
    event_uuid: str,
) -> None:
    tree = _parse_pointer(pointer_path)
    relationship = tree.find(
        './/mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]/mets:xmlData/premis:object/premis:relationship',
        METS_NSMAP,
    )
    assert relationship is not None
    assert (
        relationship.findtext("premis:relationshipType", namespaces=METS_NSMAP)
        == "derivation"
    )
    assert (
        relationship.findtext(
            "premis:relatedObjectIdentifier/premis:relatedObjectIdentifierValue",
            namespaces=METS_NSMAP,
        )
        == related_object_uuid
    )
    assert (
        relationship.findtext(
            "premis:relatedEventIdentifier/premis:relatedEventIdentifierValue",
            namespaces=METS_NSMAP,
        )
        == event_uuid
    )


def _can_list_archive(path: Path) -> bool:
    result = subprocess.run(
        ["7z", "l", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def assert_on_disk_package_encrypted(pointer_path: Path) -> None:
    package_path = get_pointer_aip_path(pointer_path)
    assert_on_disk_path_encrypted(package_path)


def assert_on_disk_path_encrypted(package_path: Path) -> None:
    assert package_path.exists()
    assert not package_path.is_dir()
    assert not tarfile.is_tarfile(package_path)
    assert not _can_list_archive(package_path)


def assert_on_disk_package_not_encrypted(pointer_path: Path) -> None:
    package_path = get_pointer_aip_path(pointer_path)
    assert package_path.exists()
    assert _can_list_archive(package_path) or tarfile.is_tarfile(package_path)


def assert_downloaded_aip_is_not_encrypted(archive_path: Path) -> None:
    assert archive_path.exists()
    assert _can_list_archive(archive_path) or tarfile.is_tarfile(archive_path)


def assert_downloaded_uncompressed_aip_is_tarfile(archive_path: Path) -> None:
    assert archive_path.exists()
    assert tarfile.is_tarfile(archive_path)


def assert_archives_are_identical(left: Path, right: Path) -> None:
    assert left.is_file()
    assert right.is_file()
    assert left.read_bytes() == right.read_bytes()
