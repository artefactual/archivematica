"""Tests for the archivematica_clamscan.py client script."""

from collections import OrderedDict
from collections import namedtuple
from unittest import mock

import pytest
from archivematica_clamscan import create_scanner
from archivematica_clamscan import scan_file
from clamav_client.scanner import ClamdScanner
from clamav_client.scanner import ClamscanScanner
from clamav_client.scanner import Scanner
from clamav_client.scanner import ScanResult


def test_create_scanner(settings):
    """Test that create_scanner returns the correct instance of antivirus
    per the user's configuration. Test return of clamdscanner by default."""

    # Testing to ensure clamscanner is returned when explicitly set.
    settings.CLAMAV_CLIENT_BACKEND = "clamscanner"
    scanner = create_scanner()
    assert isinstance(scanner, ClamscanScanner)

    # Testing to ensure that clamdscanner is returned when explicitly set.
    settings.CLAMAV_CLIENT_BACKEND = "clamdscanner"
    scanner = create_scanner()
    assert isinstance(scanner, ClamdScanner)

    # Testing to ensure that clamdscanner is the default returned scanner.
    settings.CLAMAV_CLIENT_BACKEND = "fprot"
    scanner = create_scanner()
    assert isinstance(scanner, ClamdScanner)

    # Testing to ensure that clamdscanner is the default returned scanner when
    # the user configures an empty string.
    settings.CLAMAV_CLIENT_BACKEND = ""
    scanner = create_scanner()
    assert isinstance(scanner, ClamdScanner)

    # Testing to ensure that clamdscanner is returned when the environment
    # hasn't been configured appropriately and None is returned.
    settings.CLAMAV_CLIENT_BACKEND = None
    scanner = create_scanner()
    assert isinstance(scanner, ClamdScanner)

    # Testing to ensure that clamdscanner is returned when another variable
    # type is specified, e.g. in this instance, an integer.
    settings.CLAMAV_CLIENT_BACKEND = 10
    scanner = create_scanner()
    assert isinstance(scanner, ClamdScanner)


args = OrderedDict()
args["file_uuid"] = "ec26199f-72a4-4fd8-a94a-29144b02ddd8"
args["path"] = "/path"
args["date"] = "2019-12-01"
args["task_uuid"] = "c380e94e-7a7b-4ab8-aa72-ec0644cc3f5d"


class FileMock:
    def __init__(self, size):
        self.size = size


class ScannerMock(Scanner):
    _program = "ClamAV (clamd)"
    _command = "mock"

    def __init__(self, should_except=False, passed=False):
        self.should_except = should_except
        self.passed = passed

    def scan(self, path):
        if self.should_except:
            raise Exception("Something really bad happened!")
        result = ScanResult(filename=path, state="OK", details="details", err=None)
        mock.patch.object(
            result.__class__,
            "passed",
            new_callable=mock.PropertyMock,
            return_value=self.passed,
        ).start()
        return result

    def _get_version(self):
        return "ClamAV 0.103.11/27400/Mon Sep 16 10:52:36 2024"


def setup_test_scan_file_mocks(
    mocker,
    file_already_scanned=False,
    file_size=1024,
    scanner_should_except=False,
    scanner_passed=False,
):
    deps = namedtuple("deps", ["file_already_scanned", "file_get", "scanner"])(
        file_already_scanned=mocker.patch(
            "archivematica_clamscan.file_already_scanned",
            return_value=file_already_scanned,
        ),
        file_get=mocker.patch(
            "main.models.File.objects.get", return_value=FileMock(size=file_size)
        ),
        scanner=ScannerMock(should_except=scanner_should_except, passed=scanner_passed),
    )

    mocker.patch("archivematica_clamscan.get_scanner", return_value=deps.scanner)

    return deps


def test_scan_file_already_scanned(mocker):
    deps = setup_test_scan_file_mocks(mocker, file_already_scanned=True)

    exit_code = scan_file([], **dict(args))

    assert exit_code == 0
    deps.file_already_scanned.assert_called_once_with(args["file_uuid"])


QueueEventParams = namedtuple("QueueEventParams", ["scanner_is_None", "passed"])


@pytest.mark.parametrize(
    "setup_kwargs, exit_code, queue_event_params",
    [
        # File size too big for given file_size param
        (
            {"file_size": 43, "scanner_passed": None},
            0,
            QueueEventParams(scanner_is_None=None, passed=None),
        ),
        # File size too big for given file_scan param
        (
            {"file_size": 85, "scanner_passed": None},
            0,
            QueueEventParams(scanner_is_None=None, passed=None),
        ),
        # File size within given file_size param, and file_scan param
        (
            {"file_size": 42, "scanner_passed": True},
            0,
            QueueEventParams(scanner_is_None=False, passed=True),
        ),
        # Scan returns None with no-error, e.g. Broken Pipe
        (
            {"scanner_passed": None},
            0,
            QueueEventParams(scanner_is_None=None, passed=None),
        ),
        # Zero byte file passes
        (
            {"file_size": 0, "scanner_passed": True},
            0,
            QueueEventParams(scanner_is_None=False, passed=True),
        ),
        # Virus found
        (
            {"scanner_passed": False},
            1,
            QueueEventParams(scanner_is_None=False, passed=False),
        ),
        # Passed
        (
            {"scanner_passed": True},
            0,
            QueueEventParams(scanner_is_None=False, passed=True),
        ),
    ],
)
def test_scan_file(mocker, setup_kwargs, exit_code, queue_event_params, settings):
    setup_test_scan_file_mocks(mocker, **setup_kwargs)

    # Here the user configurable thresholds for maimum file size, and maximum
    # scan size are being tested. The scan size is offset so as to enable the
    # test to fall through correctly and eventually return None for
    # not-scanned.
    settings.CLAMAV_CLIENT_MAX_FILE_SIZE = 42
    settings.CLAMAV_CLIENT_MAX_SCAN_SIZE = 84

    event_queue = []

    ret = scan_file(event_queue, **dict(args))

    # The integer returned by scan_file() is going to be used as the exit code
    # of the archivematica_clamscan.py script which is important for the AM
    # workflow in order to control what to do next.
    assert exit_code == ret

    # A side effect of scan_file() is to queue an event to be created in the
    # database.
    if queue_event_params.passed is None:
        assert len(event_queue) == 0
    else:
        assert len(event_queue) == 1

        event = event_queue[0]
        assert event["eventType"] == "virus check"
        assert event["fileUUID"] == args["file_uuid"]
        assert (
            event["eventOutcome"] == "Pass"
            if setup_kwargs["scanner_passed"]
            else "Fail"
        )
