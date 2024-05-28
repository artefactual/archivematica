import uuid
from contextlib import ExitStack as does_not_raise

import pytest
from client.job import Job
from create_mets_v2 import createDMDIDsFromCSVMetadata
from create_mets_v2 import main
from lxml import etree
from main.models import SIP
from main.models import DublinCore
from main.models import Event
from main.models import File
from main.models import MetadataAppliesToType
from main.models import RightsStatement
from main.models import SIPArrange
from namespaces import NSMAP


def test_createDMDIDsFromCSVMetadata_finds_non_ascii_paths(mocker):
    dmd_secs_creator_mock = mocker.patch(
        "create_mets_v2.createDmdSecsFromCSVParsedMetadata", return_value=[]
    )
    state_mock = mocker.Mock(
        **{
            "CSV_METADATA": {
                "montréal": "montreal metadata",
                "dvořák": "dvorak metadata",
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
        originallocation=originallocation.encode(),
        currentlocation=currentlocation.encode(),
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
        originallocation=originallocation.encode(),
        currentlocation=currentlocation.encode(),
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
    mets_path = sip_path / f"METS.{sip.uuid}.xml"
    main(
        job,
        sipType="SIP",
        baseDirectoryPath=sip.currentpath,
        XMLFile=str(mets_path),
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
    mets_path = sip_path / f"METS.{sip.uuid}.xml"
    main(
        job,
        sipType="SIP",
        baseDirectoryPath=sip.currentpath,
        XMLFile=str(mets_path),
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
    mets_path = sip_path / f"METS.{sip.uuid}.xml"
    main(
        job,
        sipType="SIP",
        baseDirectoryPath=sip.currentpath,
        XMLFile=str(mets_path),
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
    mets_path = sip_path / f"METS.{sip.uuid}.xml"
    main(
        job,
        sipType="SIP",
        baseDirectoryPath=sip.currentpath,
        XMLFile=str(mets_path),
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


@pytest.mark.parametrize(
    "fail_on_error, errors, expectation",
    [
        (True, ["xml_validation_error"], pytest.raises(Exception)),
        (True, [], does_not_raise()),
        (False, ["xml_validation_error"], does_not_raise()),
        (False, [], does_not_raise()),
        (None, [], does_not_raise()),
    ],
)
def test_xml_validation_fail_on_error(
    mocker, settings, job, sip_path, sip, file_obj, fail_on_error, errors, expectation
):
    mock_mets = mocker.Mock(
        **{
            "serialize.return_value": etree.Element("tag"),
            "get_subsections_counts.return_value": {},
        }
    )
    mocker.patch(
        "create_mets_v2.archivematicaCreateMETSMetadataXML.process_xml_metadata",
        return_value=(mock_mets, errors),
    )
    if fail_on_error is not None:
        settings.XML_VALIDATION_FAIL_ON_ERROR = fail_on_error
    with expectation:
        main(
            job,
            sipType="SIP",
            baseDirectoryPath=sip.currentpath,
            XMLFile=str(sip_path / "METS.xml"),
            sipUUID=sip.pk,
            includeAmdSec=False,
            createNormativeStructmap=False,
        )
    if errors:
        assert (
            "Error(s) processing and/or validating XML metadata:\n\t- xml_validation_error"
            in job.get_stderr()
        )


@pytest.fixture
def arranged_sip(db, tmp_path):
    # Create an arranged SIP.
    sip_path = tmp_path / "sip"
    sip_path.mkdir()
    sip = SIP.objects.create(
        sip_type="SIP",
        currentpath=str(sip_path),
    )

    # Create the directory structure representing the new arrangement.
    objects_path = sip_path / "objects"
    objects_path.mkdir()
    SIPArrange.objects.create(sip=sip, arrange_path=b".")

    for path, level_of_description in [
        ((sip_path / "objects" / "subdir"), "Series"),
        ((sip_path / "objects" / "subdir" / "first"), "Subseries"),
        ((sip_path / "objects" / "subdir" / "second"), "Subseries"),
    ]:
        path.mkdir()
        SIPArrange.objects.create(
            sip=sip,
            arrange_path=bytes(path.relative_to(objects_path)),
            level_of_description=level_of_description,
        )

    # Add files to the arrangement.
    for path in [
        (sip_path / "objects" / "file1"),
        (sip_path / "objects" / "subdir" / "file2"),
        (sip_path / "objects" / "subdir" / "first" / "file3"),
        (sip_path / "objects" / "subdir" / "second" / "file4"),
    ]:
        path.touch()
        f = File.objects.create(
            originallocation=f"%TransferDirectory%{path.relative_to(sip_path)}".encode(),
            currentlocation=f"%SIPDirectory%{path.relative_to(sip_path)}".encode(),
            sip=sip,
            filegrpuse="original",
        )
        SIPArrange.objects.create(
            sip=sip,
            arrange_path=bytes(path.relative_to(objects_path)),
            level_of_description="File",
            file_uuid=f.uuid,
        )

    return sip


def test_structmap_is_created_from_sip_arrangement(job, arranged_sip):
    mets_path = f"{arranged_sip.currentpath}/METS.{arranged_sip.uuid}.xml"

    main(
        job,
        sipType="SIP",
        baseDirectoryPath=arranged_sip.currentpath,
        XMLFile=mets_path,
        sipUUID=arranged_sip.pk,
        includeAmdSec=False,
        createNormativeStructmap=False,
    )

    # Verify the logical structMap for the SIP arrangement.
    mets_xml = etree.parse(mets_path)
    logical_structmap = mets_xml.find(
        './/mets:structMap[@TYPE="logical"]', namespaces=NSMAP
    )
    assert logical_structmap.attrib["LABEL"] == "Hierarchical"

    # Get the relevant elements from the logical structMap.
    sip_div = logical_structmap.find('mets:div[@LABEL="sip"]', namespaces=NSMAP)
    objects_div = sip_div.find('mets:div[@LABEL="objects"]', namespaces=NSMAP)
    file1_div = objects_div.find('mets:div[@LABEL="file1"]', namespaces=NSMAP)
    subdir_div = objects_div.find('mets:div[@LABEL="subdir"]', namespaces=NSMAP)
    file2_div = subdir_div.find('mets:div[@LABEL="file2"]', namespaces=NSMAP)
    subdir_first_div = subdir_div.find('mets:div[@LABEL="first"]', namespaces=NSMAP)
    file3_div = subdir_first_div.find('mets:div[@LABEL="file3"]', namespaces=NSMAP)
    subdir_second_div = subdir_div.find('mets:div[@LABEL="second"]', namespaces=NSMAP)
    file4_div = subdir_second_div.find('mets:div[@LABEL="file4"]', namespaces=NSMAP)

    # Verify the levels of descriptions are preserved.
    assert file1_div.attrib["TYPE"] == "File"
    assert subdir_div.attrib["TYPE"] == "Series"
    assert file2_div.attrib["TYPE"] == "File"
    assert subdir_first_div.attrib["TYPE"] == "Subseries"
    assert file3_div.attrib["TYPE"] == "File"
    assert subdir_second_div.attrib["TYPE"] == "Subseries"
    assert file4_div.attrib["TYPE"] == "File"
