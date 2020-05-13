# -*- coding: utf-8 -*-
from __future__ import absolute_import

import mock

from django.conf import settings
from django.test import TestCase

from components import helpers


class TestUsage(TestCase):
    fixtures = ["test_user"]

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
        self.assertEqual(mock_dir_used.call_count, 45)
