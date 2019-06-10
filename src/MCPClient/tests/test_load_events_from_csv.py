from __future__ import absolute_import, unicode_literals

import datetime
import os
import sys
import uuid

import pytest
from django.utils import timezone

from main.models import File, Transfer

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
from load_events_from_csv import parse_events_csv


BASIC_CSV = """filename,eventType,eventDateTime,eventDetail,eventDetailExtension,eventOutcome,eventOutcomeDetailNote,eventOutcomeDetailExtension,linkingObjectIdentifierType,linkingObjectIndentifierValue,linkingObjectRole,agentIdentifierType,agentIdentifierValue,agentName,agentType
objects/image1.jpg,creation,2019-05-30,Creation event detail,More details about the creation of the file.,success,Notes about the outcome,Extensive notes about the outcome.,,,,repository code,NHA,Norsk helsearkiv,organization
objects/image1.jpg,message digest calculation,2019-05-30,hashlib.sha256,,,383d349019ace0e235443c6cb8c5fa3174f00d562281947d36f5fd12aa263687,,,,,repository code,NHA,Norsk helsearkiv,organization
"""


@pytest.fixture()
def basic_csv(tmp_path):
    csv_path = tmp_path / "events.csv"
    csv_path.write_text(BASIC_CSV)

    return csv_path


@pytest.fixture()
def transfer(db):
    return Transfer.objects.create(
        uuid=uuid.uuid4(), currentlocation=r"%transferDirectory%"
    )


@pytest.fixture()
def file_obj(db, transfer):
    return File.objects.create(
        uuid=uuid.uuid4(),
        transfer=transfer,
        originallocation=r"%transferDirectory%objects/image1.jpg",
        currentlocation=r"%transferDirectory%objects/image1.jpg",
        removedtime=None,
        size=113318,
        checksum="35e0cc683d75704fc5b04fc3633f6c654e10cd3af57471271f370309c7ff9dba",
        checksumtype="sha256",
    )


@pytest.mark.django_db
def test_parse_events_csv(basic_csv, transfer, file_obj):
    # Iterate over the generator, even though we're not using the results here.
    for event, line in parse_events_csv(
        str(basic_csv), File.objects.filter(transfer=transfer)
    ):
        pass

    events = file_obj.event_set.all().order_by("pk")

    assert len(events) == 2
    assert events[0].event_datetime == datetime.datetime(
        2019, 5, 30, 0, 0, 0, tzinfo=timezone.utc
    )
    assert events[0].event_detail == "Creation event detail"
    assert events[0].event_outcome == "success"
    assert events[0].event_outcome_detail == "Notes about the outcome"
    assert events[0].agents.first() == events[1].agents.first()

    agent = events[0].agents.first()
    assert agent.identifiertype == "repository code"
    assert agent.identifiervalue == "NHA"
    assert agent.name == "Norsk helsearkiv"
    assert agent.agenttype == "organization"
