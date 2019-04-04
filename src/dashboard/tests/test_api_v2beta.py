# -*- coding: utf-8 -*-

import base64
import json
import os

from django.test import TestCase, Client
import mock

from components import helpers
from components.api import validators


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


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
        return b"59402c61-3aba-4af7-966a-996073c0601d"


class TestAPIv2(TestCase):
    fixture_files = ["test_user.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    # This is valid path value that we're going to pass to the API server.
    path = base64.b64encode(
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
        assert resp.content == json.dumps(
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
        payload = json.loads(resp.content)
        assert payload["error"] is True
        assert payload["message"] == "Package cannot be created"


class TestValidate(TestCase):
    fixture_files = ["test_user.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_validate_with_unknown_validator(self):
        resp = self.client.post(
            "/api/v2beta/validate/",
            json.dumps({"validator": "!!unknown", "payload": "..."}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert resp.content == json.dumps(
            {
                "message": "Unknown validator. Accepted values: {}".format(
                    ",".join(validators._VALIDATORS.keys())
                ),
                "error": True,
            }
        )

    def test_validate_with_undecodable_base64(self):
        resp = self.client.post(
            "/api/v2beta/validate/",
            json.dumps({"validator": "avalon", "payload": "badpadding="}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.content == json.dumps(
            {"valid": False, "reason": "Base64 decoding failed: Incorrect padding"}
        )

    @mock.patch(
        "components.api.validators.AvalonValidator.validate",
        side_effect=validators.ValidationError("Bad contents!"),
    )
    def test_validate_valid_err(self, validate_mock):
        resp = self.client.post(
            "/api/v2beta/validate/",
            json.dumps({"validator": "avalon", "payload": "Rm9vYmFy"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.content == json.dumps({"valid": False, "reason": "Bad contents!"})
        validate_mock.assert_called_once_with("Rm9vYmFy")

    @mock.patch("components.api.validators.AvalonValidator.validate")
    def test_validate_valid_ok(self, validate_mock):
        resp = self.client.post(
            "/api/v2beta/validate/",
            json.dumps({"validator": "avalon", "payload": "Rm9vYmFy"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.content == json.dumps({"valid": True})
        validate_mock.assert_called_once_with("Rm9vYmFy")

    def test_validate_avalon_err(self):
        SAMPLE = b"""Avalon Demo Batch,archivist1@example.com,,,,,,,,,,,,,,,,,,,,,,
Bibliographic ID,Bibliographic ID Lbl,Title,Creator,Contributor,Contributor,Contributor,Contributor,Contributor,Publisher,Date Created,Date Issued,Abstract,Topical Subject,Topical Subject,Publish,File,Skip Transcoding,Label,File,Skip Transcoding,Label,Note Type,Note
,,Symphony no. 3,"Mahler, Gustav, 1860-1911",,,,,,,,1996,,,,Yes,assets/agz3068a.wav,no,CD 1,,,,local,This was batch ingested without skip transcoding
,,Fete (Excerpt),"Langlais, Jean, 1907-1991","Young, Christopher C. (Christopher Clark)",,,,,William and Gayle Cook Music Library,,2010,"Recorded on May 2, 2010, Auer Concert Hall, Indiana University, Bloomington.",Organ music,,Yes,assets/OrganClip.mp4,yes,,,,,local,This was batch ingested with multiple quality level skip transcoding
,,Beginning Responsibility: Lunchroom Manners,Coronet Films,,,,,,Coronet Films,,1959,"The rude, clumsy puppet Mr. Bungle shows kids how to behave in the school cafeteria - the assumption being that kids actually want to behave during lunch. This film has a cult following since it appeared on a Pee Wee Herman HBO special.",Social engineering,Puppet theater,Yes,assets/lunchroom_manners_512kb.mp4,yes,Lunchroom 1,assets/lunchroom_manners_512kb.mp4,yes,Lunchroom Again,local,This was batch ingested with skip transcoding and with structure
"""

        resp = self.client.post(
            "/api/v2beta/validate/",
            json.dumps(
                {
                    "validator": "avalon",
                    "payload": base64.b64encode(SAMPLE).decode("utf-8"),
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.content == json.dumps(
            {
                "reason": "Manifest includes invalid metadata field(s). Invalid field(s): Bibliographic ID Lbl",
                "valid": False,
            }
        )

    def test_validate_avalon_ok(self):
        SAMPLE = b"""Avalon Demo Batch,archivist1@example.com,,,,,,,,,,,,,,,,,,,,,,
Bibliographic ID,Bibliographic ID Label,Title,Creator,Contributor,Contributor,Contributor,Contributor,Contributor,Publisher,Date Created,Date Issued,Abstract,Topical Subject,Topical Subject,Publish,File,Skip Transcoding,Label,File,Skip Transcoding,Label,Note Type,Note
,,Symphony no. 3,"Mahler, Gustav, 1860-1911",,,,,,,,1996,,,,yes,assets/agz3068a.wav,no,CD 1,,,,local,This was batch ingested without skip transcoding
,,Fete (Excerpt),"Langlais, Jean, 1907-1991","Young, Christopher C. (Christopher Clark)",,,,,William and Gayle Cook Music Library,,2010,"Recorded on May 2, 2010, Auer Concert Hall, Indiana University, Bloomington.",Organ music,,yes,assets/OrganClip.mp4,yes,,,,,local,This was batch ingested with multiple quality level skip transcoding
,,Beginning Responsibility: Lunchroom Manners,Coronet Films,,,,,,Coronet Films,,1959,"The rude, clumsy puppet Mr. Bungle shows kids how to behave in the school cafeteria - the assumption being that kids actually want to behave during lunch. This film has a cult following since it appeared on a Pee Wee Herman HBO special.",Social engineering,Puppet theater,yes,assets/lunchroom_manners_512kb.high.mp4,yes,Lunchroom 1,assets/lunchroom_manners_512kb.mp4,yes,Lunchroom Again,local,This was batch ingested with skip transcoding and with structure
"""
        resp = self.client.post(
            "/api/v2beta/validate/",
            json.dumps(
                {
                    "validator": "avalon",
                    "payload": base64.b64encode(SAMPLE).decode("utf-8"),
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.content == json.dumps({"valid": True})
