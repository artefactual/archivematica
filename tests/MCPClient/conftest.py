import pathlib

import pytest
from client.job import Job
from django.utils import timezone
from fpr import models as fprmodels
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
def job():
    return models.Job.objects.create(createdtime=timezone.now())


@pytest.fixture
def task(job):
    return models.Task.objects.create(job=job, createdtime=timezone.now())


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


@pytest.fixture
def format_group():
    return fprmodels.FormatGroup.objects.create()


@pytest.fixture
def format(format_group):
    return fprmodels.Format.objects.create(group=format_group)


@pytest.fixture
def format_version(format):
    return fprmodels.FormatVersion.objects.create(format=format)


@pytest.fixture
def fptool():
    return fprmodels.FPTool.objects.create()


@pytest.fixture
def fpcommand(fptool, sip_file):
    return fprmodels.FPCommand.objects.create(
        tool=fptool, output_location=sip_file.currentlocation.decode()
    )


@pytest.fixture
def fprule(fpcommand, format_version):
    return fprmodels.FPRule.objects.create(command=fpcommand, format=format_version)


@pytest.fixture()
def fprule_characterization(fprule):
    fprule.purpose = fprmodels.FPRule.CHARACTERIZATION
    fprule.save()

    return fprule


@pytest.fixture
def fprule_extraction(fprule):
    fprule.purpose = fprmodels.FPRule.EXTRACTION
    fprule.save()

    return fprule


@pytest.fixture
def fprule_validation(fprule):
    fprule.purpose = fprmodels.FPRule.VALIDATION
    fprule.save()

    return fprule


@pytest.fixture
def fprule_transcription(fprule):
    fprule.purpose = fprmodels.FPRule.TRANSCRIPTION
    fprule.save()

    return fprule


@pytest.fixture
def fprule_preservation(fprule):
    fprule.purpose = fprmodels.FPRule.PRESERVATION
    fprule.save()

    return fprule


@pytest.fixture
def transfer_file(transfer):
    location = b"%transferDirectory%objects/file.mp3"
    return models.File.objects.create(
        transfer=transfer,
        filegrpuse="original",
        originallocation=location,
        currentlocation=location,
    )


@pytest.fixture
def sip_file(sip, transfer):
    location = "objects/file.mp3"
    return models.File.objects.create(
        transfer=transfer,
        sip=sip,
        filegrpuse="original",
        originallocation=f"%transferDirectory%{location}".encode(),
        currentlocation=f"%SIPDirectory%{location}".encode(),
    )


@pytest.fixture
def preservation_file(sip, transfer):
    location = b"%SIPDirectory%objects/file.wav"
    return models.File.objects.create(
        transfer=transfer,
        sip=sip,
        filegrpuse="preservation",
        originallocation=location,
        currentlocation=location,
    )


@pytest.fixture
def file_format_version(sip_file, format_version):
    return models.FileFormatVersion.objects.create(
        file_uuid=sip_file, format_version=format_version
    )


@pytest.fixture
def shared_directory_path(tmp_path):
    result = tmp_path / "sharedDirectory"
    result.mkdir()

    for directory in ["currentlyProcessing", "tmp"]:
        (result / directory).mkdir()

    return result


@pytest.fixture
def transfer_directory_path(tmp_path):
    result = tmp_path / "transfer"
    result.mkdir()

    return result


@pytest.fixture
def sip_directory_path(tmp_path):
    result = tmp_path / "sip"
    result.mkdir()

    return result


@pytest.fixture
def settings(settings, shared_directory_path):
    settings.SHARED_DIRECTORY = f"{shared_directory_path}/"
    settings.PROCESSING_DIRECTORY = f'{shared_directory_path / "currentlyProcessing"}/'

    return settings
