import os

import pytest
from dicts import ChoicesDict
from dicts import ReplacementDict
from dicts import setup as setup_dicts
from main import models


@pytest.fixture
def TRANSFER(db):
    return models.Transfer.objects.create(
        uuid="fb0aa04d-8547-46fc-bb7f-288ea5827d2c",
        currentlocation="%sharedDirectory%foo",
        type="Standard",
        accessionid="accession1",
        hidden=True,
    )


@pytest.fixture
def SIP():
    return models.SIP(
        uuid="c58794fd-4fb8-42a0-b9be-e75191696ab8",
        currentpath="%sharedDirectory%bar",
        hidden=True,
    )


@pytest.fixture
def FILE(db, TRANSFER):
    return models.File.objects.create(
        uuid="ee61d09b-2790-4980-827a-135346657eec",
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


def test_replacementdict_model_constructor_transfer(TRANSFER, FILE):
    rd = ReplacementDict.frommodel(sip=TRANSFER, file_=FILE, type_="transfer")

    # Transfer-specific variables
    assert rd["%SIPUUID%"] == TRANSFER.uuid
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
    assert rd["%fileUUID%"] == FILE.uuid
    assert rd["%originalLocation%"] == FILE.originallocation.decode()
    assert rd["%currentLocation%"] == FILE.currentlocation.decode()
    assert rd["%fileGrpUse%"] == FILE.filegrpuse


def test_replacementdict_model_constructor_sip(SIP, FILE):
    rd = ReplacementDict.frommodel(sip=SIP, file_=FILE, type_="sip")

    # SIP-specific variables
    assert rd["%SIPUUID%"] == SIP.uuid
    assert rd["%relativeLocation%"] == SIP.currentpath
    assert rd["%currentPath%"] == SIP.currentpath
    assert rd["%SIPDirectory%"] == SIP.currentpath
    assert "%transferDirectory%" not in rd
    assert rd["%SIPDirectoryBasename%"] == os.path.basename(SIP.currentpath)
    assert rd["%SIPLogsDirectory%"] == os.path.join(SIP.currentpath, "logs/")
    assert rd["%SIPObjectsDirectory%"] == os.path.join(SIP.currentpath, "objects/")
    assert rd["%relativeLocation%"] == SIP.currentpath

    # File-specific variables
    assert rd["%fileUUID%"] == FILE.uuid
    assert rd["%originalLocation%"] == FILE.originallocation.decode()
    assert rd["%currentLocation%"] == FILE.currentlocation.decode()
    assert rd["%fileGrpUse%"] == FILE.filegrpuse


def test_replacementdict_model_constructor_file_only(FILE):
    rd = ReplacementDict.frommodel(file_=FILE, type_="file")

    assert rd["%fileUUID%"] == FILE.uuid
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
