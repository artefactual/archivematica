"""Tests for the antivirus.py client script."""

import uuid
from collections import OrderedDict
from collections import namedtuple
from contextlib import nullcontext
from unittest import mock

import pytest
import pytest_django
from clamav_client.scanner import ClamdScanner
from clamav_client.scanner import ClamscanScanner
from clamav_client.scanner import Scanner
from clamav_client.scanner import ScanResult
from django.contrib.auth.models import User

from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts.antivirus import AntivirusBatchData
from archivematica.MCPClient.clientScripts.antivirus import call as antivirus_call
from archivematica.MCPClient.clientScripts.antivirus import create_scanner
from archivematica.MCPClient.clientScripts.antivirus import get_size
from archivematica.MCPClient.clientScripts.antivirus import load_file_data
from archivematica.MCPClient.clientScripts.antivirus import scan_file


@pytest.mark.parametrize(
    "backend_setting, expected_scanner_class",
    [
        ("clamscanner", ClamscanScanner),
        ("clamdscanner", ClamdScanner),
        ("fprot", ClamdScanner),  # Default when unknown backend.
        ("", ClamdScanner),  # Default when empty string.
        (None, ClamdScanner),  # Default when None.
        (10, ClamdScanner),  # Default when non-string.
    ],
)
def test_create_scanner(backend_setting, expected_scanner_class, settings):
    """Test that create_scanner returns the correct instance of antivirus
    per the user's configuration."""
    settings.CLAMAV_CLIENT_BACKEND = backend_setting
    scanner = create_scanner()
    assert isinstance(scanner, expected_scanner_class)


args = OrderedDict()
args["file_uuid"] = "ec26199f-72a4-4fd8-a94a-29144b02ddd8"
args["path"] = "/path"
args["date"] = "2019-12-01"


class ScanResultMock(ScanResult):
    def __init__(self, filename, state, details, err, passed):
        super().__init__(filename=filename, state=state, details=details, err=err)
        self._passed_override = passed

    @property
    def passed(self) -> bool:
        return self._passed_override


class ScannerMock(Scanner):
    _program = "ClamAV (clamd)"
    _command = "mock"

    def __init__(self, *, should_except: bool = False, passed: bool = False):
        super().__init__()
        self.should_except = should_except
        self.passed = passed

    def scan(self, path: str) -> ScanResultMock:
        if self.should_except:
            raise Exception("Something really bad happened!")
        return ScanResultMock(
            filename=path,
            state="OK",
            details="details",
            err=None,
            passed=self.passed,
        )

    def _get_version(self) -> str:
        return "ClamAV 0.103.11/27400/Mon Sep 16 10:52:36 2024"


@mock.patch("archivematica.MCPClient.clientScripts.antivirus.create_scanner")
def test_scan_file_already_scanned(create_scanner: mock.Mock) -> None:
    batch_data = AntivirusBatchData(
        file_sizes={args["file_uuid"]: 1024},
        scanned_file_uuids={args["file_uuid"]},
    )

    exit_code = scan_file([], **dict(args), batch_data=batch_data)

    assert exit_code == 0
    create_scanner.assert_not_called()


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
@mock.patch("archivematica.MCPClient.clientScripts.antivirus.create_scanner")
def test_scan_file(
    create_scanner,
    setup_kwargs,
    exit_code,
    queue_event_params,
    settings,
):
    create_scanner.return_value = ScannerMock(
        should_except=setup_kwargs.get("scanner_should_except", False),
        passed=setup_kwargs.get("scanner_passed", False),
    )

    # Here the user configurable thresholds for maimum file size, and maximum
    # scan size are being tested. The scan size is offset so as to enable the
    # test to fall through correctly and eventually return None for
    # not-scanned.
    settings.CLAMAV_CLIENT_MAX_FILE_SIZE = 42
    settings.CLAMAV_CLIENT_MAX_SCAN_SIZE = 84

    event_queue = []
    batch_data = AntivirusBatchData(
        file_sizes={args["file_uuid"]: setup_kwargs.get("file_size", 1024)},
        scanned_file_uuids=set(),
    )

    ret = scan_file(event_queue, **dict(args), batch_data=batch_data)

    # The integer returned by scan_file() is going to be used as the exit code
    # of the antivirus.py script which is important for the AM workflow in order
    # to control what to do next.
    assert exit_code == ret

    # A side effect of scan_file() is to queue an event to be created in the
    # database.
    if queue_event_params.passed is None:
        assert len(event_queue) == 0
    else:
        assert len(event_queue) == 1

        event = event_queue[0]
        assert event.event_type == "virus check"
        assert event.file_uuid == args["file_uuid"]
        assert (
            event.event_outcome == "Pass" if setup_kwargs["scanner_passed"] else "Fail"
        )


@pytest.mark.django_db
def test_load_file_data_batches_queries(
    transfer: models.Transfer,
    django_assert_num_queries: pytest_django.fixtures.DjangoAssertNumQueries,
) -> None:
    scanned_file = models.File.objects.create(
        transfer=transfer,
        originallocation=b"objects/scanned",
        currentlocation=b"objects/scanned",
        size=42,
    )
    unscanned_file = models.File.objects.create(
        transfer=transfer,
        originallocation=b"objects/unscanned",
        currentlocation=b"objects/unscanned",
        size=84,
    )
    models.Event.objects.create(file_uuid=scanned_file, event_type="virus check")
    jobs = [
        mock.Mock(args=["antivirus", str(scanned_file.uuid)]),
        mock.Mock(args=["antivirus", str(unscanned_file.uuid).upper()]),
        mock.Mock(args=["antivirus", "None"]),
        mock.Mock(args=["antivirus", "not-a-uuid"]),
        mock.Mock(args=["antivirus"]),
    ]

    with django_assert_num_queries(2):
        batch_data = load_file_data(jobs)

    assert batch_data.file_sizes == {
        str(scanned_file.uuid): 42,
        str(unscanned_file.uuid): 84,
    }
    assert batch_data.scanned_file_uuids == {str(scanned_file.uuid)}


@mock.patch("archivematica.MCPClient.clientScripts.antivirus.os.path.getsize")
def test_get_size_uses_batch_data(path_getsize: mock.Mock) -> None:
    file_uuid = str(uuid.uuid4())

    assert get_size(file_uuid, "/path", {file_uuid: 42}) == 42
    assert get_size(file_uuid, "/path", {file_uuid: None}) is None

    path_getsize.assert_not_called()


@mock.patch(
    "archivematica.MCPClient.clientScripts.antivirus.os.path.getsize",
    return_value=84,
)
def test_get_size_uses_filesystem_for_file_missing_from_batch(
    path_getsize: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())

    assert get_size(file_uuid, "/path", {}) == 84

    path_getsize.assert_called_once_with("/path")


@mock.patch("archivematica.MCPClient.clientScripts.antivirus.insert_events")
@mock.patch("archivematica.MCPClient.clientScripts.antivirus.load_file_data")
@mock.patch("archivematica.MCPClient.clientScripts.antivirus.create_scanner")
def test_call_reuses_scanner_and_batch_data(
    create_scanner: mock.Mock,
    load_file_data: mock.Mock,
    insert_events: mock.Mock,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    file_uuids = [str(uuid.uuid4()), str(uuid.uuid4())]
    paths = ["/path/one", "/path/two"]
    jobs = [
        mock.Mock(
            spec=Job,
            args=["antivirus", file_uuid, path, args["date"]],
            JobContext=mock.MagicMock(),
        )
        for file_uuid, path in zip(file_uuids, paths)
    ]
    scanner = ScannerMock(passed=True)
    scanner.scan = mock.Mock(wraps=scanner.scan)
    create_scanner.return_value = scanner
    load_file_data.return_value = AntivirusBatchData(
        file_sizes=dict.fromkeys(file_uuids, 42),
        scanned_file_uuids=set(),
    )
    settings.CLAMAV_CLIENT_MAX_FILE_SIZE = 42
    settings.CLAMAV_CLIENT_MAX_SCAN_SIZE = 84

    antivirus_call(jobs)

    load_file_data.assert_called_once_with(jobs)
    create_scanner.assert_called_once_with()
    assert scanner.scan.mock_calls == [mock.call(path) for path in paths]
    for job in jobs:
        job.set_status.assert_called_once_with(0)
    (event_queue,) = insert_events.call_args.args
    assert len(event_queue) == 2
    assert [event.file_uuid for event in event_queue] == file_uuids


@pytest.mark.django_db
@mock.patch("archivematica.MCPClient.clientScripts.antivirus.create_scanner")
def test_call_preserves_scan_and_event_behavior(
    create_scanner: mock.Mock,
    transfer: models.Transfer,
    transfer_file: models.File,
    user: User,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    transfer_file.size = 42
    transfer_file.save(update_fields=["size"])
    scanned_file = models.File.objects.create(
        transfer=transfer,
        originallocation=b"objects/scanned",
        currentlocation=b"objects/scanned",
        size=42,
    )
    models.Event.objects.create(file_uuid=scanned_file, event_type="virus check")
    paths = ["/path/scanned", "/path/unscanned"]
    jobs = [
        mock.Mock(
            spec=Job,
            args=["antivirus", str(file.uuid), path, args["date"]],
            JobContext=mock.Mock(return_value=nullcontext()),
        )
        for file, path in zip([scanned_file, transfer_file], paths)
    ]
    scanner = ScannerMock(passed=True)
    scanner.scan = mock.Mock(wraps=scanner.scan)
    create_scanner.return_value = scanner
    settings.CLAMAV_CLIENT_MAX_FILE_SIZE = 42
    settings.CLAMAV_CLIENT_MAX_SCAN_SIZE = 84

    antivirus_call(jobs)

    scanner.scan.assert_called_once_with(paths[1])
    create_scanner.assert_called_once_with()
    for job in jobs:
        job.set_status.assert_called_once_with(0)
    assert (
        models.Event.objects.filter(
            file_uuid=scanned_file, event_type="virus check"
        ).count()
        == 1
    )
    event = models.Event.objects.get(file_uuid=transfer_file, event_type="virus check")
    assert event.event_outcome == "Pass"
    assert set(event.agents.values_list("pk", flat=True)) == {
        2,
        user.userprofile.agent_id,
    }


@mock.patch("archivematica.MCPClient.clientScripts.antivirus.insert_events")
@mock.patch("archivematica.MCPClient.clientScripts.antivirus.scan_file")
@mock.patch(
    "archivematica.MCPClient.clientScripts.antivirus.load_file_data",
    side_effect=RuntimeError,
)
def test_call_propagates_batch_load_failure(
    load_file_data: mock.Mock,
    scan_file: mock.Mock,
    insert_events: mock.Mock,
) -> None:
    job = mock.Mock(
        spec=Job,
        args=["antivirus", args["file_uuid"], args["path"], args["date"]],
        JobContext=mock.MagicMock(),
    )

    with pytest.raises(RuntimeError):
        antivirus_call([job])

    load_file_data.assert_called_once_with([job])
    scan_file.assert_not_called()
    job.JobContext.assert_not_called()
    job.set_status.assert_not_called()
    insert_events.assert_not_called()
