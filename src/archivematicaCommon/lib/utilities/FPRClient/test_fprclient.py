#!/usr/bin/env python2
import os
import sys
import vcr

from django.test import TestCase

sys.path.append("/usr/share/archivematica/dashboard/")
from fpr import models
import main.models

import client
import getFromRestAPI

# WARNING Rules must be refetched from the DB to get updated values
FPRSERVER = 'http://localhost:9000/fpr/api/v2/'
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class TestGetFromFPRRESTAPI(TestCase):
    """
    Test functions in getFromRestAPI.py
    """
    @vcr.use_cassette(os.path.join(THIS_DIR, "../fixtures/vcr_cassettes/get_from_rest_api_id-commands.yaml"))
    def test_can_get_info_from_fprserver(self):
        """ Confirm the configured fprserver is accessible, and returns info. """
        params = {
            "format": "json",
            "limit": "0"
        }
        entries = getFromRestAPI._get_from_rest_api(url=FPRSERVER, resource='id-command', params=params, verbose=False, auth=None, verify=False)
        assert len(entries) == 2

    @vcr.use_cassette(os.path.join(THIS_DIR, "../fixtures/vcr_cassettes/each_record_id-commands.yaml"))
    def test_can_fetch_records(self):
        records = list(getFromRestAPI.each_record("id-command", url=FPRSERVER))
        assert len(records) == 2

class TestFPRClient(TestCase):
    """
    Test fetching and updating rules.
    """

    # ID commands that replace each other
    rule_a = {
        "replaces": None,
        "uuid": "1c7dd02f-dfd8-46cb-af68-5b305aea1d6e",
        "script": "script contents",
        "tool": None,
        "enabled": True,
        "script_type": "pythonScript",
        "config": "PUID",
        "description": "Rule A",
    }
    rule_b = {
        "replaces_id": "1c7dd02f-dfd8-46cb-af68-5b305aea1d6e",
        "uuid": "889a79ca-3964-409c-b943-40edc5d33f0f",
        "script": "script contents",
        "tool": None,
        "enabled": True,
        "script_type": "pythonScript",
        "config": "PUID",
        "description": "Rule B (replaces rule A, locally)",
    }
    rule_c = {
        "replaces_id": "889a79ca-3964-409c-b943-40edc5d33f0f",
        "uuid": "f73d72ef-6818-45ad-b351-fe0cdede9419",
        "script": "script contents",
        "tool": None,
        "enabled": True,
        "script_type": "pythonScript",
        "config": "PUID",
        "description": "Rule C (replaces rule B, locally)",  # Could have been generated by replacing A
    }
    rule_a_fpr = {
        "replaces": None,
        "uuid": "1c7dd02f-dfd8-46cb-af68-5b305aea1d6e",
        "script": "script contents",
        "tool": None,
        "enabled": False,
        "script_type": "pythonScript",
        "config": "PUID",
        "description": "Rule A (from FPR)",
        "resource_uri": "/fpr/api/v2/id-command/1c7dd02f-dfd8-46cb-af68-5b305aea1d6e/",
        "lastmodified": "2011-9-18T18:31:29",
    }

    rule_r = {
        "replaces": "/fpr/api/v2/id-command/1c7dd02f-dfd8-46cb-af68-5b305aea1d6e/",
        "uuid": "e3ca565f-1cf9-4a6c-9732-70f7ed33a2fa",
        "script": "script contents",
        "tool": None,
        "enabled": True,
        "script_type": "pythonScript",
        "config": "PUID",
        "description": "Rule R (replaces A, from FPR)",
        "resource_uri": "/fpr/api/v2/id-command/e3ca565f-1cf9-4a6c-9732-70f7ed33a2fa/",
        "lastmodified": "2011-10-18T18:31:29",
    }

    def setUp(self):
        self.fprclient = client.FPRClient(fprserver=FPRSERVER)
        # Delete real IDcommands so we can test with our stub ones
        models.IDCommand.objects.all().delete()
        models.Format.objects.all().delete()
        models.IDTool.objects.all().delete()
        models.FPTool.objects.all().delete()

    def test_insert_initial_chain(self):
        """ Insert a chain of rules into a new install. """
        # Use the FPR to add the first in a replacement chain
        # Initial rule in a chain should always be enabled
        self.fprclient.addResource(self.rule_a_fpr, models.IDCommand)
        rule_a = models.IDCommand.objects.get(uuid=self.rule_a_fpr['uuid'])
        assert rule_a.enabled is True
        assert rule_a.replaces is None

        # Use the FPR to add a replacement R for A
        self.fprclient.addResource(self.rule_r, models.IDCommand)
        rule_a = models.IDCommand.objects.get(uuid=self.rule_a_fpr['uuid'])
        rule_r = models.IDCommand.objects.get(uuid=self.rule_r['uuid'])
        assert rule_a.enabled is False
        assert rule_r.enabled is True
        assert rule_r.replaces == rule_a

    def test_add_replacement_rule_for_existing_rule(self):
        """ Insert a replacement rule for a rule that was not added via the fprclient. """
        # Insert initial rule A
        rule_a = models.IDCommand.objects.create(**self.rule_a)
        assert rule_a.enabled is True
        assert rule_a.replaces is None
        # Use the FPR to add a replacement R for A
        self.fprclient.addResource(self.rule_r, models.IDCommand)
        rule_a = models.IDCommand.objects.get(uuid=self.rule_a['uuid'])
        rule_r = models.IDCommand.objects.get(uuid=self.rule_r['uuid'])
        assert rule_a.enabled is False
        assert rule_a.replaces is None
        assert rule_r.enabled is True
        assert rule_r.replaces == rule_a

    def test_replace_of_manually_modified_rule(self):
        """ Insert a replacement rule for a rule that was locally modified. """
        # Initial setup: A <- B (active)
        # B replaced A
        # Insert from FPR rule R, replaces A
        # Result: A <- R <- B (active)

        # Insert initial rule A
        rule_a = models.IDCommand.objects.create(**self.rule_a)
        assert rule_a.enabled is True
        assert rule_a.replaces is None

        # Insert rule B replacing A
        rule_b = models.IDCommand.objects.create(**self.rule_b)
        rule_b.save(replacing=rule_a)
        rule_a = models.IDCommand.objects.get(uuid=self.rule_a['uuid'])
        assert rule_a.enabled is False
        assert rule_a.replaces is None
        assert rule_b.enabled is True
        assert rule_b.replaces == rule_a

        # Use the FPR to add a replacement R for A
        self.fprclient.addResource(self.rule_r, models.IDCommand)
        rule_a = models.IDCommand.objects.get(uuid=self.rule_a['uuid'])
        rule_b = models.IDCommand.objects.get(uuid=self.rule_b['uuid'])
        rule_r = models.IDCommand.objects.get(uuid=self.rule_r['uuid'])
        assert rule_a.enabled is False
        assert rule_a.replaces is None
        assert rule_r.enabled is False
        assert rule_r.replaces == rule_a
        assert rule_b.enabled is True
        assert rule_b.replaces == rule_r

    @vcr.use_cassette(os.path.join(THIS_DIR, "../fixtures/vcr_cassettes/update_all_rules.yaml"))
    def test_update_all_rules(self):
        """ Test running the whole FPRClient autoupdate. """
        # Check things were inserted into DB
        assert models.Format.objects.count() == 0
        assert models.FormatVersion.objects.count() == 0
        assert models.IDTool.objects.count() == 0
        assert models.IDCommand.objects.count() == 0
        assert models.IDRule.objects.count() == 0
        assert models.FPTool.objects.count() == 0
        assert models.FPCommand.objects.count() == 0
        assert models.FPRule.objects.count() == 0

        (status, response, exception) = self.fprclient.getUpdates()

        assert status == 'success'
        assert 'Error' not in response
        assert exception is None
        # Check things were inserted into DB
        assert models.Format.objects.count() > 0
        assert models.FormatVersion.objects.count() > 0
        assert models.IDTool.objects.count() > 0
        assert models.IDCommand.objects.count() > 0
        assert models.IDRule.objects.count() > 0
        assert models.FPTool.objects.count() > 0
        assert models.FPCommand.objects.count() > 0
        assert models.FPRule.objects.count() > 0
        assert main.models.UnitVariable.objects.get(unittype='FPR', variable='maxLastUpdate') != "2000-01-01T00:00:00"
