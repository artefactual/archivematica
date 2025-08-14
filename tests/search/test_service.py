import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from elasticsearch import Elasticsearch

from archivematica.search.constants import AIP_FILES_INDEX
from archivematica.search.constants import AIPS_INDEX
from archivematica.search.constants import STATUS_BACKLOG
from archivematica.search.constants import TRANSFER_FILES_INDEX
from archivematica.search.constants import TRANSFERS_INDEX
from archivematica.search.service import AIPFileNotFoundError
from archivematica.search.service import AIPNotFoundError
from archivematica.search.service import ElasticsearchSearchService
from archivematica.search.service import MultipleResultsError
from archivematica.search.service import SearchBackendInfo
from archivematica.search.service import SearchServiceError
from archivematica.search.service import SortSpec
from archivematica.search.service import TransferFileNotFoundError
from archivematica.search.service import get_search_service_instance
from archivematica.search.service import setup_search_service
from archivematica.search.service import setup_search_service_from_conf


def _mock_es_response(response_body: Any, status: int = 200) -> tuple[mock.Mock, Any]:
    """Helper to create proper Elasticsearch response format."""
    meta = mock.Mock()
    meta.status = status
    meta.headers = {"x-elastic-product": "Elasticsearch"}
    return (meta, response_body)


def _mock_es_not_exists() -> tuple[mock.Mock, bool]:
    """Helper to create Elasticsearch response for non-existent indexes."""
    return _mock_es_response(False, status=404)


def _make_es_call(
    method: str, path: str, params: Any = None, body: Any = None, headers: Any = None
) -> tuple[Any, ...]:
    """Helper to create mock.call for Elasticsearch requests with common parameters."""
    return mock.call(
        method,
        path,
        headers=mock.ANY,
        body=body,
        request_timeout=mock.ANY,
        max_retries=mock.ANY,
        retry_on_status=mock.ANY,
        retry_on_timeout=mock.ANY,
        client_meta=mock.ANY,
        otel_span=mock.ANY,
    )


@pytest.fixture
def mock_transport() -> Generator[mock.Mock, None, None]:
    with mock.patch("elastic_transport.Transport.perform_request") as mock_perform:
        yield mock_perform


@pytest.fixture
def es_client(mock_transport: mock.Mock) -> Elasticsearch:
    client = Elasticsearch(["http://localhost:9200"])
    return client


@pytest.fixture
def es_search_service(es_client: Elasticsearch) -> ElasticsearchSearchService:
    return ElasticsearchSearchService(
        client=es_client,
        transfer_files_index="transferfiles",
        aip_files_index="aipfiles",
        aips_index="aips",
        transfers_index="transfers",
        max_query_size=10000,
    )


@pytest.fixture
def mock_aip_parser() -> mock.Mock:
    mock_parser = mock.Mock()
    mock_parser.files.return_value = [
        (
            {
                "FILEUUID": str(uuid.uuid4()),
                "filePath": "data/objects/file1.txt",
                "transferMetadata": [],
                "identifiers": [],
            },
            ["accession-1"],
        ),
        (
            {
                "FILEUUID": str(uuid.uuid4()),
                "filePath": "data/objects/file2.txt",
                "transferMetadata": [],
                "identifiers": [],
            },
            ["accession-2"],
        ),
    ]
    mock_parser.aip_metadata = []
    mock_parser.is_part_of = "test-collection"
    mock_parser.aic_identifier = "aic-123"
    mock_parser.created = 1640995200.0
    return mock_parser


@pytest.fixture
def transfer_directory(tmp_path: Path) -> str:
    transfer_path = tmp_path / "test-transfer"
    transfer_path.mkdir()

    # Create the expected transfer directory structure
    data_dir = transfer_path / "data"
    data_dir.mkdir()

    objects_dir = data_dir / "objects"
    objects_dir.mkdir()

    # Create test files
    file1 = objects_dir / "file1.txt"
    file1.write_text("This is test file 1")

    file2 = objects_dir / "file2.txt"
    file2.write_text("This is test file 2")

    return str(transfer_path) + "/"


@pytest.fixture
def mock_transfer_index_data(transfer_directory: str) -> mock.Mock:
    mock_file_record1 = mock.Mock()
    mock_file_record1.uuid = uuid.uuid4()
    mock_file_record1.modificationtime = None

    mock_file_record2 = mock.Mock()
    mock_file_record2.uuid = uuid.uuid4()
    mock_file_record2.modificationtime = None

    mock_data = mock.Mock()
    mock_data.file_paths = [
        transfer_directory + "data/objects/file1.txt",
        transfer_directory + "data/objects/file2.txt",
    ]
    mock_data.files_by_location = {
        "%transferDirectory%objects/file1.txt": mock_file_record1,
        "%transferDirectory%objects/file2.txt": mock_file_record2,
    }
    mock_data.format_cache = {
        str(mock_file_record1.uuid): [
            {"puid": "fmt/95", "format": "PDF/A", "group": "Portable Document Format"}
        ],
        str(mock_file_record2.uuid): [
            {"puid": "fmt/14", "format": "PDF", "group": "Portable Document Format"}
        ],
    }
    mock_data.bulk_extractor_reports = {
        str(mock_file_record1.uuid): ["credit_card_report", "email_report"],
        str(mock_file_record2.uuid): ["email_report"],
    }
    return mock_data


def test_delete_transfer_removes_transfer_for_single_uuid(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    transfer_uuid = str(uuid.uuid4())

    delete_by_query_response = {"deleted": 1}
    mock_transport.return_value = _mock_es_response(delete_by_query_response)

    es_search_service.delete_transfer(transfer_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_delete_by_query",
            params={},
            body={"query": {"term": {"uuid": transfer_uuid}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_delete_transfer_does_nothing_when_empty_string(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    es_search_service.delete_transfer("")

    assert mock_transport.mock_calls == []


def test_delete_transfer_files_removes_files_for_single_transfer(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    transfer_id = str(uuid.uuid4())

    delete_by_query_response = {"deleted": 5}
    mock_transport.return_value = _mock_es_response(delete_by_query_response)

    es_search_service.delete_transfer_files({transfer_id})

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_delete_by_query",
            params={},
            body={"query": {"terms": {"sipuuid": [transfer_id]}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_delete_transfer_files_removes_files_for_multiple_transfers(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    transfer_ids = {str(uuid.uuid4()), str(uuid.uuid4())}

    delete_by_query_response = {"deleted": 8}
    mock_transport.return_value = _mock_es_response(delete_by_query_response)

    es_search_service.delete_transfer_files(transfer_ids)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_delete_by_query",
            params={},
            body={"query": {"terms": {"sipuuid": mock.ANY}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls

    # Validate sipuuid values independently, since the input set order is unpredictable.
    body = mock_transport.mock_calls[0][2]["body"]
    assert set(body["query"]["terms"]["sipuuid"]) == transfer_ids


def test_delete_transfer_files_does_nothing_when_empty_set(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    es_search_service.delete_transfer_files(set())

    assert mock_transport.mock_calls == []


def test_delete_transfer_files_escapes_forward_slashes_in_transfer_id(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    transfer_id = "path/with/slashes"

    delete_by_query_response = {"deleted": 0}
    mock_transport.return_value = _mock_es_response(delete_by_query_response)

    es_search_service.delete_transfer_files({transfer_id})

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_delete_by_query",
            params={},
            body={"query": {"terms": {"sipuuid": ["path\\/with\\/slashes"]}}},
        )
    ]
    assert mock_transport.mock_calls == expected_calls


def test_delete_aip_deletes_aip_for_single_uuid(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())

    delete_by_query_response = {"deleted": 1}
    mock_transport.return_value = _mock_es_response(delete_by_query_response)

    es_search_service.delete_aip(aip_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_delete_by_query",
            params={},
            body={"query": {"term": {"uuid": aip_uuid}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_delete_aip_does_nothing_when_empty_string(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    es_search_service.delete_aip("")

    assert mock_transport.mock_calls == []


def test_delete_aip_files_deletes_files_for_single_aip(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())

    delete_by_query_response = {"deleted": 5}
    mock_transport.return_value = _mock_es_response(delete_by_query_response)

    es_search_service.delete_aip_files(aip_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_delete_by_query",
            params={},
            body={"query": {"term": {"AIPUUID": aip_uuid}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_delete_aip_files_does_nothing_when_empty_string(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    es_search_service.delete_aip_files("")

    assert mock_transport.mock_calls == []


def test_mark_transfer_for_deletion_updates_transfer_and_files(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    transfer_uuid = str(uuid.uuid4())

    update_by_query_responses = [
        _mock_es_response({"updated": 1}),
        _mock_es_response({"updated": 5}),
    ]
    mock_transport.side_effect = update_by_query_responses

    es_search_service.mark_transfer_for_deletion(transfer_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.pending_deletion = params.value",
                    "params": {"value": True},
                },
                "query": {"term": {"uuid": transfer_uuid}},
            },
        ),
        _make_es_call(
            "POST",
            "/transferfiles/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.pending_deletion = params.value",
                    "params": {"value": True},
                },
                "query": {"term": {"sipuuid": transfer_uuid}},
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_unmark_transfer_for_deletion_updates_transfer_and_files(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    transfer_uuid = str(uuid.uuid4())

    update_by_query_responses = [
        _mock_es_response({"updated": 1}),
        _mock_es_response({"updated": 5}),
    ]
    mock_transport.side_effect = update_by_query_responses

    es_search_service.unmark_transfer_for_deletion(transfer_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.pending_deletion = params.value",
                    "params": {"value": False},
                },
                "query": {"term": {"uuid": transfer_uuid}},
            },
        ),
        _make_es_call(
            "POST",
            "/transferfiles/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.pending_deletion = params.value",
                    "params": {"value": False},
                },
                "query": {"term": {"sipuuid": transfer_uuid}},
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_mark_aip_for_deletion_updates_aip_and_files(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())

    update_by_query_responses = [
        _mock_es_response({"updated": 1}),
        _mock_es_response({"updated": 5}),
    ]
    mock_transport.side_effect = update_by_query_responses

    es_search_service.mark_aip_for_deletion(aip_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.status = params.value",
                    "params": {"value": "DEL_REQ"},
                },
                "query": {"term": {"uuid": aip_uuid}},
            },
        ),
        _make_es_call(
            "POST",
            "/aipfiles/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.status = params.value",
                    "params": {"value": "DEL_REQ"},
                },
                "query": {"term": {"AIPUUID": aip_uuid}},
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_unmark_aip_for_deletion_updates_aip_and_files(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())

    update_by_query_responses = [
        _mock_es_response({"updated": 1}),
        _mock_es_response({"updated": 5}),
    ]
    mock_transport.side_effect = update_by_query_responses

    es_search_service.unmark_aip_for_deletion(aip_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.status = params.value",
                    "params": {"value": "UPLOADED"},
                },
                "query": {"term": {"uuid": aip_uuid}},
            },
        ),
        _make_es_call(
            "POST",
            "/aipfiles/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.status = params.value",
                    "params": {"value": "UPLOADED"},
                },
                "query": {"term": {"AIPUUID": aip_uuid}},
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_ensure_indexes_exist_does_nothing_when_all_indexes_exist(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    indexes = ["aips", "transfers"]

    mock_transport.return_value = _mock_es_response(True)

    es_search_service.ensure_indexes_exist(indexes)

    expected_calls = [
        _make_es_call(
            "HEAD",
            "/aips,transfers",
            params={},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_ensure_indexes_exist_creates_missing_indexes(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    indexes = ["aips", "transfers"]

    # Set up responses for the sequence: exists check returns False, then two create responses.
    mock_transport.side_effect = [
        _mock_es_response(False, status=404),
        _mock_es_response({"acknowledged": True}),
        _mock_es_response({"acknowledged": True}),
    ]

    es_search_service.ensure_indexes_exist(indexes)

    expected_calls = [
        _make_es_call(
            "HEAD",
            "/aips,transfers",
            params={},
        ),
        _make_es_call(
            "PUT",
            "/aips",
            params={"ignore": 400},
            body={"settings": mock.ANY, "mappings": mock.ANY},
        ),
        _make_es_call(
            "PUT",
            "/transfers",
            params={"ignore": 400},
            body={"settings": mock.ANY, "mappings": mock.ANY},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_ensure_indexes_exist_skips_invalid_index_names(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    indexes = ["aips", "invalid_index", "transfers"]

    # Only valid indexes get created, so we expect two create responses after the exists check.
    mock_transport.side_effect = [
        _mock_es_response(False, status=404),
        _mock_es_response({"acknowledged": True}),
        _mock_es_response({"acknowledged": True}),
    ]

    es_search_service.ensure_indexes_exist(indexes)

    expected_calls = [
        _make_es_call(
            "HEAD",
            "/aips,invalid_index,transfers",
            params={},
        ),
        _make_es_call(
            "PUT",
            "/aips",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
        _make_es_call(
            "PUT",
            "/transfers",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_ensure_indexes_exist_does_nothing_with_empty_list(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    es_search_service.ensure_indexes_exist([])

    assert mock_transport.mock_calls == []


def test_ensure_indexes_exist_creates_all_supported_indexes(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    indexes = ["aips", "aipfiles", "transfers", "transferfiles"]

    mock_transport.side_effect = [
        _mock_es_response(False, status=404),
        _mock_es_response({"acknowledged": True}),
        _mock_es_response({"acknowledged": True}),
        _mock_es_response({"acknowledged": True}),
        _mock_es_response({"acknowledged": True}),
    ]

    es_search_service.ensure_indexes_exist(indexes)

    expected_calls = [
        _make_es_call(
            "HEAD",
            "/aips,aipfiles,transfers,transferfiles",
            params={},
        ),
        _make_es_call(
            "PUT",
            "/aips",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
        _make_es_call(
            "PUT",
            "/aipfiles",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
        _make_es_call(
            "PUT",
            "/transfers",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
        _make_es_call(
            "PUT",
            "/transferfiles",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_delete_indexes_deletes_single_index(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    indexes = ["aips"]

    delete_response = {"acknowledged": True}
    mock_transport.return_value = _mock_es_response(delete_response)

    es_search_service.delete_indexes(indexes)

    expected_calls = [
        _make_es_call(
            "DELETE",
            "/aips",
            params={"ignore": 404},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_delete_indexes_deletes_multiple_indexes(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    indexes = ["aips", "transfers"]

    delete_response = {"acknowledged": True}
    mock_transport.return_value = _mock_es_response(delete_response)

    es_search_service.delete_indexes(indexes)

    expected_calls = [
        _make_es_call(
            "DELETE",
            "/aips,transfers",
            params={"ignore": 404},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_delete_indexes_does_nothing_with_empty_list(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    es_search_service.delete_indexes([])

    assert mock_transport.mock_calls == []


def test_update_index_mappings_updates_mappings(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    index = "aips"
    mappings = {
        "properties": {"status": {"type": "keyword"}, "filecount": {"type": "integer"}}
    }

    update_response = {"acknowledged": True}
    mock_transport.return_value = _mock_es_response(update_response)

    es_search_service.update_index_mappings(index, mappings)

    expected_calls = [
        _make_es_call(
            "PUT",
            "/aips/_mapping",
            params={},
            body=mappings,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_reindex_from_remote_handles_successful_reindex(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    remote_config = {
        "host": "https://remote:9200",
        "username": "user",
        "password": "pass",
        "socket_timeout": "30s",
        "connect_timeout": "30s",
        "size": 100,
    }
    index_mappings = [{"dest_index": "aips", "source_index": "aips"}]

    reindex_response = {"took": 123, "total": 5, "created": 5}
    mock_transport.return_value = _mock_es_response(reindex_response)

    result = es_search_service.reindex_from_remote(remote_config, index_mappings)

    expected_calls = [
        _make_es_call(
            "POST",
            "/_reindex",
            params={},
            body={
                "source": {
                    "remote": remote_config,
                    "index": "aips",
                    "size": 100,
                },
                "dest": {"index": "aips"},
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == {
        "successful": [{"index": "aips", "response": reindex_response}],
        "failed": [],
    }


def test_reindex_from_remote_handles_failed_reindex(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    remote_config = {
        "host": "https://remote:9200",
        "size": 10,
    }
    index_mappings = [
        {"dest_index": "aips", "source_index": "aips", "source_type": "aip"},
    ]

    mock_transport.side_effect = Exception("Connection failed")

    result = es_search_service.reindex_from_remote(remote_config, index_mappings)

    assert result == {
        "successful": [],
        "failed": [{"index": "aips", "error": "Connection failed"}],
    }


def test_reindex_from_remote_handles_mixed_results(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    remote_config = {
        "host": "https://remote:9200",
        "size": 50,
    }
    index_mappings = [
        {"dest_index": "aips", "source_index": "aips", "source_type": "aip"},
        {
            "dest_index": "transfers",
            "source_index": "transfers",
            "source_type": "transfer",
        },
    ]

    reindex_response = {"took": 123, "total": 3, "created": 3}
    mock_transport.side_effect = [
        _mock_es_response(reindex_response),
        Exception("Failed"),
    ]

    result = es_search_service.reindex_from_remote(remote_config, index_mappings)

    assert result == {
        "successful": [{"index": "aips", "response": reindex_response}],
        "failed": [{"index": "transfers", "error": "Failed"}],
    }


def test_update_all_documents_updates_all_documents(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    index = "aipfiles"

    update_response = {"took": 456, "updated": 100}
    mock_transport.return_value = _mock_es_response(update_response)

    result = es_search_service.update_all_documents(index)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_update_by_query",
            params={},
            body=None,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == update_response


def test_get_aip_data_returns_single_document(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())
    aip_document = {
        "_id": "doc123",
        "_source": {
            "uuid": aip_uuid,
            "name": "test-aip",
            "status": "UPLOADED",
            "size": 1024,
        },
    }

    search_response = {
        "hits": {
            "total": {"value": 1},
            "hits": [aip_document],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.get_aip_data(aip_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={},
            body={"query": {"term": {"uuid": aip_uuid}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == aip_document


def test_get_aip_data_with_fields_parameter(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())
    aip_document = {
        "_id": "doc123",
        "_source": {
            "uuid": aip_uuid,
            "name": "test-aip",
        },
    }

    search_response = {
        "hits": {
            "total": {"value": 1},
            "hits": [aip_document],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.get_aip_data(aip_uuid, fields=["uuid", "name"])

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={"_source": b"uuid,name"},
            body={"query": {"term": {"uuid": aip_uuid}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == aip_document


def test_get_aip_data_raises_exception_when_not_found(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())

    search_response = {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    with pytest.raises(AIPNotFoundError, match=f"No AIP found with uuid {aip_uuid}"):
        es_search_service.get_aip_data(aip_uuid)


def test_get_aip_data_raises_exception_when_multiple_found(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())

    search_response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {"_id": "doc1", "_source": {"uuid": aip_uuid}},
                {"_id": "doc2", "_source": {"uuid": aip_uuid}},
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    with pytest.raises(
        MultipleResultsError,
        match=f"2 AIPs found with uuid {aip_uuid}; unable to fetch a single result",
    ):
        es_search_service.get_aip_data(aip_uuid)


def test_get_aipfile_data_returns_single_document(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    aipfile_document = {
        "_id": "file123",
        "_source": {
            "FILEUUID": file_uuid,
            "AIPUUID": str(uuid.uuid4()),
            "filePath": "data/objects/test.txt",
            "fileExtension": "txt",
        },
    }

    search_response = {
        "hits": {
            "total": {"value": 1},
            "hits": [aipfile_document],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.get_aipfile_data(file_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={},
            body={"query": {"term": {"FILEUUID": file_uuid}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == aipfile_document


def test_get_aipfile_data_with_fields_parameter(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    aipfile_document = {
        "_id": "file123",
        "_source": {
            "FILEUUID": file_uuid,
            "filePath": "data/objects/test.txt",
        },
    }

    search_response = {
        "hits": {
            "total": {"value": 1},
            "hits": [aipfile_document],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.get_aipfile_data(
        file_uuid, fields=["FILEUUID", "filePath"]
    )

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={"_source": b"FILEUUID,filePath"},
            body={"query": {"term": {"FILEUUID": file_uuid}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == aipfile_document


def test_get_aipfile_data_raises_exception_when_not_found(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())

    search_response = {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    with pytest.raises(
        AIPFileNotFoundError, match=f"No AIP file found with FILEUUID {file_uuid}"
    ):
        es_search_service.get_aipfile_data(file_uuid)


def test_get_aipfile_data_raises_exception_when_multiple_found(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())

    search_response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {"_id": "file1", "_source": {"FILEUUID": file_uuid}},
                {"_id": "file2", "_source": {"FILEUUID": file_uuid}},
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    with pytest.raises(
        MultipleResultsError,
        match=f"2 AIP files found with FILEUUID {file_uuid}; unable to fetch a single result",
    ):
        es_search_service.get_aipfile_data(file_uuid)


def test_get_transfer_file_tags_returns_tags_when_present(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    tags = ["tag1", "tag2", "tag3"]
    transfer_file_document = {
        "_id": "file123",
        "_source": {
            "fileuuid": file_uuid,
            "sipuuid": str(uuid.uuid4()),
            "filename": "test.txt",
            "tags": tags,
        },
    }

    search_response = {
        "hits": {
            "total": {"value": 1},
            "hits": [transfer_file_document],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.get_transfer_file_tags(file_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"_source": b"tags"},
            body={"query": {"term": {"fileuuid": file_uuid}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == tags


def test_get_transfer_file_tags_returns_empty_list_when_no_tags(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    transfer_file_document = {
        "_id": "file123",
        "_source": {
            "fileuuid": file_uuid,
            "sipuuid": str(uuid.uuid4()),
            "filename": "test.txt",
        },
    }

    search_response = {
        "hits": {
            "total": {"value": 1},
            "hits": [transfer_file_document],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.get_transfer_file_tags(file_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"_source": b"tags"},
            body={"query": {"term": {"fileuuid": file_uuid}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == []


def test_get_transfer_file_tags_returns_empty_list_when_no_source(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    transfer_file_document = {
        "_id": "file123",
    }

    search_response = {
        "hits": {
            "total": {"value": 1},
            "hits": [transfer_file_document],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.get_transfer_file_tags(file_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"_source": b"tags"},
            body={"query": {"term": {"fileuuid": file_uuid}}},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == []


def test_get_transfer_file_tags_raises_exception_when_not_found(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())

    search_response = {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    with pytest.raises(
        TransferFileNotFoundError,
        match=f"No transfer file found with fileuuid {file_uuid}",
    ):
        es_search_service.get_transfer_file_tags(file_uuid)


def test_get_transfer_file_tags_raises_exception_when_multiple_found(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())

    search_response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {"_id": "file1", "_source": {"fileuuid": file_uuid, "tags": ["tag1"]}},
                {"_id": "file2", "_source": {"fileuuid": file_uuid, "tags": ["tag2"]}},
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    with pytest.raises(
        MultipleResultsError,
        match=f"2 transfer files found with fileuuid {file_uuid}; unable to fetch a single result",
    ):
        es_search_service.get_transfer_file_tags(file_uuid)


def test_get_transfer_file_data_returns_single_result(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    transfer_file_data = {
        "filename": "test.txt",
        "fileuuid": file_uuid,
        "sipuuid": str(uuid.uuid4()),
        "relative_path": "data/test.txt",
        "size": 1024,
    }

    search_response = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "doc123",
                    "_source": transfer_file_data,
                }
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.get_transfer_file_data(file_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={},
            body={"query": {"term": {"fileuuid": file_uuid}}, "size": 10000},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == transfer_file_data


def test_get_transfer_file_data_handles_multiple_results_with_exact_match(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    correct_file_data = {
        "filename": "correct.txt",
        "fileuuid": file_uuid,
    }
    incorrect_file_data = {
        "filename": "incorrect.txt",
        "fileuuid": "different-uuid",
    }

    search_response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_id": "doc1",
                    "_source": incorrect_file_data,
                },
                {
                    "_id": "doc2",
                    "_source": correct_file_data,
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.get_transfer_file_data(file_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={},
            body={"query": {"term": {"fileuuid": file_uuid}}, "size": 10000},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == correct_file_data


def test_get_transfer_file_data_uses_first_when_multiple_exact_matches(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    first_file_data = {
        "filename": "first.txt",
        "fileuuid": file_uuid,
    }
    second_file_data = {
        "filename": "second.txt",
        "fileuuid": file_uuid,
    }

    search_response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_id": "doc1",
                    "_source": first_file_data,
                },
                {
                    "_id": "doc2",
                    "_source": second_file_data,
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.get_transfer_file_data(file_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={},
            body={"query": {"term": {"fileuuid": file_uuid}}, "size": 10000},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == first_file_data


def test_get_transfer_file_data_raises_exception_when_no_exact_matches(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    incorrect_file_data_1 = {
        "filename": "incorrect1.txt",
        "fileuuid": "different-uuid-1",
    }
    incorrect_file_data_2 = {
        "filename": "incorrect2.txt",
        "fileuuid": "different-uuid-2",
    }

    search_response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_id": "doc1",
                    "_source": incorrect_file_data_1,
                },
                {
                    "_id": "doc2",
                    "_source": incorrect_file_data_2,
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    with pytest.raises(
        SearchServiceError,
        match="get_transfer_file_data returned no exact results",
    ):
        es_search_service.get_transfer_file_data(file_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={},
            body={"query": {"term": {"fileuuid": file_uuid}}, "size": 10000},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_get_transfer_file_data_raises_exception_when_no_results(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())

    search_response = {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    with pytest.raises(
        TransferFileNotFoundError,
        match=f"No transfer file found with fileuuid {file_uuid}",
    ):
        es_search_service.get_transfer_file_data(file_uuid)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={},
            body={"query": {"term": {"fileuuid": file_uuid}}, "size": 10000},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_set_transfer_file_tags_updates_tags_with_list(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    tags = ["tag1", "tag2", "tag3"]

    update_by_query_response = {"updated": 1}
    mock_transport.return_value = _mock_es_response(update_by_query_response)

    es_search_service.set_transfer_file_tags(file_uuid, tags)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.tags = params.value",
                    "params": {"value": tags},
                },
                "query": {"term": {"fileuuid": file_uuid}},
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_set_transfer_file_tags_clears_tags_with_empty_list(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    tags: list[str] = []

    update_by_query_response = {"updated": 1}
    mock_transport.return_value = _mock_es_response(update_by_query_response)

    es_search_service.set_transfer_file_tags(file_uuid, tags)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.tags = params.value",
                    "params": {"value": []},
                },
                "query": {"term": {"fileuuid": file_uuid}},
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_set_transfer_file_tags_escapes_forward_slashes_in_uuid(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = "path/with/slashes"
    tags = ["tag1"]

    update_by_query_response = {"updated": 1}
    mock_transport.return_value = _mock_es_response(update_by_query_response)

    es_search_service.set_transfer_file_tags(file_uuid, tags)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.tags = params.value",
                    "params": {"value": tags},
                },
                "query": {"term": {"fileuuid": "path\\/with\\/slashes"}},
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_set_transfer_file_tags_handles_single_tag(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    file_uuid = str(uuid.uuid4())
    tags = ["single_tag"]

    update_by_query_response = {"updated": 1}
    mock_transport.return_value = _mock_es_response(update_by_query_response)

    es_search_service.set_transfer_file_tags(file_uuid, tags)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_update_by_query",
            params={},
            body={
                "script": {
                    "source": "ctx._source.tags = params.value",
                    "params": {"value": tags},
                },
                "query": {"term": {"fileuuid": file_uuid}},
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_search_transfer_files_returns_search_results(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"status": "completed"}},
                    {"match": {"filename": "test"}},
                ]
            }
        }
    }

    search_response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_id": "file1",
                    "_source": {
                        "fileuuid": str(uuid.uuid4()),
                        "filename": "test1.txt",
                        "status": "completed",
                    },
                },
                {
                    "_id": "file2",
                    "_source": {
                        "fileuuid": str(uuid.uuid4()),
                        "filename": "test2.txt",
                        "status": "completed",
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfer_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfer_files_uses_max_query_size(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 5000},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    es_search_service.search_transfer_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_search_transfer_files_with_complex_query(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"size": {"gte": 1000}}},
                    {"terms": {"file_extension": ["txt", "pdf"]}},
                ],
                "filter": [
                    {"term": {"pending_deletion": False}},
                ],
            }
        },
        "sort": [
            {"created": {"order": "desc"}},
        ],
    }

    search_response = {
        "hits": {
            "total": {"value": 150},
            "hits": [
                {
                    "_id": "file1",
                    "_source": {
                        "fileuuid": str(uuid.uuid4()),
                        "filename": "large_doc.pdf",
                        "size": 5000,
                        "file_extension": "pdf",
                        "pending_deletion": False,
                        "created": 1234567890,
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfer_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfer_files_returns_empty_results(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"term": {"nonexistent_field": "value"}}}

    search_response = {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfer_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfer_files_with_custom_size(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 50},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfer_files(query, size=50)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"size": "50"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfer_files_with_pagination(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 100},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfer_files(query, size=20, from_=40)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"size": "20", "from": "40"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfer_files_with_sort(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 10},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfer_files(
        query, sort=SortSpec(field="filename", order="asc")
    )

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"size": "10000", "sort": b"filename:asc"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfer_files_with_fields(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}
    fields = ["filename", "fileuuid", "sipuuid"]

    search_response = {
        "hits": {
            "total": {"value": 5},
            "hits": [
                {
                    "_id": "file1",
                    "_source": {
                        "filename": "test.txt",
                        "fileuuid": str(uuid.uuid4()),
                        "sipuuid": str(uuid.uuid4()),
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfer_files(query, fields=fields)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"_source": b"filename,fileuuid,sipuuid", "size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfer_files_with_all_parameters(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"status": "backlog"}},
                    {"match": {"filename": "test"}},
                ]
            }
        }
    }
    fields = ["filename", "sipuuid", "relative_path", "accessionid", "pending_deletion"]

    search_response = {
        "hits": {
            "total": {"value": 25},
            "hits": [
                {
                    "_id": "file1",
                    "_source": {
                        "filename": "test1.txt",
                        "sipuuid": str(uuid.uuid4()),
                        "relative_path": "data/test1.txt",
                        "accessionid": "ACC001",
                        "pending_deletion": False,
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfer_files(
        query=query,
        size=10,
        from_=20,
        sort=SortSpec(field="filename.raw", order="desc"),
        fields=fields,
    )

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={
                "size": "10",
                "from": "20",
                "sort": b"filename.raw:desc",
                "_source": b"filename,sipuuid,relative_path,accessionid,pending_deletion",
            },
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfer_files_with_zero_from_parameter(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 30},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfer_files(query, from_=0)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transferfiles/_search",
            params={"size": "10000", "from": "0"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfers_returns_search_results(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"status": "backlog"}},
                    {"match": {"name": "test"}},
                ]
            }
        }
    }

    search_response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_id": "transfer1",
                    "_source": {
                        "uuid": str(uuid.uuid4()),
                        "name": "test-transfer-1",
                        "status": "backlog",
                    },
                },
                {
                    "_id": "transfer2",
                    "_source": {
                        "uuid": str(uuid.uuid4()),
                        "name": "test-transfer-2",
                        "status": "backlog",
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfers(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfers_uses_max_query_size(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 5000},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    es_search_service.search_transfers(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_search_transfers_with_complex_query(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"file_count": {"gte": 10}}},
                    {"terms": {"status": ["backlog", "completed"]}},
                ],
                "filter": [
                    {"term": {"pending_deletion": False}},
                ],
            }
        },
        "sort": [
            {"ingest_date": {"order": "desc"}},
        ],
    }

    search_response = {
        "hits": {
            "total": {"value": 150},
            "hits": [
                {
                    "_id": "transfer1",
                    "_source": {
                        "uuid": str(uuid.uuid4()),
                        "name": "large-transfer",
                        "file_count": 50,
                        "status": "backlog",
                        "pending_deletion": False,
                        "ingest_date": "2024-01-01",
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfers(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfers_returns_empty_results(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"term": {"nonexistent_field": "value"}}}

    search_response = {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfers(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfers_with_custom_size(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 50},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfers(query, size=50)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_search",
            params={"size": "50"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfers_with_pagination(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 100},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfers(query, size=20, from_=40)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_search",
            params={"size": "20", "from": "40"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfers_with_sort(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 10},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfers(
        query, sort=SortSpec(field="name", order="asc")
    )

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_search",
            params={"size": "10000", "sort": b"name:asc"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfers_with_fields(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}
    fields = ["name", "uuid", "status"]

    search_response = {
        "hits": {
            "total": {"value": 5},
            "hits": [
                {
                    "_id": "transfer1",
                    "_source": {
                        "name": "test-transfer",
                        "uuid": str(uuid.uuid4()),
                        "status": "backlog",
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfers(query, fields=fields)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_search",
            params={"size": "10000", "_source": b"name,uuid,status"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfers_with_all_parameters(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"status": "backlog"}},
                    {"match": {"name": "test"}},
                ]
            }
        }
    }
    fields = ["name", "uuid", "accessionid", "file_count", "pending_deletion"]

    search_response = {
        "hits": {
            "total": {"value": 25},
            "hits": [
                {
                    "_id": "transfer1",
                    "_source": {
                        "name": "test-transfer-1",
                        "uuid": str(uuid.uuid4()),
                        "accessionid": "ACC001",
                        "file_count": 15,
                        "pending_deletion": False,
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfers(
        query=query,
        size=10,
        from_=20,
        sort=SortSpec(field="name.raw", order="desc"),
        fields=fields,
    )

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_search",
            params={
                "size": "10",
                "from": "20",
                "sort": b"name.raw:desc",
                "_source": b"name,uuid,accessionid,file_count,pending_deletion",
            },
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_transfers_with_zero_from_parameter(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 30},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_transfers(query, from_=0)

    expected_calls = [
        _make_es_call(
            "POST",
            "/transfers/_search",
            params={"size": "10000", "from": "0"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aips_returns_search_results(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"status": "UPLOADED"}},
                    {"match": {"name": "test"}},
                ]
            }
        }
    }

    search_response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_id": "aip1",
                    "_source": {
                        "uuid": str(uuid.uuid4()),
                        "name": "test-aip-1",
                        "status": "UPLOADED",
                    },
                },
                {
                    "_id": "aip2",
                    "_source": {
                        "uuid": str(uuid.uuid4()),
                        "name": "test-aip-2",
                        "status": "UPLOADED",
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aips(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aips_uses_max_query_size(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 5000},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    es_search_service.search_aips(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_search_aips_with_complex_query(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"filecount": {"gte": 100}}},
                    {"terms": {"status": ["UPLOADED", "STORED"]}},
                ],
                "filter": [
                    {"exists": {"field": "location"}},
                ],
            }
        },
        "sort": [
            {"name": {"order": "asc"}},
        ],
    }

    search_response = {
        "hits": {
            "total": {"value": 150},
            "hits": [
                {
                    "_id": "aip1",
                    "_source": {
                        "uuid": str(uuid.uuid4()),
                        "name": "large-aip",
                        "filecount": 500,
                        "status": "UPLOADED",
                        "location": "/storage/aips/large-aip",
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aips(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aips_returns_empty_results(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"term": {"nonexistent_field": "value"}}}

    search_response = {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aips(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aips_with_custom_size(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 50},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aips(query, size=50)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={"size": "50"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aips_with_pagination(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 100},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aips(query, size=20, from_=40)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={"size": "20", "from": "40"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aips_with_sort(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 10},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aips(
        query, sort=SortSpec(field="name", order="asc")
    )

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={"size": "10000", "sort": b"name:asc"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aips_with_fields(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}
    fields = ["name", "uuid", "status"]

    search_response = {
        "hits": {
            "total": {"value": 5},
            "hits": [
                {
                    "_id": "aip1",
                    "_source": {
                        "name": "test-aip",
                        "uuid": str(uuid.uuid4()),
                        "status": "UPLOADED",
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aips(query, fields=fields)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={"size": "10000", "_source": b"name,uuid,status"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aips_with_all_parameters(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"status": "UPLOADED"}},
                    {"match": {"name": "test"}},
                ]
            }
        }
    }
    fields = ["name", "uuid", "accessionid", "filecount", "size"]

    search_response = {
        "hits": {
            "total": {"value": 25},
            "hits": [
                {
                    "_id": "aip1",
                    "_source": {
                        "name": "test-aip-1",
                        "uuid": str(uuid.uuid4()),
                        "accessionid": "ACC001",
                        "filecount": 15,
                        "size": 1024000,
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aips(
        query=query,
        size=10,
        from_=20,
        sort=SortSpec(field="name.raw", order="desc"),
        fields=fields,
    )

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={
                "size": "10",
                "from": "20",
                "sort": b"name.raw:desc",
                "_source": b"name,uuid,accessionid,filecount,size",
            },
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aips_with_zero_from_parameter(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 30},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aips(query, from_=0)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aips/_search",
            params={"size": "10000", "from": "0"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aip_files_returns_search_results(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"status": "UPLOADED"}},
                    {"match": {"filePath": "test"}},
                ]
            }
        }
    }

    search_response = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_id": "aipfile1",
                    "_source": {
                        "FILEUUID": str(uuid.uuid4()),
                        "AIPUUID": str(uuid.uuid4()),
                        "filePath": "data/objects/test1.txt",
                        "status": "UPLOADED",
                    },
                },
                {
                    "_id": "aipfile2",
                    "_source": {
                        "FILEUUID": str(uuid.uuid4()),
                        "AIPUUID": str(uuid.uuid4()),
                        "filePath": "data/objects/test2.txt",
                        "status": "UPLOADED",
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aip_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aip_files_uses_max_query_size(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 5000},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    es_search_service.search_aip_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_search_aip_files_with_complex_query(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"fileExtension": "pdf"}},
                    {"terms": {"status": ["UPLOADED", "INDEXED"]}},
                ],
                "filter": [
                    {"range": {"indexedAt": {"gte": 1234567890}}},
                ],
            }
        },
        "sort": [
            {"filePath": {"order": "asc"}},
        ],
    }

    search_response = {
        "hits": {
            "total": {"value": 150},
            "hits": [
                {
                    "_id": "aipfile1",
                    "_source": {
                        "FILEUUID": str(uuid.uuid4()),
                        "AIPUUID": str(uuid.uuid4()),
                        "filePath": "data/objects/document.pdf",
                        "fileExtension": "pdf",
                        "status": "UPLOADED",
                        "indexedAt": 1234567900,
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aip_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aip_files_returns_empty_results(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"term": {"nonexistent_field": "value"}}}

    search_response = {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aip_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={"size": "10000"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aip_files_with_custom_size(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 50},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aip_files(query, size=50)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={"size": "50"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aip_files_with_pagination(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 100},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aip_files(query, size=20, from_=40)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={"size": "20", "from": "40"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aip_files_with_sort(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 10},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aip_files(
        query, sort=SortSpec(field="filePath", order="asc")
    )

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={"size": "10000", "sort": b"filePath:asc"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aip_files_with_fields(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}
    fields = ["filePath", "FILEUUID", "AIPUUID"]

    search_response = {
        "hits": {
            "total": {"value": 5},
            "hits": [
                {
                    "_id": "aipfile1",
                    "_source": {
                        "filePath": "data/objects/test.txt",
                        "FILEUUID": str(uuid.uuid4()),
                        "AIPUUID": str(uuid.uuid4()),
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aip_files(query, fields=fields)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={"size": "10000", "_source": b"filePath,FILEUUID,AIPUUID"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aip_files_with_all_parameters(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"status": "UPLOADED"}},
                    {"match": {"filePath": "test"}},
                ]
            }
        }
    }
    fields = ["filePath", "FILEUUID", "AIPUUID", "fileExtension", "origin"]

    search_response = {
        "hits": {
            "total": {"value": 25},
            "hits": [
                {
                    "_id": "aipfile1",
                    "_source": {
                        "filePath": "data/objects/test1.txt",
                        "FILEUUID": str(uuid.uuid4()),
                        "AIPUUID": str(uuid.uuid4()),
                        "fileExtension": "txt",
                        "origin": "transfer",
                    },
                },
            ],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aip_files(
        query=query,
        size=10,
        from_=20,
        sort=SortSpec(field="filePath.raw", order="desc"),
        fields=fields,
    )

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={
                "size": "10",
                "from": "20",
                "sort": b"filePath.raw:desc",
                "_source": b"filePath,FILEUUID,AIPUUID,fileExtension,origin",
            },
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_search_aip_files_with_zero_from_parameter(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    search_response = {
        "hits": {
            "total": {"value": 30},
            "hits": [],
        }
    }
    mock_transport.return_value = _mock_es_response(search_response)

    result = es_search_service.search_aip_files(query, from_=0)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_search",
            params={"size": "10000", "from": "0"},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == search_response


def test_get_aipfile_by_document_id_returns_document(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    document_id = "aipfile123"
    aipfile_document = {
        "_id": document_id,
        "_source": {
            "FILEUUID": str(uuid.uuid4()),
            "AIPUUID": str(uuid.uuid4()),
            "filePath": "data/objects/test.txt",
            "fileExtension": "txt",
            "status": "UPLOADED",
        },
        "_index": "aipfiles",
        "_version": 1,
        "found": True,
    }

    mock_transport.return_value = _mock_es_response(aipfile_document)

    result = es_search_service.get_aipfile_by_document_id(document_id)

    expected_calls = [
        _make_es_call(
            "GET",
            "/aipfiles/_doc/aipfile123",
            params={},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == aipfile_document


def test_get_aipfile_by_document_id_raises_exception_when_not_found(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    document_id = "nonexistent_doc"

    mock_transport.side_effect = Exception("Document not found")

    with pytest.raises(
        AIPFileNotFoundError,
        match=f"AIP file document {document_id} not found: Document not found",
    ):
        es_search_service.get_aipfile_by_document_id(document_id)

    expected_calls = [
        _make_es_call(
            "GET",
            "/aipfiles/_doc/nonexistent_doc",
            params={},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_count_aip_files_returns_count(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"status": "UPLOADED"}},
                ]
            }
        }
    }

    count_response = {"count": 42}
    mock_transport.return_value = _mock_es_response(count_response)

    result = es_search_service.count_aip_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_count",
            params={},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == 42


def test_count_aip_files_returns_zero_on_exception(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"match_all": {}}}

    mock_transport.side_effect = Exception("Elasticsearch error")

    result = es_search_service.count_aip_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_count",
            params={},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == 0


def test_count_aip_files_returns_zero_for_empty_result(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    query: dict[str, Any] = {"query": {"term": {"nonexistent_field": "value"}}}

    count_response = {"count": 0}
    mock_transport.return_value = _mock_es_response(count_response)

    result = es_search_service.count_aip_files(query)

    expected_calls = [
        _make_es_call(
            "POST",
            "/aipfiles/_count",
            params={},
            body=query,
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == 0


@pytest.mark.parametrize(
    "elasticsearch_info,expected_result",
    [
        (
            {
                "name": "elasticsearch-node-1",
                "cluster_name": "archivematica-cluster",
                "cluster_uuid": "uuid-123",
                "version": {
                    "number": "7.17.0",
                    "build_flavor": "default",
                    "build_type": "docker",
                    "build_hash": "bee86328705acaa9a6daede7140defd4d9ec56bd",
                    "build_date": "2022-01-28T08:36:04.875279988Z",
                    "build_snapshot": False,
                    "lucene_version": "8.11.1",
                    "minimum_wire_compatibility_version": "6.8.0",
                    "minimum_index_compatibility_version": "6.0.0-beta1",
                },
                "tagline": "You Know, for Search",
            },
            "with_cluster_name",
        ),
        (
            {
                "name": "elasticsearch-node-1",
                "version": {
                    "number": "7.17.0",
                    "build_flavor": "default",
                    "build_type": "docker",
                    "build_hash": "bee86328705acaa9a6daede7140defd4d9ec56bd",
                    "build_date": "2022-01-28T08:36:04.875279988Z",
                    "build_snapshot": False,
                    "lucene_version": "8.11.1",
                    "minimum_wire_compatibility_version": "6.8.0",
                    "minimum_index_compatibility_version": "6.0.0-beta1",
                },
                "tagline": "You Know, for Search",
            },
            "without_cluster_name",
        ),
    ],
    ids=["with_cluster_name", "without_cluster_name"],
)
def test_get_cluster_info_returns_elasticsearch_info(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
    elasticsearch_info: dict[str, Any],
    expected_result: str,
) -> None:
    mock_transport.return_value = _mock_es_response(elasticsearch_info)

    result = es_search_service.get_cluster_info()

    expected_calls = [
        _make_es_call(
            "GET",
            "/",
            params={},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls

    # Construct the expected SearchBackendInfo based on the test scenario
    expected_cluster_name = (
        elasticsearch_info.get("cluster_name")
        if expected_result == "with_cluster_name"
        else None
    )
    expected = SearchBackendInfo(
        name="elasticsearch-node-1",
        version="7.17.0",
        cluster_name=expected_cluster_name,
        raw_info=elasticsearch_info,
    )
    assert result == expected


def test_get_cluster_info_raises_exception_when_connection_fails(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
) -> None:
    error_message = "Connection refused"
    mock_transport.side_effect = Exception(error_message)

    with pytest.raises(
        SearchServiceError,
        match=f"Unable to connect to Elasticsearch: {error_message}",
    ):
        es_search_service.get_cluster_info()

    expected_calls = [
        _make_es_call(
            "GET",
            "/",
            params={},
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_index_aip_successfully_indexes_aip_and_files(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
    mock_aip_parser: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())
    aip_name = "test-aip"
    aip_stored_path = "/path/to/aip"
    aip_size = 2048000
    am_version = "1.17.0"
    indexed_at = "2024-01-01T00:00:00Z"
    identifiers = [{"type": "dc", "value": "test-id"}]
    dashboard_uuid = str(uuid.uuid4())
    location = "test-location"

    bulk_response = {"took": 100, "errors": False, "items": []}
    cluster_health_response = {"status": "yellow"}
    aip_index_response = {"_id": "aip1", "result": "created"}

    mock_transport.side_effect = [
        _mock_es_response(bulk_response),
        _mock_es_response(cluster_health_response),
        _mock_es_response(aip_index_response),
    ]

    result = es_search_service.index_aip(
        uuid=aip_uuid,
        aip_stored_path=aip_stored_path,
        parser=mock_aip_parser,
        name=aip_name,
        aip_size=aip_size,
        am_version=am_version,
        indexed_at=indexed_at,
        identifiers=identifiers,
        aips_in_aic=5,
        encrypted=False,
        location=location,
        dashboard_uuid=dashboard_uuid,
    )

    mock_aip_parser.files.assert_called_once()

    expected_calls = [
        _make_es_call(
            "PUT",
            "/_bulk",
            params={},
            body=mock.ANY,
        ),
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call(
            "POST",
            "/aips/_doc",
            params={},
            body={
                "uuid": aip_uuid,
                "name": "test-aip",
                "filePath": "/path/to/aip",
                "size": 1.953125,  # 2048000 / 1024 / 1024.
                "file_count": 0,
                "origin": dashboard_uuid,
                "created": 1640995200.0,
                "AICID": "aic-123",
                "isPartOf": "test-collection",
                "countAIPsinAIC": 5,
                "identifiers": [{"type": "dc", "value": "test-id"}],
                "transferMetadata": [],
                "encrypted": False,
                "accessionids": mock.ANY,  # Order not guaranteed due to set operations.
                "status": "UPLOADED",
                "location": "test-location",
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == 0


def test_index_aip_handles_parser_exception_and_returns_error(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
    mock_aip_parser: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())
    aip_name = "test-aip"
    aip_stored_path = "/path/to/aip"
    aip_size = 2048000
    am_version = "1.17.0"
    indexed_at = "2024-01-01T00:00:00Z"
    identifiers = [{"type": "dc", "value": "test-id"}]
    dashboard_uuid = str(uuid.uuid4())
    location = "test-location"

    mock_aip_parser.files.side_effect = Exception("Parser failed to read METS file")

    result = es_search_service.index_aip(
        uuid=aip_uuid,
        aip_stored_path=aip_stored_path,
        parser=mock_aip_parser,
        name=aip_name,
        aip_size=aip_size,
        am_version=am_version,
        indexed_at=indexed_at,
        identifiers=identifiers,
        aips_in_aic=5,
        encrypted=False,
        location=location,
        dashboard_uuid=dashboard_uuid,
    )

    mock_aip_parser.files.assert_called_once()
    assert mock_transport.mock_calls == []
    assert result == 1


def test_index_aip_handles_elasticsearch_exception_and_returns_error(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
    mock_aip_parser: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())
    aip_name = "test-aip"
    aip_stored_path = "/path/to/aip"
    aip_size = 2048000
    am_version = "1.17.0"
    indexed_at = "2024-01-01T00:00:00Z"
    identifiers = [{"type": "dc", "value": "test-id"}]
    dashboard_uuid = str(uuid.uuid4())
    location = "test-location"

    mock_transport.side_effect = Exception("Elasticsearch connection failed")

    result = es_search_service.index_aip(
        uuid=aip_uuid,
        aip_stored_path=aip_stored_path,
        parser=mock_aip_parser,
        name=aip_name,
        aip_size=aip_size,
        am_version=am_version,
        indexed_at=indexed_at,
        identifiers=identifiers,
        aips_in_aic=5,
        encrypted=False,
        location=location,
        dashboard_uuid=dashboard_uuid,
    )

    mock_aip_parser.files.assert_called_once()
    expected_calls = [
        _make_es_call(
            "PUT",
            "/_bulk",
            params={},
            body=mock.ANY,
        )
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == 1


def test_index_aip_with_optional_parameters(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
    mock_aip_parser: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())
    aip_name = "encrypted-aip"
    aip_stored_path = "/secure/path/to/aip"
    aip_size = 5242880
    am_version = "1.18.0"
    indexed_at = "2024-02-15T10:30:00Z"
    identifiers = [{"type": "handle", "value": "hdl:123/456"}]
    dashboard_uuid = str(uuid.uuid4())
    location = "secure-storage"

    bulk_response = {"took": 150, "errors": False, "items": []}
    cluster_health_response = {"status": "green"}
    aip_index_response = {"_id": "aip2", "result": "created"}

    mock_transport.side_effect = [
        _mock_es_response(bulk_response),
        _mock_es_response(cluster_health_response),
        _mock_es_response(aip_index_response),
    ]

    result = es_search_service.index_aip(
        uuid=aip_uuid,
        aip_stored_path=aip_stored_path,
        parser=mock_aip_parser,
        name=aip_name,
        aip_size=aip_size,
        am_version=am_version,
        indexed_at=indexed_at,
        identifiers=identifiers,
        aips_in_aic=10,
        encrypted=True,
        location=location,
        dashboard_uuid=dashboard_uuid,
    )

    mock_aip_parser.files.assert_called_once()

    expected_calls = [
        _make_es_call(
            "PUT",
            "/_bulk",
            params={},
            body=mock.ANY,
        ),
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call(
            "POST",
            "/aips/_doc",
            params={},
            body={
                "uuid": aip_uuid,
                "name": "encrypted-aip",
                "filePath": "/secure/path/to/aip",
                "size": 5.0,  # 5242880 / 1024 / 1024.
                "file_count": 0,
                "origin": dashboard_uuid,
                "created": 1640995200.0,
                "AICID": "aic-123",
                "isPartOf": "test-collection",
                "countAIPsinAIC": 10,
                "identifiers": [{"type": "handle", "value": "hdl:123/456"}],
                "transferMetadata": [],
                "encrypted": True,
                "accessionids": mock.ANY,
                "status": "UPLOADED",
                "location": "secure-storage",
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == 0


def test_index_aip_waits_for_cluster_health_before_indexing(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
    mock_aip_parser: mock.Mock,
) -> None:
    aip_uuid = str(uuid.uuid4())
    aip_name = "test-aip"
    aip_stored_path = "/path/to/aip"
    aip_size = 2048000
    am_version = "1.17.0"
    indexed_at = "2024-01-01T00:00:00Z"
    identifiers = [{"type": "dc", "value": "test-id"}]
    dashboard_uuid = str(uuid.uuid4())
    location = "test-location"

    bulk_response = {"took": 100, "errors": False, "items": []}
    red_health_response = {"status": "red"}
    yellow_health_response = {"status": "yellow"}
    aip_index_response = {"_id": "aip1", "result": "created"}

    mock_transport.side_effect = [
        _mock_es_response(bulk_response),
        _mock_es_response(red_health_response),
        _mock_es_response(yellow_health_response),
        _mock_es_response(aip_index_response),
    ]

    with mock.patch("archivematica.search.service.time.sleep") as mock_sleep:
        result = es_search_service.index_aip(
            uuid=aip_uuid,
            aip_stored_path=aip_stored_path,
            parser=mock_aip_parser,
            name=aip_name,
            aip_size=aip_size,
            am_version=am_version,
            indexed_at=indexed_at,
            identifiers=identifiers,
            aips_in_aic=5,
            encrypted=False,
            location=location,
            dashboard_uuid=dashboard_uuid,
        )

    mock_aip_parser.files.assert_called_once()
    mock_sleep.assert_called_once_with(10)

    expected_calls = [
        _make_es_call(
            "PUT",
            "/_bulk",
            params={},
            body=mock.ANY,
        ),
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call(
            "POST",
            "/aips/_doc",
            params={},
            body={
                "uuid": aip_uuid,
                "name": "test-aip",
                "filePath": "/path/to/aip",
                "size": 1.953125,
                "file_count": 0,
                "origin": dashboard_uuid,
                "created": 1640995200.0,
                "AICID": "aic-123",
                "isPartOf": "test-collection",
                "countAIPsinAIC": 5,
                "identifiers": [{"type": "dc", "value": "test-id"}],
                "transferMetadata": [],
                "encrypted": False,
                "accessionids": mock.ANY,
                "status": "UPLOADED",
                "location": "test-location",
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == 0


def test_index_transfer_successfully_indexes_transfer_and_files(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
    transfer_directory: str,
    mock_transfer_index_data: mock.Mock,
) -> None:
    transfer_uuid = str(uuid.uuid4())
    transfer_name = "test-transfer"
    size = 1024000
    accession_id = "ACC-123"
    ingest_date = "2024-01-01T00:00:00Z"
    dashboard_uuid = str(uuid.uuid4())

    bulk_response = {"took": 100, "errors": False, "items": []}
    cluster_health_response = {"status": "yellow"}
    transfer_index_response = {"_id": "transfer1", "result": "created"}

    mock_transport.side_effect = [
        _mock_es_response(cluster_health_response),
        _mock_es_response(bulk_response),
        _mock_es_response(cluster_health_response),
        _mock_es_response(transfer_index_response),
    ]

    result = es_search_service.index_transfer(
        uuid=transfer_uuid,
        path=transfer_directory,
        size=size,
        transfer_index_data=mock_transfer_index_data,
        pending_deletion=False,
        dashboard_uuid=dashboard_uuid,
        transfer_name=transfer_name,
        accession_id=accession_id,
        ingest_date=ingest_date,
    )

    expected_calls = [
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call(
            "PUT",
            "/_bulk",
            params={},
            body=mock.ANY,
        ),
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call(
            "POST",
            "/transfers/_doc",
            params={},
            body={
                "name": transfer_name,
                "status": STATUS_BACKLOG,
                "accessionid": accession_id,
                "ingest_date": ingest_date,
                "file_count": 0,  # Actual bulk index return count from mock
                "size": size,
                "uuid": transfer_uuid,
                "pending_deletion": False,
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == 0


def test_index_transfer_handles_exception_and_returns_error(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
    transfer_directory: str,
    mock_transfer_index_data: mock.Mock,
) -> None:
    transfer_uuid = str(uuid.uuid4())
    transfer_name = "test-transfer"
    size = 1024000
    accession_id = "ACC-123"
    ingest_date = "2024-01-01T00:00:00Z"
    dashboard_uuid = str(uuid.uuid4())

    mock_transport.side_effect = Exception("Elasticsearch connection failed")

    with mock.patch("archivematica.search.service.time.sleep") as mock_sleep:
        result = es_search_service.index_transfer(
            uuid=transfer_uuid,
            path=transfer_directory,
            size=size,
            transfer_index_data=mock_transfer_index_data,
            pending_deletion=False,
            dashboard_uuid=dashboard_uuid,
            transfer_name=transfer_name,
            accession_id=accession_id,
            ingest_date=ingest_date,
        )

    # First cluster health check (10 retries), then bulk index, then subsequent health checks fail
    expected_calls = [_make_es_call("GET", "/_cluster/health", params={})] * 10 + [
        _make_es_call(
            "PUT",
            "/_bulk",
            params={},
            body=mock.ANY,
        )
    ]
    mock_sleep.assert_called_with(10)
    assert mock_sleep.call_count == 10
    assert mock_transport.mock_calls == expected_calls
    assert result == 1


def test_index_transfer_with_optional_parameters(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
    transfer_directory: str,
    mock_transfer_index_data: mock.Mock,
) -> None:
    transfer_uuid = str(uuid.uuid4())
    transfer_name = "secure-transfer"
    size = 2048000
    accession_id = "SEC-456"
    ingest_date = "2024-02-15T10:30:00Z"
    dashboard_uuid = str(uuid.uuid4())

    bulk_response = {"took": 150, "errors": False, "items": []}
    cluster_health_response = {"status": "green"}
    transfer_index_response = {"_id": "transfer2", "result": "created"}

    mock_transport.side_effect = [
        _mock_es_response(cluster_health_response),
        _mock_es_response(bulk_response),
        _mock_es_response(cluster_health_response),
        _mock_es_response(transfer_index_response),
    ]

    result = es_search_service.index_transfer(
        uuid=transfer_uuid,
        path=transfer_directory,
        size=size,
        transfer_index_data=mock_transfer_index_data,
        pending_deletion=True,
        dashboard_uuid=dashboard_uuid,
        transfer_name=transfer_name,
        accession_id=accession_id,
        ingest_date=ingest_date,
    )

    expected_calls = [
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call(
            "PUT",
            "/_bulk",
            params={},
            body=mock.ANY,
        ),
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call(
            "POST",
            "/transfers/_doc",
            params={},
            body={
                "name": transfer_name,
                "status": STATUS_BACKLOG,
                "accessionid": accession_id,
                "ingest_date": ingest_date,
                "file_count": 0,  # Actual bulk index return count from mock
                "size": size,
                "uuid": transfer_uuid,
                "pending_deletion": True,
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == 0


def test_index_transfer_waits_for_cluster_health_before_indexing(
    es_search_service: ElasticsearchSearchService,
    mock_transport: mock.Mock,
    transfer_directory: str,
    mock_transfer_index_data: mock.Mock,
) -> None:
    transfer_uuid = str(uuid.uuid4())
    transfer_name = "test-transfer"
    size = 1024000
    accession_id = "ACC-123"
    ingest_date = "2024-01-01T00:00:00Z"
    dashboard_uuid = str(uuid.uuid4())

    bulk_response = {"took": 100, "errors": False, "items": []}
    red_health_response = {"status": "red"}
    yellow_health_response = {"status": "yellow"}
    transfer_index_response = {"_id": "transfer1", "result": "created"}

    mock_transport.side_effect = [
        _mock_es_response(red_health_response),
        _mock_es_response(yellow_health_response),
        _mock_es_response(bulk_response),
        _mock_es_response(red_health_response),
        _mock_es_response(yellow_health_response),
        _mock_es_response(transfer_index_response),
    ]

    with mock.patch("archivematica.search.service.time.sleep") as mock_sleep:
        result = es_search_service.index_transfer(
            uuid=transfer_uuid,
            path=transfer_directory,
            size=size,
            transfer_index_data=mock_transfer_index_data,
            pending_deletion=False,
            dashboard_uuid=dashboard_uuid,
            transfer_name=transfer_name,
            accession_id=accession_id,
            ingest_date=ingest_date,
        )

    mock_sleep.assert_called_with(10)
    assert mock_sleep.call_count == 2

    expected_calls = [
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call(
            "PUT",
            "/_bulk",
            params={},
            body=mock.ANY,
        ),
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call("GET", "/_cluster/health", params={}),
        _make_es_call(
            "POST",
            "/transfers/_doc",
            params={},
            body={
                "name": transfer_name,
                "status": STATUS_BACKLOG,
                "accessionid": accession_id,
                "ingest_date": ingest_date,
                "file_count": 0,  # Actual bulk index return count from mock
                "size": size,
                "uuid": transfer_uuid,
                "pending_deletion": False,
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls
    assert result == 0


def test_setup_search_service_creates_elasticsearch_service_with_default_params(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.return_value = _mock_es_response(True)
    result = setup_search_service("http://localhost:9200")

    assert isinstance(result, ElasticsearchSearchService)
    nodes = list(result.client.transport.node_pool.all())
    assert nodes[0].host == "localhost"
    assert nodes[0].port == 9200


def test_setup_search_service_creates_elasticsearch_service_with_custom_params(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.return_value = _mock_es_response(True)
    hosts = ["http://localhost:9200", "http://localhost:9201"]
    timeout = 60
    enabled = (AIPS_INDEX,)

    result = setup_search_service(hosts, timeout, enabled)

    assert isinstance(result, ElasticsearchSearchService)
    nodes = sorted(result.client.transport.node_pool.all(), key=lambda h: h.port)
    assert len(nodes) == 2
    assert nodes[0].host == "localhost"
    assert nodes[0].port == 9200
    assert nodes[1].host == "localhost"
    assert nodes[1].port == 9201


def test_setup_search_service_creates_aips_and_transfers_indexes_by_default(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.side_effect = [
        _mock_es_response(False, status=404),  # Exists check returns False.
        _mock_es_response({"acknowledged": True}),  # AIPs create.
        _mock_es_response({"acknowledged": True}),  # AIP files create.
        _mock_es_response({"acknowledged": True}),  # Transfers create.
        _mock_es_response({"acknowledged": True}),  # Transfer files create.
    ]

    setup_search_service("http://localhost:9200")

    expected_calls = [
        _make_es_call(
            "HEAD",
            f"/{AIPS_INDEX},{AIP_FILES_INDEX},{TRANSFERS_INDEX},{TRANSFER_FILES_INDEX}",
            params={},
        ),
        _make_es_call(
            "PUT",
            f"/{AIPS_INDEX}",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
        _make_es_call(
            "PUT",
            f"/{AIP_FILES_INDEX}",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
        _make_es_call(
            "PUT",
            f"/{TRANSFERS_INDEX}",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
        _make_es_call(
            "PUT",
            f"/{TRANSFER_FILES_INDEX}",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_setup_search_service_creates_only_aips_indexes_when_enabled(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.side_effect = [
        _mock_es_response(False, status=404),  # Exists check returns False.
        _mock_es_response({"acknowledged": True}),  # AIPs create.
        _mock_es_response({"acknowledged": True}),  # AIP files create.
    ]
    enabled = (AIPS_INDEX,)

    setup_search_service("http://localhost:9200", enabled=enabled)

    expected_calls = [
        _make_es_call(
            "HEAD",
            f"/{AIPS_INDEX},{AIP_FILES_INDEX}",
            params={},
        ),
        _make_es_call(
            "PUT",
            f"/{AIPS_INDEX}",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
        _make_es_call(
            "PUT",
            f"/{AIP_FILES_INDEX}",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_setup_search_service_creates_only_transfers_indexes_when_enabled(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.side_effect = [
        _mock_es_response(False, status=404),  # Exists check returns False.
        _mock_es_response({"acknowledged": True}),  # Transfers create.
        _mock_es_response({"acknowledged": True}),  # Transfer files create.
    ]
    enabled = (TRANSFERS_INDEX,)

    setup_search_service("http://localhost:9200", enabled=enabled)

    expected_calls = [
        _make_es_call(
            "HEAD",
            f"/{TRANSFERS_INDEX},{TRANSFER_FILES_INDEX}",
            params={},
        ),
        _make_es_call(
            "PUT",
            f"/{TRANSFERS_INDEX}",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
        _make_es_call(
            "PUT",
            f"/{TRANSFER_FILES_INDEX}",
            params={"ignore": 400},
            body={
                "settings": mock.ANY,
                "mappings": mock.ANY,
            },
        ),
    ]
    assert mock_transport.mock_calls == expected_calls


def test_setup_search_service_logs_warning_when_no_indexes_enabled(
    mock_transport: mock.Mock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    enabled = ()

    setup_search_service("http://localhost:9200", enabled=enabled)

    # Should not make any transport calls for index operations.
    assert mock_transport.call_count == 0
    assert "Setting up the search service without enabled indexes." in caplog.text


def test_setup_search_service_sets_global_instance(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.return_value = _mock_es_response(True)
    result = setup_search_service("http://localhost:9200")

    assert get_search_service_instance() is result


def test_setup_search_service_accepts_string_hosts(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.return_value = _mock_es_response(True)
    result = setup_search_service("http://localhost:9200")

    assert isinstance(result, ElasticsearchSearchService)
    nodes = list(result.client.transport.node_pool.all())
    assert nodes[0].host == "localhost"


def test_setup_search_service_accepts_list_hosts(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.return_value = _mock_es_response(True)
    hosts = ["http://localhost:9200", "http://localhost:9201"]

    result = setup_search_service(hosts)

    assert isinstance(result, ElasticsearchSearchService)
    nodes = list(result.client.transport.node_pool.all())
    assert len(nodes) == 2


def test_setup_search_service_accepts_tuple_hosts(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.return_value = _mock_es_response(True)
    hosts = ("http://localhost:9200", "http://localhost:9201")

    result = setup_search_service(hosts)

    assert isinstance(result, ElasticsearchSearchService)
    nodes = list(result.client.transport.node_pool.all())
    assert len(nodes) == 2


def test_setup_search_service_from_conf_calls_setup_with_settings_values() -> None:
    with mock.patch("archivematica.search.service.setup_search_service") as mock_setup:
        mock_service = mock.Mock()
        mock_setup.return_value = mock_service

        mock_settings = mock.Mock()
        mock_settings.ELASTICSEARCH_SERVER = "http://localhost:9200"
        mock_settings.ELASTICSEARCH_TIMEOUT = 30
        mock_settings.SEARCH_ENABLED = (AIPS_INDEX, TRANSFERS_INDEX)

        result = setup_search_service_from_conf(mock_settings)

        mock_setup.assert_called_once_with(
            "http://localhost:9200", 30, (AIPS_INDEX, TRANSFERS_INDEX)
        )
        assert result is mock_service


def test_setup_search_service_from_conf_with_different_settings() -> None:
    with mock.patch("archivematica.search.service.setup_search_service") as mock_setup:
        mock_service = mock.Mock()
        mock_setup.return_value = mock_service

        mock_settings = mock.Mock()
        mock_settings.ELASTICSEARCH_SERVER = ["es1:9200", "es2:9200"]
        mock_settings.ELASTICSEARCH_TIMEOUT = 60
        mock_settings.SEARCH_ENABLED = (AIPS_INDEX,)

        result = setup_search_service_from_conf(mock_settings)

        mock_setup.assert_called_once_with(["es1:9200", "es2:9200"], 60, (AIPS_INDEX,))
        assert result is mock_service


def test_get_search_service_instance_returns_none_when_not_initialized(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.return_value = _mock_es_response(True)
    result = get_search_service_instance()

    assert result is None


def test_get_search_service_instance_returns_service_after_setup(
    mock_transport: mock.Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("archivematica.search.service._search_service_instance", None)
    mock_transport.return_value = _mock_es_response(True)
    assert get_search_service_instance() is None

    es_search_service = setup_search_service("http://localhost:9200")
    assert get_search_service_instance() is es_search_service
    assert isinstance(get_search_service_instance(), ElasticsearchSearchService)
