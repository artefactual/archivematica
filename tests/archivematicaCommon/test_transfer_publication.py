"""Unit tests for transfer publication."""

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
from unittest import mock
from uuid import UUID

import pytest
from filelock import StrictSoftFileLock

try:
    from builtins import ExceptionGroup
except ImportError:  # pragma: no cover - Python 3.10 only
    from exceptiongroup import ExceptionGroup

from archivematica.archivematicaCommon import transfer_publication
from archivematica.archivematicaCommon.transfer_publication import (
    TransferSourceRetrievalError,
)
from archivematica.archivematicaCommon.transfer_publication import (
    check_retrieved_path_exists,
)
from archivematica.archivematicaCommon.transfer_publication import (
    move_to_internal_shared_dir,
)
from archivematica.archivematicaCommon.transfer_publication import (
    pad_destination_path_if_it_already_exists,
)


@pytest.fixture
def retrieval_paths(tmp_path):
    """Create the staging and processing layout used by publication helpers."""
    shared = tmp_path / "sharedDirectory"
    processing = shared / "currentlyProcessing"
    copied = shared / "tmp" / "tmp123" / "transfer"
    copied.mkdir(parents=True)
    processing.mkdir()

    return SimpleNamespace(shared=shared, processing=processing, copied=copied)


@pytest.mark.parametrize(
    "path_name,create_path,expected",
    [
        ("", False, "No filepath provided."),
        ("missing", False, "Filepath {path} does not exist."),
        ("path..with-parent-reference", True, "Illegal path."),
    ],
)
def test_check_retrieved_path_exists_rejects_invalid_paths(
    tmp_path, path_name, create_path, expected
):
    path = "" if path_name == "" else tmp_path / path_name
    if create_path:
        path.mkdir()

    assert check_retrieved_path_exists(path) == expected.format(path=path)


@pytest.mark.parametrize(
    "existing_paths,destination,expected",
    [
        ([], "transfer", "transfer"),
        (["transfer/"], "transfer", "transfer_1"),
        (["transfer/", "transfer_1/"], "transfer", "transfer_2"),
        (["transfer.zip"], "transfer.zip", "transfer_1.zip"),
    ],
)
def test_pad_destination_path_if_it_already_exists(
    tmp_path, existing_paths, destination, expected
):
    for existing_path in existing_paths:
        path = tmp_path / existing_path.rstrip("/")
        if existing_path.endswith("/"):
            path.mkdir()
        else:
            path.touch()

    assert pad_destination_path_if_it_already_exists(tmp_path / destination) == (
        tmp_path / expected
    )


def test_move_to_internal_shared_dir_moves_and_returns_db_location(retrieval_paths):
    result = move_to_internal_shared_dir(
        retrieval_paths.copied,
        retrieval_paths.processing,
        f"{retrieval_paths.shared}/",
    )

    final_path = retrieval_paths.processing / "transfer"
    assert result.final_path == final_path.as_posix()
    assert result.current_location == "%sharedPath%currentlyProcessing/transfer"
    assert not retrieval_paths.copied.exists()
    assert final_path.exists()


def test_move_to_internal_shared_dir_prepares_metadata_before_publication(
    retrieval_paths,
):
    prepared = []
    metadata = mock.Mock()

    def reserve(result):
        destination = Path(result.final_path)
        assert retrieval_paths.copied.exists()
        assert not destination.exists()
        prepared.append(result)

    metadata.reserve.side_effect = reserve
    result = move_to_internal_shared_dir(
        retrieval_paths.copied,
        retrieval_paths.processing,
        f"{retrieval_paths.shared}/",
        metadata=metadata,
    )

    assert prepared == [result]
    assert Path(result.final_path).exists()
    metadata.rollback.assert_not_called()


def test_move_to_internal_shared_dir_rolls_back_metadata_when_rename_fails(
    retrieval_paths,
):
    metadata = mock.Mock()

    with mock.patch.object(Path, "rename", side_effect=OSError("rename failed")):
        with pytest.raises(TransferSourceRetrievalError, match="rename failed"):
            move_to_internal_shared_dir(
                retrieval_paths.copied,
                retrieval_paths.processing,
                f"{retrieval_paths.shared}/",
                metadata=metadata,
            )

    metadata.reserve.assert_called_once_with(mock.ANY)
    metadata.rollback.assert_called_once_with()
    assert retrieval_paths.copied.exists()


def test_move_to_internal_shared_dir_preserves_move_and_rollback_errors(
    retrieval_paths,
):
    metadata = mock.Mock()
    rollback_error = RuntimeError("rollback failed")
    metadata.rollback.side_effect = rollback_error

    with mock.patch.object(Path, "rename", side_effect=OSError("rename failed")):
        with pytest.raises(TransferSourceRetrievalError) as exc_info:
            move_to_internal_shared_dir(
                retrieval_paths.copied,
                retrieval_paths.processing,
                f"{retrieval_paths.shared}/",
                metadata=metadata,
            )

    assert "rename failed" in str(exc_info.value)
    assert "rollback failed" in str(exc_info.value)
    assert exc_info.value.__cause__ is rollback_error


def test_move_to_internal_shared_dir_releases_lock_after_rollback(retrieval_paths):
    events = []
    metadata = mock.Mock()
    metadata.reserve.side_effect = lambda result: events.append("reserve")
    metadata.rollback.side_effect = lambda: events.append("rollback")
    lock = mock.Mock(lock_file="destination-lock")
    lock.release.side_effect = lambda: events.append("release")

    def fail_rename(destination):
        events.append("rename")
        raise OSError(f"rename failed for {destination}")

    with (
        mock.patch.object(
            transfer_publication, "_acquire_destination_lock", return_value=lock
        ),
        mock.patch.object(transfer_publication, "_refresh_destination_directory"),
        mock.patch.object(
            Path,
            "rename",
            side_effect=fail_rename,
        ),
    ):
        with pytest.raises(TransferSourceRetrievalError, match="rename failed"):
            move_to_internal_shared_dir(
                retrieval_paths.copied,
                retrieval_paths.processing,
                f"{retrieval_paths.shared}/",
                metadata=metadata,
            )

    assert events == ["reserve", "rename", "rollback", "release"]


def test_move_to_internal_shared_dir_rejects_reserved_destination_name(
    retrieval_paths,
):
    marker = (
        f"{transfer_publication.DESTINATION_REFRESH_PREFIX}{'0123456789abcdef' * 2}"
    )
    copied = retrieval_paths.copied.with_name(marker)
    retrieval_paths.copied.rename(copied)

    with pytest.raises(TransferSourceRetrievalError, match="is reserved"):
        move_to_internal_shared_dir(
            copied,
            retrieval_paths.processing,
            f"{retrieval_paths.shared}/",
        )

    assert copied.exists()
    assert not any(retrieval_paths.processing.iterdir())


def test_refresh_destination_directory_links_into_destination(tmp_path):
    lock_file = tmp_path / "locks" / "00"
    destination = tmp_path / "processing" / "transfer"
    lock_file.parent.mkdir()
    destination.parent.mkdir()
    lock_file.write_text("lock")
    lock = SimpleNamespace(lock_file=str(lock_file))
    refresh_uuid = UUID("00000000-0000-0000-0000-000000000123")
    refresh_path = destination.parent / (
        f"{transfer_publication.DESTINATION_REFRESH_PREFIX}{refresh_uuid.hex}"
    )

    with (
        mock.patch.object(transfer_publication, "uuid4", return_value=refresh_uuid),
        mock.patch.object(os, "link", wraps=os.link) as link,
    ):
        transfer_publication._refresh_destination_directory(destination, lock)

    link.assert_called_once_with(str(lock_file), refresh_path)
    assert not refresh_path.exists()


def test_move_to_internal_shared_dir_refreshes_stale_destination_lookup(
    retrieval_paths,
):
    retrieval_paths.copied.rmdir()
    copied = retrieval_paths.copied.with_suffix(".zip")
    copied.write_text("new")
    existing = retrieval_paths.processing / "transfer.zip"
    existing.write_text("existing")
    cache = {"negative": True}
    real_exists = Path.exists

    def cached_exists(path):
        if path == existing and cache["negative"]:
            return False
        return real_exists(path)

    def refresh(destination, lock):
        assert destination == existing
        cache["negative"] = False

    with (
        mock.patch.object(Path, "exists", new=cached_exists),
        mock.patch.object(
            transfer_publication,
            "_refresh_destination_directory",
            side_effect=refresh,
        ) as destination_refresh,
    ):
        result = move_to_internal_shared_dir(
            copied,
            retrieval_paths.processing,
            f"{retrieval_paths.shared}/",
        )

    final_path = Path(result.final_path)
    assert destination_refresh.call_count == 1
    assert existing.read_text() == "existing"
    assert final_path == retrieval_paths.processing / "transfer_1.zip"
    assert final_path.read_text() == "new"


def test_move_to_internal_shared_dir_fails_closed_when_refresh_fails(
    retrieval_paths,
):
    refresh_error = TransferSourceRetrievalError("destination refresh failed")
    with mock.patch.object(
        transfer_publication,
        "_refresh_destination_directory",
        side_effect=refresh_error,
    ):
        with pytest.raises(TransferSourceRetrievalError, match="destination refresh"):
            move_to_internal_shared_dir(
                retrieval_paths.copied,
                retrieval_paths.processing,
                f"{retrieval_paths.shared}/",
            )

    assert retrieval_paths.copied.exists()
    assert not (retrieval_paths.processing / "transfer").exists()


@pytest.mark.parametrize("path_type", ["directory", "file"])
def test_move_to_internal_shared_dir_avoids_concurrent_collisions(tmp_path, path_type):
    shared = tmp_path / "sharedDirectory"
    processing = shared / "currentlyProcessing"
    processing.mkdir(parents=True)

    sources = []
    for index in range(8):
        source = shared / "tmp" / str(index) / "transfer"
        source.parent.mkdir(parents=True)
        if path_type == "directory":
            source.mkdir()
            (source / "content").write_text(str(index))
        else:
            source = source.with_suffix(".zip")
            source.write_text(str(index))
        sources.append(source)

    start = Barrier(len(sources))

    def move(source):
        start.wait(timeout=5)
        return move_to_internal_shared_dir(source, processing, f"{shared}/")

    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        results = list(executor.map(move, sources))

    final_paths = [Path(result.final_path) for result in results]
    assert len(set(final_paths)) == len(sources)
    assert all(not source.exists() for source in sources)
    if path_type == "directory":
        assert {path.name for path in final_paths} == {
            "transfer",
            *(f"transfer_{index}" for index in range(1, len(sources))),
        }
        assert {(path / "content").read_text() for path in final_paths} == {
            str(index) for index in range(len(sources))
        }
    else:
        assert {path.name for path in final_paths} == {
            "transfer.zip",
            *(f"transfer_{index}.zip" for index in range(1, len(sources))),
        }
        assert {path.read_text() for path in final_paths} == {
            str(index) for index in range(len(sources))
        }


def test_move_to_internal_shared_dir_coordinates_padded_and_original_names(tmp_path):
    shared = tmp_path / "sharedDirectory"
    processing = shared / "currentlyProcessing"
    processing.mkdir(parents=True)
    (processing / "foo.zip").write_text("existing")

    sources = []
    for index, name in enumerate(("foo.zip", "foo_1.zip")):
        source = shared / "tmp" / str(index) / name
        source.parent.mkdir(parents=True)
        source.write_text(name)
        sources.append(source)

    start = Barrier(len(sources))

    def move(source):
        start.wait(timeout=5)
        return move_to_internal_shared_dir(source, processing, f"{shared}/")

    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        results = list(executor.map(move, sources))

    final_paths = [Path(result.final_path) for result in results]
    assert len(set(final_paths)) == len(sources)
    assert (processing / "foo.zip").read_text() == "existing"
    assert {path.read_text() for path in final_paths} == {"foo.zip", "foo_1.zip"}


@pytest.mark.parametrize("path_type", ["directory", "file"])
def test_move_to_internal_shared_dir_uses_unique_fallback_when_locking_fails(
    retrieval_paths, path_type
):
    copied = retrieval_paths.copied
    existing = retrieval_paths.processing / "transfer"
    if path_type == "directory":
        copied_content = copied / "content"
        existing.mkdir()
        existing_content = existing / "content"
    else:
        copied.rmdir()
        copied = copied.with_suffix(".zip")
        copied_content = copied
        existing = existing.with_suffix(".zip")
        existing_content = existing
    copied_content.write_text("new")
    existing_content.write_text("existing")

    fallback_uuid = UUID("00000000-0000-0000-0000-000000000123")
    with (
        mock.patch.object(
            StrictSoftFileLock,
            "acquire",
            side_effect=OSError("locking unavailable"),
        ),
        mock.patch.object(transfer_publication, "uuid4", return_value=fallback_uuid),
    ):
        result = move_to_internal_shared_dir(
            copied,
            retrieval_paths.processing,
            f"{retrieval_paths.shared}/",
        )

    final_path = Path(result.final_path)
    expected_name = f"transfer_{fallback_uuid.hex}"
    if path_type == "file":
        expected_name += ".zip"
    assert final_path.name == expected_name
    assert final_path != existing
    assert existing_content.read_text() == "existing"
    assert final_path.exists()
    final_content = final_path / "content" if path_type == "directory" else final_path
    assert final_content.read_text() == "new"


def test_move_to_internal_shared_dir_uses_unique_fallback_when_lock_is_held(
    retrieval_paths, monkeypatch
):
    destination = retrieval_paths.processing / "transfer"
    lock_path = transfer_publication._destination_lock_path(
        destination, retrieval_paths.shared
    )
    lock_path.parent.mkdir(parents=True)
    monkeypatch.setattr(transfer_publication, "DESTINATION_LOCK_TIMEOUT", 0)

    with StrictSoftFileLock(lock_path):
        result = move_to_internal_shared_dir(
            retrieval_paths.copied,
            retrieval_paths.processing,
            f"{retrieval_paths.shared}/",
        )

    final_path = Path(result.final_path)
    assert final_path.name.startswith("transfer_")
    assert final_path.exists()


def test_move_to_internal_shared_dir_handles_grouped_lock_failure(retrieval_paths):
    lock_error = ExceptionGroup(
        "strict lock cleanup failed",
        [OSError("first claim unlink failed"), OSError("second claim unlink failed")],
    )
    with mock.patch.object(StrictSoftFileLock, "acquire", side_effect=lock_error):
        result = move_to_internal_shared_dir(
            retrieval_paths.copied,
            retrieval_paths.processing,
            f"{retrieval_paths.shared}/",
        )

    final_path = Path(result.final_path)
    assert final_path.name.startswith("transfer_")
    assert final_path.exists()


def test_move_to_internal_shared_dir_ignores_grouped_lock_release_failure(
    retrieval_paths,
):
    lock = mock.Mock(lock_file="destination-lock")
    lock.release.side_effect = ExceptionGroup(
        "strict lock release failed",
        [OSError("first claim unlink failed"), OSError("second claim unlink failed")],
    )
    with (
        mock.patch.object(
            transfer_publication, "_acquire_destination_lock", return_value=lock
        ),
        mock.patch.object(transfer_publication, "_refresh_destination_directory"),
    ):
        result = move_to_internal_shared_dir(
            retrieval_paths.copied,
            retrieval_paths.processing,
            f"{retrieval_paths.shared}/",
        )

    assert Path(result.final_path).exists()
    lock.release.assert_called_once_with()


@pytest.mark.parametrize("path_type", ["directory", "file"])
def test_move_to_internal_shared_dir_bounds_unique_fallback_name(tmp_path, path_type):
    shared = tmp_path / "sharedDirectory"
    processing = shared / "currentlyProcessing"
    copied_directory = shared / "tmp" / "tmp123"
    processing.mkdir(parents=True)
    copied_directory.mkdir(parents=True)
    name_max = os.pathconf(copied_directory, "PC_NAME_MAX")
    extension = ".zip" if path_type == "file" else ""
    source = copied_directory / ("a" * (name_max - len(extension)) + extension)
    if path_type == "directory":
        source.mkdir()
    else:
        source.write_text("content")

    fallback_uuid = UUID("00000000-0000-0000-0000-000000000123")
    with (
        mock.patch.object(
            StrictSoftFileLock,
            "acquire",
            side_effect=OSError("locking unavailable"),
        ),
        mock.patch.object(transfer_publication, "uuid4", return_value=fallback_uuid),
    ):
        result = move_to_internal_shared_dir(
            source,
            processing,
            f"{shared}/",
        )

    final_path = Path(result.final_path)
    assert len(os.fsencode(final_path.name)) <= name_max
    assert fallback_uuid.hex in final_path.name
    assert final_path.suffix == extension
    assert final_path.exists()


def test_destination_lock_key_is_independent_of_shared_directory_mount_point():
    first = transfer_publication._destination_lock_path(
        Path("/mnt/first/currentlyProcessing/transfer"), "/mnt/first"
    )
    second = transfer_publication._destination_lock_path(
        Path("/mnt/second/currentlyProcessing/transfer"), "/mnt/second"
    )

    assert first.name == second.name


@pytest.mark.parametrize(
    "original,padded",
    [
        ("foo", "foo_1"),
        ("foo.zip", "foo_1.zip"),
        ("foo.zip", "foo.zip_1"),
        ("foo_1.tar.gz", "foo_1_2.tar.gz"),
    ],
)
def test_destination_lock_key_coordinates_padded_name_families(original, padded):
    shared = Path("/mnt/shared")
    original_lock = transfer_publication._destination_lock_path(
        shared / "currentlyProcessing" / original, shared
    )
    padded_lock = transfer_publication._destination_lock_path(
        shared / "currentlyProcessing" / padded, shared
    )

    assert original_lock == padded_lock


def test_destination_lock_paths_use_a_bounded_number_of_shards():
    lock_paths = {
        transfer_publication._destination_lock_path(
            Path(f"/mnt/shared/currentlyProcessing/transfer-{index}"), "/mnt/shared"
        )
        for index in range(1000)
    }

    assert len(lock_paths) <= transfer_publication.DESTINATION_LOCK_SHARDS
