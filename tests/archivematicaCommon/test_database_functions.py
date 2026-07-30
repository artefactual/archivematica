import pathlib
import uuid

import pytest
from django.db import IntegrityError
from django.test import TestCase

from archivematica.archivematicaCommon import databaseFunctions
from archivematica.dashboard.main.models import SIP
from archivematica.dashboard.main.models import Directory
from archivematica.dashboard.main.models import Event
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import Identifier

AGENTS_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "agents.json"
TEST_DATABASE_FUNCTIONS_FIXTURE = (
    pathlib.Path(__file__).parent / "fixtures" / "test_database_functions.json"
)


class TestDatabaseFunctions(TestCase):
    fixtures = [AGENTS_FIXTURE, TEST_DATABASE_FUNCTIONS_FIXTURE]

    # insertIntoFiles
    def test_insert_into_files_with_sip(self):
        path = "%sharedDirectory%/"
        assert File.objects.filter(currentlocation=path.encode()).count() == 0

        databaseFunctions.insertIntoFiles(
            "690c2fb5-7fee-4c29-a8b2-e3758ab9871e",
            path,
            sipUUID="0049fa6c-152f-44a0-93b0-c5e856a02292",
        )
        assert File.objects.filter(currentlocation=path.encode()).count() == 1

    def test_insert_into_files_raises_if_no_sip_or_transfer_provided(self):
        with pytest.raises(Exception) as excinfo:
            databaseFunctions.insertIntoFiles("no_sip", "no_sip_path")
        assert "neither defined" in str(excinfo.value)

    def test_insert_into_files_raises_if_both_sip_and_transfer_provided(self):
        with pytest.raises(Exception) as excinfo:
            databaseFunctions.insertIntoFiles(
                "both", "both_path", sipUUID="sip", transferUUID="transfer"
            )
        assert "both SIP and transfer UUID" in str(excinfo.value)

    def test_insert_into_files_with_original_path(self):
        # A filepath set during the extract contents microservice. Note the
        # filename contains underscorres from normalization.
        file_path = (
            "%transferDirectory%objects/another_parent_directory/"
            "compressed_directory.zip"
        )

        # What that path might look like when set correctly in the original
        # location field.
        original_location = (
            "%transferDirectory%objects/another parent "
            "directory/compressed directory.zip"
        )

        # If originalLocation is set, then test that it is set with the right
        # value. Check also that we haven't set the current location field
        # inaccurately.
        databaseFunctions.insertIntoFiles(
            fileUUID="e0a1fdc4-605a-4104-bf59-039859ee8238",
            filePath=file_path,
            sipUUID="0049fa6c-152f-44a0-93b0-c5e856a02292",
            originalLocation=original_location,
        )
        assert (
            File.objects.filter(originallocation=original_location.encode()).count()
            == 1
        )
        assert (
            File.objects.get(
                originallocation=original_location.encode()
            ).currentlocation.decode()
            != original_location
        )

        # If originalLocation is not set (here we use None to be explicit),
        # then default to the filePath.
        databaseFunctions.insertIntoFiles(
            fileUUID="554661f1-b331-452c-a583-0c582ebcb298",
            filePath=file_path,
            sipUUID="01cf9fb8-bc01-40b4-b830-feb66e912f40",
            originalLocation=None,
        )
        assert (
            File.objects.filter(uuid="554661f1-b331-452c-a583-0c582ebcb298")[
                0
            ].originallocation.decode()
            == file_path
        )

    # getAMAgentsForFile
    def test_get_agent_for_file_with_sip_agent(self):
        agents = databaseFunctions.getAMAgentsForFile(
            "88c8f115-80bc-4da4-a1e6-0158f5df13b9"
        )
        assert 5 in agents
        assert 2 in agents  # organization

    def test_get_agent_for_file_with_transfer_agent(self):
        agents = databaseFunctions.getAMAgentsForFile(
            "1f4af873-8d60-4907-a92e-d1889e643524"
        )
        assert 10 in agents
        assert 2 in agents  # organization

    def test_get_agent_prefers_sip_if_both_exist(self):
        agents = databaseFunctions.getAMAgentsForFile(
            "dc569efe-c88f-4be3-94d3-d9eac0c5d410"
        )
        assert 5 in agents
        assert 2 in agents  # organization

    def test_get_agent_returns_none_for_invalid_uuid(self):
        fileuuid = str(uuid.uuid4())
        assert databaseFunctions.getAMAgentsForFile(fileuuid) == []

    def test_get_agent_returns_none_if_no_unit_variable(self):
        agents = databaseFunctions.getAMAgentsForFile(
            "d4e599bd-f9ab-48d4-9ae7-9e87d4ac1619"
        )
        assert 2 in agents  # organization

    # insertIntoEvents

    def test_insert_into_events(self):
        assert (
            Event.objects.filter(
                event_id="15a3467d-4c7f-45a5-b879-401b73b7cf7a"
            ).count()
            == 0
        )
        databaseFunctions.insertIntoEvents(
            fileUUID="88c8f115-80bc-4da4-a1e6-0158f5df13b9",
            eventIdentifierUUID="15a3467d-4c7f-45a5-b879-401b73b7cf7a",
        )
        assert (
            Event.objects.filter(
                event_id="15a3467d-4c7f-45a5-b879-401b73b7cf7a"
            ).count()
            == 1
        )

    def test_insert_into_event_fetches_correct_agent_from_file(self):
        databaseFunctions.insertIntoEvents(
            fileUUID="88c8f115-80bc-4da4-a1e6-0158f5df13b9",
            eventIdentifierUUID="fdbf54da-2b21-4364-be3a-a99ad788cdb6",
        )
        agents = Event.objects.get(
            event_id="fdbf54da-2b21-4364-be3a-a99ad788cdb6"
        ).agents
        assert agents.get(id=2)
        assert agents.get(id=5)

    # insert_events

    def test_insert_events_batches_writes_and_preserves_agents(self) -> None:
        event_ids = [uuid.uuid4(), uuid.uuid4()]
        event_inputs = [
            databaseFunctions.EventInput(
                file_uuid="88c8f115-80bc-4da4-a1e6-0158f5df13b9",
                event_id=event_ids[0],
                event_type="virus check",
                event_detail="SIP detail",
                event_outcome="Pass",
            ),
            databaseFunctions.EventInput(
                file_uuid="1f4af873-8d60-4907-a92e-d1889e643524",
                event_id=event_ids[1],
                event_type="virus check",
                event_detail="transfer detail",
                event_outcome="Fail",
            ),
        ]

        with self.assertNumQueries(9):
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
            2,
            5,
        }
        assert events[str(event_ids[1])].event_detail == "transfer detail"
        assert events[str(event_ids[1])].event_outcome == "Fail"
        assert set(events[str(event_ids[1])].agents.values_list("pk", flat=True)) == {
            2,
            10,
        }

    def test_insert_events_prefers_sip_agents_and_supports_explicit_agents(
        self,
    ) -> None:
        event_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

        databaseFunctions.insert_events(
            [
                databaseFunctions.EventInput(
                    file_uuid="dc569efe-c88f-4be3-94d3-d9eac0c5d410",
                    event_id=event_ids[0],
                ),
                databaseFunctions.EventInput(
                    file_uuid="d4e599bd-f9ab-48d4-9ae7-9e87d4ac1619",
                    event_id=event_ids[1],
                    agent_ids={11},
                ),
                databaseFunctions.EventInput(
                    file_uuid="d4e599bd-f9ab-48d4-9ae7-9e87d4ac1619",
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
            2,
            5,
        }
        assert set(events[str(event_ids[1])].agents.values_list("pk", flat=True)) == {
            11
        }
        assert not events[str(event_ids[2])].agents.exists()

    def test_insert_events_generates_defaults(self) -> None:
        (event,) = databaseFunctions.insert_events(
            iter(
                [
                    databaseFunctions.EventInput(
                        file_uuid="d4e599bd-f9ab-48d4-9ae7-9e87d4ac1619"
                    )
                ]
            )
        )

        saved_event = Event.objects.get(pk=event.pk)
        assert saved_event.event_id is not None
        assert saved_event.event_datetime is not None
        assert saved_event.event_type == ""
        assert saved_event.event_detail == ""
        assert saved_event.event_outcome == ""
        assert saved_event.event_outcome_detail == ""
        assert set(saved_event.agents.values_list("pk", flat=True)) == {2}

    def test_insert_events_is_atomic(self) -> None:
        event_ids = [uuid.uuid4(), uuid.uuid4()]

        with pytest.raises(IntegrityError):
            databaseFunctions.insert_events(
                [
                    databaseFunctions.EventInput(
                        file_uuid="d4e599bd-f9ab-48d4-9ae7-9e87d4ac1619",
                        event_id=event_ids[0],
                        agent_ids={11},
                    ),
                    databaseFunctions.EventInput(
                        file_uuid="d4e599bd-f9ab-48d4-9ae7-9e87d4ac1619",
                        event_id=event_ids[1],
                        agent_ids={999999},
                    ),
                ]
            )

        assert not Event.objects.filter(event_id__in=event_ids).exists()

    def test_insert_events_rejects_invalid_batch_size(self) -> None:
        with pytest.raises(ValueError, match="batch_size must be greater than zero"):
            databaseFunctions.insert_events([], batch_size=0)


@pytest.fixture
def sip(db):
    sip = SIP.objects.create(uuid="f663fd87-5ce4-4114-886e-4856371cf0d6")
    sip.identifiers.add(Identifier.objects.create(value="sip_identifier"))
    return sip


@pytest.fixture
def directories(db, sip):
    # Two directories are created but only one is associated with the SIP
    dir1 = Directory.objects.create(
        uuid="49fe38a0-c50a-4fdf-9353-04d61057220d", sip=sip
    )
    dir1.identifiers.add(Identifier.objects.create(value="dir1"))
    dir2 = Directory.objects.create(uuid="58eaa39c-2a0b-47fd-9d81-52fbaa108abc")
    dir2.identifiers.add(Identifier.objects.create(value="dir2"))


def test_get_sip_identifiers_returns_sip_and_directory_identifiers(sip, directories):
    result = databaseFunctions.get_sip_identifiers(sip.uuid)
    assert sorted(result) == ["dir1", "sip_identifier"]
