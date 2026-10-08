import importlib.resources
import pathlib
from types import SimpleNamespace

import pytest
import pytest_django

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
def retrieval_directories(
    settings: pytest_django.Settings, shared_directory_path: pathlib.Path
) -> SimpleNamespace:
    """The shared, staging and processing directories of transfer retrieval."""
    return SimpleNamespace(
        shared=shared_directory_path,
        staging=shared_directory_path / "tmp",
        processing=shared_directory_path / "currentlyProcessing",
    )
