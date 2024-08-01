import pathlib
import uuid
from unittest import mock

import normalize
import pytest
from client.job import Job
from fpr import models as fprmodels
from main import models


@pytest.mark.django_db
@mock.patch("argparse.ArgumentParser.parse_args")
def test_thumbnail_mode_disables_thumbnail_generation(parse_args):
    parse_args.return_value = mock.Mock(
        purpose="thumbnail", thumbnail_mode="do_not_generate"
    )
    job = mock.Mock(args=[], JobContext=mock.MagicMock(), spec=Job)

    normalize.call([job])

    job.pyprint.assert_called_once_with("Thumbnail generation has been disabled")
    job.set_status.assert_called_once_with(normalize.SUCCESS)


@pytest.mark.django_db
def test_normalization_fails_if_original_file_does_not_exist():
    file_uuid = str(uuid.uuid4())
    job = mock.Mock(spec=Job)
    opts = mock.Mock(file_uuid=file_uuid)

    result = normalize.main(job, opts)

    assert result == normalize.NO_RULE_FOUND
    job.print_error.assert_called_once_with(
        "File with uuid", file_uuid, "does not exist in database."
    )


@pytest.mark.django_db
def test_normalization_skips_submission_documentation_file_if_group_use_does_not_match(
    sip_file,
):
    file_path = "%SIPDirectory%objects/submissionDocumentation/file.mp3"
    sip_file.currentlocation = file_path.encode()
    sip_file.save()
    job = mock.Mock(spec=Job)
    opts = mock.Mock(
        file_uuid=str(sip_file.uuid),
        file_path=file_path,
        normalize_file_grp_use="original",
    )

    result = normalize.main(job, opts)

    assert result == normalize.SUCCESS
    assert job.print_output.mock_calls == [
        mock.call("File found:", sip_file.uuid, file_path),
        mock.call(
            "File",
            pathlib.Path(file_path).name,
            "in objects/submissionDocumentation, skipping",
        ),
    ]


@pytest.mark.django_db
def test_normalization_skips_file_if_group_use_does_not_match(sip_file):
    sip_file.filegrpuse = "original"
    sip_file.save()
    job = mock.Mock(spec=Job)
    opts = mock.Mock(
        file_uuid=str(sip_file.uuid),
        file_path=sip_file.currentlocation.decode(),
        normalize_file_grp_use="access",
    )

    result = normalize.main(job, opts)

    assert result == normalize.SUCCESS
    assert job.print_output.mock_calls == [
        mock.call("File found:", sip_file.uuid, sip_file.currentlocation.decode()),
        mock.call(
            pathlib.Path(sip_file.currentlocation.decode()).name,
            "is file group usage",
            sip_file.filegrpuse,
            "instead of ",
            opts.normalize_file_grp_use,
            " - skipping",
        ),
    ]


@pytest.fixture
def manual_preservation_file(preservation_file):
    preservation_file.originallocation = (
        b"%SIPDirectory%objects/manualNormalization/preservation/file.wav"
    )
    preservation_file.currentlocation = (
        b"%SIPDirectory%objects/manualNormalization/preservation/file.wav"
    )
    preservation_file.save()

    return preservation_file


@pytest.fixture
def normalization_csv(sip_directory_path, sip_file, manual_preservation_file):
    manual_normalization_directory = (
        sip_directory_path / "objects" / "manualNormalization"
    )
    manual_normalization_directory.mkdir(parents=True)

    original_file_path = pathlib.Path(sip_file.currentlocation.decode()).name
    preservation_file_path = str(
        pathlib.Path(manual_preservation_file.originallocation.decode()).relative_to(
            "%SIPDirectory%objects"
        )
    )

    result = manual_normalization_directory / "normalization.csv"
    result.write_text(
        "\n".join(
            [
                "# original, access, preservation",
                "",
                f"{original_file_path},,{preservation_file_path}",
            ]
        )
    )

    return result


@pytest.mark.django_db
def test_manual_normalization_creates_event_and_derivation(
    sip, sip_directory_path, normalization_csv, sip_file, manual_preservation_file
):
    original_file_path = pathlib.Path(sip_file.currentlocation.decode())
    preservation_file_path = str(
        pathlib.Path(manual_preservation_file.originallocation.decode()).relative_to(
            "%SIPDirectory%objects"
        )
    )
    job = mock.Mock(spec=Job)
    opts = mock.Mock(
        file_uuid=str(sip_file.uuid),
        file_path=str(original_file_path),
        sip_uuid=str(sip.uuid),
        purpose="preservation",
        sip_path=str(sip_directory_path),
        normalize_file_grp_use="original",
    )

    result = normalize.main(job, opts)

    assert result == normalize.SUCCESS
    assert job.print_output.mock_calls == [
        mock.call("File found:", sip_file.uuid, sip_file.currentlocation.decode()),
        mock.call(
            "Filename",
            original_file_path.name,
            "matches entry in normalization.csv",
            original_file_path.name,
        ),
        mock.call("Looking for", preservation_file_path, "in database"),
        mock.call(
            original_file_path.name,
            "was already manually normalized into",
            manual_preservation_file.currentlocation.decode(),
        ),
    ]

    # A normalization event is created.
    assert (
        models.Event.objects.filter(
            file_uuid=sip_file,
            event_type="normalization",
            event_detail="manual normalization",
        ).count()
        == 1
    )

    # A derivation from the original file to the normalized file is created.
    assert (
        models.Derivation.objects.filter(
            source_file=sip_file, derived_file=manual_preservation_file
        ).count()
        == 1
    )


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
def test_manual_normalization_fails_with_invalid_normalization_csv(
    sip,
    sip_directory_path,
    invalid_normalization_csv,
    sip_file,
    manual_preservation_file,
):
    original_file_path = pathlib.Path(sip_file.currentlocation.decode())
    job = mock.Mock(spec=Job)
    opts = mock.Mock(
        file_uuid=str(sip_file.uuid),
        file_path=str(original_file_path),
        sip_uuid=str(sip.uuid),
        purpose="preservation",
        sip_path=str(sip_directory_path),
        normalize_file_grp_use="original",
    )

    result = normalize.main(job, opts)

    assert result == normalize.NO_RULE_FOUND
    assert job.print_error.mock_calls == [
        mock.call("Error reading", str(invalid_normalization_csv), " on line", 3),
        # This is an exception encoded as a string.
        mock.call(mock.ANY),
    ]
    assert job.print_output.mock_calls == [
        mock.call("File found:", sip_file.uuid, sip_file.currentlocation.decode()),
        mock.call(
            "Not normalizing",
            pathlib.Path(sip_file.currentlocation.decode()).name,
            " - No rule or default rule found to normalize for",
            "preservation",
        ),
    ]

    # No normalization event is created.
    assert models.Event.objects.filter().count() == 0

    # No derivation from the original file to the normalized file is created.
    assert models.Derivation.objects.filter().count() == 0


@pytest.mark.django_db
def test_manual_normalization_matches_by_filename_instead_of_normalization_csv(
    sip, sip_directory_path, sip_file, manual_preservation_file
):
    original_file_path = pathlib.Path(sip_file.currentlocation.decode())
    preservation_file_path_with_no_extension = str(
        pathlib.Path(manual_preservation_file.originallocation.decode())
    ).rsplit(".", 1)[0]

    job = mock.Mock(spec=Job)
    opts = mock.Mock(
        file_uuid=str(sip_file.uuid),
        file_path=str(original_file_path),
        sip_uuid=str(sip.uuid),
        purpose="preservation",
        sip_path=str(sip_directory_path),
        normalize_file_grp_use="original",
    )

    result = normalize.main(job, opts)

    assert result == normalize.SUCCESS
    assert job.print_error.mock_calls == []
    assert job.print_output.mock_calls == [
        mock.call("File found:", sip_file.uuid, sip_file.currentlocation.decode()),
        mock.call(
            "Checking for a manually normalized file by trying to get the"
            f" unique file that matches SIP UUID {sip.uuid} and whose currentlocation"
            f" value starts with this path: {preservation_file_path_with_no_extension}."
        ),
        mock.call(
            original_file_path.name,
            "was already manually normalized into",
            manual_preservation_file.currentlocation.decode(),
        ),
    ]


@pytest.fixture
def secondary_manual_preservation_file(sip):
    location = b"%SIPDirectory%objects/manualNormalization/preservation/file_1.wav"
    return models.File.objects.create(
        sip=sip, currentlocation=location, originallocation=location
    )


@pytest.mark.django_db
def test_manual_normalization_matches_from_multiple_filenames(
    sip,
    sip_directory_path,
    sip_file,
    manual_preservation_file,
    secondary_manual_preservation_file,
):
    original_file_path = pathlib.Path(sip_file.currentlocation.decode())
    preservation_file_path = pathlib.Path(
        manual_preservation_file.originallocation.decode()
    )
    preservation_file_path_with_no_extension = str(preservation_file_path).rsplit(
        ".", 1
    )[0]

    job = mock.Mock(spec=Job)
    opts = mock.Mock(
        file_uuid=str(sip_file.uuid),
        file_path=str(original_file_path),
        sip_uuid=str(sip.uuid),
        purpose="preservation",
        sip_path=str(sip_directory_path),
        normalize_file_grp_use="original",
    )

    result = normalize.main(job, opts)

    assert result == normalize.SUCCESS
    assert job.print_error.mock_calls == []
    assert job.print_output.mock_calls == [
        mock.call("File found:", sip_file.uuid, sip_file.currentlocation.decode()),
        mock.call(
            "Checking for a manually normalized file by trying to get the"
            f" unique file that matches SIP UUID {sip.uuid} and whose currentlocation"
            f" value starts with this path: {preservation_file_path_with_no_extension}."
        ),
        mock.call(
            f"Multiple files matching path {preservation_file_path_with_no_extension} found. Returning the shortest one."
        ),
        mock.call(f"Returning file at {preservation_file_path}"),
        mock.call(
            original_file_path.name,
            "was already manually normalized into",
            manual_preservation_file.currentlocation.decode(),
        ),
    ]


@pytest.fixture
def default_preservation_rule(fpcommand, format_version):
    return fprmodels.FPRule.objects.create(
        purpose="default_preservation", command=fpcommand, format=format_version
    )


@pytest.mark.django_db
@mock.patch(
    "transcoder.CommandLinker", return_value=mock.Mock(**{"execute.return_value": 0})
)
def test_normalization_falls_back_to_default_rule(
    command_linker,
    sip,
    sip_directory_path,
    sip_file,
    task,
    fpcommand,
    default_preservation_rule,
):
    original_file_path = pathlib.Path(sip_file.currentlocation.decode())
    expected_manually_normalized_file_path = (
        original_file_path.parent
        / "manualNormalization"
        / "preservation"
        / original_file_path.name.replace("".join(original_file_path.suffixes), "")
    )
    job = mock.Mock(spec=Job)
    opts = mock.Mock(
        file_uuid=str(sip_file.uuid),
        file_path=str(original_file_path),
        sip_uuid=str(sip.uuid),
        task_uuid=str(task.taskuuid),
        purpose="preservation",
        sip_path=str(sip_directory_path),
        normalize_file_grp_use="original",
    )

    result = normalize.main(job, opts)

    assert result == normalize.SUCCESS
    command_linker.assert_called_once()
    assert job.print_error.mock_calls == []
    assert job.print_output.mock_calls == [
        mock.call("File found:", sip_file.uuid, sip_file.currentlocation.decode()),
        mock.call(
            "Checking for a manually normalized file by trying to get the"
            f" unique file that matches SIP UUID {sip.uuid} and whose currentlocation"
            f" value starts with this path: {expected_manually_normalized_file_path}."
        ),
        mock.call("No such file found."),
        mock.call(
            original_file_path.name,
            "not identified or without rule",
            "- Falling back to default",
            opts.purpose,
            "rule",
        ),
        mock.call("Format Policy Rule:", default_preservation_rule),
        mock.call("Format Policy Command", fpcommand.description),
        mock.call(
            "Successfully normalized ", original_file_path.name, "for", opts.purpose
        ),
    ]


@pytest.mark.django_db
@mock.patch(
    "transcoder.CommandLinker", return_value=mock.Mock(**{"execute.return_value": 0})
)
def test_normalization_finds_rule_by_file_format_version(
    command_linker,
    sip,
    sip_directory_path,
    sip_file,
    task,
    fpcommand,
    format_version,
    sip_file_format_version,
    fprule_preservation,
):
    original_file_path = pathlib.Path(sip_file.currentlocation.decode())
    expected_manually_normalized_file_path = (
        original_file_path.parent
        / "manualNormalization"
        / "preservation"
        / original_file_path.name.replace("".join(original_file_path.suffixes), "")
    )
    job = mock.Mock(spec=Job)
    opts = mock.Mock(
        file_uuid=str(sip_file.uuid),
        file_path=str(original_file_path),
        sip_uuid=str(sip.uuid),
        task_uuid=str(task.taskuuid),
        purpose="preservation",
        sip_path=str(sip_directory_path),
        normalize_file_grp_use="original",
    )

    result = normalize.main(job, opts)

    assert result == normalize.SUCCESS
    command_linker.assert_called_once()
    assert job.print_error.mock_calls == []
    assert job.print_output.mock_calls == [
        mock.call("File found:", sip_file.uuid, sip_file.currentlocation.decode()),
        mock.call(
            "Checking for a manually normalized file by trying to get the"
            f" unique file that matches SIP UUID {sip.uuid} and whose currentlocation"
            f" value starts with this path: {expected_manually_normalized_file_path}."
        ),
        mock.call("No such file found."),
        mock.call("File format:", format_version),
        mock.call("Format Policy Rule:", fprule_preservation),
        mock.call("Format Policy Command", fpcommand.description),
        mock.call(
            "Successfully normalized ", original_file_path.name, "for", opts.purpose
        ),
    ]
