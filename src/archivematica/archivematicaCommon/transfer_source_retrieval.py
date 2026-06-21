"""Retrieve transfer selections from Storage Service transfer sources.

Archivematica creates transfers from a path selected in a Storage Service
transfer source. Retrieval is the handoff between two systems that describe
paths differently:

* Storage Service receives a source selection as either ``<location UUID>:<path>``
  or a legacy unqualified path. The path points inside a transfer-source
  location.
* Storage Service copies that selection into Archivematica's shared temporary
  directory. Archive selections copy one file; directory selections copy the
  contents of the directory.
* Archivematica then moves the copied result from the temporary directory into
  an internal workflow directory, such as the processing directory or a watched
  transfer directory.
* Database rows store internal paths using ``%sharedPath%`` instead of the
  absolute shared-directory root, so those paths remain portable across
  components.

This module contains the shared mechanics needed before a workflow can process
the transfer:

* ``LocationPath`` splits ``<location UUID>:<path>`` selections while still
  accepting older unqualified paths.
* ``plan_transfer_source_paths()`` decides the three paths used during
  retrieval: what Storage Service should copy, where it should copy it in the
  shared temporary directory, and which copied path Archivematica should move
  into processing.
* ``build_transfer_source_copy_files()`` converts selected paths into the
  grouped ``copy_files()`` payload expected by Storage Service.
* ``copy_transfer_source_files()`` calls Storage Service and reports copy
  failures as ``TransferSourceRetrievalError``.
* ``move_to_internal_shared_dir()`` moves the copied transfer into an internal
  Archivematica directory, avoiding destination collisions and returning the
  ``%sharedPath%`` form stored in the database.
* The ``TransferSource*`` dataclasses and ``Storage*`` typed dictionaries name
  the values passed between those steps.

MCPServer uses these helpers to preserve the legacy package-creation path, and
MCPClient uses the same behavior in the API-created transfer retrieval workflow.
Keeping the behavior here prevents the two components from disagreeing about
archive selections, directory selections, default transfer-source lookup,
destination names, collision handling, or database locations.
"""

import os
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from typing import TypeAlias
from typing import TypedDict

# Archive selections are copied as one file; directory selections copy contents.
ARCHIVE_EXTENSIONS = (".zip", ".tgz", ".tar.gz")
# Path values accepted by ``Path(...)`` and ``str(...)``.
StrPath: TypeAlias = str | os.PathLike[str]


class StorageLocation(TypedDict):
    """Storage Service location data used by transfer-source retrieval."""

    uuid: str
    path: str


class TransferSourceCopyFile(TypedDict):
    """One file copy request in the Storage Service API format."""

    source: str
    destination: str


class TransferSourceCopyGroup(TypedDict):
    """Copy requests grouped under one transfer-source location."""

    location: StorageLocation
    files: list[TransferSourceCopyFile]


class StorageService(Protocol):
    """Small Storage Service module surface needed by retrieval helpers."""

    def get_first_location(self, purpose: str) -> StorageLocation: ...

    def get_location(self, purpose: str) -> list[StorageLocation]: ...

    def get_default_location(self, purpose: str) -> StorageLocation: ...

    def copy_files(
        self,
        source_location: StorageLocation,
        destination_location: StorageLocation,
        files: list[TransferSourceCopyFile],
    ) -> tuple[object | None, object | None]: ...


class TransferSourceRetrievalError(Exception):
    """Raised when transfer-source retrieval cannot complete."""


@dataclass(frozen=True)
class TransferSourcePathPlan:
    """Paths needed to retrieve one transfer-source selection."""

    copy_destination_relative: str
    copied_path: str
    copy_source: str


@dataclass(frozen=True)
class TransferSourceRetrievalResult:
    """Result of retrieving one transfer-source selection."""

    final_path: str
    current_location: str


class LocationPath:
    """Split ``<location UUID>:<path>`` while accepting unqualified paths."""

    uuid: str | None
    path: str
    sep: str

    def __init__(self, path: str, sep: str = ":") -> None:
        self.sep = sep
        parts = path.partition(self.sep)
        if parts[1] != self.sep:
            self.uuid = None
            self.path = parts[0]
        else:
            self.uuid = parts[0]
            self.path = parts[2]

    def __repr__(self) -> str:
        return (
            f"{self.__class__} "
            f"(uuid={self.uuid!r}, sep={self.sep!r}, path={self.path!r})"
        )

    def parts(self) -> tuple[str | None, str]:
        """Return the optional location UUID and the location-relative path."""
        return self.uuid, self.path


def file_is_archive(filepath: str) -> bool:
    """Return whether a transfer selection uses supported archive semantics."""
    return filepath.lower().endswith(ARCHIVE_EXTENSIONS)


def plan_transfer_source_paths(
    name: str, path: str, tmpdir: str, shared_directory: str
) -> TransferSourcePathPlan:
    """Plan source, staging, and Storage Service destination paths without I/O."""
    if file_is_archive(path):
        transfer_dir = tmpdir
        source_path = LocationPath(path).path
        copied_path = os.path.join(tmpdir, os.path.basename(source_path))
        copy_source = path
    else:
        copy_source = os.path.join(path, ".")  # Copy contents of dir but not dir
        transfer_dir = copied_path = os.path.join(tmpdir, name)

    return TransferSourcePathPlan(
        copy_destination_relative=transfer_dir.replace(shared_directory, "", 1),
        copied_path=copied_path,
        copy_source=copy_source,
    )


def build_transfer_source_copy_files(
    paths: Sequence[str],
    relative_destination: str,
    processing_location: StorageLocation,
    transfer_sources: Sequence[StorageLocation],
    default_location_uuid: str | None = None,
    default_location_uuid_factory: Callable[[], str] | None = None,
) -> dict[str, TransferSourceCopyGroup]:
    """Group Storage Service copy specifications by transfer-source location."""
    files: dict[str, TransferSourceCopyGroup] = {
        ts["uuid"]: {"location": ts, "files": []} for ts in transfer_sources
    }

    for item in paths:
        location, path = LocationPath(item).parts()
        if location is None:
            # Avoid the Storage Service default lookup for explicitly qualified paths.
            if (
                default_location_uuid is None
                and default_location_uuid_factory is not None
            ):
                default_location_uuid = default_location_uuid_factory()
            location = default_location_uuid
        if location not in files:
            raise ValueError(
                "Location %(location)s is not associated with this pipeline"
                % {"location": location}
            )

        # Normalize the Storage Service location path out of the selected path.
        # Keep this conversion string-based so UTF-8 path names flow through
        # unchanged while we preserve directory-copy trailing slashes below.
        source = path.replace(str(files[location]["location"]["path"]), "", 1).lstrip(
            "/"
        )
        # Use the last segment for the destination: a file basename, or the
        # selected directory name with its trailing slash preserved.
        last_segment = (
            os.path.basename(source.rstrip("/")) + "/"
            if source.endswith("/")
            else os.path.basename(source)
        )
        destination = os.path.join(
            str(processing_location["path"]),
            relative_destination,
            last_segment,
        ).replace("%sharedPath%", "")
        files[location]["files"].append({"source": source, "destination": destination})

    return files


def copy_transfer_source_files(
    paths: Sequence[str],
    relative_destination: str,
    storage_service_module: StorageService,
    default_location_uuid: str | None = None,
    default_location_uuid_factory: Callable[[], str] | None = None,
) -> None:
    """Copy selections into the pipeline's currently-processing location."""
    processing_location = storage_service_module.get_first_location(purpose="CP")
    transfer_sources = storage_service_module.get_location(purpose="TS")
    if default_location_uuid_factory is None:

        def default_location_uuid_factory() -> str:
            return storage_service_module.get_default_location("TS")["uuid"]

    try:
        files = build_transfer_source_copy_files(
            paths,
            relative_destination,
            processing_location,
            transfer_sources,
            default_location_uuid=default_location_uuid,
            default_location_uuid_factory=default_location_uuid_factory,
        )
    except ValueError as err:
        raise TransferSourceRetrievalError(str(err)) from err

    errors: list[str] = []
    for item in files.values():
        reply, error = storage_service_module.copy_files(
            item["location"], processing_location, item["files"]
        )
        if reply is None:
            errors.append(str(error))
    if errors:
        raise TransferSourceRetrievalError(
            "The following errors occurred: %(message)s"
            % {"message": ", ".join(errors)}
        )


def pad_destination_path_if_it_already_exists(
    filepath: StrPath, original: StrPath | None = None, attempt: int = 0
) -> Path:
    """
    Return a path that does not yet exist, padding with numbers as necessary.
    """
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
    filepath: StrPath, dest: StrPath, shared_directory: str
) -> TransferSourceRetrievalResult:
    """Move retrieved content into an internal Archivematica directory."""
    error = check_retrieved_path_exists(filepath)
    if error:
        raise TransferSourceRetrievalError(error)

    filepath = Path(filepath)
    dest = Path(dest)
    destination = pad_destination_path_if_it_already_exists(dest / filepath.name)

    try:
        filepath.rename(destination)
    except OSError as err:
        raise TransferSourceRetrievalError(
            f"Error moving from {filepath} to {destination}: {err}"
        ) from err

    return TransferSourceRetrievalResult(
        final_path=destination.as_posix(),
        current_location=destination.as_posix().replace(
            shared_directory, "%sharedPath%", 1
        ),
    )
