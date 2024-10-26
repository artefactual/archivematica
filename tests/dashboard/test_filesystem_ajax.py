import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest import mock

import pytest
from archivematicaFunctions import b64encode_string
from components import helpers
from components.filesystem_ajax import views
from django.test import TestCase
from django.test.client import Client
from django.test.client import RequestFactory
from django.urls import reverse
from main import models

TEST_USER_FIXTURE = Path(__file__).parent / "fixtures" / "test_user.json"
SIP_ARRANGE_FIXTURE = Path(__file__).parent / "fixtures" / "sip_arrange.json"


class TestSIPArrange(TestCase):
    fixtures = [TEST_USER_FIXTURE, SIP_ARRANGE_FIXTURE]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_arrange_contents_data_no_path(self):
        # Call endpoint
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"), follow=True
        )
        # Verify
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert "directories" in response_dict
        assert b64encode_string("newsip") in response_dict["directories"]
        assert b64encode_string("toplevel") in response_dict["directories"]
        assert len(response_dict["directories"]) == 2
        assert "entries" in response_dict
        assert b64encode_string("newsip") in response_dict["entries"]
        assert b64encode_string("toplevel") in response_dict["entries"]
        assert len(response_dict["entries"]) == 2
        assert "properties" in response_dict
        assert b64encode_string("newsip") in response_dict["properties"]
        assert (
            response_dict["properties"][b64encode_string("newsip")]["display_string"]
            == "2 objects"
        )
        assert b64encode_string("toplevel") in response_dict["properties"]
        assert (
            response_dict["properties"][b64encode_string("toplevel")]["display_string"]
            == "1 object"
        )
        assert len(response_dict) == 3

    def test_arrange_contents_data_path(self):
        # Folder, without /
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode_string("/arrange/newsip/objects/")},
            follow=True,
        )
        # Verify
        assert response.status_code == 200
        response_dict = json.loads(response.content)
        assert "directories" in response_dict
        assert b64encode_string("evelyn_s_second_photo") in response_dict["directories"]
        assert len(response_dict["directories"]) == 1
        assert "entries" in response_dict
        assert b64encode_string("evelyn_s_photo.jpg") in response_dict["entries"]
        assert b64encode_string("evelyn_s_second_photo") in response_dict["entries"]
        assert len(response_dict["entries"]) == 2
        assert "properties" in response_dict
        assert b64encode_string("evelyn_s_second_photo") in response_dict["properties"]
        assert (
            response_dict["properties"][b64encode_string("evelyn_s_second_photo")][
                "display_string"
            ]
            == "1 object"
        )
        assert len(response_dict) == 3

    def test_arrange_contents_404(self):
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode_string("/arrange/nosuchpath/")},
            follow=True,
        )
        assert response.status_code == 404
        response_dict = json.loads(response.content.decode("utf8"))
        assert response_dict["success"] is False

    def test_arrange_contents_empty_base_dir(self):
        models.SIPArrange.objects.all().delete()
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode_string("/arrange/")},
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
            {"path": b64encode_string("/arrange")},
            follow=True,
        )
        assert (
            b64encode_string("newsip")
            in json.loads(response.content.decode("utf8"))["directories"]
        )
        # Delete files
        response = self.client.post(
            reverse("filesystem_ajax:delete_arrange"),
            data={"filepath": b64encode_string("/arrange/newsip/")},
            follow=True,
        )
        assert response.status_code == 200
        assert json.loads(response.content.decode("utf8")) == {
            "message": "Delete successful."
        }
        # Check deleted
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode_string("/arrange")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert b64encode_string("toplevel") in response_dict["directories"]
        assert len(response_dict["directories"]) == 1
        assert b64encode_string("toplevel") in response_dict["entries"]
        assert len(response_dict["entries"]) == 1

    def test_create_arranged_directories(self):
        # Verify does not exist already
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode_string("/arrange")},
            follow=True,
        )
        assert (
            b64encode_string("new_dir")
            not in json.loads(response.content.decode("utf8"))["directories"]
        )
        assert (
            b64encode_string("new_dir")
            not in json.loads(response.content.decode("utf8"))["entries"]
        )
        # Create directory
        response = self.client.post(
            reverse("filesystem_ajax:create_directory_within_arrange"),
            data={"paths[]": b64encode_string("/arrange/new_dir")},
            follow=True,
        )
        assert response.status_code == 201
        assert json.loads(response.content.decode("utf8")) == {
            "message": "Creation successful."
        }
        # Check created
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode_string("/arrange")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert b64encode_string("new_dir") in response_dict["directories"]
        assert b64encode_string("newsip") in response_dict["directories"]
        assert b64encode_string("toplevel") in response_dict["directories"]
        assert len(response_dict["directories"]) == 3
        assert b64encode_string("new_dir") in response_dict["entries"]
        assert b64encode_string("newsip") in response_dict["entries"]
        assert b64encode_string("toplevel") in response_dict["entries"]
        assert len(response_dict["entries"]) == 3

    def test_move_within_arrange(self):
        # Move directory
        response = self.client.post(
            reverse("filesystem_ajax:copy_to_arrange"),
            data={
                "filepath": b64encode_string("/arrange/newsip/"),
                "destination": b64encode_string("/arrange/toplevel/"),
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
            {"path": b64encode_string("/arrange")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert b64encode_string("toplevel") in response_dict["directories"]
        assert b64encode_string("newsip") not in response_dict["directories"]
        assert len(response_dict["directories"]) == 1
        assert b64encode_string("toplevel") in response_dict["entries"]
        assert b64encode_string("newsip") not in response_dict["entries"]
        assert len(response_dict["entries"]) == 1

        # Check now in subdirectory
        response = self.client.get(
            reverse("filesystem_ajax:contents_arrange"),
            {"path": b64encode_string("/arrange/toplevel")},
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert b64encode_string("subsip") in response_dict["directories"]
        assert b64encode_string("newsip") in response_dict["directories"]
        assert len(response_dict["directories"]) == 2
        assert b64encode_string("subsip") in response_dict["entries"]
        assert b64encode_string("newsip") in response_dict["entries"]
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
                        "filepath": b64encode_string("/arrange/newsip/"),
                        "uuid": sip_uuid,
                    },
                    follow=True,
                )

                assert response.status_code == 201
                response_dict = json.loads(response.content.decode("utf8"))
                assert response_dict["message"] == "SIP created."
                assert response_dict["sip_uuid"] == sip_uuid

                create_arranged_sip_mock.assert_called_once_with(
                    "staging/newsip/",
                    [
                        {
                            "source": "originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/objects/evelyn_s_photo.jpg",
                            "destination": "staging/newsip/objects/evelyn_s_photo.jpg",
                            "uuid": "4fa8f739-b633-4c0f-8833-d108a4f4e88d",
                        },
                        {
                            "source": "originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/logs/.",
                            "destination": "tmp/transfer-a29e7e86-eca9-43b6-b059-6f23a9802dc8/logs/.",
                        },
                        {
                            "source": "originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/metadata/.",
                            "destination": "tmp/transfer-a29e7e86-eca9-43b6-b059-6f23a9802dc8/metadata/.",
                        },
                        {
                            "source": "originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/objects/evelyn_s_second_photo/evelyn_s_second_photo.jpg",
                            "destination": "staging/newsip/objects/evelyn_s_second_photo/evelyn_s_second_photo.jpg",
                            "uuid": "7f889d5d-7849-490e-a8e6-ccb9595445d7",
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
        sip_uuid = "a29e7e86-eca9-43b6-b059-6f23a9802dc8"
        models.SIP.objects.create(uuid=sip_uuid)
        models.SIPArrange.objects.all().delete()
        models.SIPArrange.objects.create(arrange_path=b"/arrange/testsip/")
        models.SIPArrange.objects.create(arrange_path=b"/arrange/testsip/data/")
        models.SIPArrange.objects.create(arrange_path=b"/arrange/testsip/data/objects/")
        models.SIPArrange.objects.create(
            arrange_path=b"/arrange/testsip/data/objects/MARBLES.TGA",
            original_path=b"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/objects/MARBLES.TGA",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
            file_uuid="fe077212-094f-4df9-ac51-1bc35be0d95e",
        )
        models.SIPArrange.objects.create(
            arrange_path=b"/arrange/testsip/data/logs/BagIt/bagit.txt",
            original_path=b"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/logs/BagIt/bagit.txt",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
            file_uuid="0cf82e9a-0a54-45e8-bdff-700c2fed513c",
        )
        models.SIPArrange.objects.create(
            arrange_path=b"/arrange/testsip/data/metadata/manifest-md5.txt",
            original_path=b"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/metadata/manifest-md5.txt",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
            file_uuid="33c7b9a5-6031-4c89-847d-708fc285b1c1",
        )

        with mock.patch(
            "components.filesystem_ajax.views.storage_service.get_files_from_backlog",
            return_value=("369cdbfc-69b1-4003-8f8c-31a537d03e85", None),
        ):
            with mock.patch(
                "components.filesystem_ajax.views._create_arranged_sip",
                return_value=None,
            ) as create_arranged_sip_mock:
                response = self.client.post(
                    reverse("filesystem_ajax:copy_from_arrange"),
                    data={
                        "filepath": b64encode_string("/arrange/testsip/"),
                        "uuid": sip_uuid,
                    },
                    follow=True,
                )

                assert response.status_code == 201
                response_dict = json.loads(response.content.decode("utf8"))
                assert response_dict["message"] == "SIP created."
                assert response_dict["sip_uuid"] == sip_uuid

                create_arranged_sip_mock.assert_called_once_with(
                    "staging/testsip/",
                    [
                        {
                            "source": "originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/objects/MARBLES.TGA",
                            "destination": "staging/testsip/data/objects/MARBLES.TGA",
                            "uuid": "fe077212-094f-4df9-ac51-1bc35be0d95e",
                        },
                        {
                            "source": "originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/logs/.",
                            "destination": "tmp/transfer-a29e7e86-eca9-43b6-b059-6f23a9802dc8/logs/.",
                        },
                        {
                            "source": "originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/metadata/.",
                            "destination": "tmp/transfer-a29e7e86-eca9-43b6-b059-6f23a9802dc8/metadata/.",
                        },
                        {
                            "source": "originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/logs/BagIt/bagit.txt",
                            "destination": "staging/testsip/data/logs/BagIt/bagit.txt",
                            "uuid": "0cf82e9a-0a54-45e8-bdff-700c2fed513c",
                        },
                        {
                            "source": "originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/metadata/manifest-md5.txt",
                            "destination": "staging/testsip/data/metadata/manifest-md5.txt",
                            "uuid": "33c7b9a5-6031-4c89-847d-708fc285b1c1",
                        },
                    ],
                    sip_uuid,
                )

    def test_copy_from_arrange_to_completed_rejects_invalid_sip_uuid(self):
        response = self.client.post(
            reverse("filesystem_ajax:copy_from_arrange"),
            data={
                "filepath": b64encode_string("/arrange/testsip/"),
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
                "filepath": b64encode_string("/path/testsip/"),
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
                "filepath": b64encode_string("/arrange/testsip"),
                "uuid": "607df760-a0be-4fef-875a-74ea00c61bf9",
            },
            follow=True,
        )

        assert response.status_code == 400
        assert response.json()["message"] == "/arrange/testsip is not a directory"

    def test_copy_from_arrange_to_completed_rejects_empty_arrangements(self):
        models.SIP.objects.create(uuid="607df760-a0be-4fef-875a-74ea00c61bf9")
        models.SIPArrange.objects.all().delete()
        models.SIPArrange.objects.create(arrange_path=b"/arrange/testsip/")

        response = self.client.post(
            reverse("filesystem_ajax:copy_from_arrange"),
            data={
                "filepath": b64encode_string("/arrange/testsip/"),
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
        sip_uuid = "a29e7e86-eca9-43b6-b059-6f23a9802dc8"
        models.SIPArrange.objects.all().delete()
        models.SIPArrange.objects.create(arrange_path=b"/arrange/testsip/")
        models.SIPArrange.objects.create(arrange_path=b"/arrange/testsip/data/")
        models.SIPArrange.objects.create(arrange_path=b"/arrange/testsip/data/objects/")
        models.SIPArrange.objects.create(
            arrange_path=b"/arrange/testsip/data/objects/MARBLES.TGA",
            original_path=b"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/objects/MARBLES.TGA",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
        )
        models.SIPArrange.objects.create(
            arrange_path=b"/arrange/testsip/data/logs/BagIt/bagit.txt",
            original_path=b"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/logs/BagIt/bagit.txt",
            transfer_uuid="a29e7e86-eca9-43b6-b059-6f23a9802dc8",
        )
        models.SIPArrange.objects.create(
            arrange_path=b"/arrange/testsip/data/metadata/manifest-md5.txt",
            original_path=b"originals/newsip-a29e7e86-eca9-43b6-b059-6f23a9802dc8/data/metadata/manifest-md5.txt",
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
                            "filepath": b64encode_string("/arrange/testsip/"),
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
@pytest.mark.parametrize(
    "set_partial_reingest_flag, expected_metadata_dir",
    [
        (False, "metadata"),
        (True, os.path.join("data", "objects", "metadata")),
    ],
    ids=["regular_sip", "partial_reingest"],
)
@mock.patch(
    "components.filesystem_ajax.views._copy_from_transfer_sources",
    return_value=(None, ""),
)
def test_copy_metadata_files(
    _copy_from_transfer_sources_mock,
    rf,
    set_partial_reingest_flag,
    expected_metadata_dir,
):
    # Create a SIP
    sip_uuid = str(uuid.uuid4())
    sip = models.SIP.objects.create(
        uuid=sip_uuid,
        currentpath=f"%sharedPath%more/path/metadataReminder/mysip-{sip_uuid}/",
    )
    if set_partial_reingest_flag:
        sip.set_partial_reingest()

    # Call the view with a mocked request
    request = rf.post(
        reverse("filesystem_ajax:copy_metadata_files"),
        {
            "sip_uuid": sip_uuid,
            "source_paths[]": [b64encode_string("locationuuid:/some/path")],
        },
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
        f"more/path/metadataReminder/mysip-{sip_uuid}/{expected_metadata_dir}",
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
@mock.patch("components.helpers.stream_file_from_storage_service")
@mock.patch("components.helpers.send_file")
@mock.patch("storageService.extract_file_url")
@mock.patch("os.path.exists")
@mock.patch("storageService.get_first_location")
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.get_transfer_file_info")
def test_download_by_uuid(
    mock_get_file_info,
    get_client,
    mock_get_location,
    mock_exists,
    mock_extract_file_url,
    mock_send_file,
    mock_stream_file_from_ss,
    local_path_exists,
    preview,
):
    """Test that transfer file downloads work as expected."""
    TEST_UUID = "a29e7e86-eca9-43b6-b059-6f23a9802dc8"
    TEST_SS_URL = "http://test-url"
    TEST_BACKLOG_LOCATION_PATH = "/path/to/test/location"
    TEST_RELPATH = f"transfer-{TEST_UUID}/data/objects/bird.mp3"
    TEST_ABSPATH = os.path.join(TEST_BACKLOG_LOCATION_PATH, "originals", TEST_RELPATH)

    mock_get_file_info.return_value = {
        "sipuuid": str(uuid.uuid4()),
        "relative_path": TEST_RELPATH,
    }

    mock_get_location.return_value = {"path": TEST_BACKLOG_LOCATION_PATH}

    mock_exists.return_value = local_path_exists

    mock_extract_file_url.return_value = TEST_SS_URL

    factory = RequestFactory()
    request = factory.get(f"/filesystem/{TEST_UUID}/download/")

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


def test_contents_sorting(db, tmp_path, admin_client):
    (tmp_path / "1").mkdir()
    (tmp_path / "e").mkdir()
    (tmp_path / "a").mkdir()
    (tmp_path / "0").mkdir()
    helpers.set_setting("dashboard_uuid", "test-uuid")

    response = admin_client.get(
        reverse("filesystem_ajax:contents"), {"path": str(tmp_path)}
    )
    content = json.loads(response.content.decode("utf8"))

    assert [child["name"] for child in content["children"]] == [
        b64encode_string("0"),
        b64encode_string("1"),
        b64encode_string("a"),
        b64encode_string("e"),
    ]


@pytest.mark.django_db
@mock.patch(
    "storageService.get_first_location",
    return_value={"uuid": "355d110f-b641-4b6b-b1c0-8426e63951e5"},
)
@mock.patch(
    "storageService.get_file_metadata",
    side_effect=[
        [
            {
                "fileuuid": "0b603cee-1f8a-4842-996a-e02a0307ccf7",
                "sipuuid": "99c87143-6f74-4398-84e0-14a8ca4bd05a",
            }
        ],
        [
            {
                "fileuuid": "03a33ef5-8714-46cc-aefe-7283186341ca",
                "sipuuid": "99c87143-6f74-4398-84e0-14a8ca4bd05a",
            }
        ],
    ],
)
@mock.patch(
    "storageService.browse_location",
    return_value={
        "directories": [],
        "entries": ["file1.txt", "file2.txt"],
        "properties": {
            "file1.txt": {"size": 8},
            "file2.txt": {"size": 6},
        },
    },
)
def test_copy_within_arrange(
    browse_location, get_file_metadata, get_first_location, admin_client
):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Expected attributes for the new SIPArrange instances.
    attrs = ("original_path", "arrange_path", "file_uuid", "transfer_uuid")
    expected = {
        (
            b"originals/objects/file1.txt",
            b"/arrange/file1.txt",
            uuid.UUID("0b603cee-1f8a-4842-996a-e02a0307ccf7"),
            uuid.UUID("99c87143-6f74-4398-84e0-14a8ca4bd05a"),
        ),
        (
            b"originals/objects/file2.txt",
            b"/arrange/file2.txt",
            uuid.UUID("03a33ef5-8714-46cc-aefe-7283186341ca"),
            uuid.UUID("99c87143-6f74-4398-84e0-14a8ca4bd05a"),
        ),
    }

    # Verify there are no SIPArrange instances.
    assert models.SIPArrange.objects.count() == 0

    # Copy directory
    response = admin_client.post(
        reverse("filesystem_ajax:copy_to_arrange"),
        data={
            "filepath": b64encode_string("/originals/objects/"),
            "destination": b64encode_string("/arrange/"),
        },
        follow=True,
    )
    assert response.status_code == 201
    assert json.loads(response.content.decode("utf8")) == {
        "message": "Files added to the SIP."
    }

    # Verify SIPArrange instances were created as expected.
    assert models.SIPArrange.objects.count() == 2
    assert set(models.SIPArrange.objects.values_list(*attrs)) == expected
