# -*- coding: UTF-8 -*-
import os
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from dicts import ReplacementDict, ChoicesDict

from main import models

TRANSFER = models.Transfer(
    uuid='fb0aa04d-8547-46fc-bb7f-288ea5827d2c',
    currentlocation='%sharedDirectory%foo',
    type='Standard',
    accessionid='accession1',
    hidden=True
)

SIP = models.SIP(
    uuid='c58794fd-4fb8-42a0-b9be-e75191696ab8',
    currentpath='%sharedDirectory%bar',
    hidden=True
)

FILE = models.File(
    uuid='ee61d09b-2790-4980-827a-135346657eec',
    transfer=TRANSFER,
    originallocation='%sharedDirectory%orig',
    currentlocation='%sharedDirectory%new',
    filegrpuse='original'
)


def test_alternate_replacementdict_constructor():
    """
    This constructor allows serialized Python strings to be expanded
    into ReplacementDict instances.
    """

    d = {"foo": "bar"}
    assert ReplacementDict(d) == ReplacementDict.fromstring(str(d))


def test_alternate_choicesdict_constructor():
    d = {"foo": "bar"}
    assert ChoicesDict(d) == ChoicesDict.fromstring(str(d))


def test_replacementdict_replace():
    d = ReplacementDict({"%PREFIX%": "/usr/local"})
    assert d.replace("%PREFIX%/bin/") == ["/usr/local/bin/"]


def test_replacementdict_model_constructor_transfer():
    rd = ReplacementDict.frommodel(sip=TRANSFER, file_=FILE, type_='transfer')

    # Transfer-specific variables
    assert rd['%SIPUUID%'] == TRANSFER.uuid
    assert rd['%relativeLocation%'] == TRANSFER.currentlocation
    assert rd['%currentPath%'] == TRANSFER.currentlocation
    assert rd['%SIPDirectory%'] == TRANSFER.currentlocation
    assert rd['%transferDirectory%'] == TRANSFER.currentlocation
    assert rd['%SIPDirectoryBasename%'] == os.path.basename(TRANSFER.currentlocation)
    assert rd['%SIPLogsDirectory%'] == os.path.join(TRANSFER.currentlocation, 'logs/')
    assert rd['%SIPObjectsDirectory%'] == os.path.join(TRANSFER.currentlocation, 'objects/')
    # no, not actually relative
    assert rd['%relativeLocation%'] == TRANSFER.currentlocation

    # File-specific variables
    assert rd['%fileUUID%'] == FILE.uuid
    assert rd['%originalLocation%'] == FILE.originallocation
    assert rd['%currentLocation%'] == FILE.currentlocation
    assert rd['%fileGrpUse%'] == FILE.filegrpuse


def test_replacementdict_model_constructor_sip():
    rd = ReplacementDict.frommodel(sip=SIP, file_=FILE, type_='sip')

    # SIP-specific variables
    assert rd['%SIPUUID%'] == SIP.uuid
    assert rd['%relativeLocation%'] == SIP.currentpath
    assert rd['%currentPath%'] == SIP.currentpath
    assert rd['%SIPDirectory%'] == SIP.currentpath
    assert not '%transferDirectory%' in rd
    assert rd['%SIPDirectoryBasename%'] == os.path.basename(SIP.currentpath)
    assert rd['%SIPLogsDirectory%'] == os.path.join(SIP.currentpath, 'logs/')
    assert rd['%SIPObjectsDirectory%'] == os.path.join(SIP.currentpath, 'objects/')
    assert rd['%relativeLocation%'] == SIP.currentpath

    # File-specific variables
    assert rd['%fileUUID%'] == FILE.uuid
    assert rd['%originalLocation%'] == FILE.originallocation
    assert rd['%currentLocation%'] == FILE.currentlocation
    assert rd['%fileGrpUse%'] == FILE.filegrpuse


def test_replacementdict_model_constructor_file_only():
    rd = ReplacementDict.frommodel(file_=FILE, type_='file')

    assert rd['%fileUUID%'] == FILE.uuid
    assert rd['%originalLocation%'] == FILE.originallocation
    assert rd['%currentLocation%'] == FILE.currentlocation
    assert rd['%relativeLocation%'] == FILE.currentlocation
    assert rd['%fileGrpUse%'] == FILE.filegrpuse


def test_replacementdict_options():
    d = ReplacementDict({'%relativeLocation%': 'bar'})
    assert d.to_gnu_options() == ['--relative-location=bar']


def test_replacementdict_replace_returns_bytestring():
    in_str = u"%originalLocation%/location/การแปล"
    assert type(in_str) == unicode

    d = ReplacementDict({'%originalLocation%': '\x82\xdb\x82\xc1\x82\xd5\x82\xe9\x83\x81\x83C\x83\x8b'})
    out_str = d.replace(in_str)[0]
    assert type(out_str) == str
