import importlib.resources
from types import SimpleNamespace

import pytest

from archivematica.MCPServer.server import workflow


@pytest.fixture
def wf():
    """Load the installed workflow used by MCPServer unit tests."""
    resource = (
        importlib.resources.files("archivematica.MCPServer")
        / "assets"
        / "workflow.json"
    )
    with importlib.resources.as_file(resource) as workflow_path:
        with open(workflow_path) as fp:
            return workflow.load(fp)


@pytest.fixture
def retrieval_directories(tmp_path, settings):
    """Configure the shared staging and processing directories for retrieval."""
    shared = tmp_path / "shared"
    staging = shared / "tmp"
    processing = shared / "currentlyProcessing"
    staging.mkdir(parents=True)
    processing.mkdir()
    settings.SHARED_DIRECTORY = str(shared)
    settings.PROCESSING_DIRECTORY = f"{processing}/"

    return SimpleNamespace(
        shared=shared,
        staging=staging,
        processing=processing,
    )
