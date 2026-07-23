import functools
import importlib.resources
import json
import os
import subprocess
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from typing import Protocol

from archivematica.dashboard.fpr.models import IDCommand

ExecuteCommand = Callable[..., tuple[int, str, str]]
RunCommand = Callable[..., subprocess.CompletedProcess[str]]
TextFallback = Callable[[str], str | None]

TEXT_PUID = "x-fmt/111"
FIDO_MATCH_FORMAT = "%(info.count)s\t%(info.group_index)s\t%(info.puid)s\n"
FIDO_NO_MATCH_FORMAT = "%(info.count)s\t0\t\n"


@dataclass(frozen=True)
class IdentificationRequest:
    """A path submitted to an identification backend."""

    path: str


@dataclass(frozen=True)
class IdentificationResult:
    """The successful identifier or errors returned for one request."""

    output: str | None = None
    errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate that the result represents exactly one outcome."""

        if (self.output is None) == (not self.errors):
            raise ValueError(
                "An identification result must contain either output or errors"
            )

    @classmethod
    def identified(cls, output: str) -> "IdentificationResult":
        """Build a successful identification result."""

        return cls(output=output)

    @classmethod
    def failed(cls, *errors: str) -> "IdentificationResult":
        """Build a failed identification result."""

        return cls(errors=errors)


class IdentificationBackend(Protocol):
    """Batch identification interface implemented by all backends."""

    def identify_many(
        self, requests: Sequence[IdentificationRequest]
    ) -> list[IdentificationResult]:
        """Return one ordered identification result per request."""

        ...


class PygfriedScanner(Protocol):
    """Pygfried scanner surface used by the in-process backend."""

    def identify_many(self, paths: Sequence[str], *, workers: int) -> dict[str, Any]:
        """Return detailed Siegfried-compatible results for each path."""

        ...


class ScriptIdentificationBackend:
    """Compatibility backend for existing FPR identification scripts."""

    def __init__(self, command: IDCommand, execute_command: ExecuteCommand) -> None:
        """Initialize the adapter for an existing FPR command."""

        self.command = command
        self.execute_command = execute_command

    def identify_many(
        self, requests: Sequence[IdentificationRequest]
    ) -> list[IdentificationResult]:
        """Run each legacy script while preserving request order."""

        results = []
        for request in requests:
            exitcode, output, error = self.execute_command(
                self.command.script_type,
                self.command.script,
                arguments=[request.path],
                printing=False,
                capture_output=True,
            )
            if exitcode != 0:
                results.append(
                    IdentificationResult.failed(
                        (
                            "Error: IDCommand with UUID "
                            f"{self.command.uuid} exited non-zero."
                        ),
                        f"Error: {error}",
                    )
                )
                continue

            results.append(IdentificationResult.identified(output.strip()))

        return results


def _text_fallback(path: str) -> str | None:
    """Return the generic text PUID when file(1) reports text."""

    process = subprocess.run(
        ["file", "--brief", "--", path],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        error = process.stderr.strip() or process.stdout.strip()
        raise OSError(error or f"file exited {process.returncode}")
    return TEXT_PUID if "text" in process.stdout.lower() else None


def _unidentified(
    path: str,
    tool_name: str,
    text_fallback: TextFallback,
) -> IdentificationResult:
    """Apply the text fallback or return a tool-specific failure."""

    try:
        fallback = text_fallback(path)
    except OSError as error:
        return IdentificationResult.failed(
            f"Error: {tool_name} found no matching format for {path}; "
            f"text detection failed: {error}"
        )
    if fallback is not None:
        return IdentificationResult.identified(fallback)
    return IdentificationResult.failed(
        f"Error: {tool_name} found no matching format for {path}"
    )


def _partition_existing_files(
    requests: Sequence[IdentificationRequest],
) -> tuple[list[int], list[str], list[IdentificationResult | None]]:
    """Separate regular files while retaining their request positions."""

    indices = []
    paths = []
    results: list[IdentificationResult | None] = [None] * len(requests)
    for index, request in enumerate(requests):
        if not os.path.isfile(request.path):
            results[index] = IdentificationResult.failed(
                f"Error: File does not exist or is not a regular file: {request.path}"
            )
            continue
        indices.append(index)
        paths.append(request.path)
    return indices, paths, results


def _completed_results(
    results: Sequence[IdentificationResult | None],
) -> list[IdentificationResult]:
    """Validate and unwrap a complete ordered result list."""

    if any(result is None for result in results):
        raise ValueError(
            "Identification backend did not produce a result for every file"
        )
    return [result for result in results if result is not None]


def _parse_siegfried_results(
    paths: Sequence[str],
    output: dict[str, Any],
    *,
    tool_name: str,
    text_fallback: TextFallback,
) -> list[IdentificationResult]:
    """Convert Siegfried-compatible output into ordered results."""

    file_results = output.get("files")
    if not isinstance(file_results, list) or len(file_results) != len(paths):
        raise ValueError(f"{tool_name} returned an unexpected number of file results")

    results = []
    for path, file_result in zip(paths, file_results):
        if not isinstance(file_result, dict):
            results.append(
                IdentificationResult.failed(
                    f"Error: {tool_name} returned an invalid result for {path}"
                )
            )
            continue
        if file_result.get("errors"):
            results.append(
                IdentificationResult.failed(
                    f"Error: {tool_name} could not identify {path}: "
                    f"{file_result['errors']}"
                )
            )
            continue

        matches = file_result.get("matches")
        identifier = None
        if isinstance(matches, list) and matches:
            match = matches[0]
            if isinstance(match, dict):
                identifier = match.get("puid") or match.get("id")
        if identifier and identifier != "UNKNOWN":
            results.append(IdentificationResult.identified(str(identifier)))
        else:
            results.append(_unidentified(path, tool_name, text_fallback))

    return results


class FidoCLIIdentificationBackend:
    """Identify a batch after loading Fido signatures in one CLI process."""

    def __init__(
        self,
        run_command: RunCommand = subprocess.run,
        text_fallback: TextFallback = _text_fallback,
    ) -> None:
        """Configure process execution and fallback detection."""

        self.run_command = run_command
        self.text_fallback = text_fallback

    def identify_many(
        self, requests: Sequence[IdentificationRequest]
    ) -> list[IdentificationResult]:
        """Identify all regular files in one Fido process."""

        indices, paths, results = _partition_existing_files(requests)
        if not paths:
            return _completed_results(results)

        extensions = (
            importlib.resources.files("archivematica.archivematicaCommon")
            / "externals"
            / "fido"
            / "archivematica_format_extensions.xml"
        )
        process = self.run_command(
            [
                "fido",
                "-q",
                "-bufsize",
                "1048576",
                "-loadformats",
                str(extensions),
                "-matchprintf",
                FIDO_MATCH_FORMAT,
                "-nomatchprintf",
                FIDO_NO_MATCH_FORMAT,
                *paths,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode != 0:
            error = process.stderr.strip() or process.stdout.strip()
            for index in indices:
                results[index] = IdentificationResult.failed(
                    f"Error: Fido exited non-zero: {error}"
                )
            return _completed_results(results)

        matches: dict[int, str] = {}
        for line in process.stdout.splitlines():
            fields = line.split("\t", 2)
            if len(fields) != 3:
                raise ValueError(f"Fido returned unexpected output: {line}")
            count, group_index, puid = fields
            result_index = int(count) - 1
            if not 0 <= result_index < len(paths):
                raise ValueError(f"Fido returned an invalid result index: {count}")
            if group_index == "1":
                matches[result_index] = puid

        for result_index, (request_index, path) in enumerate(zip(indices, paths)):
            puid = matches.get(result_index)
            if puid:
                results[request_index] = IdentificationResult.identified(puid)
            else:
                results[request_index] = _unidentified(path, "Fido", self.text_fallback)

        return _completed_results(results)


class SiegfriedCLIIdentificationBackend:
    """Identify a batch in one parallel Siegfried CLI process."""

    def __init__(
        self,
        workers: int,
        run_command: RunCommand = subprocess.run,
        text_fallback: TextFallback = _text_fallback,
    ) -> None:
        """Configure worker count, process execution, and fallback detection."""

        self.workers = max(1, workers)
        self.run_command = run_command
        self.text_fallback = text_fallback

    def identify_many(
        self, requests: Sequence[IdentificationRequest]
    ) -> list[IdentificationResult]:
        """Identify all regular files in one parallel Siegfried process."""

        indices, paths, results = _partition_existing_files(requests)
        if not paths:
            return _completed_results(results)

        process = self.run_command(
            ["sf", "-json", "-multi", str(self.workers), *paths],
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode != 0:
            error = process.stderr.strip() or process.stdout.strip()
            for index in indices:
                results[index] = IdentificationResult.failed(
                    f"Error: Siegfried exited non-zero: {error}"
                )
            return _completed_results(results)

        batch_results = _parse_siegfried_results(
            paths,
            json.loads(process.stdout),
            tool_name="Siegfried",
            text_fallback=self.text_fallback,
        )
        for request_index, result in zip(indices, batch_results):
            results[request_index] = result

        return _completed_results(results)


@functools.cache
def _load_pygfried_scanner() -> PygfriedScanner:
    """Import Pygfried and cache an Archivematica-profile scanner."""

    # Keep the Go extension out of MCPClient processes unless this backend is
    # selected. Reuse the scanner and its loaded signature across batches.
    from pygfried import Scanner

    return Scanner(profile="archivematica")


class PygfriedIdentificationBackend:
    """Identify a batch in process using Pygfried's Go-side concurrency."""

    def __init__(
        self,
        workers: int,
        scanner: PygfriedScanner | None = None,
        text_fallback: TextFallback = _text_fallback,
    ) -> None:
        """Configure worker count and an optional injectable scanner."""

        self.workers = max(1, workers)
        self._scanner = scanner
        self.text_fallback = text_fallback

    def identify_many(
        self, requests: Sequence[IdentificationRequest]
    ) -> list[IdentificationResult]:
        """Identify all regular files with one Pygfried batch call."""

        indices, paths, results = _partition_existing_files(requests)
        if not paths:
            return _completed_results(results)

        scanner = (
            self._scanner if self._scanner is not None else _load_pygfried_scanner()
        )
        output = scanner.identify_many(paths, workers=self.workers)
        batch_results = _parse_siegfried_results(
            paths,
            output,
            tool_name="Pygfried",
            text_fallback=self.text_fallback,
        )
        for request_index, result in zip(indices, batch_results):
            results[request_index] = result

        return _completed_results(results)


def get_identification_backend(
    command: IDCommand,
    *,
    execute_command: ExecuteCommand,
    workers: int,
) -> IdentificationBackend:
    """Build the backend selected by an FPR identification command."""

    if command.backend == IDCommand.Backend.LEGACY:
        return ScriptIdentificationBackend(command, execute_command)
    if command.backend == IDCommand.Backend.FIDO:
        return FidoCLIIdentificationBackend()
    if command.backend == IDCommand.Backend.SIEGFRIED:
        return SiegfriedCLIIdentificationBackend(workers)
    if command.backend == IDCommand.Backend.PYGFRIED:
        return PygfriedIdentificationBackend(workers)
    raise ValueError(f"Unsupported identification backend: {command.backend}")
