# -*- coding: utf-8 -*-
from __future__ import absolute_import

from base64 import b64encode
import json
import os
import uuid
import tempfile

from django.urls import reverse
from django.test import TestCase
from django.test.client import Client, RequestFactory
import pytest
import mock

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

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

    def test_copy_from_arrange_to_completed(self):
        sip_uuid = "a29e7e86-eca9-43b6-b059-6f23a9802dc8"
        models.SIP.objects.create(uuid=sip_uuid)
        with mock.patch(
            "components.filesystem_ajax.views.storage_service.get_files_from_backlog",
            return_value=("12345", None),
        ):
            with mock.patch(
                "components.filesystem_ajax.views._create_arranged_sip",
                return_value=None,
            ) as create_arranged_sip_mock:
                response = self.client.post(
                    reverse("filesystem_ajax:copy_from_arrange"),
                    data={
                        "filepath": b64encode(b"/arrange/newsip/").decode("utf8"),
                        "uuid": sip_uuid,
                    },
                    follow=True,
                )

                assert response.status_code == 201
                response_dict = json.loads(response.content.decode("utf8"))
                assert response_dict["message"] == "SIP created."
                assert response_dict["sip_uuid"] == sip_uuid

                create_arranged_sip_mock.assert_called_once_with(
                    u"staging/newsip/",
                    [
                        {
                            "source": u"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/objects/evelyn_s_photo.jpg",
                            "destination": u"staging/newsip/objects/evelyn_s_photo.jpg",
                            "uuid": u"4fa8f739-b633-4c0f-8833-d108a4f4e88d",
                        },
                        {
                            "source": u"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/logs/.",
                            "destination": "tmp/transfer-a29e7e86-eca9-43b6-b059-6f23a9802dc8/logs/.",
                        },
                        {
                            "source": u"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/metadata/.",
                            "destination": "tmp/transfer-a29e7e86-eca9-43b6-b059-6f23a9802dc8/metadata/.",
                        },
                        {
                            "source": u"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/objects/evelyn_s_second_photo/evelyn_s_second_photo.jpg",
                            "destination": u"staging/newsip/objects/evelyn_s_second_photo/evelyn_s_second_photo.jpg",
                            "uuid": u"7f889d5d-7849-490e-a8e6-ccb9595445d7",
                        },
                    ],
                    sip_uuid,
                )

    def test_copy_from_arrange_to_completed_from_bagit_transfer(self):
        """Confirms that SIP arrangement is also possible from BagIt transfers.

        See https://github.com/archivematica/Issues/issues/1267 for a scenario
        where files in backlogged transfers such as `data/logs/*` would cause
        the endpoint to fail.
        """
        sip_uuid = u"a29e7e86-eca9-43b6-b059-6f23a9802dc8"
        models.SIP.objects.create(uuid=sip_uuid)
        models.SIPArrange.objects.all().delete()
        models.SIPArrange.objects.create(arrange_path="/arrange/testsip/")
        models.SIPArrange.objects.create(arrange_path="/arrange/testsip/data/")
        models.SIPArrange.objects.create(arrange_path="/arrange/testsip/data/objects/")
        models.SIPArrange.objects.create(
            arrange_path="/arrange/testsip/data/objects/MARBLES.TGA",
            original_path="originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/objects/MARBLES.TGA",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
        )
        models.SIPArrange.objects.create(
            arrange_path="/arrange/testsip/data/logs/BagIt/bagit.txt",
            original_path="originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/logs/BagIt/bagit.txt",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
        )
        models.SIPArrange.objects.create(
            arrange_path="/arrange/testsip/data/metadata/manifest-md5.txt",
            original_path="originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/metadata/manifest-md5.txt",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
        )

        with mock.patch(
            "components.filesystem_ajax.views.storage_service.get_files_from_backlog",
            return_value=("12345", None),
        ):
            with mock.patch(
                "components.filesystem_ajax.views._create_arranged_sip",
                return_value=None,
            ) as create_arranged_sip_mock:
                response = self.client.post(
                    reverse("filesystem_ajax:copy_from_arrange"),
                    data={
                        "filepath": b64encode(b"/arrange/testsip/").decode("utf8"),
                        "uuid": sip_uuid,
                    },
                    follow=True,
                )

                assert response.status_code == 201
                response_dict = json.loads(response.content.decode("utf8"))
                assert response_dict["message"] == "SIP created."
                assert response_dict["sip_uuid"] == sip_uuid

                create_arranged_sip_mock.assert_called_once_with(
                    u"staging/testsip/",
                    [
                        {
                            "source": u"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/objects/MARBLES.TGA",
                            "destination": u"staging/testsip/data/objects/MARBLES.TGA",
                            "uuid": None,
                        },
                        {
                            "source": u"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/logs/.",
                            "destination": "tmp/transfer-a29e7e86-eca9-43b6-b059-6f23a9802dc8/logs/.",
                        },
                        {
                            "source": u"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/metadata/.",
                            "destination": "tmp/transfer-a29e7e86-eca9-43b6-b059-6f23a9802dc8/metadata/.",
                        },
                        {
                            "source": u"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/logs/BagIt/bagit.txt",
                            "destination": u"staging/testsip/data/logs/BagIt/bagit.txt",
                            "uuid": None,
                        },
                        {
                            "source": u"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/metadata/manifest-md5.txt",
                            "destination": u"staging/testsip/data/metadata/manifest-md5.txt",
                            "uuid": None,
                        },
                    ],
                    sip_uuid,
                )

    def test_copy_from_arrange_to_completed_rejects_invalid_sip_uuid(self):
        response = self.client.post(
            reverse("filesystem_ajax:copy_from_arrange"),
            data={
                "filepath": b64encode(b"/arrange/testsip/").decode("utf8"),
                "uuid": "invalid-uuid",
            },
            follow=True,
        )

        assert response.status_code == 400
        assert (
            response.json()["message"]
            == "Provided UUID (invalid-uuid) is not a valid UUID!"
        )

    def test_copy_from_arrange_to_completed_rejects_invalid_filepath(self):
        response = self.client.post(
            reverse("filesystem_ajax:copy_from_arrange"),
            data={
                "filepath": b64encode(b"/path/testsip/").decode("utf8"),
                "uuid": "607df760-a0be-4fef-875a-74ea00c61bf9",
            },
            follow=True,
        )

        assert response.status_code == 400
        assert response.json()["message"] == "/path/testsip/ is not in /arrange/"

    def test_copy_from_arrange_to_completed_rejects_nondir_filepath(self):
        response = self.client.post(
            reverse("filesystem_ajax:copy_from_arrange"),
            data={
                "filepath": b64encode(b"/arrange/testsip").decode("utf8"),
                "uuid": "607df760-a0be-4fef-875a-74ea00c61bf9",
            },
            follow=True,
        )

        assert response.status_code == 400
        assert response.json()["message"] == "/arrange/testsip is not a directory"

    def test_copy_from_arrange_to_completed_rejects_empty_arrangements(self):
        models.SIP.objects.create(uuid="607df760-a0be-4fef-875a-74ea00c61bf9")
        models.SIPArrange.objects.all().delete()
        models.SIPArrange.objects.create(arrange_path="/arrange/testsip/")

        response = self.client.post(
            reverse("filesystem_ajax:copy_from_arrange"),
            data={
                "filepath": b64encode(b"/arrange/testsip/").decode("utf8"),
                "uuid": "607df760-a0be-4fef-875a-74ea00c61bf9",
            },
            follow=True,
        )

        assert response.status_code == 400
        assert response.json()["message"] == "No files were selected"

    def test_copy_from_arrange_to_completed_handles_name_clashes(self):
        """Confirms that SIP arrangement is also possible from BagIt transfers.

        See https://github.com/archivematica/Issues/issues/1267 for a scenario
        where files in backlogged transfers such as `data/logs/*` would cause
        the endpoint to fail.
        """
        sip_uuid = u"a29e7e86-eca9-43b6-b059-6f23a9802dc8"
        models.SIPArrange.objects.all().delete()
        models.SIPArrange.objects.create(arrange_path="/arrange/testsip/")
        models.SIPArrange.objects.create(arrange_path="/arrange/testsip/data/")
        models.SIPArrange.objects.create(arrange_path="/arrange/testsip/data/objects/")
        models.SIPArrange.objects.create(
            arrange_path="/arrange/testsip/data/objects/MARBLES.TGA",
            original_path="originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/objects/MARBLES.TGA",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
        )
        models.SIPArrange.objects.create(
            arrange_path="/arrange/testsip/data/logs/BagIt/bagit.txt",
            original_path="originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/logs/BagIt/bagit.txt",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
        )
        models.SIPArrange.objects.create(
            arrange_path="/arrange/testsip/data/metadata/manifest-md5.txt",
            original_path="originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/metadata/manifest-md5.txt",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
        )

        shared_dir = Path(tempfile.mkdtemp())
        staged_dir = shared_dir / "staging/testsip"
        (staged_dir / "logs").mkdir(parents=True)

        # Pre-create directory to produce name conflict.
        dst_dir = (
            shared_dir / "watchedDirectories/SIPCreation/SIPsUnderConstruction/testsip"
        )
        dst_dir.mkdir(parents=True)

        with self.settings(SHARED_DIRECTORY=str(shared_dir)):
            with mock.patch(
                "components.filesystem_ajax.views.storage_service.get_files_from_backlog",
                return_value=("12345", None),
            ):
                with mock.patch("shutil.move") as move_mock:
                    response = self.client.post(
                        reverse("filesystem_ajax:copy_from_arrange"),
                        data={
                            "filepath": b64encode(b"/arrange/testsip/").decode("utf8"),
                            "uuid": sip_uuid,
                        },
                        follow=True,
                    )

                    assert response.status_code == 201
                    assert response.json()["sip_uuid"] == sip_uuid

                    # Assert that "_1" suffix is appended.
                    move_mock.assert_called_once_with(
                        src=str(staged_dir) + os.sep, dst=str(dst_dir) + "_1"
                    )

                    assert (
                        models.SIP.objects.get(uuid=sip_uuid).currentpath
                        == "%sharedPath%/watchedDirectories/SIPCreation/SIPsUnderConstruction/testsip_1/"
                    )


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


@pytest.mark.parametrize(
    "local_path_exists, preview",
    [
        # Verify that transfer file is streamed directly from local
        # disk if available (e.g. on pipeline local filesystem).
        (True, True),  # Preview
        (True, False),  # Download
        # Verify that transfer file is requested from Storage Service
        # if not available on local disk (e.g. on Storage Service
        # local filesystem)
        (False, True),  # Preview
        (False, False),  # Download
    ],
)
def test_download_by_uuid(mocker, local_path_exists, preview):
    """Test that transfer file downloads work as expected."""
    TEST_UUID = "a29e7e86-eca9-43b6-b059-6f23a9802dc8"
    TEST_SS_URL = "http://test-url"
    TEST_BACKLOG_LOCATION_PATH = "/path/to/test/location"
    TEST_RELPATH = "transfer-{}/data/objects/bird.mp3".format(TEST_UUID)
    TEST_ABSPATH = os.path.join(TEST_BACKLOG_LOCATION_PATH, "originals", TEST_RELPATH)

    mock_get_file_info = mocker.patch("elasticSearchFunctions.get_transfer_file_info")
    mock_get_file_info.return_value = {
        "sipuuid": str(uuid.uuid4()),
        "relative_path": TEST_RELPATH,
    }
    mocker.patch("elasticSearchFunctions.get_client")

    mock_get_location = mocker.patch("storageService.get_first_location")
    mock_get_location.return_value = {"path": TEST_BACKLOG_LOCATION_PATH}

    mock_exists = mocker.patch("os.path.exists")
    mock_exists.return_value = local_path_exists

    mock_extract_file_url = mocker.patch("storageService.extract_file_url")
    mock_extract_file_url.return_value = TEST_SS_URL

    mock_send_file = mocker.patch("components.helpers.send_file")
    mock_stream_file_from_ss = mocker.patch(
        "components.helpers.stream_file_from_storage_service"
    )

    factory = RequestFactory()
    request = factory.get("/filesystem/{}/download/".format(TEST_UUID))

    views.download_by_uuid(request, TEST_UUID, preview_file=preview)

    if local_path_exists:
        download = not preview
        mock_send_file.assert_called_once_with(request, TEST_ABSPATH, download)
        mock_stream_file_from_ss.assert_not_called()
    else:
        mock_send_file.assert_not_called()
        mock_stream_file_from_ss.assert_called_once_with(
            TEST_SS_URL, "Storage service returned {}; check logs?", preview
        )
