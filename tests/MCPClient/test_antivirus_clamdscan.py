"""Tests for the archivematica_clamscan.py client script."""

import errno
from collections import namedtuple
from unittest import mock

import archivematica_clamscan
from clamd import BufferTooLongError
from clamd import ClamdNetworkSocket
from clamd import ClamdUnixSocket
from clamd import ConnectionError


def setup_clamdscanner(
    settings, addr="/var/run/clamav/clamd.ctl", timeout=10, stream=False
):
    settings.CLAMAV_SERVER = addr
    settings.CLAMAV_CLIENT_TIMEOUT = timeout
    settings.CLAMAV_PASS_BY_STREAM = stream

    return archivematica_clamscan.ClamdScanner()


def test_clamdscanner_version_props(settings):
    scanner = setup_clamdscanner(settings)
    with mock.patch.object(
        scanner,
        "version_attrs",
        return_value=("ClamAV 0.99.2", "23992/Fri Oct 27 05:04:12 2017"),
    ):
        assert scanner.program() == "ClamAV (clamd)"
        assert scanner.version() == "ClamAV 0.99.2"
        assert scanner.virus_definitions() == "23992/Fri Oct 27 05:04:12 2017"


def test_clamdscanner_version_attrs(settings):
    scanner = setup_clamdscanner(settings, addr="/var/run/clamav/clamd.ctl")
    with mock.patch.object(
        scanner.client,
        "version",
        return_value="ClamAV 0.99.2/23992/Fri Oct 27 05:04:12 2017",
    ) as version:
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


def test_clamdscanner_scan(settings):
    OKAY_RET = ("OK", None)
    ERROR_RET = ("ERROR", "Permission denied")
    FOUND_RET = ("FOUND", "Eicar-Test-Signature")

    def patch(pass_by_stream, pass_by_reference, scanner, ret=OKAY_RET, excepts=False):
        """Patch the scanner function and enable testing of exceptions raised
        by clamdscanner that we want to control. excepts can take an argument
        of True to pass a generic exception. excepts can also take an exception
        as an argument for better granularity.
        """
        pass_by_stream.return_value = {"stream": ret}
        pass_by_reference.return_value = {"/file": ret}
        deps = namedtuple("deps", ["pass_by_stream", "pass_by_reference"])(
            pass_by_stream=pass_by_stream,
            pass_by_reference=pass_by_reference,
        )
        if excepts is not False:
            e = excepts
            if excepts is True:
                e = Exception("Testing an unmanaged exception.")
            deps.pass_by_stream.side_effect = e
            deps.pass_by_reference.side_effect = e
        return deps

    scanner = setup_clamdscanner(settings, stream=False)

    with mock.patch.object(
        scanner, "pass_by_stream"
    ) as pass_by_stream, mock.patch.object(
        scanner, "pass_by_reference"
    ) as pass_by_reference:
        deps = patch(pass_by_stream, pass_by_reference, scanner, ret=OKAY_RET)
        passed, state, details = scanner.scan("/file")
        assert passed is True
        assert state == "OK"
        assert details is None
        deps.pass_by_stream.assert_not_called()
        deps.pass_by_reference.assert_called_once()

    scanner = setup_clamdscanner(settings, stream=True)
    with mock.patch.object(
        scanner, "pass_by_stream"
    ) as pass_by_stream, mock.patch.object(
        scanner, "pass_by_reference"
    ) as pass_by_reference:
        deps = patch(pass_by_stream, pass_by_reference, scanner, ret=OKAY_RET)
        passed, state, details = scanner.scan("/file")
        assert passed is True
        assert state == "OK"
        assert details is None
        deps.pass_by_stream.assert_called_once()
        deps.pass_by_reference.assert_not_called()

    with mock.patch.object(
        scanner, "pass_by_stream"
    ) as pass_by_stream, mock.patch.object(
        scanner, "pass_by_reference"
    ) as pass_by_reference:
        patch(pass_by_stream, pass_by_reference, scanner, ret=ERROR_RET)
        passed, state, details = scanner.scan("/file")
        assert passed is False
        assert state == "ERROR"
        assert details == "Permission denied"

    with mock.patch.object(
        scanner, "pass_by_stream"
    ) as pass_by_stream, mock.patch.object(
        scanner, "pass_by_reference"
    ) as pass_by_reference:
        patch(pass_by_stream, pass_by_reference, scanner, ret=FOUND_RET)
        passed, state, details = scanner.scan("/file")
        assert passed is False
        assert state == "FOUND"
        assert details == "Eicar-Test-Signature"

    with mock.patch.object(
        scanner, "pass_by_stream"
    ) as pass_by_stream, mock.patch.object(
        scanner, "pass_by_reference"
    ) as pass_by_reference:
        # Testing a generic Exception returned by the clamdscan micorservice.
        patch(pass_by_stream, pass_by_reference, scanner, ret=OKAY_RET, excepts=True)
        passed, state, details = scanner.scan("/file")
        assert passed is False
        assert state is None
        assert details is None

    with mock.patch.object(
        scanner, "pass_by_stream"
    ) as pass_by_stream, mock.patch.object(
        scanner, "pass_by_reference"
    ) as pass_by_reference:
        # Testing a generic IOError that is not a broken pipe error that we're
        # expecting to be able to manage from clamdscan.
        patch(
            pass_by_stream,
            pass_by_reference,
            scanner,
            ret=OKAY_RET,
            excepts=OSError("Testing a generic IO Error"),
        )
        passed, state, details = scanner.scan("/file")
        assert passed is False
        assert state is None
        assert details is None

    with mock.patch.object(
        scanner, "pass_by_stream"
    ) as pass_by_stream, mock.patch.object(
        scanner, "pass_by_reference"
    ) as pass_by_reference:
        # Broken pipe is a known error from the clamd library.
        brokenpipe_error = OSError("Testing a broken pipe error")
        brokenpipe_error.errno = errno.EPIPE
        patch(
            pass_by_stream,
            pass_by_reference,
            scanner,
            ret=OKAY_RET,
            excepts=brokenpipe_error,
        )
        passed, state, details = scanner.scan("/file")
        assert passed is None
        assert state is None
        assert details is None

    with mock.patch.object(
        scanner, "pass_by_stream"
    ) as pass_by_stream, mock.patch.object(
        scanner, "pass_by_reference"
    ) as pass_by_reference:
        # The INSTREAM size limit error is known to us; test it here.
        instream_error = BufferTooLongError("INSTREAM size limit exceeded. ERROR.")
        patch(
            pass_by_stream,
            pass_by_reference,
            scanner,
            ret=OKAY_RET,
            excepts=instream_error,
        )
        passed, state, details = scanner.scan("/file")
        assert passed is None
        assert state is None
        assert details is None

    with mock.patch.object(
        scanner, "pass_by_stream"
    ) as pass_by_stream, mock.patch.object(
        scanner, "pass_by_reference"
    ) as pass_by_reference:
        # The clamd library can return a further error code here, and we we test it
        # to make sure that if it does, it is managed.
        connection_error = ConnectionError("Error while reading from socket.")
        patch(
            pass_by_stream,
            pass_by_reference,
            scanner,
            ret=OKAY_RET,
            excepts=connection_error,
        )
        passed, state, details = scanner.scan("/file")
        assert passed is None
        assert state is None
        assert details is None
