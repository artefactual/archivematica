import importlib.resources
import pathlib
from types import SimpleNamespace

import pytest
import pytest_django

from archivematica.dashboard.main import models
from archivematica.MCPServer.server import workflow
from tests.factories import TransferFactory


@pytest.fixture(scope="session")
def wf() -> workflow.Workflow:
    """The installed workflow, loaded once per session because its decoding
    validates the whole document and nothing modifies it afterwards.
    """
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


@pytest.fixture
def processing_transfer(make_transfer: TransferFactory) -> models.Transfer:
    """A transfer in processing status at its retrieval staging location, before
    its first job runs.
    """
    return make_transfer(
        currentlocation="%sharedPath%tmp/tmp123/TransferName",
        status=models.PACKAGE_STATUS_PROCESSING,
    )
