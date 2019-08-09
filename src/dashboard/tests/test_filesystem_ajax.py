from __future__ import absolute_import
import json
from base64 import b64decode, b64encode

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from components import helpers
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
            reverse("components.filesystem_ajax.views.arrange_contents"), follow=True
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
            reverse("components.filesystem_ajax.views.arrange_contents"),
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
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": b64encode(b"/arrange/nosuchpath/")},
            follow=True,
        )
        assert response.status_code == 404
        response_dict = json.loads(response.content.decode("utf8"))
        assert response_dict["success"] is False

    def test_arrange_contents_empty_base_dir(self):
        models.SIPArrange.objects.all().delete()
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
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
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": b64encode(b"/arrange").decode("utf8")},
            follow=True,
        )
        assert (
            b64encode(b"newsip").decode("utf8")
            in json.loads(response.content.decode("utf8"))["directories"]
        )
        # Delete files
        response = self.client.post(
            reverse("components.filesystem_ajax.views.delete_arrange"),
            data={"filepath": b64encode(b"/arrange/newsip/").decode("utf8")},
            follow=True,
        )
        assert response.status_code == 200
        assert json.loads(response.content.decode("utf8")) == {
            "message": "Delete successful."
        }
        # Check deleted
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
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
            reverse("components.filesystem_ajax.views.arrange_contents"),
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
            reverse("components.filesystem_ajax.views.create_directory_within_arrange"),
            data={"paths[]": b64encode(b"/arrange/new_dir").decode("utf8")},
            follow=True,
        )
        assert response.status_code == 201
        assert json.loads(response.content.decode("utf8")) == {
            "message": "Creation successful."
        }
        # Check created
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
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
            reverse("components.filesystem_ajax.views.copy_to_arrange"),
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
            reverse("components.filesystem_ajax.views.arrange_contents"),
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
            reverse("components.filesystem_ajax.views.arrange_contents"),
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
