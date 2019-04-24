import os

import mock
import pytest
import unittest
import vcr

import elasticSearchFunctions

try:
    from unittest.mock import ANY, patch
except ImportError:
    from mock import ANY, patch

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

    @mock.patch("elasticSearchFunctions.get_dashboard_uuid")
    @mock.patch("elasticSearchFunctions._wait_for_cluster_yellow_status")
    @mock.patch("elasticSearchFunctions._try_to_index")
    def test_index_mets_file_metadata(
        self,
        dummy_try_to_index,
        dummy_wait_for_cluster_yellow_status,
        dummy_get_dashboard_uuid,
    ):
        # Set up mocked functions
        dummy_get_dashboard_uuid.return_value = "test-uuid"
        indexed_data = {}

        def get_dublincore_metadata(client, indexData, index, printfn):
            try:
                dmd_section = indexData["METS"]["dmdSec"]
                metadata_container = dmd_section["ns0:xmlData_dict_list"][0]
                dc = metadata_container["ns1:dublincore_dict_list"][0]
            except (KeyError, IndexError):
                dc = None
            indexed_data[indexData["filePath"]] = dc

        dummy_try_to_index.side_effect = get_dublincore_metadata

        # This METS file is a cut-down version of the AIP METS produced
        # using the SampleTransfers/DemoTransfer
        mets_file_path = os.path.join(
            THIS_DIR, "fixtures", "test_index_metadata-METS.xml"
        )
        mets_object_id = "771aa252-7930-4e68-b73e-f91416b1d4a4"
        uuid = "f42a260a-9b53-4555-847e-8a4329c81662"
        sipName = "DemoTransfer-{}".format(uuid)
        identifiers = []
        indexed_files_count = elasticSearchFunctions._index_aip_files(
            client=self.client,
            uuid=uuid,
            mets_path=mets_file_path,
            name=sipName,
            identifiers=identifiers,
        )

        # ES should have indexed 12 files
        # - 5 content files
        # - 5 checksum and csv files in the metadata directory
        # - 2 files generated in the transfer process
        assert indexed_files_count == 12
        assert dummy_try_to_index.call_count == 12

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
@mock.patch("elasticSearchFunctions._wait_for_cluster_yellow_status")
@mock.patch("elasticSearchFunctions._try_to_index")
def test_index_aipfile_fileuuid(
    dummy_try_to_index,
    dummy_wait_for_cluster_yellow_status,
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

    def get_fileuuid(client, indexData, index, printfn):
        indexed_data[indexData["filePath"]] = indexData["FILEUUID"]

    dummy_try_to_index.side_effect = get_fileuuid

    elasticSearchFunctions._index_aip_files(
        client=None,
        uuid=aipuuid,
        mets_path=os.path.join(THIS_DIR, "fixtures", metsfile),
        name="{}-{}".format(aipname, aipuuid),
        identifiers=[],
    )

    for file_uuid in fileuuid_dict:
        assert indexed_data[file_uuid["filePath"]] == file_uuid["FILEUUID"]
