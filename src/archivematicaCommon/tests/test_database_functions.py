# -*- coding: UTF-8 -*-
import os
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseFunctions

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import Event, File

from django.test import TestCase
import pytest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class TestDatabaseFunctions(TestCase):

    fixture_files = ['test_database_functions.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    def test_insert_into_files_with_sip(self):
        path = "%sharedDirectory%/no_such_file"
        assert File.objects.filter(currentlocation=path).count() == 0

        databaseFunctions.insertIntoFiles("uuid", path, sipUUID="0049fa6c-152f-44a0-93b0-c5e856a02292")
        assert File.objects.filter(currentlocation=path).count() == 1

    def test_insert_into_files_raises_if_no_sip_or_transfer_provided(self):
        with pytest.raises(Exception) as excinfo:
            databaseFunctions.insertIntoFiles("no_sip", "no_sip_path")
        assert "neither defined" in str(excinfo.value)

    def test_insert_into_files_raises_if_both_sip_and_transfer_provided(self):
        with pytest.raises(Exception) as excinfo:
            databaseFunctions.insertIntoFiles("both", "both_path", sipUUID="sip", transferUUID="transfer")
        assert "both SIP and transfer UUID" in str(excinfo.value)

    def test_get_agent_for_file_with_sip_agent(self):
        agent_id = databaseFunctions.getAgentForFileUUID("88c8f115-80bc-4da4-a1e6-0158f5df13b9")
        assert agent_id == "5"

    def test_get_agent_for_file_with_transfer_agent(self):
        agent_id = databaseFunctions.getAgentForFileUUID("1f4af873-8d60-4907-a92e-d1889e643524")
        assert agent_id == "10"

    def test_get_agent_prefers_sip_if_both_exist(self):
        agent_id = databaseFunctions.getAgentForFileUUID("dc569efe-c88f-4be3-94d3-d9eac0c5d410")
        assert agent_id == "sip_value"

    def test_get_agent_fails_for_special_uuid_value(self):
        with pytest.raises(Exception) as excinfo:
            databaseFunctions.getAgentForFileUUID('None')
        assert "no file UUID provided" in str(excinfo.value)

    def test_get_agent_returns_none_for_invalid_uuid(self):
        assert databaseFunctions.getAgentForFileUUID('no such file') is None

    def test_get_agent_returns_none_if_no_unit_variable(self):
        assert databaseFunctions.getAgentForFileUUID("d4e599bd-f9ab-48d4-9ae7-9e87d4ac1619") is None

    def test_insert_into_events(self):
        assert Event.objects.filter(event_id="new_event").count() == 0
        databaseFunctions.insertIntoEvents(eventIdentifierUUID="new_event")
        assert Event.objects.filter(event_id="new_event").count() == 1

    def test_insert_into_event_fetches_correct_agent_from_file(self):
        databaseFunctions.insertIntoEvents(fileUUID="88c8f115-80bc-4da4-a1e6-0158f5df13b9",
                                           eventIdentifierUUID="event_agent_id")
        assert Event.objects.get(event_id="event_agent_id").linking_agent.name == "Event agent"

    def test_get_accession_number_from_transfer(self):
        accession_id = databaseFunctions.getAccessionNumberFromTransfer("5a8d0539-8e5a-4aa9-98d8-5e5053140398")
        assert accession_id == "Accession ID"

    def test_get_acession_number_from_transfer_raises(self):
        with pytest.raises(ValueError) as excinfo:
            databaseFunctions.getAccessionNumberFromTransfer("no such transfer")
        assert "No Transfer found" in str(excinfo.value)
