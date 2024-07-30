import pathlib

import pytest
from client.job import Job
from django.utils import timezone
from main import models


@pytest.fixture(autouse=True)
def set_xml_catalog_files(monkeypatch):
    """Use local XML schemas for validation."""
    monkeypatch.setenv(
        "XML_CATALOG_FILES",
        str(
            pathlib.Path(__file__).parent.parent.parent
            / "src"
            / "MCPClient"
            / "lib"
            / "assets"
            / "catalog"
            / "catalog.xml"
        ),
    )


@pytest.fixture()
def mcp_job():
    return Job("stub", "stub", [])


@pytest.fixture
def job():
    return models.Job.objects.create(createdtime=timezone.now())
