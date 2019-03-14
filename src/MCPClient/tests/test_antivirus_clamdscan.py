"""Tests for the archivematica_clamscan.py client script."""

from __future__ import print_function

import os
import sys
import errno

from collections import namedtuple
from clamd import (
    ClamdNetworkSocket,
    ClamdUnixSocket,
    BufferTooLongError,
    ConnectionError,
)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))

import archivematica_clamscan


def setup_clamdscanner(
    settings, addr="/var/run/clamav/clamd.ctl", timeout=10, stream=False
):
    settings.CLAMAV_SERVER = addr
    settings.CLAMAV_CLIENT_TIMEOUT = timeout
    settings.CLAMAV_PASS_BY_STREAM = stream

    return archivematica_clamscan.ClamdScanner()


def test_clamdscanner_version_props(mocker, settings):
    scanner = setup_clamdscanner(settings)
    mocker.patch.object(
        scanner,
        "version_attrs",
        return_value=("ClamAV 0.99.2", "23992/Fri Oct 27 05:04:12 2017"),
    )

    assert scanner.program() == "ClamAV (clamd)"
    assert scanner.version() == "ClamAV 0.99.2"
    assert scanner.virus_definitions() == "23992/Fri Oct 27 05:04:12 2017"


def test_clamdscanner_version_attrs(mocker, settings):
    scanner = setup_clamdscanner(settings, addr="/var/run/clamav/clamd.ctl")
    version = mocker.patch.object(
        scanner.client,
        "version",
        return_value="ClamAV 0.99.2/23992/Fri Oct 27 05:04:12 2017",
    )

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
    OKAY_RET = ("OK", None)
    ERROR_RET = ("ERROR", "Permission denied")
    FOUND_RET = ("FOUND", "Eicar-Test-Signature")

    def patch(scanner, ret=OKAY_RET, excepts=False):
        """Patch the scanner function and enable testing of exceptions raised
        by clamdscanner that we want to control. excepts can take an argument
        of True to pass a generic exception. excepts can also take an exception
        as an argument for better granularity.
        """
        deps = namedtuple("deps", ["pass_by_stream", "pass_by_reference"])(
            pass_by_stream=mocker.patch.object(
                scanner, "pass_by_stream", return_value={"stream": ret}
            ),
            pass_by_reference=mocker.patch.object(
                scanner, "pass_by_reference", return_value={"/file": ret}
            ),
        )
        if excepts is not False:
            e = excepts
            if excepts is True:
                e = Exception("Testing an unmanaged exception.")
            deps.pass_by_stream.side_effect = e
            deps.pass_by_reference.side_effect = e
        return deps

    scanner = setup_clamdscanner(settings, stream=False)
    deps = patch(scanner, ret=OKAY_RET)
    passed, state, details = scanner.scan("/file")
    assert passed is True
    assert state == "OK"
    assert details is None
    deps.pass_by_stream.assert_not_called()
    deps.pass_by_reference.assert_called_once()

    scanner = setup_clamdscanner(settings, stream=True)
    deps = patch(scanner, ret=OKAY_RET)
    passed, state, details = scanner.scan("/file")
    assert passed is True
    assert state == "OK"
    assert details is None
    deps.pass_by_stream.assert_called_once()
    deps.pass_by_reference.assert_not_called()

    patch(scanner, ret=ERROR_RET)
    passed, state, details = scanner.scan("/file")
    assert passed is False
    assert state == "ERROR"
    assert details == "Permission denied"

    patch(scanner, ret=FOUND_RET)
    passed, state, details = scanner.scan("/file")
    assert passed is False
    assert state == "FOUND"
    assert details == "Eicar-Test-Signature"

    # Testing a generic Exception returned by the clamdscan micorservice.
    patch(scanner, ret=OKAY_RET, excepts=True)
    passed, state, details = scanner.scan("/file")
    assert passed is False
    assert state is None
    assert details is None

    # Testing a generic IOError that is not a broken pipe error that we're
    # expecting to be able to manage from clamdscan.
    patch(scanner, ret=OKAY_RET, excepts=IOError("Testing a generic IO Error"))
    passed, state, details = scanner.scan("/file")
    assert passed is False
    assert state is None
    assert details is None

    # Broken pipe is a known error from the clamd library.
    brokenpipe_error = IOError("Testing a broken pipe error")
    brokenpipe_error.errno = errno.EPIPE
    patch(scanner, ret=OKAY_RET, excepts=brokenpipe_error)
    passed, state, details = scanner.scan("/file")
    assert passed is None
    assert state is None
    assert details is None

    # The INSTREAM size limit error is known to us; test it here.
    instream_error = BufferTooLongError("INSTREAM size limit exceeded. ERROR.")
    patch(scanner, ret=OKAY_RET, excepts=instream_error)
    passed, state, details = scanner.scan("/file")
    assert passed is None
    assert state is None
    assert details is None

    # The clamd library can return a further error code here, and we we test it
    # to make sure that if it does, it is managed.
    connection_error = ConnectionError("Error while reading from socket.")
    patch(scanner, ret=OKAY_RET, excepts=connection_error)
    passed, state, details = scanner.scan("/file")
    assert passed is None
    assert state is None
    assert details is None
