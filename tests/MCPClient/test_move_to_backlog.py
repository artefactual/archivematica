import uuid

import metsrw
import move_to_backlog
import pytest
from lxml import etree
from main.models import Agent


@pytest.mark.django_db
def test_premis_event_data(transfer):
    event_id, event_type, created_at = (
        str(uuid.uuid4()),
        "placement in backlog",
        "__now__",
    )
    agents = move_to_backlog._transfer_agents(transfer.uuid)

    # Test the lxml._Element returned is the expected.
    premis_event = move_to_backlog._premis_event_data(
        event_id, event_type, created_at, agents
    )
    assert isinstance(premis_event, etree._Element)
    nsmap = {"premis": "http://www.loc.gov/premis/v3"}
    assert (
        premis_event.findtext(".//premis:eventIdentifierValue", namespaces=nsmap)
        == event_id
    )
    assert (
        premis_event.findtext(".//premis:eventType", namespaces=nsmap)
        == "placement in backlog"
    )
    assert (
        len(premis_event.findall(".//premis:linkingAgentIdentifier", namespaces=nsmap))
        == 2
    )

    # Test that it still returns successfully when there are no agents.
    premis_event = move_to_backlog._premis_event_data(
        event_id, event_type, created_at, Agent.objects.none()
    )
    assert isinstance(premis_event, etree._Element)
    assert (
        premis_event.findtext(".//premis:eventIdentifierValue", namespaces=nsmap)
        == event_id
    )
    assert (
        premis_event.findtext(".//premis:eventType", namespaces=nsmap)
        == "placement in backlog"
    )
    assert (
        len(premis_event.findall(".//premis:linkingAgentIdentifier", namespaces=nsmap))
        == 0
    )


@pytest.mark.django_db
def test_transfer_agents(transfer):
    ret = move_to_backlog._transfer_agents(transfer.uuid)

    assert len(ret) == 2
    assert ret.get(identifiertype="repository code")
    assert ret.get(identifiertype="Archivematica user pk")


@pytest.mark.django_db
def test_record_backlog_event(transfer, transfer_file, transfer_directory_path):
    # ``_record_backlog_event`` expects the METS file to exist already.
    # We're creating one with a single file in it.
    (transfer_directory_path / "metadata/submissionDocumentation").mkdir(parents=True)
    mets_path = str(
        transfer_directory_path / "metadata/submissionDocumentation/METS.xml"
    )
    mets = metsrw.METSDocument()
    mets.append_file(
        metsrw.FSEntry(
            path="foobar.jpg",
            label="foobar",
            type="Item",
            file_uuid=str(transfer_file.uuid),
        )
    )
    mets.write(mets_path, pretty_print=True)

    move_to_backlog._record_backlog_event(
        transfer.uuid, str(transfer_directory_path), "2019-03-12"
    )

    # Load METS document again and test that the file has a PREMIS event.
    mets = metsrw.METSDocument().fromfile(mets_path)
    fsentry = next(iter(mets.all_files()))
    premis_events = fsentry.get_premis_events()
    assert len(premis_events) == 1
    assert premis_events[0].event_type == "placement in backlog"
    assert premis_events[0].event_date_time == "2019-03-12"
