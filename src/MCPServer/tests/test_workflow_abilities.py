import os

import pytest

from server import workflow
from server.workflow_abilities import choice_is_available


ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir))), "lib", "assets"
)


CREATE_SIP_LINK_ID = "bb194013-597c-4e4a-8493-b36d190f8717"
SEND_TO_BACKLOG_CHAIN_ID = "7065d256-2f47-4b7d-baec-2c4699626121"


@pytest.fixture
def _workflow():
    path = os.path.join(ASSETS_DIR, "workflow.json")
    with open(path) as fp:
        return workflow.load(fp)


def test_choice_is_available__enabled(settings, _workflow):
    """<Send to backlog> is going to be shown to the user."""
    settings.SEARCH_ENABLED = "transfers, aips"
    link = _workflow.get_link(CREATE_SIP_LINK_ID)
    chain = _workflow.get_chain(SEND_TO_BACKLOG_CHAIN_ID)
    assert choice_is_available(link, chain) is True


def test_choice_is_available__disabled(settings, _workflow):
    """<Send to backlog> is not going to be shown to the user."""
    settings.SEARCH_ENABLED = "aips"
    link = _workflow.get_link(CREATE_SIP_LINK_ID)
    chain = _workflow.get_chain(SEND_TO_BACKLOG_CHAIN_ID)
    assert choice_is_available(link, chain) is False
