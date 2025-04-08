import importlib.resources

import pytest

from archivematica.MCPServer.server import workflow
from archivematica.MCPServer.server.workflow_abilities import choice_is_available

CREATE_SIP_LINK_ID = "bb194013-597c-4e4a-8493-b36d190f8717"
SEND_TO_BACKLOG_CHAIN_ID = "7065d256-2f47-4b7d-baec-2c4699626121"


@pytest.fixture
def _workflow():
    with open(
        importlib.resources.files("archivematica.MCPServer")
        / "assets"
        / "workflow.json"
    ) as fp:
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
