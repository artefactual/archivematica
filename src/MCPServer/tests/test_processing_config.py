import os

import pytest

from processing_config import (
    _get_options_for_chain_choice,
    _populate_duplicates_chain_choice,
    get_processing_fields,
    processing_fields,
)
from workflow import load


ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(
        os.path.join(__file__, os.pardir))), "lib", "assets")


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
        link, _workflow, config.get("ignored_choices"))
    _populate_duplicates_chain_choice(_workflow, link, config)
    duplicates = config["duplicates"]
    assert len(duplicates) > 0
