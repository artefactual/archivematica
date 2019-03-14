# -*- coding: utf8
import os
import sys

import vcr

from django.test import TestCase

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
import post_store_aip_hook
from job import Job

from main import models

my_vcr = vcr.VCR(
    cassette_library_dir=os.path.join(THIS_DIR, "fixtures", "vcr_cassettes"),
    path_transformer=vcr.VCR.ensure_suffix(".yaml"),
)


class TestDSpaceToArchivesSpace(TestCase):
    """Test sending the DSpace handle to ArchivesSpace."""

    fixture_files = [
        "archivesspaceconfig.json",
        "storageserviceconfig.json",
        "sip.json",
        "archivesspacecomponents.json",
    ]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def setUp(self):
        self.sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"

    def test_no_archivesspace(self):
        """It should abort if no ArchivesSpaceDigitalObject found."""
        models.ArchivesSpaceDigitalObject.objects.all().delete()
        rc = post_store_aip_hook.dspace_handle_to_archivesspace(
            Job("stub", "stub", []), self.sip_uuid
        )
        assert rc == 1

    def test_no_dspace(self):
        """It should abort if no DSpace handle found."""
        with my_vcr.use_cassette("test_no_dspace.yaml") as c:
            rc = post_store_aip_hook.dspace_handle_to_archivesspace(
                Job("stub", "stub", []), self.sip_uuid
            )
            assert rc == 1
            assert c.all_played

    def test_dspace_handle_to_archivesspace(self):
        """It should send the DSpace handle to ArchivesSpace."""
        with my_vcr.use_cassette("test_dspace_handle_to_archivesspace.yaml") as c:
            rc = post_store_aip_hook.dspace_handle_to_archivesspace(
                Job("stub", "stub", []), self.sip_uuid
            )
            assert rc == 0
            assert c.all_played
