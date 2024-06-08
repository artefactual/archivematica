import pathlib
from unittest import mock

import pytest
from django.db.models import Q
from fileOperations import FindFileInNormalizatonCSVError
from fileOperations import addAccessionEvent
from fileOperations import findFileInNormalizationCSV
from fileOperations import get_extract_dir_name
from main.models import SIP
from main.models import Event
from main.models import File
from main.models import Transfer


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
def test_addAccessionEvent_adds_registration_event_when_accessionid_is_set():
    f = File.objects.create()
    t = Transfer.objects.create(accessionid="my-id")
    date = None
    query_filter = Q(
        file_uuid=f,
        event_type="registration",
        event_outcome_detail="accession#my-id",
    )

    assert Event.objects.filter(query_filter).count() == 0

    addAccessionEvent(f.uuid, t.uuid, date)

    assert Event.objects.filter(query_filter).count() == 1


@pytest.fixture
def sip_directory(tmp_path):
    result = tmp_path / "sip"
    result.mkdir()

    return result


@pytest.fixture
def sip(sip_directory):
    return SIP.objects.create(currentpath=str(sip_directory))


@pytest.fixture
def file(sip):
    location = b"%SIPDirectory%objects/file.mp3"
    return File.objects.create(
        sip=sip,
        filegrpuse="original",
        currentlocation=location,
        originallocation=location,
    )


@pytest.fixture
def preservation_file(sip):
    location = b"%SIPDirectory%objects/manualNormalization/preservation/file.wav"
    return File.objects.create(
        sip=sip, currentlocation=location, originallocation=location
    )


@pytest.fixture
def access_file(sip):
    location = b"%SIPDirectory%objects/manualNormalization/access/file.mp3"
    return File.objects.create(
        sip=sip, currentlocation=location, originallocation=location
    )


@pytest.fixture
def normalization_csv(sip_directory, file, preservation_file, access_file):
    manual_normalization_directory = sip_directory / "objects" / "manualNormalization"
    manual_normalization_directory.mkdir(parents=True)

    original_file_path = pathlib.Path(file.currentlocation.decode()).name
    preservation_file_path = str(
        pathlib.Path(preservation_file.originallocation.decode()).relative_to(
            "%SIPDirectory%objects"
        )
    )
    access_file_path = str(
        pathlib.Path(access_file.originallocation.decode()).relative_to(
            "%SIPDirectory%objects"
        )
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
    normalization_csv, sip, file, access_file
):
    purpose = "access"
    target_file = pathlib.Path(access_file.originallocation.decode()).relative_to(
        "%SIPDirectory%objects"
    )
    expected_result = pathlib.Path(file.currentlocation.decode()).name
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
    normalization_csv, sip, file, preservation_file
):
    purpose = "preservation"
    target_file = pathlib.Path(preservation_file.originallocation.decode()).relative_to(
        "%SIPDirectory%objects"
    )
    expected_result = pathlib.Path(file.currentlocation.decode()).name
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
    normalization_csv, sip, access_file
):
    purpose = "preservation"
    target_file = pathlib.Path(access_file.originallocation.decode()).relative_to(
        "%SIPDirectory%objects"
    )
    expected_result = None
    printfn = mock.Mock()

    result = findFileInNormalizationCSV(
        str(normalization_csv), purpose, target_file, str(sip.uuid), printfn
    )

    assert result == expected_result
    printfn.assert_not_called()


@pytest.fixture
def invalid_normalization_csv(normalization_csv):
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


@pytest.mark.django_db
def test_findFileInNormalizationCSV_fails_with_invalid_normalization_csv(
    invalid_normalization_csv, sip, access_file
):
    purpose = "access"
    target_file = pathlib.Path(access_file.originallocation.decode()).relative_to(
        "%SIPDirectory%objects"
    )
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
def second_access_file(sip):
    location = b"%SIPDirectory%objects/manualNormalization/access/file.mp3"
    return File.objects.create(
        sip=sip, currentlocation=location, originallocation=location
    )


@pytest.mark.django_db
def test_findFileInNormalizationCSV_fails_if_multiple_target_files_exist(
    invalid_normalization_csv, sip, access_file, second_access_file
):
    purpose = "access"
    target_file = pathlib.Path(access_file.originallocation.decode()).relative_to(
        "%SIPDirectory%objects"
    )
    printfn = mock.Mock()

    with pytest.raises(FindFileInNormalizatonCSVError, match="2"):
        findFileInNormalizationCSV(
            str(invalid_normalization_csv), purpose, target_file, str(sip.uuid), printfn
        )

    printfn.assert_called_once_with(
        f"More than one result found for {purpose} file ({target_file}) in DB.",
        file=mock.ANY,
    )
