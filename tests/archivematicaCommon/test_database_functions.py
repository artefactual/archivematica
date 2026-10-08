import pathlib
import uuid

import pytest
import pytest_django
from django.core.management import call_command
from django.db import IntegrityError

from archivematica.archivematicaCommon import databaseFunctions
from archivematica.dashboard.main.models import SIP
from archivematica.dashboard.main.models import Directory
from archivematica.dashboard.main.models import Event
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import Identifier

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"

# Agents in the agents.json fixture.
ORGANIZATION_AGENT_ID = 2
SIP_AGENT_ID = 5
TRANSFER_AGENT_ID = 10
SOFTWARE_AGENT_ID = 11

# Files in the test_database_functions.json fixture. The active agent of a
# file comes from the "activeAgent" unit variable of its SIP or transfer.
FILE_WITH_SIP_AGENT_UUID = "88c8f115-80bc-4da4-a1e6-0158f5df13b9"
FILE_WITH_TRANSFER_AGENT_UUID = "1f4af873-8d60-4907-a92e-d1889e643524"
FILE_WITH_SIP_AND_TRANSFER_AGENTS_UUID = "dc569efe-c88f-4be3-94d3-d9eac0c5d410"
FILE_WITHOUT_ACTIVE_AGENT_UUID = "d4e599bd-f9ab-48d4-9ae7-9e87d4ac1619"

# SIPs in the test_database_functions.json fixture.
SIP_WITHOUT_FILES_UUID = "0049fa6c-152f-44a0-93b0-c5e856a02292"
SIP_WITHOUT_ACTIVE_AGENT_UUID = "01cf9fb8-bc01-40b4-b830-feb66e912f40"

# Current path of a file set during the extract contents microservice (the file
# name contains underscores from normalization) and the original location of the
# same file.
EXTRACTED_FILE_PATH = (
    "%transferDirectory%objects/another_parent_directory/compressed_directory.zip"
)
EXTRACTED_FILE_ORIGINAL_LOCATION = (
    "%transferDirectory%objects/another parent directory/compressed directory.zip"
)


@pytest.fixture
def files_and_agents_fixtures(db: None) -> None:
    call_command(
        "loaddata",
        FIXTURES_DIR / "agents.json",
        FIXTURES_DIR / "test_database_functions.json",
        verbosity=0,
    )


# insertIntoFiles


@pytest.mark.django_db
def test_insert_into_files_with_sip(files_and_agents_fixtures: None) -> None:
    path = "%sharedDirectory%/"
    assert File.objects.filter(currentlocation=path.encode()).count() == 0

    databaseFunctions.insertIntoFiles(
        "690c2fb5-7fee-4c29-a8b2-e3758ab9871e",
        path,
        sipUUID=SIP_WITHOUT_FILES_UUID,
    )
    assert File.objects.filter(currentlocation=path.encode()).count() == 1


def test_insert_into_files_raises_if_no_sip_or_transfer_provided() -> None:
    with pytest.raises(Exception, match="neither defined"):
        databaseFunctions.insertIntoFiles("no_sip", "no_sip_path")


def test_insert_into_files_raises_if_both_sip_and_transfer_provided() -> None:
    with pytest.raises(Exception, match="both SIP and transfer UUID"):
        databaseFunctions.insertIntoFiles(
            "both", "both_path", sipUUID="sip", transferUUID="transfer"
        )


@pytest.mark.django_db
def test_insert_into_files_records_original_location(
    files_and_agents_fixtures: None,
) -> None:
    file_uuid = "e0a1fdc4-605a-4104-bf59-039859ee8238"

    databaseFunctions.insertIntoFiles(
        fileUUID=file_uuid,
        filePath=EXTRACTED_FILE_PATH,
        sipUUID=SIP_WITHOUT_FILES_UUID,
        originalLocation=EXTRACTED_FILE_ORIGINAL_LOCATION,
    )

    created_file = File.objects.get(uuid=file_uuid)
    assert created_file.originallocation == EXTRACTED_FILE_ORIGINAL_LOCATION.encode()
    assert created_file.currentlocation == EXTRACTED_FILE_PATH.encode()


@pytest.mark.django_db
def test_insert_into_files_defaults_original_location_to_file_path(
    files_and_agents_fixtures: None,
) -> None:
    file_uuid = "554661f1-b331-452c-a583-0c582ebcb298"

    databaseFunctions.insertIntoFiles(
        fileUUID=file_uuid,
        filePath=EXTRACTED_FILE_PATH,
        sipUUID=SIP_WITHOUT_FILES_UUID,
        originalLocation=None,
    )

    created_file = File.objects.get(uuid=file_uuid)
    assert created_file.originallocation == EXTRACTED_FILE_PATH.encode()
    assert created_file.currentlocation == EXTRACTED_FILE_PATH.encode()


# getAMAgentsForFile


@pytest.mark.django_db
@pytest.mark.parametrize(
    "file_uuid, expected_agent_ids",
    [
        (FILE_WITH_SIP_AGENT_UUID, {ORGANIZATION_AGENT_ID, SIP_AGENT_ID}),
        (FILE_WITH_TRANSFER_AGENT_UUID, {ORGANIZATION_AGENT_ID, TRANSFER_AGENT_ID}),
        (FILE_WITH_SIP_AND_TRANSFER_AGENTS_UUID, {ORGANIZATION_AGENT_ID, SIP_AGENT_ID}),
        (FILE_WITHOUT_ACTIVE_AGENT_UUID, {ORGANIZATION_AGENT_ID}),
    ],
    ids=[
        "sip-agent",
        "transfer-agent",
        "sip-agent-preferred-over-transfer-agent",
        "default-agents-without-active-agent",
    ],
)
def test_get_agents_for_file(
    files_and_agents_fixtures: None, file_uuid: str, expected_agent_ids: set[int]
) -> None:
    assert set(databaseFunctions.getAMAgentsForFile(file_uuid)) == expected_agent_ids


@pytest.mark.django_db
def test_get_agents_for_file_returns_empty_list_for_unknown_file() -> None:
    assert databaseFunctions.getAMAgentsForFile(str(uuid.uuid4())) == []


# insertIntoEvents


@pytest.mark.django_db
def test_insert_into_events(files_and_agents_fixtures: None) -> None:
    event_id = "15a3467d-4c7f-45a5-b879-401b73b7cf7a"
    assert Event.objects.filter(event_id=event_id).count() == 0

    databaseFunctions.insertIntoEvents(
        fileUUID=FILE_WITH_SIP_AGENT_UUID,
        eventIdentifierUUID=event_id,
    )
    assert Event.objects.filter(event_id=event_id).count() == 1


@pytest.mark.django_db
def test_insert_into_event_fetches_correct_agent_from_file(
    files_and_agents_fixtures: None,
) -> None:
    event_id = "fdbf54da-2b21-4364-be3a-a99ad788cdb6"

    databaseFunctions.insertIntoEvents(
        fileUUID=FILE_WITH_SIP_AGENT_UUID,
        eventIdentifierUUID=event_id,
    )
    agent_ids = Event.objects.get(event_id=event_id).agents.values_list("pk", flat=True)
    assert set(agent_ids) == {ORGANIZATION_AGENT_ID, SIP_AGENT_ID}


# insert_events


@pytest.mark.django_db
def test_insert_events_batches_writes_and_preserves_agents(
    files_and_agents_fixtures: None,
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    event_ids = [uuid.uuid4(), uuid.uuid4()]
    event_inputs = [
        databaseFunctions.EventInput(
            file_uuid=FILE_WITH_SIP_AGENT_UUID,
            event_id=event_ids[0],
            event_type="virus check",
            event_detail="SIP detail",
            event_outcome="Pass",
        ),
        databaseFunctions.EventInput(
            file_uuid=FILE_WITH_TRANSFER_AGENT_UUID,
            event_id=event_ids[1],
            event_type="virus check",
            event_detail="transfer detail",
            event_outcome="Fail",
        ),
    ]

    with django_assert_num_queries(9):
        created_events = databaseFunctions.insert_events(event_inputs)

    assert [event.pk for event in created_events] == list(
        Event.objects.filter(event_id__in=event_ids)
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    assert [str(event.event_id) for event in created_events] == [
        str(event_id) for event_id in event_ids
    ]

    events = {
        str(event.event_id): event
        for event in Event.objects.filter(event_id__in=event_ids)
    }
    assert events[str(event_ids[0])].event_detail == "SIP detail"
    assert events[str(event_ids[0])].event_outcome == "Pass"
    assert set(events[str(event_ids[0])].agents.values_list("pk", flat=True)) == {
        ORGANIZATION_AGENT_ID,
        SIP_AGENT_ID,
    }
    assert events[str(event_ids[1])].event_detail == "transfer detail"
    assert events[str(event_ids[1])].event_outcome == "Fail"
    assert set(events[str(event_ids[1])].agents.values_list("pk", flat=True)) == {
        ORGANIZATION_AGENT_ID,
        TRANSFER_AGENT_ID,
    }


@pytest.mark.django_db
def test_insert_events_prefers_sip_agents_and_supports_explicit_agents(
    files_and_agents_fixtures: None,
) -> None:
    event_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

    databaseFunctions.insert_events(
        [
            databaseFunctions.EventInput(
                file_uuid=FILE_WITH_SIP_AND_TRANSFER_AGENTS_UUID,
                event_id=event_ids[0],
            ),
            databaseFunctions.EventInput(
                file_uuid=FILE_WITHOUT_ACTIVE_AGENT_UUID,
                event_id=event_ids[1],
                agent_ids={SOFTWARE_AGENT_ID},
            ),
            databaseFunctions.EventInput(
                file_uuid=FILE_WITHOUT_ACTIVE_AGENT_UUID,
                event_id=event_ids[2],
                agent_ids=set(),
            ),
        ]
    )

    events = {
        str(event.event_id): event
        for event in Event.objects.filter(event_id__in=event_ids)
    }
    assert set(events[str(event_ids[0])].agents.values_list("pk", flat=True)) == {
        ORGANIZATION_AGENT_ID,
        SIP_AGENT_ID,
    }
    assert set(events[str(event_ids[1])].agents.values_list("pk", flat=True)) == {
        SOFTWARE_AGENT_ID
    }
    assert not events[str(event_ids[2])].agents.exists()


@pytest.mark.django_db
def test_insert_events_generates_defaults(files_and_agents_fixtures: None) -> None:
    (event,) = databaseFunctions.insert_events(
        iter([databaseFunctions.EventInput(file_uuid=FILE_WITHOUT_ACTIVE_AGENT_UUID)])
    )

    saved_event = Event.objects.get(pk=event.pk)
    assert saved_event.event_id is not None
    assert saved_event.event_datetime is not None
    assert saved_event.event_type == ""
    assert saved_event.event_detail == ""
    assert saved_event.event_outcome == ""
    assert saved_event.event_outcome_detail == ""
    assert set(saved_event.agents.values_list("pk", flat=True)) == {
        ORGANIZATION_AGENT_ID
    }


@pytest.mark.django_db
def test_insert_events_is_atomic(files_and_agents_fixtures: None) -> None:
    event_ids = [uuid.uuid4(), uuid.uuid4()]

    with pytest.raises(IntegrityError):
        databaseFunctions.insert_events(
            [
                databaseFunctions.EventInput(
                    file_uuid=FILE_WITHOUT_ACTIVE_AGENT_UUID,
                    event_id=event_ids[0],
                    agent_ids={SOFTWARE_AGENT_ID},
                ),
                databaseFunctions.EventInput(
                    file_uuid=FILE_WITHOUT_ACTIVE_AGENT_UUID,
                    event_id=event_ids[1],
                    agent_ids={999999},
                ),
            ]
        )

    assert not Event.objects.filter(event_id__in=event_ids).exists()


def test_insert_events_rejects_invalid_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size must be greater than zero"):
        databaseFunctions.insert_events([], batch_size=0)


# get_sip_identifiers


@pytest.fixture
def sip(db: None) -> SIP:
    sip = SIP.objects.create(uuid="f663fd87-5ce4-4114-886e-4856371cf0d6")
    sip.identifiers.add(Identifier.objects.create(value="sip_identifier"))
    return sip


@pytest.fixture
def directories(db: None, sip: SIP) -> None:
    # Two directories are created but only one is associated with the SIP
    dir1 = Directory.objects.create(
        uuid="49fe38a0-c50a-4fdf-9353-04d61057220d", sip=sip
    )
    dir1.identifiers.add(Identifier.objects.create(value="dir1"))
    dir2 = Directory.objects.create(uuid="58eaa39c-2a0b-47fd-9d81-52fbaa108abc")
    dir2.identifiers.add(Identifier.objects.create(value="dir2"))


def test_get_sip_identifiers_returns_sip_and_directory_identifiers(
    sip: SIP, directories: None
) -> None:
    result = databaseFunctions.get_sip_identifiers(sip.uuid)
    assert sorted(result) == ["dir1", "sip_identifier"]
