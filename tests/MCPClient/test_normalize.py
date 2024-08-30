import argparse
import pathlib
import uuid
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple
from unittest import mock

import normalize
import pytest
import pytest_django
from client.job import Job
from fpr import models as fprmodels
from main import models


@pytest.mark.django_db
def test_thumbnail_mode_disables_thumbnail_generation() -> None:
    job = mock.Mock(
        args=[
            "normalize.py",
            "thumbnail",
            "file_uuid_not_used",
            "file_path_not_used",
            "sip_path_not_used",
            "sip_uuid_not_used",
            "task_uuid_not_used",
            "normalize_file_grp_use_not_used",
            "--thumbnail_mode=do_not_generate",
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    normalize.call([job])

    job.set_status.assert_called_once_with(normalize.SUCCESS)
    job.pyprint.assert_called_once_with("Thumbnail generation has been disabled")


@pytest.mark.django_db
def test_normalization_fails_if_original_file_does_not_exist() -> None:
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
    sip_file: models.File,
) -> None:
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
def test_normalization_skips_file_if_group_use_does_not_match(
    sip_file: models.File,
) -> None:
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
def manual_preservation_file(preservation_file: models.File) -> models.File:
    preservation_file.originallocation = (
        b"%SIPDirectory%objects/manualNormalization/preservation/file.wav"
    )
    preservation_file.currentlocation = (
        b"%SIPDirectory%objects/manualNormalization/preservation/file.wav"
    )
    preservation_file.save()

    return preservation_file


@pytest.fixture
def normalization_csv(
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    manual_preservation_file: models.File,
) -> pathlib.Path:
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
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    normalization_csv: pathlib.Path,
    sip_file: models.File,
    manual_preservation_file: models.File,
) -> None:
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


@pytest.mark.django_db
def test_manual_normalization_fails_with_invalid_normalization_csv(
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    invalid_normalization_csv: pathlib.Path,
    sip_file: models.File,
    manual_preservation_file: models.File,
) -> None:
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
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    manual_preservation_file: models.File,
) -> None:
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
def secondary_manual_preservation_file(sip: models.SIP) -> models.File:
    location = b"%SIPDirectory%objects/manualNormalization/preservation/file_1.wav"
    return models.File.objects.create(
        sip=sip, currentlocation=location, originallocation=location
    )


@pytest.mark.django_db
def test_manual_normalization_matches_from_multiple_filenames(
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    manual_preservation_file: models.File,
    secondary_manual_preservation_file: models.File,
) -> None:
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
def default_preservation_rule(
    fpcommand: fprmodels.FPCommand, format_version: fprmodels.FormatVersion
) -> fprmodels.FPRule:
    return fprmodels.FPRule.objects.create(
        purpose="default_preservation", command=fpcommand, format=format_version
    )


@pytest.mark.django_db
@mock.patch(
    "transcoder.CommandLinker", return_value=mock.Mock(**{"execute.return_value": 0})
)
def test_normalization_falls_back_to_default_rule(
    command_linker: mock.Mock,
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    task: models.Task,
    fpcommand: fprmodels.FPCommand,
    default_preservation_rule: fprmodels.FPRule,
) -> None:
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
    command_linker: mock.Mock,
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    task: models.Task,
    fpcommand: fprmodels.FPCommand,
    format_version: fprmodels.FormatVersion,
    sip_file_format_version: models.FileFormatVersion,
    fprule_preservation: fprmodels.FPRule,
) -> None:
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


@pytest.mark.django_db
@mock.patch("os.makedirs", side_effect=OSError("error!"))
@mock.patch(
    "transcoder.CommandLinker", return_value=mock.Mock(**{"execute.return_value": 0})
)
def test_normalization_fails_if_thumbnail_directory_cannot_be_created(
    command_linker: mock.Mock,
    makedirs: mock.Mock,
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    task: models.Task,
    sip_file_format_version: models.FileFormatVersion,
    fprule_thumbnail: fprmodels.FPRule,
) -> None:
    job = mock.Mock(
        args=[
            "normalize.py",
            "thumbnail",
            str(sip_file.uuid),
            "file_path_not_used",
            str(sip_directory_path),
            str(sip.uuid),
            str(task.taskuuid),
            "original",
            "--thumbnail_mode=generate",
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    normalize.call([job])

    job.set_status.assert_called_once_with(1)
    job.print_error.assert_called_once_with("error!")


@pytest.fixture
def fpcommand_thumbnail(
    fpcommand: fprmodels.FPCommand, format_version: fprmodels.FormatVersion
) -> fprmodels.FPCommand:
    fpcommand.output_format = format_version
    fpcommand.output_location = "%outputDirectory%%postfix%.jpg"
    fpcommand.save()

    return fpcommand


@pytest.fixture
def fprule_thumbnail(fprule_thumbnail: fprmodels.FPRule) -> fprmodels.FPRule:
    # Delete existing thumbnail rules except our default fixture.
    fprmodels.FPRule.objects.filter(purpose="thumbnail").exclude(
        uuid=fprule_thumbnail.uuid
    ).delete()

    return fprule_thumbnail


@pytest.mark.django_db
@mock.patch("transcoder.executeOrRun")
def test_normalization_copies_generated_thumbnail_to_shared_thumbnails_directory(
    execute_or_run: mock.Mock,
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    task: models.Task,
    sip_file_format_version: models.FileFormatVersion,
    fprule_thumbnail: fprmodels.FPRule,
    settings: pytest_django.fixtures.SettingsWrapper,
    fpcommand_thumbnail: fprmodels.FPCommand,
    shared_directory_path: pathlib.Path,
) -> None:
    expected_thumbnail_content = b"thumbnail image content"
    expected_thumbnail_suffix = pathlib.Path(fpcommand_thumbnail.output_location).suffix

    def execute_or_run_side_effect(
        type: str,
        text: str,
        stdIn: str = "",
        printing: bool = True,
        arguments: Optional[Sequence[str]] = None,
        env_updates: Optional[Mapping[str, str]] = None,
        capture_output: bool = True,
    ) -> Tuple[int, str, str]:
        """Mock thumbnail generation by creating a new temporary file."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--output-directory", required=True)
        parser.add_argument("--postfix", required=True)
        args, _ = parser.parse_known_args(arguments)

        thumbnail_path = pathlib.Path(args.output_directory, args.postfix).with_suffix(
            expected_thumbnail_suffix
        )
        thumbnail_path.parent.mkdir(parents=True)
        thumbnail_path.write_bytes(expected_thumbnail_content)

        return (0, "success!", "")

    execute_or_run.side_effect = execute_or_run_side_effect

    job = mock.Mock(
        args=[
            "normalize.py",
            "thumbnail",
            str(sip_file.uuid),
            "file_path_not_used",
            str(sip_directory_path),
            str(sip.uuid),
            str(task.taskuuid),
            "original",
            "--thumbnail_mode=generate",
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    assert fprule_thumbnail.count_attempts == 0
    assert fprule_thumbnail.count_okay == 0
    assert fprule_thumbnail.count_not_okay == 0

    normalize.call([job])

    job.set_status.assert_called_once_with(normalize.SUCCESS)

    # The thumbnail was generated in the thumbnails directory of the SIP.
    sip_thumbnails_path = sip_directory_path / "thumbnails"
    sip_thumbnail_path = (sip_thumbnails_path / str(sip_file.uuid)).with_suffix(
        expected_thumbnail_suffix
    )
    assert [f.name for f in sip_thumbnails_path.iterdir()] == [sip_thumbnail_path.name]
    assert sip_thumbnail_path.read_bytes() == expected_thumbnail_content

    # The thumbnail was copied to the thumbnails directory of the shared
    # directory.
    shared_thumbnails_path = shared_directory_path / "www" / "thumbnails"
    shared_thumbnail_path = (
        shared_thumbnails_path / str(sip.uuid) / str(sip_file.uuid)
    ).with_suffix(expected_thumbnail_suffix)
    assert [f.name for f in shared_thumbnails_path.iterdir()] == [
        shared_thumbnail_path.parent.name
    ]
    assert [f.name for f in shared_thumbnail_path.parent.iterdir()] == [
        shared_thumbnail_path.name
    ]
    assert shared_thumbnail_path.read_bytes() == expected_thumbnail_content

    # The attempts counter of the FPRule were updated.
    updated_fprule_thumbnail = fprmodels.FPRule.objects.get(uuid=fprule_thumbnail.uuid)
    assert updated_fprule_thumbnail.count_attempts == 1
    assert updated_fprule_thumbnail.count_okay == 1
    assert updated_fprule_thumbnail.count_not_okay == 0


FALLBACK_THUMBNAIL_COMMAND = "fallback"
VERIFICATION_THUMBNAIL_COMMAND = "verification"
EVENT_DETAIL_THUMBNAIL_COMMAND = "event detail"


@pytest.fixture
def fprule_default_thumbnail(
    fptool: fprmodels.FPTool,
    format_version: fprmodels.FormatVersion,
) -> fprmodels.FPRule:
    fprmodels.FPRule.objects.filter(purpose="default_thumbnail").delete()

    return fprmodels.FPRule.objects.create(
        purpose="default_thumbnail",
        command=fprmodels.FPCommand.objects.create(
            script_type="bashScript",
            command=FALLBACK_THUMBNAIL_COMMAND,
            tool=fptool,
            output_location="%outputDirectory%%postfix%.jpg",
            output_format=format_version,
            verification_command=fprmodels.FPCommand.objects.create(
                command=VERIFICATION_THUMBNAIL_COMMAND, tool=fptool
            ),
            event_detail_command=fprmodels.FPCommand.objects.create(
                command=EVENT_DETAIL_THUMBNAIL_COMMAND, tool=fptool
            ),
        ),
        format=format_version,
    )


@pytest.mark.django_db
@mock.patch("transcoder.executeOrRun")
def test_normalization_fallbacks_to_default_thumbnail_rule_if_initial_command_fails(
    execute_or_run: mock.Mock,
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    task: models.Task,
    sip_file_format_version: models.FileFormatVersion,
    fprule_thumbnail: fprmodels.FPRule,
    fpcommand_thumbnail: fprmodels.FPCommand,
    fprule_default_thumbnail: fprmodels.FPRule,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    expected_thumbnail_content = b"thumbnail image content"
    expected_thumbnail_path = (
        sip_directory_path / "thumbnails" / str(sip_file.uuid)
    ).with_suffix(pathlib.Path(fprule_default_thumbnail.command.output_location).suffix)

    def execute_or_run_side_effect(
        type: str,
        text: str,
        stdIn: str = "",
        printing: bool = True,
        arguments: Optional[Sequence[str]] = None,
        env_updates: Optional[Mapping[str, str]] = None,
        capture_output: bool = True,
    ) -> Tuple[int, str, str]:
        """Mock a complex normalization command that initially fails and then
        falls back to its default rule and also runs its own verification and
        event detail commands.
        """
        if text == fprule_thumbnail.command.command:
            return (-1, "", "error!")
        if text == FALLBACK_THUMBNAIL_COMMAND:
            expected_thumbnail_path.parent.mkdir(parents=True)
            expected_thumbnail_path.write_bytes(expected_thumbnail_content)
            return (0, "success!", "")
        elif text == VERIFICATION_THUMBNAIL_COMMAND:
            return (0, "success!", "")
        elif text == EVENT_DETAIL_THUMBNAIL_COMMAND:
            return (0, "success!", "")
        else:
            raise ValueError("unreachable")

    execute_or_run.side_effect = execute_or_run_side_effect

    purpose = "thumbnail"
    file_path = "file_path_not_used"
    job = mock.Mock(
        args=[
            "normalize.py",
            purpose,
            str(sip_file.uuid),
            file_path,
            str(sip_directory_path),
            str(sip.uuid),
            str(task.taskuuid),
            "original",
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    assert fprule_thumbnail.count_attempts == 0
    assert fprule_thumbnail.count_okay == 0
    assert fprule_thumbnail.count_not_okay == 0

    assert fprule_default_thumbnail.count_attempts == 0
    assert fprule_default_thumbnail.count_okay == 0
    assert fprule_default_thumbnail.count_not_okay == 0

    normalize.call([job])

    job.set_status.assert_called_once_with(normalize.SUCCESS)

    # The thumbnail normalization rule fails.
    updated_fprule_thumbnail = fprmodels.FPRule.objects.get(uuid=fprule_thumbnail.uuid)
    assert updated_fprule_thumbnail.count_attempts == 1
    assert updated_fprule_thumbnail.count_okay == 0
    assert updated_fprule_thumbnail.count_not_okay == 1

    # The default thumbnail normalization rule succeeds.
    updated_fprule_default_thumbnail = fprmodels.FPRule.objects.get(
        uuid=fprule_default_thumbnail.uuid
    )
    assert updated_fprule_default_thumbnail.count_attempts == 1
    assert updated_fprule_default_thumbnail.count_okay == 1
    assert updated_fprule_default_thumbnail.count_not_okay == 0

    # Verify the fallback, verification and event detail commands were executed.
    job.print_output.assert_has_calls(
        [
            mock.call(
                purpose,
                "normalization failed, falling back to default",
                purpose,
                "rule",
            ),
            mock.call("Command to execute:", FALLBACK_THUMBNAIL_COMMAND),
            mock.call("Running verification command", mock.ANY),
            mock.call("Command to execute:", VERIFICATION_THUMBNAIL_COMMAND),
            mock.call("Running event detail command", mock.ANY),
            mock.call("Command to execute:", EVENT_DETAIL_THUMBNAIL_COMMAND),
            mock.call("Successfully normalized ", file_path, "for", purpose),
        ],
        any_order=True,
    )


@pytest.mark.django_db
def test_thumbnail_generation_succeeds_if_thumbnail_rule_does_not_exist(
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    sip_file_format_version: models.FileFormatVersion,
    task: models.Task,
) -> None:
    job = mock.Mock(
        args=[
            "normalize.py",
            "thumbnail",
            str(sip_file.uuid),
            "file_path_not_used",
            str(sip_directory_path),
            str(sip.uuid),
            str(task.taskuuid),
            "original",
            "--thumbnail_mode=generate_non_default",
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    normalize.call([job])

    job.set_status.assert_called_once_with(normalize.SUCCESS)
    job.pyprint.assert_any_call("Thumbnail not generated as no rule found for format")


@pytest.fixture
def fpcommand_access(
    fpcommand: fprmodels.FPCommand, format_version: fprmodels.FormatVersion
) -> fprmodels.FPCommand:
    fpcommand.output_format = format_version
    fpcommand.output_location = "%outputDirectory%%postfix%.jpg"
    fpcommand.save()

    return fpcommand


@pytest.mark.django_db
@mock.patch("transcoder.executeOrRun", return_value=(-1, "", "error!"))
def test_normalization_fails_if_fallback_default_rule_does_not_exist(
    execute_or_run: mock.Mock,
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    task: models.Task,
    sip_file_format_version: models.FileFormatVersion,
    fprule_access: fprmodels.FPRule,
    fpcommand_access: fprmodels.FPCommand,
) -> None:
    fprmodels.FPRule.objects.filter(purpose="default_access").delete()

    job = mock.Mock(
        args=[
            "normalize.py",
            "access",
            str(sip_file.uuid),
            "file_path_not_used",
            str(sip_directory_path),
            str(sip.uuid),
            str(task.taskuuid),
            "original",
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    normalize.call([job])

    job.set_status.assert_called_once_with(normalize.RULE_FAILED)
    job.print_output.assert_any_call(
        "Not retrying normalizing for",
        pathlib.Path(sip_file.currentlocation.decode()).name,
        " - No default rule found to normalize for",
        "access",
    )


@pytest.mark.django_db
def test_normalization_deletes_existing_derivatives_on_reingest(
    sip: models.SIP,
    sip_directory_path: pathlib.Path,
    sip_file: models.File,
    sip_file_format_version: models.FileFormatVersion,
    fprule_preservation: fprmodels.FPRule,
    preservation_file: models.File,
    task: models.Task,
) -> None:
    job = mock.Mock(
        args=[
            "normalize.py",
            "preservation",
            str(sip_file.uuid),
            "file_path_not_used",
            str(sip_directory_path),
            str(sip.uuid),
            str(task.taskuuid),
            "original",
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    # Create a derivative file before normalization.
    models.Derivation.objects.create(
        source_file=sip_file, derived_file=preservation_file
    )

    normalize.call([job])

    job.print_output.assert_any_call(
        "preservation",
        "derivative",
        preservation_file.uuid,
        "already exists, marking as deleted",
    )
    # The derivative file was marked as deleted.
    assert models.File.objects.get(uuid=preservation_file.uuid).filegrpuse == "deleted"
    # The existing derivatives were deleted.
    assert models.Derivation.objects.count() == 0
    # A deletion event was added for the derivative file.
    assert models.Event.objects.count() == 1
    assert (
        models.Event.objects.filter(
            file_uuid=preservation_file, event_type="deletion"
        ).count()
        == 1
    )
