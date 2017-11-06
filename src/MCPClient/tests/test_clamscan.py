# -*- coding: utf8 -*-
"""Tests for the archivematicaClamscan.py client script."""

from __future__ import print_function

import os
import subprocess
import sys
from collections import OrderedDict, namedtuple

from clamd import ClamdNetworkSocket, ClamdUnixSocket
import pytest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))

import archivematicaClamscan


@pytest.mark.parametrize("version, want", [
    (
        "ClamAV 0.99.2/23992/Fri Oct 27 05:04:12 2017",
        ("ClamAV 0.99.2", "23992/Fri Oct 27 05:04:12 2017")
    ),
    (
        "ClamAV 0.99.2",
        ("ClamAV 0.99.2", None)
    ),
    (
        "Unexpected value",
        (None, None)
    ),
])
def test_clamav_version_parts(version, want):
    got = archivematicaClamscan.clamav_version_parts(version)
    assert got == want


# ClamdScanner tests

def setup_clamdscanner(settings,
                       addr="/var/run/clamav/clamd.ctl",
                       timeout=10,
                       stream=True):
    settings.CLAMAV_SERVER = addr
    settings.CLAMAV_CLIENT_TIMEOUT = timeout
    settings.CLAMAV_PASS_BY_REFERENCE = not stream

    return archivematicaClamscan.ClamdScanner()


def test_clamdscanner_version_props(mocker, settings):
    scanner = setup_clamdscanner(settings)
    mocker.patch.object(
        scanner, 'version_attrs',
        return_value=("ClamAV 0.99.2", "23992/Fri Oct 27 05:04:12 2017"))

    assert scanner.program() == "ClamAV (clamd)"
    assert scanner.version() == "ClamAV 0.99.2"
    assert scanner.virus_definitions() == "23992/Fri Oct 27 05:04:12 2017"


def test_clamdscanner_version_attrs(mocker, settings):
    scanner = setup_clamdscanner(settings, addr="/var/run/clamav/clamd.ctl")
    version = mocker.patch.object(
        scanner.client, 'version',
        return_value="ClamAV 0.99.2/23992/Fri Oct 27 05:04:12 2017")

    assert scanner.version_attrs() == (
        "ClamAV 0.99.2",
        "23992/Fri Oct 27 05:04:12 2017",
    )
    version.assert_called_once()


def test_clamdscanner_get_client(settings):
    scanner = setup_clamdscanner(settings, addr="/var/run/clamav/clamd.ctl")
    assert isinstance(scanner.client, ClamdUnixSocket)

    scanner = setup_clamdscanner(settings, addr="127.0.0.1:1234", timeout=15.5)
    assert isinstance(scanner.client, ClamdNetworkSocket)
    assert scanner.client.host == "127.0.0.1"
    assert scanner.client.port == 1234
    assert scanner.client.timeout == 15.5


def test_clamdscanner_scan(mocker, settings):
    OKAY_RET = ('OK', None)
    ERROR_RET = ('ERROR', 'Permission denied')
    FOUND_RET = ('FOUND', 'Eicar-Test-Signature')

    def patch(scanner, ret=OKAY_RET, excepts=False):
        deps = namedtuple('deps', ['pass_by_value', 'pass_by_reference'])(
            pass_by_value=mocker.patch.object(
                scanner, 'pass_by_value',
                return_value={'stream': ret}),
            pass_by_reference=mocker.patch.object(
                scanner, 'pass_by_reference',
                return_value={'/file': ret})
        )
        if excepts:
            e = Exception('Something bad happened!')
            deps.pass_by_value.side_effect = e
            deps.pass_by_reference.side_effect = e
        return deps

    scanner = setup_clamdscanner(settings, stream=True)
    deps = patch(scanner, ret=OKAY_RET)
    passed, state, details = scanner.scan('/file')
    assert passed is True
    assert state == 'OK'
    assert details is None
    deps.pass_by_value.assert_called_once()
    deps.pass_by_reference.assert_not_called()

    scanner = setup_clamdscanner(settings, stream=False)
    deps = patch(scanner, ret=OKAY_RET)
    passed, state, details = scanner.scan('/file')
    assert passed is True
    assert state == 'OK'
    assert details is None
    deps.pass_by_value.assert_not_called()
    deps.pass_by_reference.assert_called_once()

    patch(scanner, ret=ERROR_RET)
    passed, state, details = scanner.scan('/file')
    assert passed is False
    assert state == 'ERROR'
    assert details == 'Permission denied'

    patch(scanner, ret=FOUND_RET)
    passed, state, details = scanner.scan('/file')
    assert passed is False
    assert state == 'FOUND'
    assert details == 'Eicar-Test-Signature'

    patch(scanner, ret=FOUND_RET, excepts=True)
    passed, state, details = scanner.scan('/file')
    assert passed is False
    assert state is None
    assert details is None


# ClamScanner tests

def setup_clamscanner():
    return archivematicaClamscan.ClamScanner()


def test_clamscanner_version_props(mocker):
    scanner = setup_clamscanner()
    mocker.patch.object(
        scanner, 'version_attrs',
        return_value=("ClamAV 0.99.2", "23992/Fri Oct 27 05:04:12 2017"))

    assert scanner.program() == "ClamAV (clamscan)"
    assert scanner.version() == "ClamAV 0.99.2"
    assert scanner.virus_definitions() == "23992/Fri Oct 27 05:04:12 2017"


def test_clamscanner_version_attrs(mocker, settings):
    scanner = setup_clamscanner()
    mock = mocker.patch.object(
        scanner, '_call',
        return_value="ClamAV 0.99.2/23992/Fri Oct 27 05:04:12 2017")

    assert scanner.version_attrs() == (
        "ClamAV 0.99.2",
        "23992/Fri Oct 27 05:04:12 2017",
    )
    mock.assert_called_once_with('-V')


def test_clamscanner_scan(mocker):
    scanner = setup_clamscanner()
    mock = mocker.patch.object(
        scanner, '_call',
        return_value='Output of clamscan')

    assert scanner.scan('/file') == (True, 'OK', None)
    mock.assert_called_once_with('/file')

    mock.side_effect = \
        subprocess.CalledProcessError(1, 'clamscan', 'Output of clamscan')
    assert scanner.scan('/file') == (False, 'FOUND', None)

    mock.side_effect = \
        subprocess.CalledProcessError(2, 'clamscan', 'Output of clamscan')
    assert scanner.scan('/file') == (False, 'ERROR', None)


# Other tests

def test_get_scanner_threshold(settings):
    """ Test that get_scanner returns an instance of ClamScanner when the
    threshold is exceeded or an instance of ClamdScanner otherwise. """

    # ClamdScanner expects these settings to be defined.
    settings.CLAMAV_SERVER = "/var/run/clamav/clamd.ctl"
    settings.CLAMAV_CLIENT_TIMEOUT = 10
    settings.CLAMAV_PASS_BY_REFERENCE = True

    # Exceeding the threshold.
    settings.CLAMAV_CLIENT_THRESHOLD = 0.5
    file_size = 0.6 * 1024 * 1024
    scanner = archivematicaClamscan.get_scanner(file_size)
    assert isinstance(scanner, archivematicaClamscan.ClamScanner)

    # Not exceeding the threshold.
    settings.CLAMAV_CLIENT_THRESHOLD = 1
    file_size = 1 * 1024 * 1024
    scanner = archivematicaClamscan.get_scanner(file_size)
    assert isinstance(scanner, archivematicaClamscan.ClamdScanner)


args = OrderedDict()
args['file_uuid'] = 'ec26199f-72a4-4fd8-a94a-29144b02ddd8'
args['path'] = '/path'
args['date'] = '2019-12-01'
args['task_uuid'] = 'c380e94e-7a7b-4ab8-aa72-ec0644cc3f5d'


class FileMock():
    def __init__(self, size):
        self.size = size


class ScannerMock(archivematicaClamscan.ScannerBase):
    PROGRAM = "Mock"

    def __init__(self, should_except=False, passed=False):
        self.should_except = should_except
        self.passed = passed

    def scan(self, path):
        if self.should_except:
            raise Exception("Something really bad happened!")
        return self.passed, None, None

    def version_attrs(self):
        return ("version", "virus_definitions")


def test_main_with_expected_arguments(mocker):
    mocker.patch('archivematicaClamscan.scan_file')
    archivematicaClamscan.main(args.values())
    archivematicaClamscan.scan_file.assert_called_once_with(**dict(args))


def test_main_with_missing_arguments():
    with pytest.raises(SystemExit):
        archivematicaClamscan.main([])


def setup_test_scan_file_mocks(mocker,
                               file_already_scanned=False,
                               file_size=1024,
                               scanner_should_except=False,
                               scanner_passed=False):
    deps = namedtuple('deps', [
        'file_already_scanned',
        'file_get',
        'record_event',
        'scanner',
    ])(
        file_already_scanned=mocker.patch(
            'archivematicaClamscan.file_already_scanned',
            return_value=file_already_scanned),
        file_get=mocker.patch(
            'main.models.File.objects.get',
            return_value=FileMock(size=file_size)),
        record_event=mocker.patch(
            'archivematicaClamscan.record_event',
            return_value=None),
        scanner=ScannerMock(
            should_except=scanner_should_except,
            passed=scanner_passed)
    )

    mocker.patch(
        'archivematicaClamscan.get_scanner',
        return_value=deps.scanner)

    return deps


def test_scan_file_already_scanned(mocker):
    deps = setup_test_scan_file_mocks(mocker, file_already_scanned=True)

    exit_code = archivematicaClamscan.scan_file(**dict(args))

    assert exit_code == 0
    deps.file_already_scanned.assert_called_once_with(args['file_uuid'])


RecordEventParams = namedtuple('RecordEventParams', [
    'scanner_is_None',
    'passed'
])


@pytest.mark.parametrize("setup_kwargs, exit_code, record_event_params", [
    # Invalid size
    (
        {'file_size': 0},
        1,
        RecordEventParams(scanner_is_None=True, passed=False),
    ),
    # Faulty scanner
    (
        {'scanner_should_except': True},
        1,
        RecordEventParams(scanner_is_None=False, passed=False),
    ),
    # Virus found
    (
        {'scanner_passed': False},
        1,
        RecordEventParams(scanner_is_None=False, passed=False),
    ),
    # Passed
    (
        {'scanner_passed': True},
        0,
        RecordEventParams(scanner_is_None=False, passed=True),
    ),
])
def test_scan_file(mocker, setup_kwargs, exit_code, record_event_params):
    deps = setup_test_scan_file_mocks(mocker, **setup_kwargs)

    ret = archivematicaClamscan.scan_file(**dict(args))

    # The integer returned by scan_file() is going to be used as the exit code
    # of the archivematicaClamscan.py script which is important for the AM
    # workflow in order to control what to do next.
    assert exit_code == ret

    # A side effect of scan_file() is to record the corresponding event in the
    # database. Here we are making sure that record_event() is called with the
    # expected parameters.
    deps.record_event.assert_called_once_with(
        args['file_uuid'],
        args['date'],
        None if record_event_params.scanner_is_None is True else deps.scanner,
        record_event_params.passed)
