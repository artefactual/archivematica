import pathlib
from unittest import mock

import pytest
from django.db.models import Q

from archivematica.archivematicaCommon.fileOperations import (
    FindFileInNormalizatonCSVError,
)
from archivematica.archivematicaCommon.fileOperations import addAccessionEvent
from archivematica.archivematicaCommon.fileOperations import findFileInNormalizationCSV
from archivematica.archivematicaCommon.fileOperations import get_extract_dir_name
from archivematica.dashboard.main.models import SIP
from archivematica.dashboard.main.models import Event
from archivematica.dashboard.main.models import File
from tests.factories import FileFactory
from tests.factories import TransferFactory


@pytest.mark.parametrize(
    "filename,dirname",
    [
        ("/parent/test.zip", "/parent/test"),
        ("/parent/test.tar.gz", "/parent/test"),
        ("/parent/test.TAR.GZ", "/parent/test"),
        ("/parent/test.TAR.GZ", "/parent/test"),
        (
            "/parent/test.target.tar.gz",
            "/parent/test.target",
        ),  # something beginning with "tar"
    ],
)
def test_get_extract_dir_name(filename, dirname):
    assert get_extract_dir_name(filename) == dirname


def test_get_extract_dir_name_raises_if_no_extension():
    with pytest.raises(ValueError):
        get_extract_dir_name("test")


@pytest.mark.django_db
def test_addAccessionEvent_adds_registration_event_when_accessionid_is_set(
    make_transfer: TransferFactory,
) -> None:
    # The file belongs to no unit, so the event gets the default agents.
    f = File.objects.create()
    t = make_transfer(accessionid="my-id")
    date = None
    query_filter = Q(
        file_uuid=f,
        event_type="registration",
        event_outcome_detail="accession#my-id",
    )

    assert Event.objects.filter(query_filter).count() == 0

    addAccessionEvent(f.uuid, t.uuid, date)

    assert Event.objects.filter(query_filter).count() == 1


@pytest.mark.django_db
def test_findFileInNormalizationCSV_fails_if_original_file_does_not_exist(
    normalization_csv, sip
):
    purpose = "access"
    target_file = "manualNormalization/access/foo"
    printfn = mock.Mock()

    with pytest.raises(FindFileInNormalizatonCSVError, match="2"):
        findFileInNormalizationCSV(
            str(normalization_csv), purpose, target_file, str(sip.uuid), printfn
        )

    printfn.assert_called_once_with(
        f"{purpose} file ({target_file}) not found in DB.", file=mock.ANY
    )


@pytest.mark.django_db
def test_findFileInNormalizationCSV_finds_access_file(
    normalization_csv: pathlib.Path, sip: SIP, sip_file: File, manual_access_file: File
) -> None:
    purpose = "access"
    target_file = pathlib.Path(
        manual_access_file.originallocation.decode()
    ).relative_to("%SIPDirectory%objects")
    expected_result = pathlib.Path(sip_file.currentlocation.decode()).name
    printfn = mock.Mock()

    result = findFileInNormalizationCSV(
        str(normalization_csv), purpose, target_file, str(sip.uuid), printfn
    )

    assert result == expected_result
    printfn.assert_called_once_with(
        f"Found {purpose} file ({target_file}) for original ({expected_result})"
    )


@pytest.mark.django_db
def test_findFileInNormalizationCSV_finds_preservation_file(
    normalization_csv: pathlib.Path,
    sip: SIP,
    sip_file: File,
    manual_preservation_file: File,
) -> None:
    purpose = "preservation"
    target_file = pathlib.Path(
        manual_preservation_file.originallocation.decode()
    ).relative_to("%SIPDirectory%objects")
    expected_result = pathlib.Path(sip_file.currentlocation.decode()).name
    printfn = mock.Mock()

    result = findFileInNormalizationCSV(
        str(normalization_csv), purpose, target_file, str(sip.uuid), printfn
    )

    assert result == expected_result
    printfn.assert_called_once_with(
        f"Found {purpose} file ({target_file}) for original ({expected_result})"
    )


@pytest.mark.django_db
def test_findFileInNormalizationCSV_returns_None_when_cannot_match_files(
    normalization_csv: pathlib.Path, sip: SIP, manual_access_file: File
) -> None:
    purpose = "preservation"
    target_file = pathlib.Path(
        manual_access_file.originallocation.decode()
    ).relative_to("%SIPDirectory%objects")
    expected_result = None
    printfn = mock.Mock()

    result = findFileInNormalizationCSV(
        str(normalization_csv), purpose, target_file, str(sip.uuid), printfn
    )

    assert result == expected_result
    printfn.assert_not_called()


@pytest.mark.django_db
def test_findFileInNormalizationCSV_fails_with_invalid_normalization_csv(
    invalid_normalization_csv: pathlib.Path, sip: SIP, manual_access_file: File
) -> None:
    purpose = "access"
    target_file = pathlib.Path(
        manual_access_file.originallocation.decode()
    ).relative_to("%SIPDirectory%objects")
    printfn = mock.Mock()

    with pytest.raises(FindFileInNormalizatonCSVError, match="2"):
        findFileInNormalizationCSV(
            str(invalid_normalization_csv), purpose, target_file, str(sip.uuid), printfn
        )

    printfn.assert_called_once_with(
        f"Error reading {invalid_normalization_csv} on line 3",
        file=mock.ANY,
    )


@pytest.fixture
def second_access_file(make_file: FileFactory, manual_access_file: File) -> File:
    """Another file at the location of the manual access file."""
    return make_file(
        "objects/manualNormalization/access/file.mp3",
        sip=manual_access_file.sip,
        filegrpuse="access",
    )


@pytest.mark.django_db
def test_findFileInNormalizationCSV_fails_if_multiple_target_files_exist(
    invalid_normalization_csv: pathlib.Path,
    sip: SIP,
    manual_access_file: File,
    second_access_file: File,
) -> None:
    purpose = "access"
    target_file = pathlib.Path(
        manual_access_file.originallocation.decode()
    ).relative_to("%SIPDirectory%objects")
    printfn = mock.Mock()

    with pytest.raises(FindFileInNormalizatonCSVError, match="2"):
        findFileInNormalizationCSV(
            str(invalid_normalization_csv), purpose, target_file, str(sip.uuid), printfn
        )

    printfn.assert_called_once_with(
        f"More than one result found for {purpose} file ({target_file}) in DB.",
        file=mock.ANY,
    )
