#!/usr/bin/env python2
import os
import sys
import vcr

from django.test import TestCase

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
import dip_generation_helper

from main.models import ArchivesSpaceDIPObjectResourcePairing


class TestParseArchivesSpaceIDs(TestCase):

    fixture_files = ["sip.json", "files.json", "archivesspaceconfig.json"]
    sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def test_no_archivesspace_csv(self):
        """ It should do nothing. """
        sip_path = os.path.join(THIS_DIR, "fixtures", "emptysip", "")
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
        rc = dip_generation_helper.parse_archivesspace_ids(sip_path, self.sip_uuid)
        assert rc == 0
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False

    def test_empty_csv(self):
        """ It should do nothing if the CSV is empty. """
        sip_path = os.path.join(THIS_DIR, "fixtures", "empty_metadata_files", "")
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
        rc = dip_generation_helper.parse_archivesspace_ids(sip_path, self.sip_uuid)
        assert rc == 1
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False

    @vcr.use_cassette(os.path.join(THIS_DIR, "fixtures", "test_no_files_in_db.yaml"))
    def test_no_files_in_db(self):
        """ It should do nothing if no files are found in the DB. """
        sip_path = os.path.join(THIS_DIR, "fixtures", "metadata_csv_sip", "")
        sip_uuid = "dne"
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
        rc = dip_generation_helper.parse_archivesspace_ids(sip_path, sip_uuid)
        assert rc == 0
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False

    @vcr.use_cassette(
        os.path.join(THIS_DIR, "fixtures", "test_parse_archivesspace_ids.yaml")
    )
    def test_parse_to_db(self):
        """
        It should create an entry in ArchivesSpaceDIPObjectResourcePairing for each file in archivesspaceids.csv
        It should match the reference ID to a resource ID.
        """
        sip_path = os.path.join(THIS_DIR, "fixtures", "archivesspaceid_sip", "")
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
        rc = dip_generation_helper.parse_archivesspace_ids(sip_path, self.sip_uuid)
        assert rc == 0
        assert len(ArchivesSpaceDIPObjectResourcePairing.objects.all()) == 1
        r = ArchivesSpaceDIPObjectResourcePairing.objects.all()[0]
        assert r.dipuuid == self.sip_uuid
        assert r.fileuuid == "ae8d4290-fe52-4954-b72a-0f591bee2e2f"
        assert r.resourceid == "/repositories/2/archival_objects/752250"
