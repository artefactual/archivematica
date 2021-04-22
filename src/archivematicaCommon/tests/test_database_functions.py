# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

import databaseFunctions

from main.models import Event, File

from django.test import TestCase
import pytest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestDatabaseFunctions(TestCase):

    fixture_files = ["agents.json", "test_database_functions.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    # insertIntoFiles
    def test_insert_into_files_with_sip(self):
        path = "%sharedDirectory%/no_such_file"
        assert File.objects.filter(currentlocation=path).count() == 0

        databaseFunctions.insertIntoFiles(
            "uuid", path, sipUUID="0049fa6c-152f-44a0-93b0-c5e856a02292"
        )
        assert File.objects.filter(currentlocation=path).count() == 1

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
        assert File.objects.filter(originallocation=original_location).count() == 1
        assert (
            File.objects.get(originallocation=original_location).currentlocation
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
            ].originallocation
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
        assert databaseFunctions.getAMAgentsForFile("no such file") == []

    def test_get_agent_returns_none_if_no_unit_variable(self):
        agents = databaseFunctions.getAMAgentsForFile(
            "d4e599bd-f9ab-48d4-9ae7-9e87d4ac1619"
        )
        assert 2 in agents  # organization

    # insertIntoEvents

    def test_insert_into_events(self):
        assert Event.objects.filter(event_id="new_event").count() == 0
        databaseFunctions.insertIntoEvents(
            fileUUID="88c8f115-80bc-4da4-a1e6-0158f5df13b9",
            eventIdentifierUUID="new_event",
        )
        assert Event.objects.filter(event_id="new_event").count() == 1

    def test_insert_into_event_fetches_correct_agent_from_file(self):
        databaseFunctions.insertIntoEvents(
            fileUUID="88c8f115-80bc-4da4-a1e6-0158f5df13b9",
            eventIdentifierUUID="event_agent_id",
        )
        agents = Event.objects.get(event_id="event_agent_id").agents
        assert agents.get(id=2)
        assert agents.get(id=5)
