import json
import pathlib
import subprocess
from unittest import mock

import pytest

from archivematica.dashboard.fpr.models import IDCommand
from archivematica.MCPClient.clientScripts import file_identification


def test_script_backend_adapts_existing_commands_to_batch_contract() -> None:
    command = IDCommand(
        script_type="pythonScript",
        script="print('fmt/1')",
    )
    execute_command = mock.Mock(
        side_effect=[
            (0, "fmt/1\n", ""),
            (1, "", "identification failed"),
        ]
    )
    backend = file_identification.ScriptIdentificationBackend(command, execute_command)

    results = backend.identify_many(
        [
            file_identification.IdentificationRequest("/first"),
            file_identification.IdentificationRequest("/second"),
        ]
    )

    assert results == [
        file_identification.IdentificationResult.identified("fmt/1"),
        file_identification.IdentificationResult.failed(
            f"Error: IDCommand with UUID {command.uuid} exited non-zero.",
            "Error: identification failed",
        ),
    ]


def test_fido_identifies_many_in_one_process_and_preserves_duplicates(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "duplicate"
    path.touch()
    run_command = mock.Mock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="1\t1\tfmt/1\n2\t1\tfmt/2\n",
            stderr="",
        )
    )
    backend = file_identification.FidoCLIIdentificationBackend(run_command=run_command)

    results = backend.identify_many(
        [
            file_identification.IdentificationRequest(str(path)),
            file_identification.IdentificationRequest(str(path)),
        ]
    )

    assert results == [
        file_identification.IdentificationResult.identified("fmt/1"),
        file_identification.IdentificationResult.identified("fmt/2"),
    ]
    command = run_command.call_args.args[0]
    assert command[0] == "fido"
    assert command[-2:] == [str(path), str(path)]
    run_command.assert_called_once()


def test_fido_correlates_results_after_missing_files(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "available"
    path.touch()
    missing_path = tmp_path / "missing"
    run_command = mock.Mock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="1\t1\tfmt/1\n",
            stderr="",
        )
    )
    backend = file_identification.FidoCLIIdentificationBackend(run_command=run_command)

    results = backend.identify_many(
        [
            file_identification.IdentificationRequest(str(missing_path)),
            file_identification.IdentificationRequest(str(path)),
        ]
    )

    assert results[0].errors == (
        f"Error: File does not exist or is not a regular file: {missing_path}",
    )
    assert results[1] == file_identification.IdentificationResult.identified("fmt/1")
    assert run_command.call_args.args[0][-1] == str(path)


def test_fido_uses_text_fallback_for_an_unidentified_file(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "text"
    path.touch()
    run_command = mock.Mock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="1\t0\t\n",
            stderr="",
        )
    )
    text_fallback = mock.Mock(return_value=file_identification.TEXT_PUID)
    backend = file_identification.FidoCLIIdentificationBackend(
        run_command=run_command,
        text_fallback=text_fallback,
    )

    assert backend.identify_many(
        [file_identification.IdentificationRequest(str(path))]
    ) == [
        file_identification.IdentificationResult.identified(
            file_identification.TEXT_PUID
        )
    ]
    text_fallback.assert_called_once_with(str(path))


def test_file_text_fallback_uses_file_command(
    tmp_path: pathlib.Path,
) -> None:
    """Preserve the historical file(1) text classification."""

    path = tmp_path / "extensionless"
    path.touch()
    process = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="Unicode text, UTF-8 text\n",
        stderr="",
    )

    with mock.patch.object(
        file_identification.subprocess, "run", return_value=process
    ) as run_command:
        result = file_identification._text_fallback(str(path))

    assert result == file_identification.TEXT_PUID
    run_command.assert_called_once_with(
        ["file", "--brief", "--", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_fido_keeps_text_fallback_failure_isolated(
    tmp_path: pathlib.Path,
) -> None:
    """Keep a fallback failure from aborting the remaining batch."""

    unmatched_path = tmp_path / "unmatched"
    unmatched_path.touch()
    identified_path = tmp_path / "identified"
    identified_path.touch()
    run_command = mock.Mock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="1\t0\t\n2\t1\tfmt/1\n",
            stderr="",
        )
    )
    text_fallback = mock.Mock(side_effect=OSError("file failed"))
    backend = file_identification.FidoCLIIdentificationBackend(
        run_command=run_command,
        text_fallback=text_fallback,
    )

    results = backend.identify_many(
        [
            file_identification.IdentificationRequest(str(unmatched_path)),
            file_identification.IdentificationRequest(str(identified_path)),
        ]
    )

    assert results == [
        file_identification.IdentificationResult.failed(
            f"Error: Fido found no matching format for {unmatched_path}; "
            "text detection failed: file failed"
        ),
        file_identification.IdentificationResult.identified("fmt/1"),
    ]


def test_siegfried_identifies_many_in_one_parallel_process(
    tmp_path: pathlib.Path,
) -> None:
    first_path = tmp_path / "first"
    second_path = tmp_path / "second"
    first_path.touch()
    second_path.touch()
    run_command = mock.Mock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "files": [
                        {"errors": "", "matches": [{"id": "fmt/1"}]},
                        {"errors": "", "matches": [{"puid": "fmt/2"}]},
                    ]
                }
            ),
            stderr="",
        )
    )
    backend = file_identification.SiegfriedCLIIdentificationBackend(
        workers=4, run_command=run_command
    )

    results = backend.identify_many(
        [
            file_identification.IdentificationRequest(str(first_path)),
            file_identification.IdentificationRequest(str(second_path)),
        ]
    )

    assert results == [
        file_identification.IdentificationResult.identified("fmt/1"),
        file_identification.IdentificationResult.identified("fmt/2"),
    ]
    assert run_command.call_args.args[0] == [
        "sf",
        "-json",
        "-multi",
        "4",
        str(first_path),
        str(second_path),
    ]
    run_command.assert_called_once()


def test_siegfried_reports_per_file_errors(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "file"
    path.touch()
    run_command = mock.Mock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"files": [{"errors": "permission denied", "matches": []}]}
            ),
            stderr="",
        )
    )
    backend = file_identification.SiegfriedCLIIdentificationBackend(
        workers=1, run_command=run_command
    )

    [result] = backend.identify_many(
        [file_identification.IdentificationRequest(str(path))]
    )

    assert result.errors == (
        f"Error: Siegfried could not identify {path}: permission denied",
    )


def test_pygfried_loads_archivematica_profile_scanner() -> None:
    scanner = mock.Mock()
    scanner_type = mock.Mock(return_value=scanner)
    pygfried = mock.Mock(Scanner=scanner_type)
    file_identification._load_pygfried_scanner.cache_clear()

    try:
        with mock.patch.dict("sys.modules", {"pygfried": pygfried}):
            loaded_scanner = file_identification._load_pygfried_scanner()
    finally:
        file_identification._load_pygfried_scanner.cache_clear()

    assert loaded_scanner is scanner
    scanner_type.assert_called_once_with(profile="archivematica")


def test_pygfried_calls_scanner_once_without_a_subprocess(
    tmp_path: pathlib.Path,
) -> None:
    first_path = tmp_path / "first"
    second_path = tmp_path / "second"
    first_path.write_bytes(b"\x89PNG\r\n")
    second_path.touch()
    scanner = mock.Mock()
    scanner.identify_many.return_value = {
        "files": [
            {"errors": "", "matches": [{"id": "fmt/11"}]},
            {"errors": "", "matches": [{"id": "fmt/12"}]},
        ]
    }
    backend = file_identification.PygfriedIdentificationBackend(
        workers=3,
        scanner=scanner,
    )

    with mock.patch.object(file_identification.subprocess, "run") as run_command:
        results = backend.identify_many(
            [
                file_identification.IdentificationRequest(str(first_path)),
                file_identification.IdentificationRequest(str(second_path)),
            ]
        )

    assert results == [
        file_identification.IdentificationResult.identified("fmt/11"),
        file_identification.IdentificationResult.identified("fmt/12"),
    ]
    scanner.identify_many.assert_called_once_with(
        [str(first_path), str(second_path)], workers=3
    )
    run_command.assert_not_called()


@pytest.mark.parametrize(
    ("backend_name", "backend_type"),
    [
        (
            IDCommand.Backend.FIDO,
            file_identification.FidoCLIIdentificationBackend,
        ),
        (
            IDCommand.Backend.SIEGFRIED,
            file_identification.SiegfriedCLIIdentificationBackend,
        ),
        (
            IDCommand.Backend.PYGFRIED,
            file_identification.PygfriedIdentificationBackend,
        ),
    ],
)
def test_backend_selection(
    backend_name: str,
    backend_type: type[file_identification.IdentificationBackend],
) -> None:
    command = IDCommand(script_type=backend_name)

    backend = file_identification.get_identification_backend(
        command,
        execute_command=mock.Mock(),
        workers=2,
    )

    assert isinstance(backend, backend_type)
