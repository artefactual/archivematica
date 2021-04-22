# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

import mock
import pytest
import unittest
import vcr

import elasticSearchFunctions

from lxml import etree
import six

try:
    from unittest.mock import ANY, patch
except ImportError:
    from mock import ANY, patch


from main.models import Directory, Identifier, SIP

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestElasticSearchFunctions(unittest.TestCase):
    @vcr.use_cassette(
        os.path.join(THIS_DIR, "fixtures", "test_elasticsearch_setup.yaml")
    )
    def setUp(self):
        elasticSearchFunctions.setup("elasticsearch:9200")
        self.client = elasticSearchFunctions.get_client()
        self.aip_uuid = "b34521a3-1c63-43dd-b901-584416f36c91"
        self.file_uuid = "268421a7-a986-4fa0-95c1-54176e508210"

    @vcr.use_cassette(os.path.join(THIS_DIR, "fixtures", "test_delete_aip.yaml"))
    def test_delete_aip(self):
        # Verify AIP exists
        results = self.client.search(
            index="aips",
            body={"query": {"term": {"uuid": self.aip_uuid}}},
            _source="uuid",
        )
        assert results["hits"]["total"] == 1
        assert results["hits"]["hits"][0]["_source"]["uuid"] == self.aip_uuid
        # Delete AIP
        elasticSearchFunctions.delete_aip(self.client, self.aip_uuid)
        # Verify AIP gone
        results = self.client.search(
            index="aips",
            body={"query": {"term": {"uuid": self.aip_uuid}}},
            _source="uuid",
        )
        assert results["hits"]["total"] == 0

    @vcr.use_cassette(os.path.join(THIS_DIR, "fixtures", "test_delete_aip_files.yaml"))
    def test_delete_aip_files(self):
        # Verify AIP files exist
        results = self.client.search(
            index="aipfiles", body={"query": {"term": {"AIPUUID": self.aip_uuid}}}
        )
        assert results["hits"]["total"] == 2
        # Delete AIP files
        elasticSearchFunctions.delete_aip_files(self.client, self.aip_uuid)
        # Verify AIP files gone
        results = self.client.search(
            index="aipfiles", body={"query": {"term": {"AIPUUID": self.aip_uuid}}}
        )
        assert results["hits"]["total"] == 0

    @vcr.use_cassette(os.path.join(THIS_DIR, "fixtures", "test_set_get_tags.yaml"))
    def test_set_get_tags(self):
        elasticSearchFunctions.set_file_tags(self.client, self.file_uuid, ["test"])
        assert elasticSearchFunctions.get_file_tags(self.client, self.file_uuid) == [
            "test"
        ]

    @vcr.use_cassette(
        os.path.join(THIS_DIR, "fixtures", "test_get_tags_no_matches.yaml")
    )
    def test_list_tags_fails_when_file_cant_be_found(self):
        with pytest.raises(elasticSearchFunctions.EmptySearchResultError):
            elasticSearchFunctions.get_file_tags(self.client, "no_such_file")

    @vcr.use_cassette(
        os.path.join(THIS_DIR, "fixtures", "test_set_tags_no_matches.yaml")
    )
    def test_set_tags_fails_when_file_cant_be_found(self):
        with pytest.raises(elasticSearchFunctions.EmptySearchResultError):
            elasticSearchFunctions.set_file_tags(self.client, "no_such_file", [])

    @pytest.mark.django_db
    @mock.patch("elasticSearchFunctions.get_dashboard_uuid")
    @mock.patch("elasticSearchFunctions.bulk")
    def test_index_mets_file_metadata(
        self, dummy_helpers_bulk, dummy_get_dashboard_uuid
    ):
        # Set up mocked functions
        dummy_get_dashboard_uuid.return_value = "test-uuid"
        indexed_data = {}

        def _bulk(client, actions, stats_only=False, *args, **kwargs):
            for item in actions:
                try:
                    dmd_section = item["_source"]["METS"]["dmdSec"]
                    metadata_container = dmd_section["mets:xmlData_dict_list"][0]
                    dc = metadata_container["dcterms:dublincore_dict_list"][0]
                except (KeyError, IndexError):
                    dc = None
                indexed_data[item["_source"]["filePath"]] = dc

        dummy_helpers_bulk.side_effect = _bulk

        # This METS file is a cut-down version of the AIP METS produced
        # using the SampleTransfers/DemoTransfer
        mets_file_path = os.path.join(
            THIS_DIR, "fixtures", "test_index_metadata-METS.xml"
        )
        mets_object_id = "771aa252-7930-4e68-b73e-f91416b1d4a4"
        uuid = "f42a260a-9b53-4555-847e-8a4329c81662"
        sipName = "DemoTransfer-{}".format(uuid)
        identifiers = []
        elasticSearchFunctions._index_aip_files(
            client=self.client,
            uuid=uuid,
            mets=etree.parse(mets_file_path).getroot(),
            name=sipName,
            identifiers=identifiers,
        )

        assert dummy_helpers_bulk.call_count == 1

        # ES should have indexed 12 files
        # - 5 content files
        # - 5 checksum and csv files in the metadata directory
        # - 2 files generated in the transfer process
        assert len(indexed_data) == 12

        # Metadata should have been indexed only for these content
        # files because they are listed in the metadata.csv file
        content_files_with_metadata = (
            {
                "path": (
                    "objects/View_from_lookout_over_Queenstown_"
                    "towards_the_Remarkables_in_spring.jpg"
                ),
                "title": (
                    "Morning view from lookout over Queenstown "
                    "towards the Remarkables in spring"
                ),
                "creator": "Pseudopanax at English Wikipedia",
            },
            {
                "path": "objects/beihai.tif",
                "title": "Beihai, Guanxi, China, 1988",
                "creator": (
                    "NASA/GSFC/METI/ERSDAC/JAROS and U.S./Japan " "ASTER Science Team"
                ),
            },
            {
                "path": "objects/bird.mp3",
                "title": "14000 Caen, France - Bird in my garden",
                "creator": "Nicolas Germain",
            },
            {
                "path": "objects/ocr-image.png",
                "title": "OCR image",
                "creator": "Tesseract",
            },
        )
        for file_metadata in content_files_with_metadata:
            dc = indexed_data[file_metadata["path"]]
            assert dc["dc:title"] == file_metadata["title"]
            assert dc["dc:creator"] == file_metadata["creator"]

        # There is no metadata for this content file because
        # it was not listed in the metadata.csv file
        assert indexed_data["objects/piiTestDataCreditCardNumbers.txt"] is None

        # Checksum and csv files in the metadata directory
        # won't have dublin core metadata indexed
        files_in_metadata_directory = (
            "checksum.md5",
            "checksum.sha1",
            "checksum.sha256",
            "metadata.csv",
            "rights.csv",
        )
        for filename in files_in_metadata_directory:
            path = "objects/metadata/transfers/DemoTransfer-{}/{}".format(
                mets_object_id, filename
            )
            assert indexed_data[path] is None

        # Neither will the generated files during the transfer process
        generated_files = ("dc.json", "directory_tree.txt")
        for filename in generated_files:
            path = "objects/metadata/transfers/DemoTransfer-{}/{}".format(
                mets_object_id, filename
            )
            assert indexed_data[path] is None

    @patch("elasticSearchFunctions.create_indexes_if_needed")
    def test_default_setup(self, patch):
        elasticSearchFunctions.setup("elasticsearch:9200")
        patch.assert_called_with(
            ANY, ["aips", "aipfiles", "transfers", "transferfiles"]
        )

    @patch("elasticSearchFunctions.create_indexes_if_needed")
    def test_only_aips_setup(self, patch):
        elasticSearchFunctions.setup("elasticsearch:9200", enabled=["aips"])
        patch.assert_called_with(ANY, ["aips", "aipfiles"])

    @patch("elasticSearchFunctions.create_indexes_if_needed")
    def test_only_transfers_setup(self, patch):
        elasticSearchFunctions.setup("elasticsearch:9200", enabled=["transfers"])
        patch.assert_called_with(ANY, ["transfers", "transferfiles"])

    @patch("elasticSearchFunctions.create_indexes_if_needed")
    def test_no_indexes_setup(self, patch):
        elasticSearchFunctions.setup("elasticsearch:9200", enabled=[])
        elasticSearchFunctions.setup("elasticsearch:9200", enabled=["unknown"])
        patch.assert_not_called()

    @patch("elasticsearch.client.indices.IndicesClient.create")
    @patch("elasticsearch.client.indices.IndicesClient.exists", return_value=True)
    def test_create_indexes_already_created(self, mock, patch):
        elasticSearchFunctions.create_indexes_if_needed(
            self.client, ["aips", "aipfiles", "transfers", "transferfiles"]
        )
        patch.assert_not_called()

    @patch("elasticsearch.client.indices.IndicesClient.create")
    @patch("elasticsearch.client.indices.IndicesClient.exists", return_value=False)
    def test_create_indexes_creation_calls(self, mock, patch):
        elasticSearchFunctions.create_indexes_if_needed(
            self.client, ["aips", "aipfiles", "transfers", "transferfiles"]
        )
        assert patch.call_count == 4

    @patch("elasticsearch.client.indices.IndicesClient.create")
    @patch("elasticsearch.client.indices.IndicesClient.exists", return_value=False)
    def test_create_indexes_wrong_index(self, mock, patch):
        elasticSearchFunctions.create_indexes_if_needed(
            self.client, ["aips", "aipfiles", "unknown"]
        )
        assert patch.call_count == 2


fileuuid_premisv3 = (
    {
        "filePath": "objects/evelyn_s_photo.jpg",
        "FILEUUID": "e9caf37c-93cb-4c37-ab5f-157c7d2611ac",
    },
    {
        "filePath": "objects/metadata/transfers/evelynphotos-96344c4e-bdaa-4e57-a271-408234de976d/directory_tree.txt",
        "FILEUUID": "61e56606-a1d6-456d-9c97-406feaa13b85",
    },
)
fileuuid_premisv2 = (
    {
        "filePath": "objects/metadata/transfers/MAPS2015-AM641-44f3ee8e-88fd-424c-9d2b-f35d69b148e1/directory_tree.txt",
        "FILEUUID": "44d3aa6d-8bb0-4cfb-bd93-f1121c08916e",
    },
    {
        "filePath": "objects/LEG1363.01.TIF",
        "FILEUUID": "0552c02b-8626-456f-89cc-bc5f3ce8a112",
    },
)
fileuuid_premisv2_no_ns = (
    {
        "filePath": "objects/AM68.csv",
        "FILEUUID": "fc0e52ca-a688-41c0-a10b-c1d36e21e804",
    },
    {
        "filePath": "objects/V00154.MPG",
        "FILEUUID": "3a6a182a-40a0-4c2b-9752-fc7e91ac1edf",
    },
    {
        "filePath": "objects/V00158.MPG",
        "FILEUUID": "431913ba-4379-4373-8798-cc5f2b9dd769",
    },
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "metsfile,fileuuid_dict,aipuuid,aipname",
    [
        (
            "test_index_fileuuid_METS_premisv3.xml",
            fileuuid_premisv3,
            "37abc30b-a258-4389-b1f2-67ccd330bc7e",
            "evelynphotos",
        ),
        (
            "test_index_fileuuid_METS_premisv2.xml",
            fileuuid_premisv2,
            "9559945a-52e8-4eb4-ac1a-e0e794e758fb",
            "MAPS2015-AM641",
        ),
        (
            "test_index_fileuuid_METS_premisv2_no_ns.xml",
            fileuuid_premisv2_no_ns,
            "bdcb560d-7ddd-4c13-8040-1e565b4eddff",
            "AM68",
        ),
    ],
)
@mock.patch("elasticSearchFunctions.get_dashboard_uuid")
@mock.patch("elasticSearchFunctions.bulk")
def test_index_aipfile_fileuuid(
    dummy_helpers_bulk,
    dummy_get_dashboard_uuid,
    metsfile,
    fileuuid_dict,
    aipuuid,
    aipname,
):
    """Check AIP file uuids are being correctly parsed from METS files.

    Mock _try_to_index() with a function that populates a dict
    indexed_data, with the fileuuids that _index_aip_files() obtained
    from the METS
    """

    dummy_get_dashboard_uuid.return_value = "test-uuid"

    indexed_data = {}

    def _bulk(client, actions, stats_only=False, *args, **kwargs):
        for item in actions:
            indexed_data[item["_source"]["filePath"]] = item["_source"]["FILEUUID"]

    dummy_helpers_bulk.side_effect = _bulk

    elasticSearchFunctions._index_aip_files(
        client=None,
        uuid=aipuuid,
        mets=etree.parse(os.path.join(THIS_DIR, "fixtures", metsfile)).getroot(),
        name="{}-{}".format(aipname, aipuuid),
        identifiers=[],
    )

    for file_uuid in fileuuid_dict:
        assert indexed_data[file_uuid["filePath"]] == file_uuid["FILEUUID"]


dmdsec_dconly = {
    "filePath": "objects/lion.svg",
    "dublincore_dict": {
        "dc:language": "English",
        "dc:title": "Test Title",
        "dc:date": "2019-05-03",
        "dc:description": "Test description",
    },
}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "metsfile,dmdsec_dict",
    [
        ("test_index_aipfile_dmdsec_METS_dconly.xml", dmdsec_dconly),
        (
            "test_index_aipfile_dmdsec_METS_mixed.xml",
            dmdsec_dconly,  # non-DC metadata should be ignored without error
        ),
    ],
)
@mock.patch("elasticSearchFunctions.get_dashboard_uuid")
@mock.patch("elasticSearchFunctions.bulk")
def test_index_aipfile_dmdsec(
    dummy_helpers_bulk, dummy_get_dashboard_uuid, metsfile, dmdsec_dict
):
    """Check AIP file dmdSec is correctly parsed from METS files.

    Mock _try_to_index() with a function that populates a dict
    indexed_data, with the dmdSec data that _index_aip_files() obtained
    from the METS
    """

    dummy_get_dashboard_uuid.return_value = "test-uuid"

    indexed_data = {}

    def _bulk(client, actions, stats_only=False, *args, **kwargs):
        for item in actions:
            try:
                dmd_section = item["_source"]["METS"]["dmdSec"]
                metadata_container = dmd_section["mets:xmlData_dict_list"][0]
                dc = metadata_container["dcterms:dublincore_dict_list"][0]
            except (KeyError, IndexError):
                dc = None
            indexed_data[item["_source"]["filePath"]] = dc

    dummy_helpers_bulk.side_effect = _bulk

    elasticSearchFunctions._index_aip_files(
        client=None,
        uuid="DUMMYUUID",
        mets=etree.parse(os.path.join(THIS_DIR, "fixtures", metsfile)).getroot(),
        name="{}-{}".format("DUMMYNAME", "DUMMYUUID"),
        identifiers=[],
    )

    for key, value in six.iteritems(dmdsec_dict["dublincore_dict"]):
        assert indexed_data[dmdsec_dict["filePath"]][key] == value


@pytest.fixture
def sip(db):
    sip = SIP.objects.create(uuid="f663fd87-5ce4-4114-886e-4856371cf0d6")
    sip.identifiers.add(Identifier.objects.create(value="sip_identifier"))
    return sip


@pytest.fixture
def directories(db, sip):
    # Two directories are created but only one is associated with the SIP
    dir1 = Directory.objects.create(
        uuid="49fe38a0-c50a-4fdf-9353-04d61057220d", sip=sip
    )
    dir1.identifiers.add(Identifier.objects.create(value="dir1"))
    dir2 = Directory.objects.create(uuid="58eaa39c-2a0b-47fd-9d81-52fbaa108abc")
    dir2.identifiers.add(Identifier.objects.create(value="dir2"))


def test_get_sip_identifiers_returns_sip_and_directory_identifiers(sip, directories):
    result = elasticSearchFunctions._get_sip_identifiers(sip.uuid)
    assert sorted(result) == ["dir1", "sip_identifier"]


PHYSICAL_STRUCT_MAP = """<mets:structMap ID="structMap_1" LABEL="Archivematica default" TYPE="physical" xmlns:mets="http://www.loc.gov/METS/">
  <mets:div LABEL="Demo-166e916c-0676-4324-8045-bfc628bebcea" TYPE="Directory" DMDID="dmdSec_1">
    <mets:div LABEL="objects" TYPE="Directory" DMDID="dmdSec_2 dmdSec_3">
      <mets:div LABEL="View_from_lookout_over_Queenstown_towards_the_Remarkables_in_spring-49ad492e-7f1f-4f76-a394-17fa9c9a392d.tif" TYPE="Item">
        <mets:fptr FILEID="file-49ad492e-7f1f-4f76-a394-17fa9c9a392d"/>
      </mets:div>
      <mets:div LABEL="View_from_lookout_over_Queenstown_towards_the_Remarkables_in_spring.jpg" TYPE="Item" ADMID="amdSec_1">
        <mets:fptr FILEID="file-e36a4785-f271-405d-ac75-e54cfdbf74e4"/>
      </mets:div>
      <mets:div LABEL="artwork" TYPE="Directory" ADMID="amdSec_2">
        <mets:div LABEL="MARBLES-9077d660-cc89-4ea3-a61c-f932328985ef.tif" TYPE="Item">
          <mets:fptr FILEID="file-9077d660-cc89-4ea3-a61c-f932328985ef"/>
        </mets:div>
      </mets:div>
      <mets:div LABEL="empty" TYPE="Directory">
      </mets:div>
    </mets:div>
  </mets:div>
</mets:structMap>
"""


@pytest.fixture
def physical_struct_map():
    return etree.fromstring(PHYSICAL_STRUCT_MAP)


def test_get_directories_with_metadata(physical_struct_map):
    result = elasticSearchFunctions._get_directories_with_metadata(physical_struct_map)
    labels = sorted([directory.attrib["LABEL"] for directory in result])
    assert labels == ["Demo-166e916c-0676-4324-8045-bfc628bebcea", "artwork", "objects"]


METS = """<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <mets:dmdSec ID="dmdSec_1">
    <mets:mdWrap MDTYPE="DC">
      <mets:xmlData>
        <dcterms:dublincore xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xsi:schemaLocation="http://purl.org/dc/terms/ https://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd">
          <dc:title>Some title</dc:title>
          <dc:creator>AM</dc:creator>
          <dc:subject></dc:subject>
          <dc:subject></dc:subject>
          <dc:subject></dc:subject>
        </dcterms:dublincore>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:dmdSec ID="dmdSec_2">
    <mets:mdWrap MDTYPE="OTHER" OTHERMDTYPE="CUSTOM">
      <mets:xmlData>
        <custom_field>custom field part 1</custom_field>
        <custom_field>custom field part 2</custom_field>
        <custom_field2>custom field 2</custom_field2>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:amdSec ID="amdSec_1">
    <mets:sourceMD ID="sourceMD_1">
      <mets:mdWrap MDTYPE="OTHER" OTHERMDTYPE="BagIt">
        <mets:xmlData>
          <transfer_metadata>
            <Payload-Oxum>63140.2</Payload-Oxum>
            <FIELD_CONTACT_NAME>A.</FIELD_CONTACT_NAME>
            <FIELD_CONTACT_NAME>R.</FIELD_CONTACT_NAME>
            <FIELD_CONTACT_NAME>Chivist</FIELD_CONTACT_NAME>
          </transfer_metadata>
        </mets:xmlData>
      </mets:mdWrap>
    </mets:sourceMD>
  </mets:amdSec>
</mets:mets>
"""


@pytest.fixture
def mets():
    return etree.fromstring(METS)


@pytest.fixture
def directory():
    result = etree.Element("directory")
    result.set("LABEL", "some/path/to/directory")
    result.set("DMDID", "dmdSec_1 dmdSec_2")
    result.set("ADMID", "amdSec_1")
    return result


@pytest.fixture
def directory_with_no_metadata():
    result = etree.Element("directory")
    result.set("DMDID", "dmdSec_3")
    return result


def test_get_directory_metadata(mets, directory, directory_with_no_metadata):
    result = elasticSearchFunctions._get_directory_metadata(
        directory_with_no_metadata, mets
    )
    assert result == {}
    result = elasticSearchFunctions._get_directory_metadata(directory, mets)
    # all fields are combined into a single dictionary
    assert result == {
        "__DIRECTORY_LABEL__": "some/path/to/directory",
        "FIELD_CONTACT_NAME": ["A.", "R.", "Chivist"],
        "Payload-Oxum": "63140.2",
        "custom_field": ["custom field part 1", "custom field part 2"],
        "custom_field2": "custom field 2",
        "dc:creator": "AM",
        "dc:subject": [None, None, None],
        "dc:title": "Some title",
    }


@pytest.fixture
def file_pointer():
    result = etree.Element("file")
    result.set("DMDID", "dmdSec_1 dmdSec_2")
    return result


@pytest.fixture
def file_pointer_with_no_metadata():
    result = etree.Element("file")
    result.set("DMDID", "dmdSec_3")
    return result


def test_get_file_metadata(mets, file_pointer, file_pointer_with_no_metadata):
    result = elasticSearchFunctions._get_file_metadata(
        file_pointer_with_no_metadata, mets
    )
    assert result == {}
    result = elasticSearchFunctions._get_file_metadata(file_pointer, mets)
    # all fields are combined into a single dictionary
    assert result == {
        "custom_field": ["custom field part 1", "custom field part 2"],
        "custom_field2": "custom field 2",
        "dc:creator": "AM",
        "dc:subject": [None, None, None],
        "dc:title": "Some title",
    }
