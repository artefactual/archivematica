import os
import sys
import uuid

from main.models import Agent, File, Transfer, User

from lxml import etree
import metsrw
import pytest


THIS_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))

import move_to_backlog


@pytest.fixture
def transfer(db):
    transfer = Transfer.objects.create(uuid="756db89c-1380-459d-83bc-d3772f1e7dd8")
    user = User.objects.create(id=1)
    transfer.update_active_agent(user_id=user.id)
    return transfer


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
def test_record_backlog_event(tmp_path, transfer):
    file_obj = File.objects.create(
        uuid="3c567bc8-0847-4d12-a77d-0ed3a0361c0a", transfer=transfer
    )

    # ``_record_backlog_event`` expects the METS file to exist already.
    # We're creating one with a single file in it.
    (tmp_path / "metadata/submissionDocumentation").mkdir(parents=True)
    mets_path = str(tmp_path / "metadata/submissionDocumentation/METS.xml")
    mets = metsrw.METSDocument()
    mets.append_file(
        metsrw.FSEntry(
            path="foobar.jpg", label="foobar", type="Item", file_uuid=file_obj.uuid
        )
    )
    mets.write(mets_path, pretty_print=True)

    move_to_backlog._record_backlog_event(transfer.uuid, str(tmp_path), "2019-03-12")

    # Load METS document again and test that the file has a PREMIS event.
    mets = metsrw.METSDocument().fromfile(mets_path)
    fsentry = next(iter(mets.all_files()))
    premis_events = fsentry.get_premis_events()
    assert len(premis_events) == 1
    assert premis_events[0].event_type == "placement in backlog"
    assert premis_events[0].event_date_time == "2019-03-12"
