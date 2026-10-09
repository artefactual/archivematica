"""Test extracting additional identifiers for indexing."""

import os

from archivematica.archivematicaCommon import identifier_functions

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(THIS_DIR, "fixtures")
MODS_METS_PATH = os.path.join(FIXTURES_DIR, "test-identifiers-MODS-METS.xml")
ISLANDORA_METS_PATH = os.path.join(FIXTURES_DIR, "test-identifiers-islandora-METS.xml")


def test_mods() -> None:
    """It should return all identifiers."""
    identifiers = identifier_functions.extract_identifiers_from_mods(MODS_METS_PATH)
    assert sorted(identifiers) == [
        "28475",
        "Glaive 18",
        "Yamani",
        "http://archives.tortall.gov/yamani/permalink/28475",
    ]


def test_islandora() -> None:
    """It should return the object ID."""
    assert identifier_functions.extract_identifier_from_islandora(
        ISLANDORA_METS_PATH
    ) == ["yamani:12"]


def test_islandora_no_id() -> None:
    """It should return an empty list for a METS document without an OBJID."""
    assert identifier_functions.extract_identifier_from_islandora(MODS_METS_PATH) == []
