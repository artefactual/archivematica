from types import SimpleNamespace
from unittest import mock

from archivematica.archivematicaCommon.transfer_publication import (
    DESTINATION_REFRESH_PREFIX,
)
from archivematica.MCPServer.server import watch_dirs


def test_is_destination_refresh_matches_only_generated_names():
    marker = f"{DESTINATION_REFRESH_PREFIX}{'0123456789abcdef' * 2}"

    assert watch_dirs.is_destination_refresh_name(marker)
    assert not watch_dirs.is_destination_refresh_name(
        f"{DESTINATION_REFRESH_PREFIX}claim"
    )
    assert not watch_dirs.is_destination_refresh_name(f"{marker}0")
    assert not watch_dirs.is_destination_refresh_name(marker.upper())


def test_watch_directories_poll_ignores_destination_refresh_entries(
    tmp_path, monkeypatch
):
    watched_path = tmp_path / "active"
    watched_path.mkdir()
    transfer = watched_path / "transfer"
    transfer.mkdir()
    prefixed_transfer = watched_path / f"{DESTINATION_REFRESH_PREFIX}claim"
    prefixed_transfer.mkdir()
    marker = watched_path / f"{DESTINATION_REFRESH_PREFIX}{'0123456789abcdef' * 2}"
    marker.touch()
    watched_dir = SimpleNamespace(path="/active", only_dirs=False)
    shutdown = mock.Mock()
    shutdown.is_set.side_effect = [False, True]
    callback = mock.Mock()
    monkeypatch.setattr(watch_dirs, "WATCHED_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(watch_dirs.time, "sleep", lambda interval: None)

    watch_dirs.watch_directories_poll([watched_dir], shutdown, callback, interval=0)

    callback.assert_has_calls(
        [
            mock.call(str(transfer), watched_dir),
            mock.call(str(prefixed_transfer), watched_dir),
        ],
        any_order=True,
    )
    assert callback.call_count == 2
