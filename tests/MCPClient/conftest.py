import pathlib

import pytest
import pytest_django
from client.job import Job
from django.utils import timezone
from fpr import models as fprmodels
from main import models


@pytest.fixture(autouse=True)
def set_xml_catalog_files(monkeypatch: pytest.MonkeyPatch) -> None:
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
def mcp_job() -> Job:
    return Job("stub", "stub", [])


@pytest.fixture()
def user() -> models.User:
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
def job() -> models.Job:
    return models.Job.objects.create(createdtime=timezone.now())


@pytest.fixture
def task(job: models.Job) -> models.Task:
    return models.Task.objects.create(job=job, createdtime=timezone.now())


@pytest.fixture
def transfer(user: models.User) -> models.Transfer:
    result = models.Transfer.objects.create(
        currentlocation=r"%transferDirectory%",
        access_system_id="atom-description-id",
        diruuids=True,
    )
    result.update_active_agent(user.id)

    return result


@pytest.fixture
def sip() -> models.SIP:
    return models.SIP.objects.create(currentpath=r"%SIPDirectory%", diruuids=True)


@pytest.fixture
def format_group() -> fprmodels.FormatGroup:
    return fprmodels.FormatGroup.objects.create()


@pytest.fixture
def format(format_group: fprmodels.FormatGroup) -> fprmodels.Format:
    return fprmodels.Format.objects.create(group=format_group)


@pytest.fixture
def format_version(format: fprmodels.Format) -> fprmodels.FormatVersion:
    return fprmodels.FormatVersion.objects.create(format=format)


@pytest.fixture
def fptool() -> fprmodels.FPTool:
    return fprmodels.FPTool.objects.create()


@pytest.fixture
def idtool() -> fprmodels.IDTool:
    return fprmodels.IDTool.objects.create()


@pytest.fixture
def fpcommand(fptool: fprmodels.FPTool) -> fprmodels.FPCommand:
    return fprmodels.FPCommand.objects.create(tool=fptool)


@pytest.fixture
def idcommand(idtool: fprmodels.IDTool) -> fprmodels.IDCommand:
    return fprmodels.IDCommand.objects.create(tool=idtool, config="PUID")


@pytest.fixture
def fprule(
    fpcommand: fprmodels.FPCommand, format_version: fprmodels.FormatVersion
) -> fprmodels.FPRule:
    return fprmodels.FPRule.objects.create(command=fpcommand, format=format_version)


@pytest.fixture
def idrule(
    idcommand: fprmodels.IDCommand, format_version: fprmodels.FormatVersion
) -> fprmodels.IDRule:
    return fprmodels.IDRule.objects.create(command=idcommand, format=format_version)


@pytest.fixture()
def fprule_characterization(fprule: fprmodels.FPRule) -> fprmodels.FPRule:
    fprule.purpose = fprmodels.FPRule.CHARACTERIZATION
    fprule.save()

    return fprule


@pytest.fixture
def fprule_extraction(fprule: fprmodels.FPRule) -> fprmodels.FPRule:
    fprule.purpose = fprmodels.FPRule.EXTRACTION
    fprule.save()

    return fprule


@pytest.fixture
def fprule_validation(fprule: fprmodels.FPRule) -> fprmodels.FPRule:
    fprule.purpose = fprmodels.FPRule.VALIDATION
    fprule.save()

    return fprule


@pytest.fixture
def fprule_transcription(fprule: fprmodels.FPRule) -> fprmodels.FPRule:
    fprule.purpose = fprmodels.FPRule.TRANSCRIPTION
    fprule.save()

    return fprule


@pytest.fixture
def fprule_preservation(fprule: fprmodels.FPRule) -> fprmodels.FPRule:
    fprule.purpose = fprmodels.FPRule.PRESERVATION
    fprule.save()

    return fprule


@pytest.fixture
def fprule_policy_check(fprule: fprmodels.FPRule) -> fprmodels.FPRule:
    fprule.purpose = fprmodels.FPRule.POLICY
    fprule.save()

    return fprule


@pytest.fixture
def fprule_thumbnail(fprule: fprmodels.FPRule) -> fprmodels.FPRule:
    fprule.purpose = fprmodels.FPRule.THUMBNAIL
    fprule.save()

    return fprule


@pytest.fixture
def fprule_access(fprule: fprmodels.FPRule) -> fprmodels.FPRule:
    fprule.purpose = fprmodels.FPRule.ACCESS
    fprule.save()

    return fprule


@pytest.fixture
def transfer_file(transfer: models.Transfer) -> models.File:
    location = b"%transferDirectory%objects/file.mp3"
    return models.File.objects.create(
        transfer=transfer,
        filegrpuse="original",
        originallocation=location,
        currentlocation=location,
    )


@pytest.fixture
def sip_file(sip: models.SIP, transfer: models.Transfer) -> models.File:
    location = "objects/file.mp3"
    return models.File.objects.create(
        transfer=transfer,
        sip=sip,
        filegrpuse="original",
        originallocation=f"%transferDirectory%{location}".encode(),
        currentlocation=f"%SIPDirectory%{location}".encode(),
    )


@pytest.fixture
def preservation_file(sip: models.SIP, transfer: models.Transfer) -> models.File:
    location = b"%SIPDirectory%objects/file.wav"
    return models.File.objects.create(
        transfer=transfer,
        sip=sip,
        filegrpuse="preservation",
        originallocation=location,
        currentlocation=location,
    )


@pytest.fixture
def transfer_file_format_version(
    transfer_file: models.File, format_version: fprmodels.FormatVersion
) -> models.FileFormatVersion:
    return models.FileFormatVersion.objects.create(
        file_uuid=transfer_file, format_version=format_version
    )


@pytest.fixture
def sip_file_format_version(
    sip_file: models.File, format_version: fprmodels.FormatVersion
) -> models.FileFormatVersion:
    return models.FileFormatVersion.objects.create(
        file_uuid=sip_file, format_version=format_version
    )


@pytest.fixture
def shared_directory_path(tmp_path: pathlib.Path) -> pathlib.Path:
    result = tmp_path / "sharedDirectory"
    result.mkdir()

    for directory in ["currentlyProcessing", "tmp"]:
        (result / directory).mkdir()

    return result


@pytest.fixture
def transfer_directory_path(tmp_path: pathlib.Path) -> pathlib.Path:
    result = tmp_path / "transfer"
    result.mkdir()

    return result


@pytest.fixture
def sip_directory_path(tmp_path: pathlib.Path) -> pathlib.Path:
    result = tmp_path / "sip"
    result.mkdir()

    return result


@pytest.fixture
def settings(
    settings: pytest_django.fixtures.SettingsWrapper,
    shared_directory_path: pathlib.Path,
) -> pytest_django.fixtures.SettingsWrapper:
    settings.SHARED_DIRECTORY = f"{shared_directory_path}/"
    settings.PROCESSING_DIRECTORY = f'{shared_directory_path / "currentlyProcessing"}/'

    return settings
