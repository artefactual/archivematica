import datetime
import os
import pathlib
import uuid
from unittest import mock

import elasticSearchFunctions
import pytest
from components import helpers
from django.utils.timezone import make_aware
from lxml import etree
from main.models import SIP
from main.models import Directory
from main.models import File
from main.models import Identifier
from main.models import Transfer

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def es_client():
    with mock.patch("elasticsearch.transport.Transport.perform_request"):
        elasticSearchFunctions.setup("elasticsearch:9200")
    return elasticSearchFunctions.get_client()


@mock.patch(
    "elasticsearch.transport.Transport.perform_request",
    side_effect=[
        {
            "took": 2,
            "timed_out": False,
            "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
            "hits": {
                "total": 1,
                "max_score": 0.2876821,
                "hits": [
                    {
                        "_index": "aips",
                        "_type": "_doc",
                        "_id": "lBsZBWgBn49OAVhMXeO8",
                        "_score": 0.2876821,
                        "_source": {"uuid": "b34521a3-1c63-43dd-b901-584416f36c91"},
                    }
                ],
            },
        },
        {
            "took": 8,
            "timed_out": False,
            "total": 1,
            "deleted": 1,
            "batches": 1,
            "version_conflicts": 0,
            "noops": 0,
            "retries": {"bulk": 0, "search": 0},
            "throttled_millis": 0,
            "requests_per_second": -1.0,
            "throttled_until_millis": 0,
            "failures": [],
        },
        {
            "took": 0,
            "timed_out": False,
            "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
            "hits": {"total": 0, "max_score": None, "hits": []},
        },
    ],
)
def test_delete_aip(perform_request, es_client):
    aip_uuid = "b34521a3-1c63-43dd-b901-584416f36c91"

    # Verify AIP exists
    results = es_client.search(
        index="aips",
        body={"query": {"term": {"uuid": aip_uuid}}},
        _source="uuid",
    )
    assert results["hits"]["total"] == 1
    assert results["hits"]["hits"][0]["_source"]["uuid"] == aip_uuid

    # Delete AIP
    elasticSearchFunctions.delete_aip(es_client, "b34521a3-1c63-43dd-b901-584416f36c91")

    # Verify AIP gone
    results = es_client.search(
        index="aips",
        body={"query": {"term": {"uuid": aip_uuid}}},
        _source="uuid",
    )
    assert results["hits"]["total"] == 0


@mock.patch(
    "elasticsearch.transport.Transport.perform_request",
    side_effect=[
        {
            "took": 1,
            "timed_out": False,
            "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
            "hits": {
                "total": 2,
                "max_score": 0.2876821,
                "hits": [
                    {
                        "_index": "aipfiles",
                        "_type": "_doc",
                        "_id": "lRsZBWgBn49OAVhMXuMC",
                        "_score": 0.2876821,
                        "_source": {"origin": "1a14043f-68ef-4bfe-a129-e2e4cdbe391b"},
                    },
                    {
                        "_index": "aipfiles",
                        "_type": "_doc",
                        "_id": "lhsZBWgBn49OAVhMXuMh",
                        "_score": 0.2876821,
                        "_source": {"origin": "1a14043f-68ef-4bfe-a129-e2e4cdbe391b"},
                    },
                ],
            },
        },
        {
            "took": 11,
            "timed_out": False,
            "total": 2,
            "deleted": 2,
            "batches": 1,
            "version_conflicts": 0,
            "noops": 0,
            "retries": {"bulk": 0, "search": 0},
            "throttled_millis": 0,
            "requests_per_second": -1.0,
            "throttled_until_millis": 0,
            "failures": [],
        },
        {
            "took": 0,
            "timed_out": False,
            "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
            "hits": {"total": 0, "max_score": None, "hits": []},
        },
    ],
)
def test_delete_aip_files(perform_request, es_client):
    aip_uuid = "b34521a3-1c63-43dd-b901-584416f36c91"

    # Verify AIP files exist
    results = es_client.search(
        index="aipfiles", body={"query": {"term": {"AIPUUID": aip_uuid}}}
    )
    assert results["hits"]["total"] == 2

    # Delete AIP files
    elasticSearchFunctions.delete_aip_files(es_client, aip_uuid)
    # Verify AIP files gone
    results = es_client.search(
        index="aipfiles", body={"query": {"term": {"AIPUUID": aip_uuid}}}
    )
    assert results["hits"]["total"] == 0

    assert perform_request.mock_calls == [
        mock.call(
            "GET",
            "/aipfiles/_search",
            params={},
            body={
                "query": {"term": {"AIPUUID": "b34521a3-1c63-43dd-b901-584416f36c91"}}
            },
        ),
        mock.call(
            "POST",
            "/aipfiles/_delete_by_query",
            params={},
            body={
                "query": {"term": {"AIPUUID": "b34521a3-1c63-43dd-b901-584416f36c91"}}
            },
        ),
        mock.call(
            "GET",
            "/aipfiles/_search",
            params={},
            body={
                "query": {"term": {"AIPUUID": "b34521a3-1c63-43dd-b901-584416f36c91"}}
            },
        ),
    ]


@mock.patch(
    "elasticsearch.transport.Transport.perform_request",
    side_effect=[
        {
            "took": 1,
            "timed_out": False,
            "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
            "hits": {
                "total": 1,
                "max_score": 0.6931472,
                "hits": [
                    {
                        "_index": "transferfiles",
                        "_type": "_doc",
                        "_id": "mBsZBWgBn49OAVhMh-OV",
                        "_score": 0.6931472,
                        "_source": {
                            "accessionid": "",
                            "status": "backlog",
                            "sipuuid": "17b168b6-cbba-4f43-8838-a53360238acb",
                            "tags": [],
                            "file_extension": "jpg",
                            "relative_path": "test-17b168b6-cbba-4f43-8838-a53360238acb/objects/Landing_zone.jpg",
                            "bulk_extractor_reports": [],
                            "origin": "1a14043f-68ef-4bfe-a129-e2e4cdbe391b",
                            "size": 1.2982568740844727,
                            "modification_date": "2018-12-11",
                            "created": 1546273029.7313669,
                            "format": [],
                            "ingestdate": "2018-12-31",
                            "filename": "Landing_zone.jpg",
                            "fileuuid": "268421a7-a986-4fa0-95c1-54176e508210",
                        },
                    }
                ],
            },
        },
        {
            "_index": "transferfiles",
            "_type": "_doc",
            "_id": "mBsZBWgBn49OAVhMh-OV",
            "_version": 2,
            "result": "updated",
            "forced_refresh": True,
            "_shards": {"total": 2, "successful": 1, "failed": 0},
            "_seq_no": 2,
            "_primary_term": 1,
        },
        {
            "took": 2,
            "timed_out": False,
            "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
            "hits": {
                "total": 1,
                "max_score": 0.47000363,
                "hits": [
                    {
                        "_index": "transferfiles",
                        "_type": "_doc",
                        "_id": "mBsZBWgBn49OAVhMh-OV",
                        "_score": 0.47000363,
                        "_source": {"tags": ["test"]},
                    }
                ],
            },
        },
    ],
)
def test_set_get_tags(perform_request, es_client):
    file_uuid = "268421a7-a986-4fa0-95c1-54176e508210"
    elasticSearchFunctions.set_file_tags(es_client, file_uuid, ["test"])
    assert elasticSearchFunctions.get_file_tags(es_client, file_uuid) == ["test"]

    assert perform_request.mock_calls == [
        mock.call(
            "GET",
            "/transferfiles/_search",
            params={"size": "10000"},
            body={
                "query": {"term": {"fileuuid": "268421a7-a986-4fa0-95c1-54176e508210"}}
            },
        ),
        mock.call(
            "POST",
            "/transferfiles/_doc/mBsZBWgBn49OAVhMh-OV/_update",
            params={},
            body={"doc": {"tags": ["test"]}},
        ),
        mock.call(
            "GET",
            "/transferfiles/_search",
            params={"_source": b"tags"},
            body={
                "query": {"term": {"fileuuid": "268421a7-a986-4fa0-95c1-54176e508210"}}
            },
        ),
    ]


@mock.patch(
    "elasticsearch.transport.Transport.perform_request",
    side_effect=[
        {
            "took": 1,
            "timed_out": False,
            "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
            "hits": {"total": 0, "max_score": None, "hits": []},
        }
    ],
)
def test_list_tags_fails_when_file_cant_be_found(perform_request, es_client):
    with pytest.raises(elasticSearchFunctions.EmptySearchResultError):
        elasticSearchFunctions.get_file_tags(es_client, "no_such_file")
    perform_request.assert_called_once_with(
        "GET",
        "/transferfiles/_search",
        params={"_source": b"tags"},
        body={"query": {"term": {"fileuuid": "no_such_file"}}},
    )


@mock.patch(
    "elasticsearch.transport.Transport.perform_request",
    side_effect=[
        {
            "took": 0,
            "timed_out": False,
            "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
            "hits": {"total": 0, "max_score": None, "hits": []},
        }
    ],
)
def test_set_tags_fails_when_file_cant_be_found(perform_request, es_client):
    with pytest.raises(elasticSearchFunctions.EmptySearchResultError):
        elasticSearchFunctions.set_file_tags(es_client, "no_such_file", [])
    perform_request.assert_called_once_with(
        "GET",
        "/transferfiles/_search",
        params={"size": "10000"},
        body={"query": {"term": {"fileuuid": "no_such_file"}}},
    )


@pytest.mark.django_db
@mock.patch("elasticSearchFunctions.get_dashboard_uuid")
@mock.patch("elasticSearchFunctions.bulk")
def test_index_mets_file_metadata(bulk, get_dashboard_uuid, es_client):
    # Set up mocked functions
    get_dashboard_uuid.return_value = "test-uuid"
    indexed_data = {}

    def _bulk(client, actions, stats_only=False, *args, **kwargs):
        for item in actions:
            try:
                dmd_section = item["_source"]["METS"]["dmdSec"]
                metadata_container = dmd_section["mets:xmlData_dict"]
                dc = metadata_container["dcterms:dublincore_dict"]
            except (KeyError, IndexError):
                dc = None
            indexed_data[item["_source"]["filePath"]] = dc

    bulk.side_effect = _bulk

    # This METS file is a cut-down version of the AIP METS produced
    # using the SampleTransfers/DemoTransfer
    mets_file_path = os.path.join(THIS_DIR, "fixtures", "test_index_metadata-METS.xml")
    mets_object_id = "771aa252-7930-4e68-b73e-f91416b1d4a4"
    aip_uuid = "f42a260a-9b53-4555-847e-8a4329c81662"
    sipName = f"DemoTransfer-{aip_uuid}"
    identifiers = []
    elasticSearchFunctions._index_aip_files(
        client=es_client,
        uuid=aip_uuid,
        mets=etree.parse(mets_file_path).getroot(),
        name=sipName,
        identifiers=identifiers,
    )

    assert bulk.call_count == 1

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
        path = f"objects/metadata/transfers/DemoTransfer-{mets_object_id}/{filename}"
        assert indexed_data[path] is None

    # Neither will the generated files during the transfer process
    generated_files = ("dc.json", "directory_tree.txt")
    for filename in generated_files:
        path = f"objects/metadata/transfers/DemoTransfer-{mets_object_id}/{filename}"
        assert indexed_data[path] is None


@pytest.mark.django_db
@mock.patch("elasticSearchFunctions.bulk")
def test_index_mets_file_metadata_with_utf8(bulk, es_client):
    def _bulk(client, actions, stats_only=False, *args, **kwargs):
        pass

    bulk.side_effect = _bulk
    mets_file_path = os.path.join(
        THIS_DIR, "fixtures", "test_index_metadata-METS-utf8.xml"
    )
    elasticSearchFunctions._index_aip_files(
        client=es_client,
        uuid="",
        mets=etree.parse(mets_file_path).getroot(),
        name="",
        identifiers=[],
    )


@mock.patch("elasticSearchFunctions.create_indexes_if_needed")
def test_default_setup(create_indexes_if_needed):
    elasticSearchFunctions.setup("elasticsearch:9200")
    create_indexes_if_needed.assert_called_with(
        mock.ANY, ["aips", "aipfiles", "transfers", "transferfiles"]
    )


@mock.patch("elasticSearchFunctions.create_indexes_if_needed")
def test_only_aips_setup(create_indexes_if_needed):
    elasticSearchFunctions.setup("elasticsearch:9200", enabled=["aips"])
    create_indexes_if_needed.assert_called_with(mock.ANY, ["aips", "aipfiles"])


@mock.patch("elasticSearchFunctions.create_indexes_if_needed")
def test_only_transfers_setup(create_indexes_if_needed):
    elasticSearchFunctions.setup("elasticsearch:9200", enabled=["transfers"])
    create_indexes_if_needed.assert_called_with(
        mock.ANY, ["transfers", "transferfiles"]
    )


@mock.patch("elasticSearchFunctions.create_indexes_if_needed")
def test_no_indexes_setup(create_indexes_if_needed):
    elasticSearchFunctions.setup("elasticsearch:9200", enabled=[])
    elasticSearchFunctions.setup("elasticsearch:9200", enabled=["unknown"])
    create_indexes_if_needed.assert_not_called()


@mock.patch("elasticsearch.client.indices.IndicesClient.create")
@mock.patch("elasticsearch.client.indices.IndicesClient.exists", return_value=True)
def test_create_indexes_already_created(exists, create, es_client):
    elasticSearchFunctions.create_indexes_if_needed(
        es_client, ["aips", "aipfiles", "transfers", "transferfiles"]
    )
    create.assert_not_called()


@mock.patch("elasticsearch.client.indices.IndicesClient.create")
@mock.patch("elasticsearch.client.indices.IndicesClient.exists", return_value=False)
def test_create_indexes_creation_calls(exists, create, es_client):
    elasticSearchFunctions.create_indexes_if_needed(
        es_client, ["aips", "aipfiles", "transfers", "transferfiles"]
    )
    assert create.call_count == 4


@mock.patch("elasticsearch.client.indices.IndicesClient.create")
@mock.patch("elasticsearch.client.indices.IndicesClient.exists", return_value=False)
def test_create_indexes_wrong_index(exists, create, es_client):
    elasticSearchFunctions.create_indexes_if_needed(
        es_client, ["aips", "aipfiles", "unknown"]
    )
    assert create.call_count == 2


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
    bulk, get_dashboard_uuid, metsfile, fileuuid_dict, aipuuid, aipname
):
    """Check AIP file uuids are being correctly parsed from METS files.

    Mock _try_to_index() with a function that populates a dict
    indexed_data, with the fileuuids that _index_aip_files() obtained
    from the METS
    """

    get_dashboard_uuid.return_value = "test-uuid"

    indexed_data = {}

    def _bulk(client, actions, stats_only=False, *args, **kwargs):
        for item in actions:
            indexed_data[item["_source"]["filePath"]] = item["_source"]["FILEUUID"]

    bulk.side_effect = _bulk

    elasticSearchFunctions._index_aip_files(
        client=None,
        uuid=aipuuid,
        mets=etree.parse(os.path.join(THIS_DIR, "fixtures", metsfile)).getroot(),
        name=f"{aipname}-{aipuuid}",
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
def test_index_aipfile_dmdsec(bulk, get_dashboard_uuid, metsfile, dmdsec_dict):
    """Check AIP file dmdSec is correctly parsed from METS files.

    Mock _try_to_index() with a function that populates a dict
    indexed_data, with the dmdSec data that _index_aip_files() obtained
    from the METS
    """

    get_dashboard_uuid.return_value = "test-uuid"

    indexed_data = {}

    def _bulk(client, actions, stats_only=False, *args, **kwargs):
        for item in actions:
            try:
                dmd_section = item["_source"]["METS"]["dmdSec"]
                metadata_container = dmd_section["mets:xmlData_dict"]
                dc = metadata_container["dcterms:dublincore_dict"]
            except (KeyError, IndexError):
                dc = None
            indexed_data[item["_source"]["filePath"]] = dc

    bulk.side_effect = _bulk

    elasticSearchFunctions._index_aip_files(
        client=None,
        uuid="DUMMYUUID",
        mets=etree.parse(os.path.join(THIS_DIR, "fixtures", metsfile)).getroot(),
        name="{}-{}".format("DUMMYNAME", "DUMMYUUID"),
        identifiers=[],
    )

    for key, value in dmdsec_dict["dublincore_dict"].items():
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
    labels = sorted(directory.attrib["LABEL"] for directory in result)
    assert labels == ["Demo-166e916c-0676-4324-8045-bfc628bebcea", "artwork", "objects"]


METS = """<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <mets:dmdSec ID="dmdSec_1" CREATED="2022-02-18T18:44:33" STATUS="original">
    <mets:mdWrap MDTYPE="PREMIS:OBJECT">
      <mets:xmlData>
        <premis:object xmlns:premis="http://www.loc.gov/premis/v3" xsi:type="premis:intellectualEntity" xsi:schemaLocation="http://www.loc.gov/premis/v3 http://www.loc.gov/standards/premis/v3/premis.xsd" version="3.0">
          <premis:objectIdentifier>
            <premis:objectIdentifierType>UUID</premis:objectIdentifierType>
            <premis:objectIdentifierValue>6cebefad-2b19-4874-b014-094ec35a85aa</premis:objectIdentifierValue>
          </premis:objectIdentifier>
          <premis:originalName>pics_2-6cebefad-2b19-4874-b014-094ec35a85aa</premis:originalName>
        </premis:object>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:dmdSec ID="dmdSec_2" CREATED="2022-02-18T18:44:33" STATUS="original">
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
  <mets:dmdSec ID="dmdSec_3" CREATED="2022-02-18T18:44:33" STATUS="original-superseded" GROUPID="5329fa70-214e-43a8-8974-958bbfc19c4c">
    <mets:mdWrap MDTYPE="OTHER" OTHERMDTYPE="CUSTOM">
      <mets:xmlData>
        <custom_field>custom field part 1</custom_field>
        <custom_field>custom field part 2</custom_field>
        <custom_field2>custom field 2</custom_field2>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:dmdSec ID="dmdSec_4" CREATED="2022-02-18T18:44:33" STATUS="deleted">
    <mets:mdWrap MDTYPE="OTHER" OTHERMDTYPE="">
      <mets:xmlData>
        <record>
          <idfield>deleted</idfield>
        </record>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:dmdSec ID="dmdSec_5" CREATED="2022-02-19T18:44:33" STATUS="update" GROUPID="5329fa70-214e-43a8-8974-958bbfc19c4c">
    <mets:mdWrap MDTYPE="OTHER" OTHERMDTYPE="CUSTOM">
      <mets:xmlData>
        <custom_field>updated custom field part 1</custom_field>
        <custom_field>updated custom field part 2</custom_field>
        <custom_field2>updated custom field 2</custom_field2>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:dmdSec ID="dmdSec_6" CREATED="2022-02-19T18:44:33" STATUS="update">
    <mets:mdWrap MDTYPE="OTHER" OTHERMDTYPE="">
      <mets:xmlData>
        <record>
          <idfield>idfield</idfield>
          <controlfield>controlfield 1</controlfield>
          <controlfield>controlfield 2</controlfield>
          <datafield>
            <subfield>subfield 1</subfield>
            <subfield>subfield 2</subfield>
          </datafield>
          <datafield>
            <subfield>subfield 3</subfield>
          </datafield>
        </record>
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
    result.set("DMDID", "dmdSec_1 dmdSec_2 dmdSec_3 dmdSec_4 dmdSec_5 dmdSec_6")
    result.set("ADMID", "amdSec_1")
    return result


@pytest.fixture
def directory_with_no_metadata():
    result = etree.Element("directory")
    return result


@pytest.fixture
def file_pointer():
    result = etree.Element("file")
    result.set("DMDID", "dmdSec_1 dmdSec_2 dmdSec_3 dmdSec_4 dmdSec_5 dmdSec_6")
    return result


@pytest.fixture
def file_pointer_with_no_metadata():
    result = etree.Element("file")
    return result


expected_file_metadata = {
    "custom_field": ["updated custom field part 1", "updated custom field part 2"],
    "custom_field2": "updated custom field 2",
    "dc:creator": "AM",
    "dc:subject": [None, None, None],
    "dc:title": "Some title",
    "record_dict": {
        "idfield": "idfield",
        "controlfield": [
            "controlfield 1",
            "controlfield 2",
        ],
        "datafield_dict": [
            {
                "subfield": [
                    "subfield 1",
                    "subfield 2",
                ]
            },
            {
                "subfield": "subfield 3",
            },
        ],
    },
}


expected_directory_metadata = {
    "__DIRECTORY_LABEL__": "some/path/to/directory",
    "FIELD_CONTACT_NAME": ["A.", "R.", "Chivist"],
    "Payload-Oxum": "63140.2",
    **expected_file_metadata,
}


@pytest.mark.parametrize(
    "element_fixture_name, method_name, expected_metadata",
    [
        ("directory", "_get_directory_metadata", expected_directory_metadata),
        ("directory_with_no_metadata", "_get_directory_metadata", {}),
        ("file_pointer", "_get_file_metadata", expected_file_metadata),
        ("file_pointer_with_no_metadata", "_get_file_metadata", {}),
    ],
)
def test_get_metadata(
    request, mets, element_fixture_name, method_name, expected_metadata
):
    assert (
        getattr(elasticSearchFunctions, method_name)(
            request.getfixturevalue(element_fixture_name), mets
        )
        == expected_metadata
    )


def test_index_aip_and_files_logs_error_if_mets_does_not_exist(
    es_client, tmp_path, caplog
):
    printfn = mock.Mock()
    aip_uuid = uuid.uuid4()
    aip_stored_path = tmp_path / "aip.7z"
    mets_staging_path = tmp_path / "mets.XML"
    expected_error_message = f"METS file does not exist at: {mets_staging_path}"

    result = elasticSearchFunctions.index_aip_and_files(
        es_client,
        str(aip_uuid),
        str(aip_stored_path),
        str(mets_staging_path),
        "aip",
        1024,
        printfn=printfn,
    )
    assert result == 1

    assert [r.message for r in caplog.records] == [expected_error_message]
    printfn.assert_called_once_with(expected_error_message, file=mock.ANY)


@pytest.mark.django_db
@mock.patch("elasticsearch.Elasticsearch.index")
@mock.patch(
    "elasticsearch.client.cluster.ClusterClient.health",
    return_value={"status": "green"},
)
@mock.patch("elasticSearchFunctions._index_aip_files")
def test_index_aip_and_files(_index_aip_files, health, index, es_client, tmp_path):
    dashboard_uuid = uuid.uuid4()
    helpers.set_setting("dashboard_uuid", str(dashboard_uuid))
    printfn = mock.Mock()
    aip_name = "aip"
    aip_uuid = str(uuid.uuid4())
    aip_stored_path = tmp_path / "aip.7z"
    mets_staging_path = pathlib.Path(
        THIS_DIR, "fixtures", "test_index_aip_and_files_METS.xml"
    )
    expected_file_count = 3
    accession_ids = "accession_ids"
    _index_aip_files.return_value = (expected_file_count, accession_ids)

    result = elasticSearchFunctions.index_aip_and_files(
        es_client,
        str(aip_uuid),
        str(aip_stored_path),
        str(mets_staging_path),
        aip_name,
        1024 * 1024 * 10,
        printfn=printfn,
    )
    assert result == 0

    health.assert_called_once()
    index.assert_called_once_with(
        body={
            "AICID": None,
            "accessionids": accession_ids,
            "countAIPsinAIC": None,
            "created": 1714362668,
            "encrypted": False,
            "filePath": str(aip_stored_path),
            "file_count": expected_file_count,
            "identifiers": [],
            "isPartOf": "",
            "location": "",
            "name": aip_name,
            "origin": str(dashboard_uuid),
            "size": 10.0,
            "status": elasticSearchFunctions.STATUS_UPLOADED,
            "transferMetadata": [
                {
                    "__DIRECTORY_LABEL__": "objects",
                    "dc:title": "Pictures with DublinCore",
                    "dc:type": "Archival Information Package",
                },
            ],
            "uuid": str(aip_uuid),
        },
        doc_type="_doc",
        index="aips",
    )
    assert printfn.mock_calls == [
        mock.call(f"AIP UUID: {aip_uuid}"),
        mock.call("Indexing AIP files ..."),
        mock.call(f"Files indexed: {expected_file_count}"),
        mock.call("Indexing AIP ..."),
        mock.call("Done."),
    ]


def test_index_transfer_and_files_logs_error_if_transfer_path_does_not_exist(
    es_client, tmp_path, caplog
):
    printfn = mock.Mock()
    transfer_uuid = uuid.uuid4()
    transfer_path = tmp_path / "transfer"
    expected_error_message = f"Transfer does not exist at: {transfer_path}"

    result = elasticSearchFunctions.index_transfer_and_files(
        es_client,
        str(transfer_uuid),
        str(transfer_path),
        1024,
        printfn=printfn,
    )
    assert result == 1

    assert [r.message for r in caplog.records] == [expected_error_message]
    printfn.assert_called_once_with(expected_error_message, file=mock.ANY)


@pytest.mark.django_db
@pytest.fixture
def transfer(tmp_path):
    transfer_dir = tmp_path / "transfer"
    transfer_dir.mkdir()

    (transfer_dir / "processingMCP.xml").touch()

    return Transfer.objects.create(
        # The trailing slash is expected by index_transfer_and_files.
        currentlocation=f"{transfer_dir}/",
        accessionid="accession_id",
    )


@pytest.mark.django_db
@pytest.fixture
def transfer_file(transfer):
    filename = "file.txt"
    (pathlib.Path(transfer.currentlocation) / filename).touch()

    result = File.objects.create(
        transfer=transfer, currentlocation=f"%transferDirectory%{filename}".encode()
    )

    # enteredsystem is an auto_now DateTimeField. This resets its value.
    dt = make_aware(datetime.datetime(2024, 1, 1))
    result.enteredsystem = dt
    result.modificationtime = dt
    result.save()

    return result


@pytest.mark.django_db
@mock.patch("elasticsearch.Elasticsearch.index")
@mock.patch(
    "elasticsearch.client.cluster.ClusterClient.health",
    return_value={"status": "green"},
)
def test_index_transfer_and_files(health, index, es_client, transfer, transfer_file):
    dashboard_uuid = uuid.uuid4()
    helpers.set_setting("dashboard_uuid", str(dashboard_uuid))
    printfn = mock.Mock()
    expected_transfer_name = "transfer"
    expected_file_count = 1
    expected_file_name = "file.txt"
    expected_date = "2024-01-01"
    expected_status = "backlog"

    result = elasticSearchFunctions.index_transfer_and_files(
        es_client,
        str(transfer.uuid),
        str(transfer.currentlocation),
        1024,
        printfn=printfn,
    )
    assert result == 0

    assert health.mock_calls == [mock.call(), mock.call()]
    assert index.mock_calls == [
        mock.call(
            body={
                "filename": expected_file_name,
                "relative_path": f"{expected_transfer_name}/{expected_file_name}",
                "fileuuid": str(transfer_file.uuid),
                "sipuuid": str(transfer.uuid),
                "accessionid": transfer.accessionid,
                "status": expected_status,
                "origin": str(dashboard_uuid),
                "ingestdate": expected_date,
                "created": mock.ANY,
                "modification_date": expected_date,
                "size": 0.0,
                "tags": [],
                "file_extension": "txt",
                "bulk_extractor_reports": [],
                "format": [],
                "pending_deletion": False,
            },
            index="transferfiles",
            doc_type="_doc",
        ),
        mock.call(
            body={
                "accessionid": transfer.accessionid,
                "file_count": expected_file_count,
                "ingest_date": expected_date,
                "name": expected_transfer_name,
                "pending_deletion": False,
                "size": 1024,
                "status": expected_status,
                "uuid": str(transfer.uuid),
            },
            doc_type="_doc",
            index="transfers",
        ),
    ]
    # Cannot compare using mock_calls here because the use of os.listdir in
    # _list_files_in_dir returns files in arbitrary order.
    printfn.assert_has_calls(
        [
            mock.call(f"Transfer UUID: {transfer.uuid}"),
            mock.call("Indexing Transfer files ..."),
            mock.call(
                f"Indexing {expected_transfer_name}/{expected_file_name} (UUID: {transfer_file.uuid})"
            ),
            mock.call(f"Skipping indexing {expected_transfer_name}/processingMCP.xml"),
            mock.call(f"Files indexed: {expected_file_count}"),
            mock.call("Indexing Transfer ..."),
            mock.call("Done."),
        ],
        any_order=True,
    )


@mock.patch(
    "elasticSearchFunctions.search_all_results",
    return_value={
        "hits": {
            "hits": [
                {
                    "_source": {
                        "filename": "file.txt",
                        "fileuuid": "f704ab10-d52e-482f-af4a-cc21111f8df4",
                    },
                }
            ],
        },
    },
)
def test_get_transfer_file_info_when_search_returns_a_single_document(
    search_all_results, es_client
):
    field = "fileuuid"
    value = "f704ab10-d52e-482f-af4a-cc21111f8df4"

    result = elasticSearchFunctions.get_transfer_file_info(es_client, field, value)

    assert result == {
        "filename": "file.txt",
        "fileuuid": "f704ab10-d52e-482f-af4a-cc21111f8df4",
    }

    search_all_results.assert_called_once_with(
        es_client,
        body={"query": {"term": {field: value}}},
        index=elasticSearchFunctions.TRANSFER_FILES_INDEX,
    )


@mock.patch(
    "elasticSearchFunctions.search_all_results",
    return_value={
        "hits": {
            "hits": [
                {
                    "_source": {
                        "fileuuid": "f704ab10-d52e-482f-af4a-cc21111f8df4",
                        "filename": "foo.txt",
                    }
                },
                {
                    "_source": {
                        "fileuuid": "f704ab10-d52e-482f-af4a-cc21111f8df4",
                        "filename": "bar.txt",
                    }
                },
            ],
        },
    },
)
def test_get_transfer_file_info_logs_multiple_results(search_all_results, es_client):
    field = "fileuuid"
    value = "f704ab10-d52e-482f-af4a-cc21111f8df4"

    result = elasticSearchFunctions.get_transfer_file_info(es_client, field, value)

    assert result == {field: value, "filename": "foo.txt"}

    search_all_results.assert_called_once_with(
        es_client,
        body={"query": {"term": {field: value}}},
        index=elasticSearchFunctions.TRANSFER_FILES_INDEX,
    )


@pytest.mark.django_db
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.search_all_results")
def test_remove_backlog_transfer_files(search_all_results, client, transfer):
    file_doc_id = "123"
    search_all_results.return_value = {
        "hits": {
            "hits": [
                {
                    "_id": file_doc_id,
                    "_source": {"filename": "file.txt", "fileuuid": str(uuid.uuid4())},
                }
            ]
        }
    }

    elasticSearchFunctions.remove_backlog_transfer_files(client, transfer.uuid)

    search_all_results.assert_called_once_with(
        client,
        body={"query": {"term": {"sipuuid": str(transfer.uuid)}}},
        index=elasticSearchFunctions.TRANSFER_FILES_INDEX,
    )
    client.delete.assert_called_once_with(
        index=elasticSearchFunctions.TRANSFER_FILES_INDEX,
        doc_type=elasticSearchFunctions.DOC_TYPE,
        id=file_doc_id,
    )


@pytest.mark.django_db
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.search_all_results")
def test_remove_sip_transfer_files(search_all_results, client, transfer, transfer_file):
    file_doc_id = "123"
    search_all_results.return_value = {
        "hits": {
            "hits": [
                {
                    "_id": file_doc_id,
                    "_source": {"filename": "file.txt", "fileuuid": str(uuid.uuid4())},
                }
            ]
        }
    }

    elasticSearchFunctions.remove_sip_transfer_files(client, transfer.uuid)

    search_all_results.assert_called_once_with(
        client,
        body={"query": {"term": {"sipuuid": str(transfer.uuid)}}},
        index=elasticSearchFunctions.TRANSFER_FILES_INDEX,
    )
    client.delete.assert_called_once_with(
        index=elasticSearchFunctions.TRANSFER_FILES_INDEX,
        doc_type=elasticSearchFunctions.DOC_TYPE,
        id=file_doc_id,
    )


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions._document_ids_from_field_query", return_value=[])
def test_mark_aip_stored_logs_error(_document_ids_from_field_query, client, caplog):
    aip_uuid = str(uuid.uuid4())

    elasticSearchFunctions.mark_aip_stored(es_client, aip_uuid)

    _document_ids_from_field_query.assert_called_once_with(
        es_client,
        elasticSearchFunctions.AIPS_INDEX,
        elasticSearchFunctions.ES_FIELD_UUID,
        aip_uuid,
    )
    assert [r.message for r in caplog.records] == [
        f"Unable to find document with UUID {aip_uuid} in index {elasticSearchFunctions.AIPS_INDEX}"
    ]


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions._document_ids_from_field_query")
def test_mark_aip_stored(_document_ids_from_field_query, client):
    aip_uuid = str(uuid.uuid4())
    aip_doc_id = str(uuid.uuid4())
    _document_ids_from_field_query.return_value = [aip_doc_id]

    elasticSearchFunctions.mark_aip_stored(client, aip_uuid)

    client.update.assert_called_once_with(
        body={
            "doc": {
                elasticSearchFunctions.ES_FIELD_STATUS: elasticSearchFunctions.STATUS_UPLOADED
            }
        },
        index=elasticSearchFunctions.AIPS_INDEX,
        doc_type=elasticSearchFunctions.DOC_TYPE,
        id=aip_doc_id,
    )
    _document_ids_from_field_query.assert_called_once_with(
        client,
        elasticSearchFunctions.AIPS_INDEX,
        elasticSearchFunctions.ES_FIELD_UUID,
        aip_uuid,
    )


@pytest.mark.parametrize(
    "helper,package_index,files_index,package_uuid_field,field,value",
    (
        (
            elasticSearchFunctions.mark_aip_deletion_requested,
            elasticSearchFunctions.AIPS_INDEX,
            elasticSearchFunctions.AIP_FILES_INDEX,
            "AIPUUID",
            elasticSearchFunctions.ES_FIELD_STATUS,
            elasticSearchFunctions.STATUS_DELETE_REQUESTED,
        ),
        (
            elasticSearchFunctions.mark_backlog_deletion_requested,
            elasticSearchFunctions.TRANSFERS_INDEX,
            elasticSearchFunctions.TRANSFER_FILES_INDEX,
            "sipuuid",
            "pending_deletion",
            True,
        ),
        (
            elasticSearchFunctions.revert_aip_deletion_request,
            elasticSearchFunctions.AIPS_INDEX,
            elasticSearchFunctions.AIP_FILES_INDEX,
            "AIPUUID",
            elasticSearchFunctions.ES_FIELD_STATUS,
            elasticSearchFunctions.STATUS_UPLOADED,
        ),
        (
            elasticSearchFunctions.revert_backlog_deletion_request,
            elasticSearchFunctions.TRANSFERS_INDEX,
            elasticSearchFunctions.TRANSFER_FILES_INDEX,
            "sipuuid",
            "pending_deletion",
            False,
        ),
    ),
    ids=[
        "mark_aip_deletion_requested",
        "mark_backlog_deletion_requested",
        "revert_aip_deletion_request",
        "revert_backlog_deletion_request",
    ],
)
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions._document_ids_from_field_query")
def test_update_helpers(
    _document_ids_from_field_query,
    client,
    helper,
    package_index,
    files_index,
    package_uuid_field,
    field,
    value,
):
    package_uuid = str(uuid.uuid4())
    package_doc_id = str(uuid.uuid4())
    file_doc_id = str(uuid.uuid4())
    _document_ids_from_field_query.side_effect = [[package_doc_id], [file_doc_id]]

    helper(client, package_uuid)

    assert client.update.mock_calls == [
        mock.call(
            body={"doc": {field: value}},
            index=package_index,
            doc_type=elasticSearchFunctions.DOC_TYPE,
            id=package_doc_id,
        ),
        mock.call(
            body={"doc": {field: value}},
            index=files_index,
            doc_type=elasticSearchFunctions.DOC_TYPE,
            id=file_doc_id,
        ),
    ]
    assert _document_ids_from_field_query.mock_calls == [
        mock.call(
            client, package_index, elasticSearchFunctions.ES_FIELD_UUID, package_uuid
        ),
        mock.call(client, files_index, package_uuid_field, package_uuid),
    ]


def test_augment_raw_search_results():
    raw_results = {
        "hits": {
            "hits": [
                {"_id": "123", "_source": {"filename": "foo.txt"}},
                {"_id": "456", "_source": {"filename": "bar.txt"}},
            ],
        },
    }

    result = elasticSearchFunctions.augment_raw_search_results(raw_results)

    assert result == [
        {"document_id": "123", "filename": "foo.txt"},
        {"document_id": "456", "filename": "bar.txt"},
    ]


@mock.patch("elasticSearchFunctions.get_client")
def test_try_to_index_fails_with_invalid_maximum_retries(client):
    with pytest.raises(ValueError, match="max_tries must be 1 or greater"):
        elasticSearchFunctions._try_to_index(
            client, {}, elasticSearchFunctions.AIPS_INDEX, max_tries=0
        )


@mock.patch("elasticSearchFunctions.get_client")
def test_try_to_index_retries_after_error(client):
    error = Exception("error")
    client.index.side_effect = [error, None]
    printfn = mock.Mock()
    data = {}
    index = elasticSearchFunctions.AIPS_INDEX

    elasticSearchFunctions._try_to_index(
        client, data, index, wait_between_tries=0, printfn=printfn
    )

    assert client.index.mock_calls == [
        mock.call(body=data, index=index, doc_type=elasticSearchFunctions.DOC_TYPE),
        mock.call(body=data, index=index, doc_type=elasticSearchFunctions.DOC_TYPE),
    ]
    assert printfn.mock_calls == [
        mock.call("ERROR: error trying to index."),
        mock.call(error),
    ]


@mock.patch("elasticSearchFunctions.get_client")
def test_try_to_index_raises_exception_after_retries(client):
    error = Exception("error")
    client.index.side_effect = [error, None]
    printfn = mock.Mock()
    data = {}
    index = elasticSearchFunctions.AIPS_INDEX

    with pytest.raises(Exception, match="error"):
        elasticSearchFunctions._try_to_index(
            client, data, index, wait_between_tries=0, max_tries=1, printfn=printfn
        )

    assert client.index.mock_calls == [
        mock.call(body=data, index=index, doc_type=elasticSearchFunctions.DOC_TYPE),
    ]
    assert printfn.mock_calls == [
        mock.call("ERROR: error trying to index."),
        mock.call(error),
    ]
