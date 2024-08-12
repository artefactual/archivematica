import pathlib
import subprocess
from unittest import mock

from components import helpers
from django.conf import settings
from django.test import TestCase

TEST_USER_FIXTURE = (
    pathlib.Path(__file__).parent.parent.parent / "fixtures" / "test_user.json"
)


class TestUsage(TestCase):
    fixtures = [TEST_USER_FIXTURE]

    def setUp(self):
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_no_calculation(self):
        for calculate in [None, "False", "false", "no", "0", "random"]:
            if calculate is None:
                response = self.client.get("/administration/usage/")
            else:
                response = self.client.get(
                    "/administration/usage/?calculate=%s" % calculate
                )
            self.assertFalse(response.context["calculate_usage"])
            content = response.content.decode("utf8")
            self.assertIn('<a href="?calculate=true"', content)
            self.assertIn("Calculate disk usage", content)

    @mock.patch(
        "components.administration.views._usage_get_directory_used_bytes",
        return_value=5368709120,
    )
    @mock.patch(
        "components.administration.views._usage_check_directory_volume_size",
        return_value=10737418240,
    )
    @mock.patch(
        "components.administration.views._get_mount_point_path", return_value="/"
    )
    def test_calculation(self, mock_mount_path, mock_dir_size, mock_dir_used):
        for calculate in ["true", "True", "ON", "yes", "1"]:
            response = self.client.get(
                "/administration/usage/?calculate=%s" % calculate
            )
            self.assertTrue(response.context["calculate_usage"])

        mock_mount_path.assert_called_with(settings.SHARED_DIRECTORY)
        mock_dir_size.assert_called_with("/")
        self.assertEqual(mock_mount_path.call_count, 5)
        self.assertEqual(mock_dir_size.call_count, 5)
        self.assertEqual(mock_dir_used.call_count, 35)

    @mock.patch(
        "subprocess.check_output",
        side_effect=[
            subprocess.CalledProcessError(1, cmd="du", output=b"unknown error ocurred"),
            subprocess.CalledProcessError(
                1, cmd="du", output=b"14141414\t/var/archivematica/sharedDirectory/\n"
            ),
        ],
    )
    @mock.patch(
        "components.administration.views._usage_check_directory_volume_size",
        return_value=10737418240,
    )
    @mock.patch(
        "components.administration.views._get_shared_dirs",
        return_value={},
    )
    def test_calculation_with_disk_usage_errors(
        self, check_output, dir_size, shared_dirs
    ):
        """Test calculations of the usage view when the `du` call raises errors.

        We've mocked the helper that iterates disk usage on each
        shared directory so `du` is only called twice in this test
        case:

        - First with the mount point to which we raise an unknown
          error that results in a 0 bytes calculation
        - Then with the SHARED_DIRECTORY root to which we return
          parseable output that results in a valid integer
        """
        response = self.client.get("/administration/usage/?calculate=yes")
        assert response.context["root"] == {"path": "/", "size": 10737418240, "used": 0}
        assert response.context["shared"] == {
            "path": "/var/archivematica/sharedDirectory/",
            "used": 14141414,
        }
