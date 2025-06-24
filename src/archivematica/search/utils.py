import time

from archivematica.search.constants import DOC_TYPE


def _wait_for_cluster_yellow_status(client, wait_between_tries=10, max_tries=10):
    health = {}
    health["status"] = None
    tries = 0

    # Wait for either yellow or green status
    while (
        health["status"] != "yellow"
        and health["status"] != "green"
        and tries < max_tries
    ):
        tries = tries + 1

        try:
            health = client.cluster.health()
        except Exception:
            print("ERROR: failed health check.")
            health["status"] = None

        # Sleep if cluster not healthy
        if health["status"] != "yellow" and health["status"] != "green":
            print("Cluster not in yellow or green state... waiting to retry.")
            time.sleep(wait_between_tries)


def _try_to_index(
    client, data, index, wait_between_tries=10, max_tries=10, printfn=print
):
    exception = None
    if max_tries < 1:
        raise ValueError("max_tries must be 1 or greater")
    for _ in range(0, max_tries):
        try:
            client.index(body=data, index=index, doc_type=DOC_TYPE)
            return
        except Exception as e:
            exception = e
            printfn("ERROR: error trying to index.")
            printfn(e)
            time.sleep(wait_between_tries)

    # If indexing did not succeed after max_tries is already complete,
    # reraise the Elasticsearch exception to aid in debugging.
    if exception:
        raise exception


def augment_raw_search_results(raw_results):
    """Normalize search results response.

    This function takes JSON returned by an ES query and returns the source
    document for each result.

    :param raw_results: the raw JSON result from an elastic search query
    :return: JSON result simplified, with document_id set
    """
    modifiedResults = []

    for item in raw_results["hits"]["hits"]:
        clone = item["_source"].copy()
        clone["document_id"] = item["_id"]
        modifiedResults.append(clone)

    return modifiedResults
