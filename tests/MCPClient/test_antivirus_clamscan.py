"""Tests for the archivematica_clamscan.py client script."""

import subprocess
from unittest import mock

import archivematica_clamscan
import pytest


@pytest.mark.parametrize(
    "version, want",
    [
        (
            "ClamAV 0.99.2/23992/Fri Oct 27 05:04:12 2017",
            ("ClamAV 0.99.2", "23992/Fri Oct 27 05:04:12 2017"),
        ),
        ("ClamAV 0.99.2", ("ClamAV 0.99.2", None)),
        ("Unexpected value", (None, None)),
    ],
)
def test_clamav_version_parts(version, want):
    got = archivematica_clamscan.clamav_version_parts(version)
    assert got == want


def setup_clamscanner():
    return archivematica_clamscan.ClamScanner()


def test_clamscanner_version_props():
    scanner = setup_clamscanner()
    with mock.patch.object(
        scanner,
        "version_attrs",
        return_value=("ClamAV 0.99.2", "23992/Fri Oct 27 05:04:12 2017"),
    ):
        assert scanner.program() == "ClamAV (clamscan)"
        assert scanner.version() == "ClamAV 0.99.2"
        assert scanner.virus_definitions() == "23992/Fri Oct 27 05:04:12 2017"


def test_clamscanner_version_attrs(settings):
    scanner = setup_clamscanner()
    with mock.patch.object(
        scanner, "_call", return_value="ClamAV 0.99.2/23992/Fri Oct 27 05:04:12 2017"
    ) as mock_call:
        assert scanner.version_attrs() == (
            "ClamAV 0.99.2",
            "23992/Fri Oct 27 05:04:12 2017",
        )
        mock_call.assert_called_once_with("-V")


def test_clamscanner_scan(settings):
    scanner = setup_clamscanner()
    with mock.patch.object(
        scanner, "_call", return_value="Output of clamscan"
    ) as mock_call:
        # User configured thresholds need to be sent through to clamscanner and
        # executed as part of the call to it.
        settings.CLAMAV_CLIENT_MAX_FILE_SIZE = 20
        settings.CLAMAV_CLIENT_MAX_SCAN_SIZE = 20

        max_file_size = "--max-filesize=%dM" % settings.CLAMAV_CLIENT_MAX_FILE_SIZE
        max_scan_size = "--max-scansize=%dM" % settings.CLAMAV_CLIENT_MAX_SCAN_SIZE

        assert scanner.scan("/file") == (True, "OK", None)
        mock_call.assert_called_once_with(max_file_size, max_scan_size, "/file")

        mock_call.side_effect = subprocess.CalledProcessError(
            1, "clamscan", "Output of clamscan"
        )
        assert scanner.scan("/file") == (False, "FOUND", None)

        mock_call.side_effect = subprocess.CalledProcessError(
            2, "clamscan", "Output of clamscan"
        )
        assert scanner.scan("/file") == (False, "ERROR", None)
