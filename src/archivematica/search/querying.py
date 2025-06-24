import logging

from archivematica.search.constants import AIP_FILES_INDEX
from archivematica.search.constants import AIPS_INDEX
from archivematica.search.constants import ES_FIELD_UUID
from archivematica.search.constants import MAX_QUERY_SIZE
from archivematica.search.constants import TRANSFER_FILES_INDEX
from archivematica.search.exceptions import EmptySearchResultError
from archivematica.search.exceptions import SearchEngineError
from archivematica.search.exceptions import TooManyResultsError

logger = logging.getLogger("archivematica.search")


def search_all_results(client, body, index):
    """Performs client.search with the size set to MAX_QUERY_SIZE.

    By default search_raw returns only 10 results. Since we usually want all
    results, this is a wrapper that fetches MAX_QUERY_SIZE results and logs a
    warning if more results were available.
    """
    if isinstance(index, list):
        index = ",".join(index)

    results = client.search(body=body, index=index, size=MAX_QUERY_SIZE)

    if results["hits"]["total"] > MAX_QUERY_SIZE:
        logger.warning(
            "Number of items in backlog (%s) exceeds maximum amount fetched (%s)",
            results["hits"]["total"],
            MAX_QUERY_SIZE,
        )
    return results


def get_aip_data(client, uuid, fields=None):
    search_params = {
        "body": {"query": {"term": {ES_FIELD_UUID: uuid}}},
        "index": AIPS_INDEX,
    }

    if fields:
        search_params["_source"] = fields

    aips = client.search(**search_params)

    return aips["hits"]["hits"][0]


def get_aipfile_data(client, uuid, fields=None):
    search_params = {
        "body": {"query": {"term": {"FILEUUID": uuid}}},
        "index": AIP_FILES_INDEX,
    }

    if fields:
        search_params["_source"] = fields

    aipfiles = client.search(**search_params)

    return aipfiles["hits"]["hits"][0]


def get_file_tags(client, uuid):
    """Gets the tags of a given file by its UUID.

    Retrieve the complete set of tags for the file with the fileuuid `uuid`.
    Returns a list of zero or more strings.

    :param Elasticsearch client: Elasticsearch client
    :param str uuid: A file UUID.
    """
    query = {"query": {"term": {"fileuuid": uuid}}}

    results = client.search(body=query, index=TRANSFER_FILES_INDEX, _source="tags")

    count = results["hits"]["total"]
    if count == 0:
        raise EmptySearchResultError(f"No matches found for file with UUID {uuid}")
    if count > 1:
        raise TooManyResultsError(
            f"{count} matches found for file with UUID {uuid}; unable to fetch a single result"
        )

    result = results["hits"]["hits"][0]
    # File has no tags
    if "_source" not in result:
        return []
    return result["_source"]["tags"]


def get_transfer_file_info(client, field, value):
    """
    Get transferfile information from ElasticSearch with query field = value.
    """
    logger.debug("get_transfer_file_info: field: %s, value: %s", field, value)
    results = {}
    query = {"query": {"term": {field: value}}}
    documents = search_all_results(client, body=query, index=TRANSFER_FILES_INDEX)
    result_count = len(documents["hits"]["hits"])
    if result_count == 1:
        results = documents["hits"]["hits"][0]["_source"]
    elif result_count > 1:
        # Elasticsearch was sometimes ranking results for a different filename above
        # the actual file being queried for; in that case only consider results
        # where the value is an actual precise match.
        filtered_results = [
            results
            for results in documents["hits"]["hits"]
            if results["_source"][field] == value
        ]

        result_count = len(filtered_results)
        if result_count == 1:
            results = filtered_results[0]["_source"]
        if result_count > 1:
            results = filtered_results[0]["_source"]
            logger.warning(
                "get_transfer_file_info returned %s results for query %s: %s (using first result)",
                result_count,
                field,
                value,
            )
        elif result_count < 1:
            logger.error(
                "get_transfer_file_info returned no exact results for query %s: %s",
                field,
                value,
            )
            raise SearchEngineError("get_transfer_file_info returned no exact results")

    logger.debug("get_transfer_file_info: results: %s", results)
    return results


def _document_ids_from_field_query(client, index, field, value):
    document_ids = []

    # Escape /'s with \\
    searchvalue = str(value).replace("/", "\\/")
    query = {"query": {"term": {field: searchvalue}}}
    documents = search_all_results(client, body=query, index=index)

    if len(documents["hits"]["hits"]) > 0:
        document_ids = [d["_id"] for d in documents["hits"]["hits"]]

    return document_ids
