import logging

from elasticsearch import Elasticsearch
from elasticsearch import ImproperlyConfigured

from archivematica.search.constants import AIP_FILES_INDEX
from archivematica.search.constants import AIPS_INDEX
from archivematica.search.constants import DEFAULT_TIMEOUT
from archivematica.search.constants import TRANSFER_FILES_INDEX
from archivematica.search.constants import TRANSFERS_INDEX
from archivematica.search.indices import create_indexes_if_needed

logger = logging.getLogger("archivematica.search")

_es_hosts = None
_es_client = None


def setup(hosts, timeout=DEFAULT_TIMEOUT, enabled=(AIPS_INDEX, TRANSFERS_INDEX)):
    """Initialize and share the Elasticsearch client.

    Share it as the attribute _es_client in the current module. An additional
    attribute _es_hosts is defined containing the Elasticsearch hosts (expected
    types are: string, list or tuple). Also, the existence of the enabled
    indexes is checked to be able to create the required indexes on the fly if
    they don't exist.
    """
    global _es_hosts
    global _es_client

    _es_hosts = hosts
    _es_client = Elasticsearch(
        **{"hosts": _es_hosts, "timeout": timeout, "dead_timeout": 2}
    )

    # TODO: Do we really need to be able to create the indexes
    # on the fly? Could we force to run the rebuild commands and
    # avoid doing this on each setup?
    indexes = []
    if AIPS_INDEX in enabled:
        indexes.extend([AIPS_INDEX, AIP_FILES_INDEX])
    if TRANSFERS_INDEX in enabled:
        indexes.extend([TRANSFERS_INDEX, TRANSFER_FILES_INDEX])
    if len(indexes) > 0:
        create_indexes_if_needed(_es_client, indexes)
    else:
        logger.warning("Setting up the Elasticsearch client without enabled indexes.")


def setup_reading_from_conf(settings):
    setup(
        settings.ELASTICSEARCH_SERVER,
        settings.ELASTICSEARCH_TIMEOUT,
        settings.SEARCH_ENABLED,
    )


def get_client():
    """Obtain the current Elasticsearch client.

    If undefined, an exception will be raised. This function also checks the
    integrity of the indexes expected by this application and populate them
    when they cannot be found.
    """
    if not _es_client:
        raise ImproperlyConfigured(
            "The Elasticsearch client has not been set up yet. Please call setup() first."
        )
    return _es_client
