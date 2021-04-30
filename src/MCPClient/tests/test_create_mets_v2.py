# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys
import uuid

from lxml import etree
import pytest
import six

from job import Job
from main.models import (
    SIP,
    File,
    DublinCore,
    MetadataAppliesToType,
    Event,
    RightsStatement,
)
from namespaces import NSMAP

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
from create_mets_v2 import main, createDMDIDsFromCSVMetadata


def test_createDMDIDsFromCSVMetadata_finds_non_ascii_paths(mocker):
    dmd_secs_creator_mock = mocker.patch(
        "create_mets_v2.createDmdSecsFromCSVParsedMetadata", return_value=[]
    )
    state_mock = mocker.Mock(
        **{
            "CSV_METADATA": {
                six.ensure_str("montréal"): "montreal metadata",
                six.ensure_str("dvořák"): "dvorak metadata",
            }
        }
    )

    createDMDIDsFromCSVMetadata(None, "montréal", state_mock)
    createDMDIDsFromCSVMetadata(None, "toronto", state_mock)
    createDMDIDsFromCSVMetadata(None, "dvořák", state_mock)

    dmd_secs_creator_mock.assert_has_calls(
        [
            mocker.call(None, "montreal metadata", state_mock),
            mocker.call(None, {}, state_mock),
            mocker.call(None, "dvorak metadata", state_mock),
        ]
    )


@pytest.fixture()
def job():
    return Job("stub", "stub", [])


@pytest.fixture()
def sip_path(tmp_path):
    sip_path = tmp_path / "pictures3-5904fdd7-85df-4d7e-99be-2d3bceba7f7a"
    sip_path.mkdir()

    return sip_path


@pytest.fixture()
def objects_path(sip_path):
    objects_path = sip_path / "objects"
    objects_path.mkdir()

    return objects_path


@pytest.fixture()
def empty_dir_path(objects_path):
    empty_dir_path = objects_path / "empty_dir"
    empty_dir_path.mkdir()

    return empty_dir_path


@pytest.fixture()
def metadata_csv(sip, sip_path, objects_path):
    (objects_path / "metadata").mkdir()
    metadata_csv = objects_path / "metadata" / "metadata.csv"
    metadata_csv.write_text("Filename,dc.title\nobjects/file1,File 1")

    originallocation = "".join(
        [r"%transferDirectory%", str(metadata_csv.relative_to(sip_path))],
    )
    currentlocation = "".join(
        [r"%SIPDirectory%", str(metadata_csv.relative_to(sip_path))],
    )
    file_obj = File.objects.create(
        uuid=uuid.uuid4(),
        sip=sip,
        originallocation=originallocation,
        currentlocation=currentlocation,
        size=1024,
        filegrpuse="metadata",
        checksum="f0e4c2f76c58916ec258f246851bea091d14d4247a2fc3e18694461b1816e13b",
        checksumtype="sha256",
    )

    return file_obj


@pytest.fixture()
def sip(db, sip_path, objects_path):
    return SIP.objects.create(
        uuid=uuid.uuid4(),
        sip_type="SIP",
        currentpath=str(sip_path),
    )


@pytest.fixture()
def sip_dublincore(sip):
    return DublinCore.objects.create(
        metadataappliestotype_id=MetadataAppliesToType.SIP_TYPE,
        metadataappliestoidentifier=sip.pk,
        title="Hello World Contents",
        is_part_of="23456",
        identifier="12345",
    )


@pytest.fixture()
def file_path(objects_path):
    file_path = objects_path / "file1"
    file_path.write_text("Hello world")

    return file_path


@pytest.fixture()
def file_obj(db, sip, sip_path, file_path):
    originallocation = "".join(
        [r"%transferDirectory%", str(file_path.relative_to(sip_path))],
    )
    currentlocation = "".join(
        [r"%SIPDirectory%", str(file_path.relative_to(sip_path))],
    )
    file_obj = File.objects.create(
        uuid=uuid.uuid4(),
        sip=sip,
        originallocation=originallocation,
        currentlocation=currentlocation,
        size=113318,
        filegrpuse="original",
        checksum="35e0cc683d75704fc5b04fc3633f6c654e10cd3af57471271f370309c7ff9dba",
        checksumtype="sha256",
    )

    Event.objects.create(
        event_id=uuid.uuid4(),
        file_uuid=file_obj,
        event_type="message digest calculation",
        event_detail='program="python"; module="hashlib.sha256()"',
        event_outcome_detail="35e0cc683d75704fc5b04fc3633f6c654e10cd3af57471271f370309c7ff9dba",
    )

    rights = RightsStatement.objects.create(
        metadataappliestotype_id=MetadataAppliesToType.FILE_TYPE,
        metadataappliestoidentifier=file_obj.uuid,
        rightsstatementidentifiertype="UUID",
        rightsstatementidentifiervalue=str(uuid.uuid4()),
    )
    rights_granted = rights.rightsstatementrightsgranted_set.create(
        act="Disseminate", startdate="2001-01-01", enddateopen=True
    )
    rights_granted.restrictions.create(restriction="Allow")
    rights_granted.notes.create(rightsgrantednote="A grant note")
    rights_granted.notes.create(rightsgrantednote="Another grant note")

    return file_obj


def test_simple_mets(job, sip_path, sip, file_obj):
    mets_path = sip_path / "METS.{}.xml".format(sip.uuid)
    main(
        job,
        sipType="SIP",
        baseDirectoryPath=sip.currentpath,
        XMLFile=six.text_type(mets_path),
        sipUUID=sip.pk,
        includeAmdSec=False,
        createNormativeStructmap=False,
    )
    mets_xml = etree.parse(mets_path.open())
    amdsecs = mets_xml.xpath(
        ".//mets:amdSec",
        namespaces=NSMAP,
    )
    dublincore = mets_xml.xpath(
        ".//mets:xmlData/dcterms:dublincore",
        namespaces=NSMAP,
    )
    structmap_types = mets_xml.xpath(
        ".//mets:structMap/@TYPE",
        namespaces=NSMAP,
    )

    assert len(amdsecs) == 0
    assert len(dublincore) == 0
    assert len(structmap_types) == 1
    assert "physical" in structmap_types


def test_aip_mets_includes_dublincore(job, sip_path, sip, sip_dublincore, file_obj):
    mets_path = sip_path / "METS.{}.xml".format(sip.uuid)
    main(
        job,
        sipType="SIP",
        baseDirectoryPath=sip.currentpath,
        XMLFile=six.text_type(mets_path),
        sipUUID=sip.pk,
        includeAmdSec=True,
        createNormativeStructmap=True,
    )
    mets_xml = etree.parse(mets_path.open())
    objects_div = mets_xml.xpath(
        ".//mets:div[@LABEL='objects']",
        namespaces=NSMAP,
    )
    dmdid = objects_div[0].get("DMDID")
    dublincore = mets_xml.xpath(
        ".//mets:dmdSec[@ID='" + dmdid + "']/*/mets:xmlData/dcterms:dublincore/*",
        namespaces=NSMAP,
    )

    assert len(objects_div) == 2
    assert len(dublincore) == 3
    assert dublincore[0].tag == "{http://purl.org/dc/elements/1.1/}title"
    assert dublincore[0].text == "Hello World Contents"
    assert dublincore[1].tag == "{http://purl.org/dc/elements/1.1/}identifier"
    assert dublincore[1].text == "12345"
    assert dublincore[2].tag == "{http://purl.org/dc/terms/}isPartOf"
    assert dublincore[2].text == "23456"


def test_aip_mets_includes_dublincore_via_metadata_csv(
    job, sip_path, sip, file_obj, metadata_csv
):
    mets_path = sip_path / "METS.{}.xml".format(sip.uuid)
    main(
        job,
        sipType="SIP",
        baseDirectoryPath=sip.currentpath,
        XMLFile=six.text_type(mets_path),
        sipUUID=sip.pk,
        includeAmdSec=True,
        createNormativeStructmap=True,
    )
    mets_xml = etree.parse(mets_path.open())
    file_div = mets_xml.xpath(
        ".//mets:div[@LABEL='file1']",
        namespaces=NSMAP,
    )
    dmdid = file_div[0].get("DMDID")
    dublincore = mets_xml.xpath(
        ".//mets:dmdSec[@ID='" + dmdid + "']/*/mets:xmlData/dcterms:dublincore/*",
        namespaces=NSMAP,
    )

    assert len(file_div) == 2
    assert len(dublincore) == 1
    assert dublincore[0].tag == "{http://purl.org/dc/elements/1.1/}title"
    assert dublincore[0].text == "File 1"


def test_aip_mets_normative_directory_structure(
    job, sip_path, sip, file_obj, metadata_csv, empty_dir_path
):
    mets_path = sip_path / "METS.{}.xml".format(sip.uuid)
    main(
        job,
        sipType="SIP",
        baseDirectoryPath=sip.currentpath,
        XMLFile=six.text_type(mets_path),
        sipUUID=sip.pk,
        includeAmdSec=True,
        createNormativeStructmap=True,
    )
    mets_xml = etree.parse(mets_path.open())
    normative_structmap = mets_xml.xpath(
        ".//mets:structMap[@LABEL='Normative Directory Structure']", namespaces=NSMAP
    )

    assert (
        normative_structmap[0]
        .xpath(
            ".//mets:div[@LABEL='pictures3-5904fdd7-85df-4d7e-99be-2d3bceba7f7a']",
            namespaces=NSMAP,
        )[0]
        .get("DMDID")
        == "dmdSec_2"
    )
    assert (
        normative_structmap[0]
        .xpath(".//mets:div[@LABEL='file1']", namespaces=NSMAP)[0]
        .get("DMDID")
        == "dmdSec_3"
    )
    assert (
        normative_structmap[0]
        .xpath(".//mets:div[@LABEL='empty_dir']", namespaces=NSMAP)[0]
        .get("DMDID")
        == "dmdSec_1"
    )
