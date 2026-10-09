"""Fixtures shared by every test suite.

The modules imported here must be importable under the settings of every suite:
the MCPServer settings install neither Tastypie nor the accounts application.
"""

import pathlib
import uuid

import pytest
import pytest_django
from django.contrib.auth.models import User

from archivematica.dashboard.fpr import models as fprmodels
from archivematica.dashboard.main import models
from tests.factories import DublinCoreFactory
from tests.factories import EventFactory
from tests.factories import FileFactory
from tests.factories import JobFactory
from tests.factories import RightsStatementFactory
from tests.factories import SIPFactory
from tests.factories import TaskFactory
from tests.factories import TransferFactory

# Directories


@pytest.fixture
def shared_directory_path(tmp_path: pathlib.Path) -> pathlib.Path:
    """The shared directory of the pipeline, with its processing and temporary
    directories.
    """
    result = tmp_path / "sharedDirectory"
    result.mkdir()

    for directory in ["currentlyProcessing", "tmp"]:
        (result / directory).mkdir()

    return result


@pytest.fixture
def settings(
    settings: pytest_django.Settings,
    shared_directory_path: pathlib.Path,
) -> pytest_django.Settings:
    """The Django settings, with the shared directory settings pointing at the
    temporary shared directory.
    """
    settings.SHARED_DIRECTORY = f"{shared_directory_path}/"
    settings.PROCESSING_DIRECTORY = f"{shared_directory_path / 'currentlyProcessing'}/"

    return settings


@pytest.fixture
def processing_configurations_path(
    settings: pytest_django.Settings, shared_directory_path: pathlib.Path
) -> pathlib.Path:
    """The directory of the processing configurations of the shared directory."""
    result = (
        shared_directory_path
        / "sharedMicroServiceTasksConfigs"
        / "processingMCPConfigs"
    )
    result.mkdir(parents=True)

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


# Dashboard settings


def _set_dashboard_setting(name: str, value: str) -> None:
    # The dashboard helpers import Tastypie, which the settings of the MCPServer
    # suite do not install, so the settings are written through the model.
    models.DashboardSetting.objects.update_or_create(
        name=name, defaults={"value": value}
    )


@pytest.fixture
def dashboard_uuid() -> uuid.UUID:
    """The UUID of the dashboard, which identifies the pipeline."""
    result = uuid.uuid4()
    _set_dashboard_setting("dashboard_uuid", str(result))

    return result


@pytest.fixture
def site_url() -> str:
    value = "https://example.com/"
    _set_dashboard_setting("site_url", value)

    return value


@pytest.fixture
def storage_service_url() -> str:
    """The URL of the Storage Service, without the trailing slash that the
    API client adds.
    """
    value = "https://ss.example.com"
    _set_dashboard_setting("storage_service_url", value)

    return value


@pytest.fixture
def storage_service_user() -> str:
    value = "test"
    _set_dashboard_setting("storage_service_user", value)

    return value


@pytest.fixture
def storage_service_apikey() -> str:
    value = "api-key"
    _set_dashboard_setting("storage_service_apikey", value)

    return value


@pytest.fixture
def checksum_type() -> str:
    value = "md5"
    _set_dashboard_setting("checksum_type", value)

    return value


@pytest.fixture
def metadata_applies_to_types() -> dict[str, models.MetadataAppliesToType]:
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


# Users and agents


@pytest.fixture
def user() -> User:
    """A superuser; the user model signal creates the agent that represents it."""
    return User.objects.create(
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
    return models.Agent.objects.get(userprofile__user=user)


@pytest.fixture
def organization_agent() -> models.Agent:
    """The default organization agent, linked to the events of every file."""
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


# Factories


@pytest.fixture
def make_transfer() -> TransferFactory:
    return TransferFactory()


@pytest.fixture
def make_sip() -> SIPFactory:
    return SIPFactory()


@pytest.fixture
def make_file() -> FileFactory:
    return FileFactory()


@pytest.fixture
def make_job() -> JobFactory:
    return JobFactory()


@pytest.fixture
def make_task() -> TaskFactory:
    return TaskFactory()


@pytest.fixture
def make_event() -> EventFactory:
    return EventFactory()


@pytest.fixture
def make_rights_statement(
    metadata_applies_to_types: dict[str, models.MetadataAppliesToType],
) -> RightsStatementFactory:
    return RightsStatementFactory(metadata_applies_to_types)


@pytest.fixture
def make_dublincore(
    metadata_applies_to_types: dict[str, models.MetadataAppliesToType],
) -> DublinCoreFactory:
    return DublinCoreFactory(metadata_applies_to_types)


@pytest.fixture
def dublincore_record() -> dict[str, str]:
    """The Dublin Core metadata of the SIP of the METS fixtures."""
    return {
        "title": "Yamani Weapons",
        "creator": "Keladry of Mindelan",
        "subject": "Glaives",
        "description": "Glaives are cool",
        "publisher": "Tortall Press",
        "contributor": "Yuki",
        "date": "2015",
        "type": "Archival Information Package",
        "format": "parchement",
        "identifier": "42/1",
        "source": "Numair's library",
        "relation": "None",
        "language": "en",
        "rights": "Public Domain",
        "is_part_of": "AIC#42",
    }


# Units, jobs and files


@pytest.fixture
def job(make_job: JobFactory) -> models.Job:
    return make_job()


@pytest.fixture
def task(make_task: TaskFactory, job: models.Job) -> models.Task:
    return make_task(job)


@pytest.fixture
def transfer(make_transfer: TransferFactory, user: User) -> models.Transfer:
    """A transfer being processed by the user."""
    result = make_transfer(access_system_id="atom-description-id", diruuids=True)
    result.update_active_agent(user.id)

    return result


@pytest.fixture
def sip(make_sip: SIPFactory) -> models.SIP:
    return make_sip(diruuids=True)


@pytest.fixture
def transfer_file(make_file: FileFactory, transfer: models.Transfer) -> models.File:
    return make_file("objects/file.mp3", transfer=transfer)


@pytest.fixture
def sip_file(
    make_file: FileFactory, sip: models.SIP, transfer: models.Transfer
) -> models.File:
    """An original file of the transfer, now in the SIP."""
    return make_file("objects/file.mp3", transfer=transfer, sip=sip)


@pytest.fixture
def preservation_file(
    make_file: FileFactory, sip: models.SIP, transfer: models.Transfer
) -> models.File:
    return make_file(
        "objects/file.wav", transfer=transfer, sip=sip, filegrpuse="preservation"
    )


@pytest.fixture
def access_file(
    make_file: FileFactory, sip: models.SIP, transfer: models.Transfer
) -> models.File:
    return make_file(
        "objects/file.wav", transfer=transfer, sip=sip, filegrpuse="access"
    )


@pytest.fixture
def manual_preservation_file(
    make_file: FileFactory, sip: models.SIP, transfer: models.Transfer
) -> models.File:
    """A preservation derivative of the SIP file, normalized manually."""
    return make_file(
        "objects/manualNormalization/preservation/file.wav",
        transfer=transfer,
        sip=sip,
        filegrpuse="preservation",
    )


@pytest.fixture
def manual_access_file(
    make_file: FileFactory, sip: models.SIP, transfer: models.Transfer
) -> models.File:
    """An access derivative of the SIP file, normalized manually."""
    return make_file(
        "objects/manualNormalization/access/file.mp3",
        transfer=transfer,
        sip=sip,
        filegrpuse="access",
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
def preservation_file_format_version(
    preservation_file: models.File, format_version: fprmodels.FormatVersion
) -> models.FileFormatVersion:
    return models.FileFormatVersion.objects.create(
        file_uuid=preservation_file, format_version=format_version
    )


@pytest.fixture
def access_file_format_version(
    access_file: models.File, format_version: fprmodels.FormatVersion
) -> models.FileFormatVersion:
    return models.FileFormatVersion.objects.create(
        file_uuid=access_file, format_version=format_version
    )


@pytest.fixture
def preservation_derivation(
    sip_file: models.File, preservation_file: models.File
) -> models.Derivation:
    return models.Derivation.objects.create(
        source_file=sip_file, derived_file=preservation_file
    )


@pytest.fixture
def access_derivation(
    sip_file: models.File, access_file: models.File
) -> models.Derivation:
    return models.Derivation.objects.create(
        source_file=sip_file, derived_file=access_file
    )


def _decode_location(location: bytes | memoryview | None) -> str:
    assert isinstance(location, bytes)

    return location.decode()


def _materialize(unit_directory_path: pathlib.Path, file: models.File) -> pathlib.Path:
    """Create an empty file at the current location of the file in the unit
    directory and return its path.
    """
    location = _decode_location(file.currentlocation)
    for prefix in [r"%SIPDirectory%", r"%transferDirectory%"]:
        location = location.removeprefix(prefix)
    result = unit_directory_path / location
    result.parent.mkdir(parents=True, exist_ok=True)
    result.touch()

    return result


@pytest.fixture
def transfer_file_path(
    transfer_directory_path: pathlib.Path, transfer_file: models.File
) -> pathlib.Path:
    """The transfer file, created in the transfer directory."""
    return _materialize(transfer_directory_path, transfer_file)


@pytest.fixture
def sip_file_path(
    sip_directory_path: pathlib.Path, sip_file: models.File
) -> pathlib.Path:
    """The SIP file, created in the SIP directory."""
    return _materialize(sip_directory_path, sip_file)


@pytest.fixture
def normalization_csv(
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    manual_access_file: models.File,
    manual_preservation_file: models.File,
) -> pathlib.Path:
    """The normalization CSV of the SIP, which maps the SIP file to its manually
    normalized derivatives.
    """
    manual_normalization_directory = (
        sip_directory_path / "objects" / "manualNormalization"
    )
    manual_normalization_directory.mkdir(parents=True)

    original_file_path = pathlib.Path(_decode_location(sip_file.currentlocation)).name
    access_file_path, preservation_file_path = (
        str(
            pathlib.Path(_decode_location(file.originallocation)).relative_to(
                "%SIPDirectory%objects"
            )
        )
        for file in [manual_access_file, manual_preservation_file]
    )

    result = manual_normalization_directory / "normalization.csv"
    result.write_text(
        "\n".join(
            [
                "# original, access, preservation",
                "",
                f"{original_file_path},{access_file_path},{preservation_file_path}",
            ]
        )
    )

    return result


@pytest.fixture
def invalid_normalization_csv(normalization_csv: pathlib.Path) -> pathlib.Path:
    normalization_csv.write_text(
        "\n".join(
            [
                "# original, access, preservation",
                "",
                'this,should,fail,because,",too,many,columns',
            ]
        )
    )

    return normalization_csv


# Format Policy Registry


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


@pytest.fixture
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
