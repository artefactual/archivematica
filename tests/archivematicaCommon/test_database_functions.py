import uuid

import pytest
import pytest_django
from django.db import IntegrityError

from archivematica.archivematicaCommon import databaseFunctions
from archivematica.dashboard.main.models import SIP
from archivematica.dashboard.main.models import Agent
from archivematica.dashboard.main.models import Directory
from archivematica.dashboard.main.models import Event
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import Identifier
from archivematica.dashboard.main.models import Transfer
from archivematica.dashboard.main.models import UnitVariable
from tests.factories import FileFactory
from tests.factories import SIPFactory

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
def sip_agent() -> Agent:
    """The agent of the user who processes SIPs."""
    return Agent.objects.create(
        agenttype="Archivematica user",
        identifiertype="Archivematica user pk",
        identifiervalue="2",
        name="SIP Agent",
    )


@pytest.fixture
def transfer_agent() -> Agent:
    """The agent of the user who processes transfers."""
    return Agent.objects.create(
        agenttype="Archivematica user",
        identifiertype="Archivematica user pk",
        identifiervalue="2",
        name="Transfer Agent",
    )


@pytest.fixture
def software_agent() -> Agent:
    """A preservation system agent other than Archivematica."""
    return Agent.objects.create(
        agenttype="software",
        identifiertype="preservation system",
        identifiervalue="Other-Software-1.0",
        name="Other Software",
    )


def set_active_agent(unit: SIP | Transfer, agent: Agent) -> None:
    """Record the agent as the active agent of the SIP or transfer."""
    UnitVariable.objects.update_variable(
        "SIP" if isinstance(unit, SIP) else "Transfer",
        unit.uuid,
        "activeAgent",
        str(agent.pk),
    )


@pytest.fixture
def file_with_sip_agent(make_file: FileFactory, sip: SIP, sip_agent: Agent) -> File:
    """A file of a SIP whose active agent is the SIP agent."""
    set_active_agent(sip, sip_agent)

    return make_file("objects/file.txt", sip=sip)


@pytest.fixture
def file_with_transfer_agent(
    transfer: Transfer, transfer_file: File, transfer_agent: Agent
) -> File:
    """The transfer file, once the transfer agent is the active agent of the
    transfer.
    """
    set_active_agent(transfer, transfer_agent)

    return transfer_file


@pytest.fixture
def file_with_sip_and_transfer_agents(
    sip: SIP,
    transfer: Transfer,
    sip_file: File,
    sip_agent: Agent,
    transfer_agent: Agent,
) -> File:
    """The SIP file, once its SIP and its transfer have different active agents."""
    set_active_agent(sip, sip_agent)
    set_active_agent(transfer, transfer_agent)

    return sip_file


@pytest.fixture
def file_without_active_agent(make_file: FileFactory, make_sip: SIPFactory) -> File:
    """A file of a SIP without an active agent.

    The SIP is its own, so that the fixtures that record an active agent on
    the shared SIP never affect this one.
    """
    return make_file("objects/file.txt", sip=make_sip())


# insertIntoFiles


@pytest.mark.django_db
def test_insert_into_files_with_sip(sip: SIP) -> None:
    path = "%sharedDirectory%/"
    assert File.objects.filter(currentlocation=path.encode()).count() == 0

    databaseFunctions.insertIntoFiles(
        str(uuid.uuid4()),
        path,
        sipUUID=str(sip.uuid),
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
def test_insert_into_files_records_original_location(sip: SIP) -> None:
    file_uuid = str(uuid.uuid4())

    databaseFunctions.insertIntoFiles(
        fileUUID=file_uuid,
        filePath=EXTRACTED_FILE_PATH,
        sipUUID=str(sip.uuid),
        originalLocation=EXTRACTED_FILE_ORIGINAL_LOCATION,
    )

    created_file = File.objects.get(uuid=file_uuid)
    assert created_file.originallocation == EXTRACTED_FILE_ORIGINAL_LOCATION.encode()
    assert created_file.currentlocation == EXTRACTED_FILE_PATH.encode()


@pytest.mark.django_db
def test_insert_into_files_defaults_original_location_to_file_path(
    sip: SIP,
) -> None:
    file_uuid = str(uuid.uuid4())

    databaseFunctions.insertIntoFiles(
        fileUUID=file_uuid,
        filePath=EXTRACTED_FILE_PATH,
        sipUUID=str(sip.uuid),
        originalLocation=None,
    )

    created_file = File.objects.get(uuid=file_uuid)
    assert created_file.originallocation == EXTRACTED_FILE_PATH.encode()
    assert created_file.currentlocation == EXTRACTED_FILE_PATH.encode()


# getAMAgentsForFile


@pytest.mark.django_db
@pytest.mark.parametrize(
    "file_fixture, expected_agent_fixtures",
    [
        ("file_with_sip_agent", ["organization_agent", "sip_agent"]),
        ("file_with_transfer_agent", ["organization_agent", "transfer_agent"]),
        ("file_with_sip_and_transfer_agents", ["organization_agent", "sip_agent"]),
        ("file_without_active_agent", ["organization_agent"]),
    ],
    ids=[
        "sip-agent",
        "transfer-agent",
        "sip-agent-preferred-over-transfer-agent",
        "default-agents-without-active-agent",
    ],
)
def test_get_agents_for_file(
    request: pytest.FixtureRequest,
    file_fixture: str,
    expected_agent_fixtures: list[str],
) -> None:
    file_: File = request.getfixturevalue(file_fixture)
    expected_agent_ids = {
        request.getfixturevalue(agent_fixture).pk
        for agent_fixture in expected_agent_fixtures
    }

    assert (
        set(databaseFunctions.getAMAgentsForFile(str(file_.uuid))) == expected_agent_ids
    )


@pytest.mark.django_db
def test_get_agents_for_file_returns_empty_list_for_unknown_file() -> None:
    assert databaseFunctions.getAMAgentsForFile(str(uuid.uuid4())) == []


# insertIntoEvents


@pytest.mark.django_db
def test_insert_into_events(file_with_sip_agent: File) -> None:
    event_id = str(uuid.uuid4())
    assert Event.objects.filter(event_id=event_id).count() == 0

    databaseFunctions.insertIntoEvents(
        fileUUID=str(file_with_sip_agent.uuid),
        eventIdentifierUUID=event_id,
    )
    assert Event.objects.filter(event_id=event_id).count() == 1


@pytest.mark.django_db
def test_insert_into_event_fetches_correct_agent_from_file(
    file_with_sip_agent: File, organization_agent: Agent, sip_agent: Agent
) -> None:
    event_id = str(uuid.uuid4())

    databaseFunctions.insertIntoEvents(
        fileUUID=str(file_with_sip_agent.uuid),
        eventIdentifierUUID=event_id,
    )
    agent_ids = Event.objects.get(event_id=event_id).agents.values_list("pk", flat=True)
    assert set(agent_ids) == {organization_agent.pk, sip_agent.pk}


# insert_events


@pytest.mark.django_db
def test_insert_events_batches_writes_and_preserves_agents(
    file_with_sip_agent: File,
    file_with_transfer_agent: File,
    organization_agent: Agent,
    sip_agent: Agent,
    transfer_agent: Agent,
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    event_ids = [uuid.uuid4(), uuid.uuid4()]
    event_inputs = [
        databaseFunctions.EventInput(
            file_uuid=file_with_sip_agent.uuid,
            event_id=event_ids[0],
            event_type="virus check",
            event_detail="SIP detail",
            event_outcome="Pass",
        ),
        databaseFunctions.EventInput(
            file_uuid=file_with_transfer_agent.uuid,
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
        organization_agent.pk,
        sip_agent.pk,
    }
    assert events[str(event_ids[1])].event_detail == "transfer detail"
    assert events[str(event_ids[1])].event_outcome == "Fail"
    assert set(events[str(event_ids[1])].agents.values_list("pk", flat=True)) == {
        organization_agent.pk,
        transfer_agent.pk,
    }


@pytest.mark.django_db
def test_insert_events_prefers_sip_agents_and_supports_explicit_agents(
    file_with_sip_and_transfer_agents: File,
    file_without_active_agent: File,
    organization_agent: Agent,
    sip_agent: Agent,
    software_agent: Agent,
) -> None:
    event_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

    databaseFunctions.insert_events(
        [
            databaseFunctions.EventInput(
                file_uuid=file_with_sip_and_transfer_agents.uuid,
                event_id=event_ids[0],
            ),
            databaseFunctions.EventInput(
                file_uuid=file_without_active_agent.uuid,
                event_id=event_ids[1],
                agent_ids={software_agent.pk},
            ),
            databaseFunctions.EventInput(
                file_uuid=file_without_active_agent.uuid,
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
        organization_agent.pk,
        sip_agent.pk,
    }
    assert set(events[str(event_ids[1])].agents.values_list("pk", flat=True)) == {
        software_agent.pk
    }
    assert not events[str(event_ids[2])].agents.exists()


@pytest.mark.django_db
def test_insert_events_generates_defaults(
    file_without_active_agent: File, organization_agent: Agent
) -> None:
    (event,) = databaseFunctions.insert_events(
        iter([databaseFunctions.EventInput(file_uuid=file_without_active_agent.uuid)])
    )

    saved_event = Event.objects.get(pk=event.pk)
    assert saved_event.event_id is not None
    assert saved_event.event_datetime is not None
    assert saved_event.event_type == ""
    assert saved_event.event_detail == ""
    assert saved_event.event_outcome == ""
    assert saved_event.event_outcome_detail == ""
    assert set(saved_event.agents.values_list("pk", flat=True)) == {
        organization_agent.pk
    }


@pytest.mark.django_db
def test_insert_events_is_atomic(
    file_without_active_agent: File, software_agent: Agent
) -> None:
    event_ids = [uuid.uuid4(), uuid.uuid4()]

    with pytest.raises(IntegrityError):
        databaseFunctions.insert_events(
            [
                databaseFunctions.EventInput(
                    file_uuid=file_without_active_agent.uuid,
                    event_id=event_ids[0],
                    agent_ids={software_agent.pk},
                ),
                databaseFunctions.EventInput(
                    file_uuid=file_without_active_agent.uuid,
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
def sip_with_identifier(sip: SIP) -> SIP:
    """The SIP with an identifier."""
    sip.identifiers.add(Identifier.objects.create(value="sip_identifier"))

    return sip


@pytest.fixture
def directories(sip_with_identifier: SIP) -> None:
    # Two directories are created but only one is associated with the SIP
    dir1 = Directory.objects.create(sip=sip_with_identifier)
    dir1.identifiers.add(Identifier.objects.create(value="dir1"))
    dir2 = Directory.objects.create()
    dir2.identifiers.add(Identifier.objects.create(value="dir2"))


@pytest.mark.django_db
def test_get_sip_identifiers_returns_sip_and_directory_identifiers(
    sip_with_identifier: SIP, directories: None
) -> None:
    result = databaseFunctions.get_sip_identifiers(sip_with_identifier.uuid)
    assert sorted(result) == ["dir1", "sip_identifier"]
