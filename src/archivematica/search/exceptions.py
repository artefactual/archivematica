class SearchEngineError(Exception):
    """Not operational errors."""

    pass


class EmptySearchResultError(SearchEngineError):
    pass


class TooManyResultsError(SearchEngineError):
    pass
