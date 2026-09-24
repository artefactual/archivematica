"""Publish retrieved transfers into internal shared directories.

Publication is the boundary where staged content becomes visible to an
Archivematica workflow.  The boundary maintains these invariants:

* names used by NFS refresh links can never be published as transfers;
* destination selection and rename are serialized across hosts when the
  shared filesystem supports ``StrictSoftFileLock``;
* the destination directory is refreshed before collision checks so stale NFS
  negative lookups cannot permit an overwrite;
* metadata is reserved after the final destination is known and before the
  rename makes content visible; and
* a failed rename rolls back a completed metadata reservation before the lock
  is released.

Locks are sharded rather than created per transfer, and padded forms of a name
share their original name's shard.  A refresh hard link in the destination
directory invalidates stale NFS directory metadata while the lock is held.

``StrictSoftFileLock`` claims may themselves be stale.  Publication deliberately
does not try to break such claims: after the accepted five-second wait, it uses
a UUID-suffixed destination instead.  This availability tradeoff can leave an
unnecessarily unique transfer name, but it cannot overwrite existing content.
"""

import hashlib
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from typing import TypeAlias
from uuid import uuid4

from filelock import StrictSoftFileLock

__all__ = [
    "DESTINATION_REFRESH_PREFIX",
    "PublicationMetadata",
    "TransferSourceRetrievalError",
    "TransferSourceRetrievalResult",
    "check_retrieved_path_exists",
    "is_destination_refresh_name",
    "move_to_internal_shared_dir",
    "pad_destination_path_if_it_already_exists",
    "validate_destination_name",
]

LOGGER = logging.getLogger(__name__)

# Destination locks live on the shared filesystem so different hosts coordinate.
DESTINATION_LOCK_DIRECTORY = ".transfer-move-locks"
DESTINATION_LOCK_SHARDS = 64
DESTINATION_LOCK_TIMEOUT = 5.0
DESTINATION_REFRESH_PREFIX = ".transfer-move-refresh-"
DESTINATION_REFRESH_NAME = re.compile(
    rf"{re.escape(DESTINATION_REFRESH_PREFIX)}[0-9a-f]{{32}}"
)
DEFAULT_NAME_MAX = 255
NUMERIC_PADDING_SUFFIX = re.compile(r"(?:_[0-9]+)+$")
StrPath: TypeAlias = str | os.PathLike[str]


class TransferSourceRetrievalError(Exception):
    """Raised when transfer retrieval or publication cannot complete."""


@dataclass(frozen=True)
class TransferSourceRetrievalResult:
    """The filesystem and database paths of a published transfer."""

    final_path: str
    current_location: str


class PublicationMetadata(Protocol):
    """Metadata transaction coordinated with filesystem publication."""

    def reserve(self, result: TransferSourceRetrievalResult) -> None:
        """Persist the selected destination before it becomes visible."""
        ...

    def rollback(self) -> None:
        """Undo a completed reservation after publication fails."""
        ...


def is_destination_refresh_name(name: str) -> bool:
    """Return whether a name is reserved for internal move coordination."""
    return DESTINATION_REFRESH_NAME.fullmatch(name) is not None


def validate_destination_name(name: str) -> None:
    """Reject names that watched-directory consumers treat as metadata."""
    if is_destination_refresh_name(name):
        raise TransferSourceRetrievalError(
            f"Transfer name {name!r} is reserved for internal move coordination."
        )


def pad_destination_path_if_it_already_exists(
    filepath: StrPath, original: StrPath | None = None, attempt: int = 0
) -> Path:
    """Return a path that does not yet exist, padding with numbers as needed."""
    if original is None:
        original = filepath
    filepath = Path(filepath)
    original = Path(original)

    attempt = attempt + 1
    if not filepath.exists():
        return filepath
    if filepath.is_dir():
        return pad_destination_path_if_it_already_exists(
            f"{original.as_posix()}_{attempt}",
            original,
            attempt,
        )

    basedirectory = original.parent
    basename = original.name
    period_position = basename.index(".")
    non_extension = basename[0:period_position]
    extension = basename[period_position:]
    new_basename = f"{non_extension}_{attempt}{extension}"
    new_filepath = basedirectory / new_basename
    return pad_destination_path_if_it_already_exists(new_filepath, original, attempt)


def _destination_lock_path(destination: Path, shared_directory: StrPath) -> Path:
    """Return a bounded lock path shared by a destination's padded names."""
    lock_directory = Path(shared_directory) / "tmp" / DESTINATION_LOCK_DIRECTORY
    relative_destination = Path(os.path.relpath(destination, start=shared_directory))
    family_name = NUMERIC_PADDING_SUFFIX.sub("", relative_destination.name)
    stem, separator, extension = family_name.partition(".")
    family_name = f"{NUMERIC_PADDING_SUFFIX.sub('', stem)}{separator}{extension}"
    family_destination = relative_destination.parent / family_name
    digest = hashlib.sha256(os.fsencode(family_destination)).digest()
    lock_name = f"{digest[0] % DESTINATION_LOCK_SHARDS:02x}"
    return lock_directory / lock_name


def _acquire_destination_lock(
    destination: Path, shared_directory: StrPath
) -> StrictSoftFileLock | None:
    """Acquire an NFS-safe lock, or return ``None`` to use a unique path."""
    lock_path = _destination_lock_path(destination, shared_directory)
    try:
        lock_path.parent.mkdir(mode=0o770, parents=True, exist_ok=True)
        lock = StrictSoftFileLock(
            lock_path,
            mode=0o660,
            timeout=DESTINATION_LOCK_TIMEOUT,
        )
        lock.acquire()
    except Exception as err:
        LOGGER.warning(
            "Unable to acquire destination lock %s; using a unique destination: %s",
            lock_path,
            err,
        )
        return None
    return lock


def _release_destination_lock(lock: StrictSoftFileLock) -> None:
    """Release a destination lock without turning cleanup into a move failure."""
    try:
        lock.release()
    except Exception:
        LOGGER.exception("Unable to release destination lock %s", lock.lock_file)


def _refresh_destination_directory(destination: Path, lock: StrictSoftFileLock) -> None:
    """Refresh cached NFS directory metadata before inspecting destinations."""
    refresh_path = destination.parent / f"{DESTINATION_REFRESH_PREFIX}{uuid4().hex}"
    try:
        # LINK is an atomic server-side directory mutation on NFS. Its response
        # updates this client's parent-directory change attributes, invalidating
        # negative dentries cached before the previous lock holder's rename.
        os.link(lock.lock_file, refresh_path)
    except (NotImplementedError, OSError) as err:
        raise TransferSourceRetrievalError(
            f"Unable to refresh destination directory {destination.parent}: {err}"
        ) from err

    try:
        refresh_path.unlink()
    except OSError:
        # The reserved prefix is ignored by watched-directory consumers, so a
        # cleanup failure must not turn a safely coordinated move into a retry.
        LOGGER.exception("Unable to remove destination refresh link %s", refresh_path)


def _truncate_to_byte_length(
    value: str, maximum: int, *, keep_end: bool = False
) -> str:
    """Truncate a filename fragment without splitting encoded characters."""
    while len(os.fsencode(value)) > maximum:
        value = value[1:] if keep_end else value[:-1]
    return value


def _destination_name_max(destination: Path) -> int:
    """Return the destination filesystem's maximum component length."""
    try:
        maximum = os.pathconf(destination.parent, "PC_NAME_MAX")
    except (OSError, ValueError):
        return DEFAULT_NAME_MAX
    return maximum if maximum > 0 else DEFAULT_NAME_MAX


def _unique_destination_path(source: Path, destination: Path) -> Path:
    """Return a unique destination that fits the filesystem component limit."""
    maximum = _destination_name_max(destination)
    suffix = f"_{uuid4().hex}"
    if len(os.fsencode(suffix)) > maximum:
        suffix = _truncate_to_byte_length(suffix, maximum)

    period_position = destination.name.find(".")
    if source.is_dir() or period_position == -1:
        stem = destination.name
        extension = ""
    else:
        stem = destination.name[:period_position]
        extension = destination.name[period_position:]

    remaining = maximum - len(os.fsencode(suffix))
    if len(os.fsencode(extension)) > remaining:
        if extension.startswith(".") and remaining > 0:
            extension = "." + _truncate_to_byte_length(
                extension[1:], remaining - 1, keep_end=True
            )
        else:
            extension = _truncate_to_byte_length(extension, remaining, keep_end=True)
        stem = ""
    else:
        stem = _truncate_to_byte_length(stem, remaining - len(os.fsencode(extension)))

    return destination.with_name(f"{stem}{suffix}{extension}")


def check_retrieved_path_exists(filepath: StrPath) -> str | None:
    """Return a validation error for unsafe or unavailable retrieved paths."""
    filepath = str(filepath)
    if filepath == "":
        return "No filepath provided."
    if not os.path.exists(filepath):
        return f"Filepath {filepath} does not exist."
    if ".." in filepath:
        return "Illegal path."
    return None


def move_to_internal_shared_dir(
    filepath: StrPath,
    dest: StrPath,
    shared_directory: str,
    metadata: PublicationMetadata | None = None,
) -> TransferSourceRetrievalResult:
    """Reserve metadata and atomically publish staged content under a lock."""
    error = check_retrieved_path_exists(filepath)
    if error:
        raise TransferSourceRetrievalError(error)

    filepath = Path(filepath)
    dest = Path(dest)
    validate_destination_name(filepath.name)
    original_destination = dest / filepath.name
    lock = _acquire_destination_lock(original_destination, shared_directory)
    try:
        if lock is None:
            destination = _unique_destination_path(filepath, original_destination)
        else:
            _refresh_destination_directory(original_destination, lock)
            destination = pad_destination_path_if_it_already_exists(
                original_destination
            )

        result = TransferSourceRetrievalResult(
            final_path=destination.as_posix(),
            current_location=destination.as_posix().replace(
                shared_directory, "%sharedPath%", 1
            ),
        )
        if metadata is not None:
            metadata.reserve(result)

        try:
            filepath.rename(destination)
        except OSError as err:
            move_error = TransferSourceRetrievalError(
                f"Error moving from {filepath} to {destination}: {err}"
            )
            if metadata is not None:
                try:
                    metadata.rollback()
                except Exception as rollback_error:
                    raise TransferSourceRetrievalError(
                        f"{move_error} Metadata rollback also failed: {rollback_error}"
                    ) from rollback_error
            raise move_error from err
    finally:
        if lock is not None:
            _release_destination_lock(lock)

    return result
