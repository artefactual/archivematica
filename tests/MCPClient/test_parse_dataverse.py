#!/usr/bin/env python
"""Tests for the parse Dataverse functionality in Archivematica."""

import datetime
import os
import uuid

import metsrw
import pytest

from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import (
    parse_dataverse_mets as parse_dataverse,
)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(THIS_DIR, "fixtures")

# UUID of the transfer of the dataverse_transfer fixture.
TRANSFER_UUID = str(uuid.uuid4())

# Transfer location is repeated throughout.
TRANSFER_LOCATION = "%transferDirectory%objects"

# Location of the Dataverse transfer for test's sakes.
UNIT_PATH = os.path.join(FIXTURES_DIR, "dataverse", "")


def load_mets(filename: str) -> metsrw.METSDocument:
    return metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "dataverse", "metadata", filename)
    )


def dataverse_file(location: str) -> models.File:
    """The file of the Dataverse transfer at the location, relative to objects."""
    return models.File.objects.get(
        currentlocation=f"{TRANSFER_LOCATION}/{location}".encode()
    )


@pytest.fixture
def dataverse_transfer() -> models.Transfer:
    """The Dataverse transfer described by the METS fixtures."""
    return models.Transfer.objects.create(
        uuid=uuid.UUID(TRANSFER_UUID),
        type="Dataverse",
        currentlocation=(
            "%sharedPath%watchedDirectories/SIPCreation/completedTransfers/"
            f"90-{TRANSFER_UUID}/"
        ),
    )


@pytest.fixture
def dataverse_files(dataverse_transfer: models.Transfer) -> list[models.File]:
    """The files of the Dataverse transfer, including two that were removed."""
    weather_checksum = (
        "c54c464c5efbdb4d6c903043c18d41b690653a38cbfcbc0cc31fabe6cda55a0e"
    )
    result = []
    for original_path, current_path, size, checksum, removedtime in [
        (
            "chelan 052.jpg",
            "chelan_052.jpg",
            76934,
            "ab61f03d25ddd0e638f1ff2a823336dc38dd0c7235ee4b6ab2ec671880f822ea",
            None,
        ),
        (
            "Weather_data/Weather_data.tab",
            "Weather_data/Weather_data.tab",
            563285,
            weather_checksum,
            None,
        ),
        (
            "Weather_data.zip",
            None,
            180399,
            "1d2323c179066fc7c5d1cfbfa7271f77f7633a63838615708a9b704e38e8b85e",
            datetime.datetime(2015, 11, 5, 22, 6, 49, tzinfo=datetime.timezone.utc),
        ),
        (
            "Weather_data/Weather_datacitation-ris.ris",
            "Weather_data/Weather_datacitation-ris.ris",
            325,
            "21b90f678beb353417f0f0d0e93bc7259c3575b336f8dd590ea6d4f8f2acfce8",
            None,
        ),
        (
            "dataset.json",
            "dataset.json",
            2832,
            "9ed70885977815b701eb325062fe1360cc8985398e9d4d536e16a0cf53293377",
            None,
        ),
        (
            "Weather_data/Weather_data-ddi.xml",
            "Weather_data/Weather_data-ddi.xml",
            15337,
            "c3fceee71ab02901f01034cfc3b50e611378e04d8e823aa564405360f3913e3a",
            None,
        ),
        (
            "Weather_data/Weather_datacitation-endnote.xml",
            "Weather_data/Weather_datacitation-endnote.xml",
            619,
            "ba57d36d8721b925117ff475a81f03180cfea0e7f9f20d22efbd0ba76ed639ef",
            None,
        ),
        (
            "Weather_data/Weather_data.RData",
            "Weather_data/Weather_data.RData",
            563285,
            weather_checksum,
            None,
        ),
        (
            "Weather_data/Weather_data.sav",
            "Weather_data/Weather_data.sav",
            563285,
            weather_checksum,
            None,
        ),
        (
            "Weather_data/i_am_a_duplicate.original",
            "Weather_data/i_am_a_duplicate.original",
            563285,
            weather_checksum,
            None,
        ),
        (
            "Weather_data/i_am_a_duplicate.original",
            "Weather_data/i_am_a_duplicate.original",
            563285,
            weather_checksum,
            None,
        ),
        (
            "Weather_data/i_have_been_removed",
            None,
            563285,
            weather_checksum,
            datetime.datetime(2019, 1, 15, 23, 13, tzinfo=datetime.timezone.utc),
        ),
    ]:
        result.append(
            models.File.objects.create(
                transfer=dataverse_transfer,
                filegrpuse="original",
                originallocation=f"{TRANSFER_LOCATION}/{original_path}".encode(),
                currentlocation=(
                    None
                    if current_path is None
                    else f"{TRANSFER_LOCATION}/{current_path}".encode()
                ),
                size=size,
                checksum=checksum,
                removedtime=removedtime,
            )
        )

    return result


@pytest.fixture
def no_agents() -> None:
    """Remove the agents of the data migrations, so the Dataverse agent is the
    only one that the parser can find or add.
    """
    models.Agent.objects.all().delete()


@pytest.fixture
def mets() -> metsrw.METSDocument:
    """A completely valid METS document where there should be very few if
    any exceptions to contend with.
    """
    return load_mets("METS.xml")


@pytest.mark.django_db
def test_mapping(
    mcp_job: Job, mets: metsrw.METSDocument, dataverse_files: list[models.File]
) -> None:
    """The first test in is to find the Dataverse objects in the Database
    and ensure they are there as expected.
    """
    # Locations of the files in the Dataverse METS, by file UUID.
    file_locations = {
        "2bd13f12-cd98-450d-8c49-416e9f666a9c": "chelan_052.jpg",
        "fb3b1250-5e45-499f-b0b1-0f6a20d77366": "Weather_data/Weather_data.sav",
        "e5fde5cb-a5d7-4e67-ae66-20b73552eedf": "Weather_data/Weather_data.tab",
        "a001048d-4c3e-485d-af02-1d19584a93b1": "Weather_data/Weather_data.RData",
        "e9e0d762-feff-4b9c-9f70-b408c47149bc": "Weather_data/Weather_datacitation-ris.ris",
        "3dfc2e3f-22e2-4d3e-9913-e4bccc5257ff": "Weather_data/Weather_data-ddi.xml",
        "d9b4e460-f306-43ce-8ee5-7f969595e4ab": "Weather_data/Weather_datacitation-endnote.xml",
    }

    mapping = parse_dataverse.get_db_objects(mcp_job, mets, TRANSFER_UUID)

    assert mapping == {
        mets.get_file(file_uuid=file_uuid): models.File.objects.get(
            currentlocation=f"{TRANSFER_LOCATION}/{location}".encode()
        )
        for file_uuid, location in file_locations.items()
    }


@pytest.mark.django_db
def test_set_filegroups(
    mcp_job: Job, mets: metsrw.METSDocument, dataverse_files: list[models.File]
) -> None:
    """
    It should set the same filegroup for all files in the bundle.
    """
    # Expected file group uses of the files in the bundle, by location.
    file_group_uses = {
        "chelan_052.jpg": "original",
        "Weather_data/Weather_data.sav": "original",
        "Weather_data/Weather_data.tab": "derivative",
        "Weather_data/Weather_data.RData": "derivative",
        "Weather_data/Weather_datacitation-ris.ris": "metadata",
        "Weather_data/Weather_data-ddi.xml": "metadata",
        "Weather_data/Weather_datacitation-endnote.xml": "metadata",
    }
    assert (
        models.File.objects.filter(transfer=TRANSFER_UUID)
        .exclude(filegrpuse="original")
        .count()
        == 0
    )
    mapping = parse_dataverse.get_db_objects(mcp_job, mets, TRANSFER_UUID)
    parse_dataverse.update_file_use(mcp_job, mapping)
    assert {
        location: models.File.objects.get(
            currentlocation=f"{TRANSFER_LOCATION}/{location}".encode()
        ).filegrpuse
        for location in file_group_uses
    } == file_group_uses


@pytest.mark.django_db
def test_parse_agent(mcp_job: Job, no_agents: None) -> None:
    """
    It should add a Dataverse agent.
    """
    assert models.Agent.objects.count() == 0
    agent_id = parse_dataverse.add_external_agents(mcp_job, UNIT_PATH)
    assert models.Agent.objects.count() == 1
    assert agent_id
    agent = models.Agent.objects.all()[0]
    assert agent.identifiertype == "URI"
    assert agent.identifiervalue == "http://dataverse.example.com/dvn/"
    assert agent.name == "Example Dataverse Network"
    assert agent.agenttype == "organization"


@pytest.mark.django_db
def test_parse_agent_already_exists(mcp_job: Job, no_agents: None) -> None:
    """
    It should not add a duplicate agent.
    """
    models.Agent.objects.create(
        identifiertype="URI",
        identifiervalue="http://dataverse.example.com/dvn/",
        name="Example Dataverse Network",
        agenttype="organization",
    )
    assert models.Agent.objects.count() == 1
    agent_id = parse_dataverse.add_external_agents(mcp_job, UNIT_PATH)
    assert models.Agent.objects.count() == 1
    assert agent_id
    agent = models.Agent.objects.all()[0]
    assert agent.identifiertype == "URI"
    assert agent.identifiervalue == "http://dataverse.example.com/dvn/"
    assert agent.name == "Example Dataverse Network"
    assert agent.agenttype == "organization"


@pytest.mark.django_db
def test_parse_agent_no_agents(mcp_job: Job, no_agents: None) -> None:
    """
    It should return None
    """
    assert models.Agent.objects.count() == 0
    agent_id = parse_dataverse.add_external_agents(
        mcp_job, os.path.join(FIXTURES_DIR, "emptysip", "")
    )
    assert models.Agent.objects.count() == 0
    assert agent_id is None


@pytest.mark.django_db
def test_parse_derivative(
    mcp_job: Job,
    mets: metsrw.METSDocument,
    dataverse_files: list[models.File],
    no_agents: None,
) -> None:
    """
    It should create a Derivation for the tabfile and related.
    """
    assert models.Derivation.objects.count() == 0
    mapping = parse_dataverse.get_db_objects(mcp_job, mets, TRANSFER_UUID)
    agent = parse_dataverse.add_external_agents(mcp_job, UNIT_PATH)
    parse_dataverse.create_db_entries(mcp_job, mapping, agent)
    assert models.Event.objects.count() == 2
    assert models.Derivation.objects.count() == 2
    assert models.Derivation.objects.get(
        source_file=dataverse_file("Weather_data/Weather_data.sav"),
        derived_file=dataverse_file("Weather_data/Weather_data.RData"),
        event__isnull=False,
    )
    assert models.Derivation.objects.get(
        source_file=dataverse_file("Weather_data/Weather_data.sav"),
        derived_file=dataverse_file("Weather_data/Weather_data.tab"),
        event__isnull=False,
    )


@pytest.mark.django_db
def test_validate_checksums(
    mcp_job: Job,
    mets: metsrw.METSDocument,
    dataverse_files: list[models.File],
    no_agents: None,
) -> None:
    """
    It should do something with checksums to validate them??
    """
    assert models.Event.objects.count() == 0
    mapping = parse_dataverse.get_db_objects(mcp_job, mets, TRANSFER_UUID)
    parse_dataverse.validate_checksums(mcp_job, mapping, UNIT_PATH)
    assert models.Event.objects.count() == 2
    events = models.Event.objects.get(file_uuid=dataverse_file("chelan_052.jpg"))
    assert events.event_type == "fixity check"
    assert events.event_detail == 'program="python"; module="hashlib.md5()"'
    assert events.event_outcome == "Pass"
    assert (
        events.event_outcome_detail
        == "Dataverse checksum 7ede51390fe3f01fb13632c001d2499d verified"
    )
    events = models.Event.objects.get(
        file_uuid=dataverse_file("Weather_data/Weather_data.sav")
    )
    assert events.event_type == "fixity check"
    assert events.event_detail == 'program="python"; module="hashlib.md5()"'
    assert events.event_outcome == "Pass"
    assert (
        events.event_outcome_detail
        == "Dataverse checksum 4ca2a78963445bce067e027e10394b61 verified"
    )


@pytest.mark.django_db
def test_get_db_objects_returns(
    mcp_job: Job, dataverse_files: list[models.File]
) -> None:
    """The get_db_objects(...) function performs the task of returning
    the objects associated with a Dataverse transfer. Because the
    population of the model is currently done via metadata and not the
    digital objects themselves, the function has a number of possible
    outcomes, and a high number of error conditions test here.
    """
    # A METS document with values that enable us to test when there are
    # duplicate objects in a Dataverse transfer.
    duplicate_file_mets = load_mets("METS.duplicate.xml")
    # A METS document with values that enable us to test when there is an
    # object missing from the transfer which can happen when we populate
    # the initial 'Dataverse' mets from metadata only.
    missing_file_mets = load_mets("METS.missing.xml")
    # A METS document with values that enable us to test when there is an
    # an object that has been purposely removed from a transfer, e.g.
    # through extract packages.
    removed_file_mets = load_mets("METS.removed.xml")

    # Retrieve database objects matching those in the Dataverse METS.
    mapping = parse_dataverse.get_db_objects(
        mcp_job, duplicate_file_mets, TRANSFER_UUID
    )
    # We expect None at this point. If there is a situation where we have
    # a duplicate file, we can't continue processing until this is solved.
    assert mapping is None
    # Retrieve database objects matching those in the Dataverse METS.
    mapping = parse_dataverse.get_db_objects(mcp_job, missing_file_mets, TRANSFER_UUID)
    # If the file cannot be found, it there shouldn't be an object mapping
    # available. The function should return None to the user so processing
    # can stop.
    assert mapping is None
    # Retrieve database objects matching those in the Dataverse METS.
    mapping = parse_dataverse.get_db_objects(mcp_job, removed_file_mets, TRANSFER_UUID)
    # If the file cannot be found, but it has been purposely removed from
    # the database by Archivematica, then the service shouldn't fail.
    # Processing should continue on the objects mapping that remains.
    assert mapping is not None
    assert len(mapping) == 1
