import importlib.resources

import pytest

from archivematica.MCPServer.server import workflow


@pytest.fixture
def wf():
    resource = (
        importlib.resources.files("archivematica.MCPServer")
        / "assets"
        / "workflow.json"
    )
    with importlib.resources.as_file(resource) as workflow_path:
        with open(workflow_path) as fp:
            return workflow.load(fp)
