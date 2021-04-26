#!/usr/bin/env python
# -*- coding: utf8

"""Tests for the parse Dataverse functionality in Archivematica."""

import os
import sys

from django.test import TestCase
import metsrw

from job import Job
from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))

import parse_dataverse_mets as parse_dataverse


class TestParseDataverse(TestCase):
    """Test Parse Dataverse test runner class."""

    fixture_files = ["dataverse_sip.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    # Transfer location is repeated throughout.
    transfer_location = "%transferDirectory%objects"

    def setUp(self):
        self.job = Job("stub", "stub", ["", ""])
        # A completely valid METS document where there should be very few if
        # any exceptions to contend with.
        self.mets = metsrw.METSDocument.fromfile(
            os.path.join(THIS_DIR, "fixtures", "dataverse", "metadata", "METS.xml")
        )
        # A METS document with values that enable us to test when there are
        # duplicate objects in a Dataverse transfer.
        self.duplicate_file_mets = metsrw.METSDocument.fromfile(
            os.path.join(
                THIS_DIR, "fixtures", "dataverse", "metadata", "METS.duplicate.xml"
            )
        )
        # A METS document with values that enable us to test when there is an
        # object missing from the transfer which can happen when we populate
        # the initial 'Dataverse' mets from metadata only.
        self.missing_file_mets = metsrw.METSDocument.fromfile(
            os.path.join(
                THIS_DIR, "fixtures", "dataverse", "metadata", "METS.missing.xml"
            )
        )
        # A METS document with values that enable us to test when there is an
        # an object that has been purposely removed from a transfer, e.g.
        # through extract packages.
        self.removed_file_mets = metsrw.METSDocument.fromfile(
            os.path.join(
                THIS_DIR, "fixtures", "dataverse", "metadata", "METS.removed.xml"
            )
        )
        # Transfer UUID and the location of that transfer for test's sakes.
        self.uuid = "6741c782-f22b-47b3-8bcf-72fd0c94e195"
        self.unit_path = os.path.join(THIS_DIR, "fixtures", "dataverse", "")
        models.Agent.objects.all().delete()

    def test_mapping(self):
        """The first test in is to find the Dataverse objects in the Database
        and ensure they are there as expected.
        """
        test_cases = [
            {
                # chelen_052.jpg
                "file_uuid": "2bd13f12-cd98-450d-8c49-416e9f666a9c",
                "file_location": "{}/chelan_052.jpg",
            },
            {
                # Weather_data.sav
                "file_uuid": "fb3b1250-5e45-499f-b0b1-0f6a20d77366",
                "file_location": "{}/Weather_data/Weather_data.sav",
            },
            {
                # Weather_data.tab
                "file_uuid": "e5fde5cb-a5d7-4e67-ae66-20b73552eedf",
                "file_location": "{}/Weather_data/Weather_data.tab",
            },
            {
                # Weather_data.RData
                "file_uuid": "a001048d-4c3e-485d-af02-1d19584a93b1",
                "file_location": "{}/Weather_data/Weather_data.RData",
            },
            {
                # ris
                "file_uuid": "e9e0d762-feff-4b9c-9f70-b408c47149bc",
                "file_location": "{}/Weather_data/Weather_datacitation-ris.ris",
            },
            {
                # ddi
                "file_uuid": "3dfc2e3f-22e2-4d3e-9913-e4bccc5257ff",
                "file_location": "{}/Weather_data/Weather_data-ddi.xml",
            },
            {
                # endnote
                "file_uuid": "d9b4e460-f306-43ce-8ee5-7f969595e4ab",
                "file_location": "{}/Weather_data/Weather_datacitation-endnote.xml",
            },
        ]

        mapping = parse_dataverse.get_db_objects(self.job, self.mets, self.uuid)
        assert len(mapping) == 7

        for test_case in test_cases:
            assert self.mets.get_file(file_uuid=test_case["file_uuid"]) in mapping
            assert models.File.objects.get(
                currentlocation=test_case.get("file_location", "").format(
                    self.transfer_location
                )
            ) in list(mapping.values())

    def test_set_filegroups(self):
        """
        It should set the same filegroup for all files in the bundle.
        """

        test_cases = [
            {
                # Original
                "file_location": "{}/chelan_052.jpg",
                "file_group_use": "original",
            },
            {
                # Original
                "file_location": "{}/Weather_data/Weather_data.sav",
                "file_group_use": "original",
            },
            {
                # Derivative
                "file_location": "{}/Weather_data/Weather_data.tab",
                "file_group_use": "derivative",
            },
            {
                # Derivative
                "file_location": "{}/Weather_data/Weather_data.RData",
                "file_group_use": "derivative",
            },
            {
                # Metadata
                "file_location": "{}/Weather_data/Weather_datacitation-ris.ris",
                "file_group_use": "metadata",
            },
            {
                # Metadata
                "file_location": "{}/Weather_data/Weather_data-ddi.xml",
                "file_group_use": "metadata",
            },
            {
                # Metadata
                "file_location": "{}/Weather_data/Weather_datacitation-endnote.xml",
                "file_group_use": "metadata",
            },
        ]
        assert (
            models.File.objects.filter(transfer="6741c782-f22b-47b3-8bcf-72fd0c94e195")
            .exclude(filegrpuse="original")
            .count()
            == 0
        )
        mapping = parse_dataverse.get_db_objects(self.job, self.mets, self.uuid)
        parse_dataverse.update_file_use(self.job, mapping)
        for test_case in test_cases:
            assert (
                models.File.objects.get(
                    currentlocation=test_case.get("file_location", "").format(
                        self.transfer_location
                    )
                ).filegrpuse
                == test_case["file_group_use"]
            )

    def test_parse_agent(self):
        """
        It should add a Dataverse agent.
        """
        assert models.Agent.objects.count() == 0
        agent_id = parse_dataverse.add_external_agents(self.job, self.unit_path)
        assert models.Agent.objects.count() == 1
        assert agent_id
        agent = models.Agent.objects.all()[0]
        assert agent.identifiertype == "URI"
        assert agent.identifiervalue == "http://dataverse.example.com/dvn/"
        assert agent.name == "Example Dataverse Network"
        assert agent.agenttype == "organization"

    def test_parse_agent_already_exists(self):
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
        agent_id = parse_dataverse.add_external_agents(self.job, self.unit_path)
        assert models.Agent.objects.count() == 1
        assert agent_id
        agent = models.Agent.objects.all()[0]
        assert agent.identifiertype == "URI"
        assert agent.identifiervalue == "http://dataverse.example.com/dvn/"
        assert agent.name == "Example Dataverse Network"
        assert agent.agenttype == "organization"

    def test_parse_agent_no_agents(self):
        """
        It should return None
        """
        assert models.Agent.objects.count() == 0
        agent_id = parse_dataverse.add_external_agents(
            self.job, os.path.join(THIS_DIR, "fixtures", "emptysip", "")
        )
        assert models.Agent.objects.count() == 0
        assert agent_id is None

    def test_parse_derivative(self):
        """
        It should create a Derivation for the tabfile and related.
        """
        assert models.Derivation.objects.count() == 0
        mapping = parse_dataverse.get_db_objects(self.job, self.mets, self.uuid)
        agent = parse_dataverse.add_external_agents(self.job, self.unit_path)
        parse_dataverse.create_db_entries(self.job, mapping, agent)
        assert models.Event.objects.count() == 2
        assert models.Derivation.objects.count() == 2
        assert models.Derivation.objects.get(
            source_file_id="e2834eed-4178-469a-9a4e-c8f1490bb804",
            derived_file_id="071e6af9-f676-40fa-a5ab-754ca6b653e0",
            event__isnull=False,
        )
        assert models.Derivation.objects.get(
            source_file_id="e2834eed-4178-469a-9a4e-c8f1490bb804",
            derived_file_id="5518a927-bae9-497c-8a16-caa072e6ef7e",
            event__isnull=False,
        )

    def test_validate_checksums(self):
        """
        It should do something with checksums to validate them??
        """
        assert models.Event.objects.count() == 0
        mapping = parse_dataverse.get_db_objects(self.job, self.mets, self.uuid)
        parse_dataverse.validate_checksums(self.job, mapping, self.unit_path)
        assert models.Event.objects.count() == 2
        events = models.Event.objects.get(
            file_uuid_id="22fade0b-d2fc-4835-b669-970c8fdd9b76"
        )
        assert events.event_type == "fixity check"
        assert events.event_detail == 'program="python"; module="hashlib.md5()"'
        assert events.event_outcome == "Pass"
        assert (
            events.event_outcome_detail
            == "Dataverse checksum 7ede51390fe3f01fb13632c001d2499d verified"
        )
        events = models.Event.objects.get(
            file_uuid_id="e2834eed-4178-469a-9a4e-c8f1490bb804"
        )
        assert events.event_type == "fixity check"
        assert events.event_detail == 'program="python"; module="hashlib.md5()"'
        assert events.event_outcome == "Pass"
        assert (
            events.event_outcome_detail
            == "Dataverse checksum 4ca2a78963445bce067e027e10394b61 verified"
        )

    def test_get_db_objects_returns(self):
        """The get_db_objects(...) function performs the task of returning
        the objects associated with a Dataverse transfer. Because the
        population of the model is currently done via metadata and not the
        digital objects themselves, the function has a number of possible
        outcomes, and a high number of error conditions test here.
        """
        # Retrieve database objects matching those in the Dataverse METS.
        mapping = parse_dataverse.get_db_objects(
            self.job, self.duplicate_file_mets, self.uuid
        )
        # We expect None at this point. If there is a situation where we have
        # a duplicate file, we can't continue processing until this is solved.
        assert mapping is None
        # Retrieve database objects matching those in the Dataverse METS.
        mapping = parse_dataverse.get_db_objects(
            self.job, self.missing_file_mets, self.uuid
        )
        # If the file cannot be found, it there shouldn't be an object mapping
        # available. The function should return None to the user so processing
        # can stop.
        assert mapping is None
        # Retrieve database objects matching those in the Dataverse METS.
        mapping = parse_dataverse.get_db_objects(
            self.job, self.removed_file_mets, self.uuid
        )
        # If the file cannot be found, but it has been purposely removed from
        # the database by Archivematica, then the service shouldn't fail.
        # Processing should continue on the objects mapping that remains.
        assert mapping is not None
        assert len(mapping) == 1
