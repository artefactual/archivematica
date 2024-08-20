import pathlib
from unittest import mock

import has_packages
import pytest
from client.job import Job
from fpr import models as fprmodels
from main import models


@pytest.fixture
def compressed_file(
    transfer: models.Transfer,
    transfer_directory_path: pathlib.Path,
    format_version: fprmodels.FormatVersion,
) -> models.File:
    # Simulate a compressed file being extracted to a directory with the same name.
    d = transfer_directory_path / "compressed.zip"
    d.mkdir()

    # Place an extracted file in it.
    f = d / "file.txt"
    f.touch()

    # Create File models for the compressed and extracted files.
    d_location = (
        f"{transfer.currentlocation}{d.relative_to(transfer_directory_path)}".encode()
    )
    f_location = (
        f"{transfer.currentlocation}{f.relative_to(transfer_directory_path)}".encode()
    )
    result = models.File.objects.create(
        transfer=transfer, originallocation=d_location, currentlocation=d_location
    )
    models.File.objects.create(
        transfer=transfer, originallocation=f_location, currentlocation=f_location
    )

    # Create a file format version for the compressed file.
    models.FileFormatVersion.objects.create(
        file_uuid=result, format_version=format_version
    )

    return result


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fprule_fixture,expected_exit_code",
    [("fprule_extraction", 0), ("fprule_characterization", 1)],
    ids=["extract_rule", "not_extract_rule"],
)
def test_main_detects_file_is_extractable_based_on_extract_fpr_rule(
    transfer: models.Transfer,
    compressed_file: models.File,
    format_version: fprmodels.FormatVersion,
    fpcommand: fprmodels.FPCommand,
    fprule_fixture: str,
    expected_exit_code: int,
    request: pytest.FixtureRequest,
) -> None:
    job = mock.Mock(spec=Job)
    request.getfixturevalue(fprule_fixture)

    result = has_packages.main(job, str(transfer.uuid))

    assert result == expected_exit_code


@pytest.mark.django_db
@pytest.mark.parametrize(
    "event_type,expected_exit_code",
    [("unpacking", 1), ("charaterization", 0)],
    ids=["unpacking_event", "not_unpacking_event"],
)
def test_main_detects_file_was_already_extracted_from_unpacking_event(
    transfer: models.Transfer,
    compressed_file: models.File,
    format_version: fprmodels.FormatVersion,
    fpcommand: fprmodels.FPCommand,
    fprule_extraction: fprmodels.FPRule,
    event_type: str,
    expected_exit_code: int,
) -> None:
    job = mock.Mock(spec=Job)
    extracted_file = models.File.objects.get(
        currentlocation__startswith=compressed_file.currentlocation.decode(),
        currentlocation__endswith="file.txt",
    )
    models.Event.objects.create(
        file_uuid=extracted_file,
        event_type=event_type,
        event_detail=f"Unpacked from: {extracted_file.currentlocation} ({compressed_file.uuid})",
    )

    result = has_packages.main(job, str(transfer.uuid))

    assert result == expected_exit_code
