import os
import pathlib
from unittest import mock

import pytest
from django.http import HttpResponse
from django.test import Client

from archivematica.archivematicaCommon.processing import AUTOMATED_PROCESSING_CONFIG
from archivematica.archivematicaCommon.processing import DEFAULT_PROCESSING_CONFIG
from archivematica.dashboard.components import helpers

pytestmark = pytest.mark.usefixtures("dashboard_uuid")


@mock.patch(
    "archivematica.dashboard.components.administration.views_processing.os.path.isfile",
    return_value=False,
)
def test_download_404(is_file: mock.MagicMock, admin_client: Client) -> None:
    response = admin_client.get("/administration/processing/download/default/")

    assert response.status_code == 404


@mock.patch(
    "archivematica.dashboard.components.helpers.send_file",
    return_value=HttpResponse("<!DOCTYPE _[<!ELEMENT _ EMPTY>]><_/>"),
)
@mock.patch(
    "archivematica.dashboard.components.administration.views_processing.os.path.isfile",
    return_value=True,
)
def test_download_ok(
    is_file: mock.MagicMock,
    send_file: mock.MagicMock,
    admin_client: Client,
) -> None:
    response = admin_client.get("/administration/processing/download/default/")

    assert response.content.decode("utf8") == "<!DOCTYPE _[<!ELEMENT _ EMPTY>]><_/>"


@mock.patch(
    "archivematica.dashboard.components.administration.forms.MCPClient.get_processing_config_fields",
    return_value={},
)
def test_edit_new_config(
    get_processing_config_fields: mock.MagicMock,
    admin_client: Client,
) -> None:
    response = admin_client.get("/administration/processing/add/")

    assert response.status_code == 200
    assert "name" not in response.context["form"].initial


@mock.patch(
    "archivematica.dashboard.components.administration.forms.MCPClient.get_processing_config_fields",
    return_value={},
)
@mock.patch(
    "archivematica.dashboard.components.administration.forms.ProcessingConfigurationForm.load_config",
    side_effect=OSError(),
)
def test_edit_not_found_config(
    load_config: mock.MagicMock,
    get_processing_config_fields: mock.MagicMock,
    admin_client: Client,
) -> None:
    response = admin_client.get("/administration/processing/edit/not_found_config/")

    assert response.status_code == 404
    load_config.assert_called_once_with("not_found_config")


@mock.patch(
    "archivematica.dashboard.components.administration.forms.MCPClient.get_processing_config_fields",
    return_value={},
)
@mock.patch(
    "archivematica.dashboard.components.administration.forms.ProcessingConfigurationForm.load_config"
)
def test_edit_found_config(
    load_config: mock.MagicMock,
    get_processing_config_fields: mock.MagicMock,
    admin_client: Client,
) -> None:
    response = admin_client.get("/administration/processing/edit/found_config/")

    assert response.status_code == 200
    load_config.assert_called_once_with("found_config")


@mock.patch(
    "archivematica.dashboard.components.administration.forms.MCPClient.get_processing_config_fields",
    return_value={},
)
@mock.patch(
    "archivematica.dashboard.components.administration.forms.ProcessingConfigurationForm.load_config"
)
def test_name_field_is_required(
    load_config: mock.MagicMock,
    get_processing_config_fields: mock.MagicMock,
    admin_client: Client,
) -> None:
    response = admin_client.post("/administration/processing/add/", data={1: 2})

    assert response.status_code == 200
    assert response.context["form"].errors["name"] == ["This field is required."]
    assert "This field is required." in response.content.decode("utf8")


@mock.patch(
    "archivematica.dashboard.components.administration.forms.MCPClient.get_processing_config_fields",
    return_value={},
)
def test_name_field_is_validated(
    get_processing_config_fields: mock.MagicMock,
    admin_client: Client,
) -> None:
    response = admin_client.post(
        "/administration/processing/add/", data={"name": "foo$bar"}
    )

    assert response.status_code == 200
    assert response.context["form"].errors["name"] == [
        "The name can contain only alphanumeric characters and the underscore character (_)."
    ]
    assert (
        "The name can contain only alphanumeric characters and the underscore character (_)."
        in response.content.decode("utf8")
    )


def test_reset_default_processing_config(
    admin_client: Client, processing_configurations_path: pathlib.Path
) -> None:
    response = admin_client.get("/administration/processing/reset/default/")

    assert response.status_code == 302
    processing_config = os.path.join(
        helpers.processing_config_path(), "defaultProcessingMCP.xml"
    )
    with open(processing_config) as actual_file:
        assert actual_file.read() == DEFAULT_PROCESSING_CONFIG


def test_reset_automated_processing_config(
    admin_client: Client, processing_configurations_path: pathlib.Path
) -> None:
    response = admin_client.get("/administration/processing/reset/automated/")

    assert response.status_code == 302
    processing_config = os.path.join(
        helpers.processing_config_path(), "automatedProcessingMCP.xml"
    )
    with open(processing_config) as actual_file:
        assert actual_file.read() == AUTOMATED_PROCESSING_CONFIG
