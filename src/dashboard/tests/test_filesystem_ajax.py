# -*- coding: utf-8 -*-
from __future__ import absolute_import

from base64 import b64encode
import json
import uuid

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
import pytest

from archivematicaFunctions import b64encode_string
from components import helpers
from components.filesystem_ajax import views
from main import models


class TestSIPArrange(TestCase):
    fixtures = ["test_user", "sip_arrange"]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_fixtures(self):
        objs = models.SIPArrange.objects.all()
        assert len(objs) > 0

    def test_arrange_contents_data_no_path(self):
        # Call endpoint
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"), follow=True
        )
        # Verify
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert "directories" in response_dict
        assert b64encode(b"newsip").decode("utf8") in response_dict["directories"]
        assert b64encode(b"toplevel").decode("utf8") in response_dict["directories"]
        assert len(response_dict["directories"]) == 2
        assert "entries" in response_dict
        assert b64encode(b"newsip").decode("utf8") in response_dict["entries"]
        assert b64encode(b"toplevel").decode("utf8") in response_dict["entries"]
        assert len(response_dict["entries"]) == 2
        assert "properties" in response_dict
        assert b64encode(b"newsip").decode("utf8") in response_dict["properties"]
        assert (
            response_dict["properties"][b64encode(b"newsip").decode("utf8")][
                "display_string"
            ]
            == "2 objects"
        )
        assert b64encode(b"toplevel").decode("utf8") in response_dict["properties"]
        assert (
            response_dict["properties"][b64encode(b"toplevel").decode("utf8")][
                "display_string"
            ]
            == "1 object"
        )
        assert len(response_dict) == 3

    def test_arrange_contents_data_path(self):
        # Folder, without /
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode(b"/arrange/newsip/objects/")},
            follow=True,
        )
        # Verify
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert "directories" in response_dict
        assert (
            b64encode(b"evelyn_s_second_photo").decode("utf8")
            in response_dict["directories"]
        )
        assert len(response_dict["directories"]) == 1
        assert "entries" in response_dict
        assert (
            b64encode(b"evelyn_s_photo.jpg").decode("utf8") in response_dict["entries"]
        )
        assert (
            b64encode(b"evelyn_s_second_photo").decode("utf8")
            in response_dict["entries"]
        )
        assert len(response_dict["entries"]) == 2
        assert "properties" in response_dict
        assert (
            b64encode(b"evelyn_s_second_photo").decode("utf8")
            in response_dict["properties"]
        )
        assert (
            response_dict["properties"][
                b64encode(b"evelyn_s_second_photo").decode("utf8")
            ]["display_string"]
            == "1 object"
        )
        assert len(response_dict) == 3

    def test_arrange_contents_404(self):
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode(b"/arrange/nosuchpath/")},
            follow=True,
        )
        assert response.status_code == 404
        response_dict = json.loads(response.content.decode("utf8"))
        assert response_dict["success"] is False

    def test_arrange_contents_empty_base_dir(self):
        models.SIPArrange.objects.all().delete()
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode(b"/arrange/")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert "directories" in response_dict
        assert len(response_dict["directories"]) == 0
        assert "entries" in response_dict
        assert len(response_dict["entries"]) == 0
        assert "properties" in response_dict
        assert len(response_dict) == 3

    def test_delete_arranged_files(self):
        # Check to-be-deleted exists
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode(b"/arrange").decode("utf8")},
            follow=True,
        )
        assert (
            b64encode(b"newsip").decode("utf8")
            in json.loads(response.content.decode("utf8"))["directories"]
        )
        # Delete files
        response = self.client.post(
            reverse("filesystem_ajax:delete_arrange"),
            data={"filepath": b64encode(b"/arrange/newsip/").decode("utf8")},
            follow=True,
        )
        assert response.status_code == 200
        assert json.loads(response.content.decode("utf8")) == {
            "message": "Delete successful."
        }
        # Check deleted
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode(b"/arrange").decode("utf8")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert b64encode(b"toplevel").decode("utf8") in response_dict["directories"]
        assert len(response_dict["directories"]) == 1
        assert b64encode(b"toplevel").decode("utf8") in response_dict["entries"]
        assert len(response_dict["entries"]) == 1

    def test_create_arranged_directories(self):
        # Verify does not exist already
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode(b"/arrange")},
            follow=True,
        )
        assert (
            b64encode(b"new_dir")
            not in json.loads(response.content.decode("utf8"))["directories"]
        )
        assert (
            b64encode(b"new_dir")
            not in json.loads(response.content.decode("utf8"))["entries"]
        )
        # Create directory
        response = self.client.post(
            reverse("filesystem_ajax:create_directory_within_arrange"),
            data={"paths[]": b64encode(b"/arrange/new_dir").decode("utf8")},
            follow=True,
        )
        assert response.status_code == 201
        assert json.loads(response.content.decode("utf8")) == {
            "message": "Creation successful."
        }
        # Check created
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode(b"/arrange")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert b64encode(b"new_dir").decode("utf8") in response_dict["directories"]
        assert b64encode(b"newsip").decode("utf8") in response_dict["directories"]
        assert b64encode(b"toplevel").decode("utf8") in response_dict["directories"]
        assert len(response_dict["directories"]) == 3
        assert b64encode(b"new_dir").decode("utf8") in response_dict["entries"]
        assert b64encode(b"newsip").decode("utf8") in response_dict["entries"]
        assert b64encode(b"toplevel").decode("utf8") in response_dict["entries"]
        assert len(response_dict["entries"]) == 3

    def test_move_within_arrange(self):
        # Move directory
        response = self.client.post(
            reverse("filesystem_ajax:copy_to_arrange"),
            data={
                "filepath": b64encode(b"/arrange/newsip/").decode("utf8"),
                "destination": b64encode(b"/arrange/toplevel/").decode("utf8"),
            },
            follow=True,
        )
        assert response.status_code == 201
        assert json.loads(response.content.decode("utf8")) == {
            "message": "Files added to the SIP."
        }
        # Check gone from parent
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode(b"/arrange")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert b64encode(b"toplevel").decode("utf8") in response_dict["directories"]
        assert b64encode(b"newsip").decode("utf8") not in response_dict["directories"]
        assert len(response_dict["directories"]) == 1
        assert b64encode(b"toplevel").decode("utf8") in response_dict["entries"]
        assert b64encode(b"newsip").decode("utf8") not in response_dict["entries"]
        assert len(response_dict["entries"]) == 1

        # Check now in subdirectory
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode(b"/arrange/toplevel")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert b64encode(b"subsip").decode("utf8") in response_dict["directories"]
        assert b64encode(b"newsip").decode("utf8") in response_dict["directories"]
        assert len(response_dict["directories"]) == 2
        assert b64encode(b"subsip").decode("utf8") in response_dict["entries"]
        assert b64encode(b"newsip").decode("utf8") in response_dict["entries"]
        assert len(response_dict["entries"]) == 2


@pytest.mark.django_db
def test_copy_metadata_files(mocker):
    # Mock helper that actually copies files from the transfer source locations
    _copy_from_transfer_sources_mock = mocker.patch(
        "components.filesystem_ajax.views._copy_from_transfer_sources",
        return_value=(None, ""),
    )

    # Create a SIP
    sip_uuid = str(uuid.uuid4())
    models.SIP.objects.create(
        uuid=sip_uuid,
        currentpath="%sharedPath%more/path/metadataReminder/mysip-{}/".format(sip_uuid),
    )

    # Call the view with a mocked request
    request = mocker.Mock(
        **{
            "POST.get.return_value": sip_uuid,
            "POST.getlist.return_value": [b64encode_string("locationuuid:/some/path")],
        }
    )
    result = views.copy_metadata_files(request)

    # Verify the contents of the response
    assert result.status_code == 201
    assert result["Content-Type"] == "application/json"
    assert json.loads(result.content) == {
        "message": "Metadata files added successfully.",
        "error": None,
    }

    # Verify the copier helper was called with the right parameters
    _copy_from_transfer_sources_mock.assert_called_once_with(
        ["locationuuid:/some/path"],
        "more/path/metadataReminder/mysip-{}/metadata".format(sip_uuid),
    )
