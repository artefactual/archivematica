# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import tempfile
import shutil

from django.http import HttpResponse
from django.test import TestCase

from components import helpers
from processing import DEFAULT_PROCESSING_CONFIG, AUTOMATED_PROCESSING_CONFIG

import mock
import pytest


@pytest.fixture
def shared_directory(settings):
    shared_dir = tempfile.mkdtemp()
    settings.SHARED_DIRECTORY = str(shared_dir)
    os.makedirs(
        os.path.join(shared_dir, "sharedMicroServiceTasksConfigs/processingMCPConfigs/")
    )
    yield shared_dir
    if tempfile._exists(shared_dir):
        shutil.rmtree(shared_dir)


class TestProcessingConfig(TestCase):
    fixtures = ["test_user"]

    def setUp(self):
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    @mock.patch("components.administration.views_processing.os.path.isfile")
    def test_download_404(self, mock_is_file):
        mock_is_file.return_value = False
        response = self.client.get("/administration/processing/download/default/")
        self.assertEqual(response.status_code, 404)

    @mock.patch("components.helpers.send_file")
    @mock.patch("components.administration.views_processing.os.path.isfile")
    def test_download_ok(self, mock_is_file, mock_send_file):
        mock_is_file.return_value = True
        mock_send_file.return_value = HttpResponse(
            "<!DOCTYPE _[<!ELEMENT _ EMPTY>]><_/>"
        )
        response = self.client.get("/administration/processing/download/default/")
        self.assertEqual(
            response.content.decode("utf8"), "<!DOCTYPE _[<!ELEMENT _ EMPTY>]><_/>"
        )

    @mock.patch(
        "components.administration.forms.MCPClient.get_processing_config_fields",
        return_value={},
    )
    def test_edit_new_config(self, mock_conf_fields):
        response = self.client.get("/administration/processing/add/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("name", response.context["form"].initial)

    @mock.patch(
        "components.administration.forms.MCPClient.get_processing_config_fields",
        return_value={},
    )
    @mock.patch(
        "components.administration.forms.ProcessingConfigurationForm.load_config",
        side_effect=IOError(),
    )
    def test_edit_not_found_config(self, mock_load_config, mock_conf_fields):
        response = self.client.get("/administration/processing/edit/not_found_config/")
        self.assertEqual(response.status_code, 404)
        mock_load_config.assert_called_once_with("not_found_config")

    @mock.patch(
        "components.administration.forms.MCPClient.get_processing_config_fields",
        return_value={},
    )
    @mock.patch(
        "components.administration.forms.ProcessingConfigurationForm.load_config"
    )
    def test_edit_found_config(self, mock_load_config, mock_conf_fields):
        response = self.client.get("/administration/processing/edit/found_config/")
        self.assertEqual(response.status_code, 200)
        mock_load_config.assert_called_once_with("found_config")

    @mock.patch(
        "components.administration.forms.MCPClient.get_processing_config_fields",
        return_value={},
    )
    @mock.patch(
        "components.administration.forms.ProcessingConfigurationForm.load_config"
    )
    def test_name_field_is_required(self, mock_load_config, mock_conf_fields):
        response = self.client.post("/administration/processing/add/", data={1: 2})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    @mock.patch(
        "components.administration.forms.MCPClient.get_processing_config_fields",
        return_value={},
    )
    def test_name_field_is_validated(self, mock_conf_fields):
        response = self.client.post(
            "/administration/processing/add/", data={"name": "foo$bar"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "The name can contain only alphanumeric characters and the underscore character (_).",
        )

    @pytest.mark.usefixtures("shared_directory")
    def test_reset_default_processing_config(self):
        response = self.client.get("/administration/processing/reset/default/")
        self.assertEqual(response.status_code, 302)
        processing_config = os.path.join(
            helpers.processing_config_path(), "defaultProcessingMCP.xml"
        )
        with open(processing_config) as actual_file:
            assert actual_file.read() == DEFAULT_PROCESSING_CONFIG

    @pytest.mark.usefixtures("shared_directory")
    def test_reset_automated_processing_config(self):
        response = self.client.get("/administration/processing/reset/automated/")
        self.assertEqual(response.status_code, 302)
        processing_config = os.path.join(
            helpers.processing_config_path(), "automatedProcessingMCP.xml"
        )
        with open(processing_config) as actual_file:
            assert actual_file.read() == AUTOMATED_PROCESSING_CONFIG
