import os

import pytest

from server.processing_config import (
    _get_options_for_chain_choice,
    _populate_duplicates_chain_choice,
    get_processing_fields,
    processing_configuration_file_exists,
    processing_fields,
)
from server.workflow import load


ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir))), "lib", "assets"
)


@pytest.fixture
def _workflow():
    path = os.path.join(ASSETS_DIR, "workflow.json")
    with open(path) as fp:
        return load(fp)


def test_get_processing_fields(_workflow):
    fields = get_processing_fields(_workflow)
    assert len(fields) == len(processing_fields)


def test__populate_duplicates_chain_choice(_workflow):
    link_id = "cb8e5706-e73f-472f-ad9b-d1236af8095f"
    link = _workflow.get_link(link_id)
    config = processing_fields[link_id]
    config["options"] = _get_options_for_chain_choice(
        link, _workflow, config.get("ignored_choices")
    )
    _populate_duplicates_chain_choice(_workflow, link, config)
    duplicates = config["duplicates"]
    assert len(duplicates) > 0


def test_processing_configuration_file_exists_with_None():
    assert not processing_configuration_file_exists(None)


def test_processing_configuration_file_exists_with_existent_file(mocker):
    mocker.patch("os.path.isfile", return_value=True)
    assert processing_configuration_file_exists("defaultProcessingMCP.xml")


def test_processing_configuration_file_exists_with_nonexistent_file(mocker):
    mocker.patch("os.path.isfile", return_value=False)
    logger = mocker.patch("server.processing_config.logger")
    assert not processing_configuration_file_exists("bogus.xml")
    logger.debug.assert_called_once_with(
        "Processing configuration file for %s does not exist", "bogus.xml"
    )
