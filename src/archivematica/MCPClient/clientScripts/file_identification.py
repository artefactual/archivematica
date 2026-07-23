from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from archivematica.dashboard.fpr.models import IDCommand

ExecuteCommand = Callable[..., tuple[int, str, str]]


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
