import base64
import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
import pytest

from components import helpers
from components.filesystem_ajax.views import _save_sip_arranges
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
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": None},
            follow=True,
        )
        # Verify
        assert response.status_code == 200
        response_dict = json.loads(response.content)
        assert "directories" in response_dict
        assert base64.b64encode("newsip") in response_dict["directories"]
        assert base64.b64encode("toplevel") in response_dict["directories"]
        assert len(response_dict["directories"]) == 2
        assert "entries" in response_dict
        assert base64.b64encode("newsip") in response_dict["entries"]
        assert base64.b64encode("toplevel") in response_dict["entries"]
        assert len(response_dict["entries"]) == 2
        assert "properties" in response_dict
        assert base64.b64encode("newsip") in response_dict["properties"]
        assert (
            response_dict["properties"][base64.b64encode("newsip")]["display_string"]
            == "2 objects"
        )
        assert base64.b64encode("toplevel") in response_dict["properties"]
        assert (
            response_dict["properties"][base64.b64encode("toplevel")]["display_string"]
            == "1 object"
        )
        assert len(response_dict) == 3

    def test_arrange_contents_data_path(self):
        # Folder, without /
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": base64.b64encode("/arrange/newsip/objects/")},
            follow=True,
        )
        # Verify
        assert response.status_code == 200
        response_dict = json.loads(response.content)
        assert "directories" in response_dict
        assert base64.b64encode("evelyn_s_second_photo") in response_dict["directories"]
        assert len(response_dict["directories"]) == 1
        assert "entries" in response_dict
        assert base64.b64encode("evelyn_s_photo.jpg") in response_dict["entries"]
        assert base64.b64encode("evelyn_s_second_photo") in response_dict["entries"]
        assert len(response_dict["entries"]) == 2
        assert "properties" in response_dict
        assert base64.b64encode("evelyn_s_second_photo") in response_dict["properties"]
        assert (
            response_dict["properties"][base64.b64encode("evelyn_s_second_photo")][
                "display_string"
            ]
            == "1 object"
        )
        assert len(response_dict) == 3

    def test_arrange_contents_404(self):
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": base64.b64encode("/arrange/nosuchpath/")},
            follow=True,
        )
        assert response.status_code == 404
        response_dict = json.loads(response.content)
        assert response_dict["success"] is False

    def test_arrange_contents_empty_base_dir(self):
        models.SIPArrange.objects.all().delete()
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": base64.b64encode("/arrange/")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content)
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
            {"path": base64.b64encode("/arrange")},
            follow=True,
        )
        assert base64.b64encode("newsip") in json.loads(response.content)["directories"]
        # Delete files
        response = self.client.post(
            reverse("components.filesystem_ajax.views.delete_arrange"),
            data={"filepath": base64.b64encode("/arrange/newsip/")},
            follow=True,
        )
        assert response.status_code == 200
        assert json.loads(response.content) == {"message": "Delete successful."}
        # Check deleted
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": base64.b64encode("/arrange")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content)
        assert base64.b64encode("toplevel") in response_dict["directories"]
        assert len(response_dict["directories"]) == 1
        assert base64.b64encode("toplevel") in response_dict["entries"]
        assert len(response_dict["entries"]) == 1

    def test_create_arranged_directories(self):
        # Verify does not exist already
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": base64.b64encode("/arrange")},
            follow=True,
        )
        assert (
            base64.b64encode("new_dir")
            not in json.loads(response.content)["directories"]
        )
        assert (
            base64.b64encode("new_dir") not in json.loads(response.content)["entries"]
        )
        # Create directory
        response = self.client.post(
            reverse("components.filesystem_ajax.views.create_directory_within_arrange"),
            data={"paths[]": [base64.b64encode("/arrange/new_dir")]},
            follow=True,
        )
        assert response.status_code == 201
        assert json.loads(response.content) == {"message": "Creation successful."}
        # Check created
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": base64.b64encode("/arrange")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content)
        assert base64.b64encode("new_dir") in response_dict["directories"]
        assert base64.b64encode("newsip") in response_dict["directories"]
        assert base64.b64encode("toplevel") in response_dict["directories"]
        assert len(response_dict["directories"]) == 3
        assert base64.b64encode("new_dir") in response_dict["entries"]
        assert base64.b64encode("newsip") in response_dict["entries"]
        assert base64.b64encode("toplevel") in response_dict["entries"]
        assert len(response_dict["entries"]) == 3

    def test_move_within_arrange(self):
        # Move directory
        response = self.client.post(
            reverse("components.filesystem_ajax.views.copy_to_arrange"),
            data={
                "filepath": base64.b64encode("/arrange/newsip/"),
                "destination": base64.b64encode("/arrange/toplevel/"),
            },
            follow=True,
        )
        assert response.status_code == 201
        assert json.loads(response.content) == {"message": "Files added to the SIP."}
        # Check gone from parent
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": base64.b64encode("/arrange")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content)
        assert base64.b64encode("toplevel") in response_dict["directories"]
        assert base64.b64encode("newsip") not in response_dict["directories"]
        assert len(response_dict["directories"]) == 1
        assert base64.b64encode("toplevel") in response_dict["entries"]
        assert base64.b64encode("newsip") not in response_dict["entries"]
        assert len(response_dict["entries"]) == 1

        # Check now in subdirectory
        response = self.client.get(
            reverse("components.filesystem_ajax.views.arrange_contents"),
            {"path": base64.b64encode("/arrange/toplevel")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content)
        assert base64.b64encode("subsip") in response_dict["directories"]
        assert base64.b64encode("newsip") in response_dict["directories"]
        assert len(response_dict["directories"]) == 2
        assert base64.b64encode("subsip") in response_dict["entries"]
        assert base64.b64encode("newsip") in response_dict["entries"]
        assert len(response_dict["entries"]) == 2


@pytest.mark.django_db(transaction=True)
def test_save_arranges():
    arranges = [
        models.SIPArrange(original_path=None, arrange_path="a.txt", file_uuid=None),
        models.SIPArrange(original_path=None, arrange_path="b.txt", file_uuid=None),
    ]
    assert not models.SIPArrange.objects.count()
    _save_sip_arranges(arranges)
    assert models.SIPArrange.objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_save_arranges_with_integrity_error():
    a_uuid = "89850069-4ff5-4162-b4dd-982bca9bb82f"
    models.SIPArrange.objects.create(
        original_path=None, arrange_path="a.txt", file_uuid=a_uuid
    )
    assert models.SIPArrange.objects.count() == 1
    arranges = [
        # a_uuid already exists in the database
        models.SIPArrange(original_path=None, arrange_path="a.txt", file_uuid=a_uuid),
        models.SIPArrange(original_path=None, arrange_path="b.txt", file_uuid=None),
    ]
    _save_sip_arranges(arranges)
    assert models.SIPArrange.objects.count() == 2
