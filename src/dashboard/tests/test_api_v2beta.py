# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json

from django.urls import reverse
from django.test import TestCase, Client
import mock

from archivematicaFunctions import b64encode_string
from components import helpers
from components.api import validators
from version import get_full_version


class MCPClientMock(object):
    def __init__(self, fails=False):
        self.fails = fails

    def create_package(
        self,
        name,
        type_,
        accession,
        access_system_id,
        path,
        metadata_set_id,
        auto_approve=True,
        wait_until_complete=False,
    ):
        if self.fails:
            raise Exception("Something bad happened!")
        return "59402c61-3aba-4af7-966a-996073c0601d"


class TestAPIv2(TestCase):
    fixtures = ["test_user"]

    # This is valid path value that we're going to pass to the API server.
    path = b64encode_string(
        "{location_uuid}:{relative_path}".format(
            **{
                "location_uuid": "671643e1-5bec-4a5f-b244-abb76fedb0c4",
                "relative_path": "foo/bar.jpg",
            }
        )
    )

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_headers(self):
        resp = self.client.get("/api/v2beta/package/")
        assert resp.get("X-Archivematica-Version") == get_full_version()
        assert resp.get("X-Archivematica-ID") == "test-uuid"

    def test_package_list(self):
        resp = self.client.get("/api/v2beta/package/")
        assert resp.status_code == 501  # Not implemented yet.

    def test_package_create_with_errors(self):
        # Missing payload
        resp = self.client.post("/api/v2beta/package/", content_type="application/json")
        assert resp.status_code == 400

        # Invalid document
        resp = self.client.post(
            "/api/v2beta/package/", "INVALID-JSON", content_type="application/json"
        )
        assert resp.status_code == 400

        # Invalid path
        resp = self.client.post(
            "/api/v2beta/package/",
            json.dumps({"path": "invalid"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    @mock.patch("components.api.views.MCPClient", return_value=MCPClientMock())
    def test_package_create_mcpclient_ok(self, patcher):
        resp = self.client.post(
            "/api/v2beta/package/",
            json.dumps({"path": self.path}),
            content_type="application/json",
        )
        assert resp.status_code == 202
        assert resp.content.decode() == json.dumps(
            {"id": "59402c61-3aba-4af7-966a-996073c0601d"}
        )

    @mock.patch(
        "components.api.views.MCPClient", return_value=MCPClientMock(fails=True)
    )
    def test_package_create_mcpclient_fails(self, patcher):
        resp = self.client.post(
            "/api/v2beta/package/",
            json.dumps({"path": self.path}),
            content_type="application/json",
        )
        assert resp.status_code == 500
        payload = json.loads(resp.content.decode())
        assert payload["error"] is True
        assert payload["message"] == "Package cannot be created"


class TestValidate(TestCase):
    fixtures = ["test_user"]

    VALID_AVALON_CSV = u"""Avalon Demo Batch,archivist1@example.com,,,,,,,,,,,,,,,,,,,,,,
Bibliographic ID,Bibliographic ID Label,Title,Creator,Contributor,Contributor,Contributor,Contributor,Contributor,Publisher,Date Created,Date Issued,Abstract,Topical Subject,Topical Subject,Publish,File,Skip Transcoding,Label,File,Skip Transcoding,Label,Note Type,Note
,,Symphony no. 3,"Mahler, Gustav, 1860-1911",,,,,,,,1996,,,,yes,assets/agz3068a.wav,no,CD 1,,,,local,This was batch ingested without skip transcoding
,,Féte (Excerpt),"Langlais, Jean, 1907-1991","Young, Christopher C. (Christopher Clark)",,,,,William and Gayle Cook Music Library,,2010,"Recorded on May 2, 2010, Auer Concert Hall, Indiana University, Bloomington.",Organ music,,yes,assets/OrganClip.mp4,yes,,,,,local,This was batch ingested with multiple quality level skip transcoding
,,Beginning Responsibility: Lunchroom Manners,Coronet Films,,,,,,Coronet Films,,1959,"The rude, clumsy puppet Mr. Bungle shows kids how to behave in the school cafeteria - the assumption being that kids actually want to behave during lunch. This film has a cult following since it appeared on a Pee Wee Herman HBO special.",Social engineering,Puppet theater,yes,assets/lunchroom_manners_512kb.high.mp4,yes,Lunchroom 1,assets/lunchroom_manners_512kb.mp4,yes,Lunchroom Again,local,This was batch ingested with skip transcoding and with structure
"""

    INVALID_AVALON_CSV = u"""Avalon Demo Batch,archivist1@example.com,,,,,,,,,,,,,,,,,,,,,,
Bibliographic ID,Bibliographic ID Lbl,Title,Creator,Contributor,Contributor,Contributor,Contributor,Contributor,Publisher,Date Created,Date Issued,Abstract,Topical Subject,Topical Subject,Publish,File,Skip Transcoding,Label,File,Skip Transcoding,Label,Note Type,Note
,,Symphony no. 3,"Mahler, Gustav, 1860-1911",,,,,,,,1996,,,,Yes,assets/agz3068a.wav,no,CD 1,,,,local,This was batch ingested without skip transcoding
,,Féte (Excerpt),"Langlais, Jean, 1907-1991","Young, Christopher C. (Christopher Clark)",,,,,William and Gayle Cook Music Library,,2010,"Recorded on May 2, 2010, Auer Concert Hall, Indiana University, Bloomington.",Organ music,,Yes,assets/OrganClip.mp4,yes,,,,,local,This was batch ingested with multiple quality level skip transcoding
,,Beginning Responsibility: Lunchroom Manners,Coronet Films,,,,,,Coronet Films,,1959,"The rude, clumsy puppet Mr. Bungle shows kids how to behave in the school cafeteria - the assumption being that kids actually want to behave during lunch. This film has a cult following since it appeared on a Pee Wee Herman HBO special.",Social engineering,Puppet theater,Yes,assets/lunchroom_manners_512kb.mp4,yes,Lunchroom 1,assets/lunchroom_manners_512kb.mp4,yes,Lunchroom Again,local,This was batch ingested with skip transcoding and with structure
"""

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def _post(self, validator_name, payload, content_type="text/csv; charset=utf-8"):
        return self.client.post(
            reverse("api:validate", args=[validator_name]),
            payload,
            content_type=content_type,
        )

    def test_unknown_validator(self):
        resp = self._post("unknown-validator", b"...")

        assert resp.status_code == 404
        assert json.loads(resp.content.decode()) == {
            "message": "Unknown validator. Accepted values: {}".format(
                ",".join(list(validators._VALIDATORS.keys()))
            ),
            "error": True,
        }

    def test_unaccepted_content_type(self):
        resp = self._post("avalon", b"...", content_type="text/plain")

        assert resp.status_code == 400
        assert json.loads(resp.content.decode()) == {
            "message": 'Content type should be "text/csv; charset=utf-8"',
            "error": True,
        }

    def test_avalon_pass(self):
        resp = self._post("avalon", self.VALID_AVALON_CSV)

        assert resp.status_code == 200
        assert json.loads(resp.content.decode()) == {"valid": True}

    def test_avalon_err(self):
        resp = self._post("avalon", self.INVALID_AVALON_CSV)

        assert resp.status_code == 400
        assert json.loads(resp.content.decode()) == {
            "valid": False,
            "reason": "Manifest includes invalid metadata field(s). Invalid field(s): Bibliographic ID Lbl",
        }
