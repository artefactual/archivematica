import os

import pytest

from archivematica.archivematicaCommon.dicts import ReplacementDict
from archivematica.archivematicaCommon.dicts import setup as setup_dicts
from archivematica.dashboard.main import models
from tests.factories import TransferFactory


@pytest.fixture
def TRANSFER(make_transfer: TransferFactory) -> models.Transfer:
    return make_transfer(
        currentlocation="%sharedDirectory%foo",
        type="Standard",
        accessionid="accession1",
        hidden=True,
    )


@pytest.fixture
def SIP():
    return models.SIP(
        currentpath="%sharedDirectory%bar",
        hidden=True,
    )


@pytest.fixture
def FILE(db, TRANSFER):
    return models.File.objects.create(
        transfer=TRANSFER,
        originallocation=b"%sharedDirectory%orig",
        currentlocation=b"%sharedDirectory%new",
        filegrpuse="original",
    )


@pytest.fixture(scope="module", autouse=True)
def with_dicts():
    setup_dicts(
        shared_directory="/shared/",
        processing_directory="/processing/",
        watch_directory="/watch/",
        rejected_directory="/rejected/",
    )


def test_replacementdict_replace():
    d = ReplacementDict({"%PREFIX%": "/usr/local"})
    assert d.replace("%PREFIX%/bin/") == ["/usr/local/bin/"]


def test_replacementdict_model_constructor_transfer(TRANSFER, FILE):
    rd = ReplacementDict.frommodel(sip=TRANSFER, file_=FILE, type_="transfer")

    # Transfer-specific variables
    assert rd["%SIPUUID%"] == str(TRANSFER.uuid)
    assert rd["%relativeLocation%"] == TRANSFER.currentlocation
    assert rd["%currentPath%"] == TRANSFER.currentlocation
    assert rd["%SIPDirectory%"] == TRANSFER.currentlocation
    assert rd["%transferDirectory%"] == TRANSFER.currentlocation
    assert rd["%SIPDirectoryBasename%"] == os.path.basename(TRANSFER.currentlocation)
    assert rd["%SIPLogsDirectory%"] == os.path.join(TRANSFER.currentlocation, "logs/")
    assert rd["%SIPObjectsDirectory%"] == os.path.join(
        TRANSFER.currentlocation, "objects/"
    )
    # no, not actually relative
    assert rd["%relativeLocation%"] == TRANSFER.currentlocation

    # File-specific variables
    assert rd["%fileUUID%"] == str(FILE.uuid)
    assert rd["%originalLocation%"] == FILE.originallocation.decode()
    assert rd["%currentLocation%"] == FILE.currentlocation.decode()
    assert rd["%fileGrpUse%"] == FILE.filegrpuse


def test_replacementdict_model_constructor_sip(SIP, FILE):
    rd = ReplacementDict.frommodel(sip=SIP, file_=FILE, type_="sip")

    # SIP-specific variables
    assert rd["%SIPUUID%"] == str(SIP.uuid)
    assert rd["%relativeLocation%"] == SIP.currentpath
    assert rd["%currentPath%"] == SIP.currentpath
    assert rd["%SIPDirectory%"] == SIP.currentpath
    assert "%transferDirectory%" not in rd
    assert rd["%SIPDirectoryBasename%"] == os.path.basename(SIP.currentpath)
    assert rd["%SIPLogsDirectory%"] == os.path.join(SIP.currentpath, "logs/")
    assert rd["%SIPObjectsDirectory%"] == os.path.join(SIP.currentpath, "objects/")
    assert rd["%relativeLocation%"] == SIP.currentpath

    # File-specific variables
    assert rd["%fileUUID%"] == str(FILE.uuid)
    assert rd["%originalLocation%"] == FILE.originallocation.decode()
    assert rd["%currentLocation%"] == FILE.currentlocation.decode()
    assert rd["%fileGrpUse%"] == FILE.filegrpuse


def test_replacementdict_model_constructor_file_only(FILE):
    rd = ReplacementDict.frommodel(file_=FILE, type_="file")

    assert rd["%fileUUID%"] == str(FILE.uuid)
    assert rd["%originalLocation%"] == FILE.originallocation.decode()
    assert rd["%currentLocation%"] == FILE.currentlocation.decode()
    assert rd["%relativeLocation%"] == FILE.currentlocation.decode()
    assert rd["%fileGrpUse%"] == FILE.filegrpuse


@pytest.mark.parametrize(
    "replacementdict_key, regex_key_value",
    [
        ("%relativeLocation%", "--relative-location=bar"),
        ("%SIPUUID%", "--sipuuid=bar"),
        ("%SIPName%", "--sip-name=bar"),
        ("%fileUUID%", "--file-uuid=bar"),
        ("%SIPDirectoryBasename%", "--sip-directory-basename=bar"),
        ("%SIPLogsDirectory%", "--sip-logs-directory=bar"),
        ("%sipLogs%", "--sip-logs=bar"),
        ("%outputLocation%", "--output-location=bar"),
        ("%TransferDirectory%", "--transfer-directory=bar"),
    ],
    ids=[
        "relative-location",
        "sipuuid",
        "sipname",
        "fileuuid",
        "sip-directory-basename",
        "sip-logs-directory",
        "sip-logs",
        "output-location",
        "transfer-directory",
    ],
)
def test_replacementdict_options(replacementdict_key, regex_key_value):
    d = ReplacementDict({replacementdict_key: "bar"})
    assert d.to_gnu_options() == [regex_key_value]
