import importlib.resources

import pytest

from archivematica.MCPServer.server import workflow as workflow_module


@pytest.fixture
def wf():
    with open(
        importlib.resources.files("archivematica.MCPServer")
        / "assets"
        / "workflow.json"
    ) as fp:
        return workflow_module.load(fp)
