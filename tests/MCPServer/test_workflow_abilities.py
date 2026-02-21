import importlib.resources

import pytest

from archivematica.MCPServer.server import workflow
from archivematica.MCPServer.server.workflow_abilities import choice_is_available

CREATE_SIP_LINK_ID = "bb194013-597c-4e4a-8493-b36d190f8717"
CREATE_SINGLE_SIP_CHAIN_ID = "61cfa825-120e-4b17-83e6-51a42b67d969"


@pytest.fixture
def _workflow():
    with open(
        importlib.resources.files("archivematica.MCPServer")
        / "assets"
        / "workflow.json"
    ) as fp:
        return workflow.load(fp)


def test_choice_is_available_default(_workflow):
    link = _workflow.get_link(CREATE_SIP_LINK_ID)
    chain = _workflow.get_chain(CREATE_SINGLE_SIP_CHAIN_ID)
    assert choice_is_available(link, chain) is True
