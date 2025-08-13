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
