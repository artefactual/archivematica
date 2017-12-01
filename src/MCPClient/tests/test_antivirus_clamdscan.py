# -*- coding: utf8 -*-
"""Tests for the archivematicaClamscan.py client script."""

from __future__ import print_function

import os
import sys

from collections import namedtuple
from clamd import ClamdNetworkSocket, ClamdUnixSocket

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(
    os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))

import archivematicaClamscan


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
