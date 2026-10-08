import importlib.resources
import pathlib
import uuid

import pytest
import pytest_django
from django.contrib.auth.models import User
from django.utils import timezone

from archivematica.dashboard.fpr import models as fprmodels
from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job


@pytest.fixture(autouse=True)
def set_xml_catalog_files(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use local XML schemas for validation."""
    monkeypatch.setenv(
        "XML_CATALOG_FILES",
        str(
            importlib.resources.files("archivematica.MCPClient")
            / "assets"
            / "catalog"
            / "catalog.xml"
        ),
    )


@pytest.fixture()
def mcp_job() -> Job:
    return Job("stub", "stub", [])


@pytest.fixture()
def metadata_applies_to_types(
    db: None,
) -> dict[str, models.MetadataAppliesToType]:
    file_type, _ = models.MetadataAppliesToType.objects.get_or_create(
        pk=uuid.UUID(models.MetadataAppliesToType.FILE_TYPE),
        description="File",
    )
    transfer_type, _ = models.MetadataAppliesToType.objects.get_or_create(
        pk=uuid.UUID(models.MetadataAppliesToType.TRANSFER_TYPE),
        description="Transfer",
    )
    sip_type, _ = models.MetadataAppliesToType.objects.get_or_create(
        pk=uuid.UUID(models.MetadataAppliesToType.SIP_TYPE),
        description="SIP",
    )

    return {"file": file_type, "transfer": transfer_type, "sip": sip_type}


@pytest.fixture()
def user() -> User:
    return User.objects.create(
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
def user_agent(user: User) -> models.Agent:
    """The agent that represents the user in PREMIS events."""
    return models.UserProfile.objects.get(user=user).agent


@pytest.fixture
def organization_agent(db: None) -> models.Agent:
    """The default organization agent, linked to the events of every file."""
    result: models.Agent
    result, _ = models.Agent.objects.get_or_create(
        pk=models.Agent.objects.DEFAULT_ORGANIZATION_AGENT_PK,
        defaults={
            "agenttype": "organization",
            "identifiertype": "repository code",
            "identifiervalue": "ORG",
            "name": "Your Organization Name Here",
        },
    )

    return result


@pytest.fixture
def demo_organization_agent(organization_agent: models.Agent) -> models.Agent:
    """The organization agent of the METS fixtures, the demo repository."""
    organization_agent.identifiervalue = "demo"
    organization_agent.name = "demo"
    organization_agent.save()

    return organization_agent


@pytest.fixture
def job() -> models.Job:
    return models.Job.objects.create(createdtime=timezone.now())


@pytest.fixture
def task(job: models.Job) -> models.Task:
    return models.Task.objects.create(job=job, createdtime=timezone.now())


@pytest.fixture
def transfer(user: User) -> models.Transfer:
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
def unicode_transfer(db: None) -> models.Transfer:
    """A standard transfer whose directory name has non-ASCII characters."""
    transfer_uuid = uuid.UUID("e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6")

    return models.Transfer.objects.create(
        uuid=transfer_uuid,
        type="Standard",
        currentlocation=f"%sharedPath%currentlyProcessing/ユニコード-{transfer_uuid}/",
    )


@pytest.fixture
def unicode_transfer_files(unicode_transfer: models.Transfer) -> list[models.File]:
    """The original files of the unicode transfer, some with non-ASCII paths."""
    photo_checksum = "d2bed92b73c7090bb30a0b30016882e7069c437488e1513e9deaacbe29d38d92"
    lion_checksum = "f78615cd834f7fb84832177e73f13e3479f5b5b22ae7a9506c7fa0a14fd9df9e"
    result = []
    for file_uuid, path, size, checksum in [
        (
            "47813453-6872-442b-9d65-6515be3c5aa1",
            "たくさん directories/need name change/checking here/evélyn's photo.jpg",
            158131,
            photo_checksum,
        ),
        (
            "60e5c61b-14ef-4e92-89ec-9b9201e68adb",
            "no_name_change/needed_here/lion.svg",
            18324,
            lion_checksum,
        ),
        (
            "791e07ea-ad44-4315-b55b-44ec771e95cf",
            "たくさん directories/need name change/checking here/lion写真.svg",
            18324,
            lion_checksum,
        ),
        (
            "8a1f0b59-cf94-47ef-8078-647b77c8a147",
            "has space/lion.svg",
            18324,
            lion_checksum,
        ),
    ]:
        location = f"%transferDirectory%objects/{path}".encode()
        result.append(
            models.File.objects.create(
                uuid=uuid.UUID(file_uuid),
                transfer=unicode_transfer,
                filegrpuse="original",
                originallocation=location,
                currentlocation=location,
                size=size,
                checksum=checksum,
                checksumtype="sha256",
            )
        )

    return result


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
    settings: pytest_django.Settings,
    shared_directory_path: pathlib.Path,
) -> pytest_django.Settings:
    settings.SHARED_DIRECTORY = f"{shared_directory_path}/"
    settings.PROCESSING_DIRECTORY = f"{shared_directory_path / 'currentlyProcessing'}/"

    return settings
