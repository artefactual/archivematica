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


@pytest.fixture()
def user():
    return models.User.objects.create(
        id=1,
        username="kmindelan",
        first_name="Keladry",
        last_name="Mindelan",
        is_active=True,
        is_superuser=True,
        is_staff=True,
        email="keladry@mindelan.com",
    )


@pytest.fixture
def transfer(user):
    result = models.Transfer.objects.create(
        currentlocation=r"%transferDirectory%",
        access_system_id="atom-description-id",
        diruuids=True,
    )
    result.update_active_agent(user.id)

    return result


@pytest.fixture
def sip():
    return models.SIP.objects.create(currentpath=r"%SIPDirectory%", diruuids=True)
