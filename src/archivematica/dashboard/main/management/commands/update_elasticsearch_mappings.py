"""Update Elasticsearch mappings for Archivematica 1.12

This command updates the Elasticsearch mappings for the aips and
aipfiles indices for Archivematica 1.12 to enable sorting on all fields
displayed in the new Archival Storage DataTable and populates the new
filePath.raw subfield in the aipfiles index using an Update By Query.

Execution example:

./manage.py update_elasticsearch_mappings
"""

import sys

from django.conf import settings
from elasticsearch import ElasticsearchException

import archivematica.search.client
import archivematica.search.constants
from archivematica.dashboard.main.management.commands import DashboardCommand


class Command(DashboardCommand):
    help = __doc__

    def handle(self, *args, **options):
        # Check that the AIPs index is enabled before proceeding.
        if archivematica.search.constants.AIPS_INDEX not in settings.SEARCH_ENABLED:
            self.error(
                "The AIPs indexes are not enabled. Please, make sure to "
                "set the *_SEARCH_ENABLED environment variables to `true` "
                "to enable the AIPs and Transfers indexes, or to `aips` "
                "to only enable the AIPs indexes."
            )
            sys.exit(1)

        try:
            archivematica.search.client.setup_reading_from_conf(settings)
            es_client = archivematica.search.client.get_client()
        except ElasticsearchException:
            self.error("Error: Elasticsearch may not be running.")
            sys.exit(1)

        # Update the AIPs index mappings.
        es_client.indices.put_mapping(
            index=archivematica.search.constants.AIPS_INDEX,
            doc_type=archivematica.search.constants.DOC_TYPE,
            body={
                "properties": {
                    archivematica.search.constants.ES_FIELD_ACCESSION_IDS: {
                        "type": "keyword"
                    },
                    archivematica.search.constants.ES_FIELD_STATUS: {"type": "keyword"},
                    archivematica.search.constants.ES_FIELD_FILECOUNT: {
                        "type": "integer"
                    },
                    archivematica.search.constants.ES_FIELD_LOCATION: {
                        "type": "keyword"
                    },
                }
            },
        )

        # Update the AIP files index mapping.
        es_client.indices.put_mapping(
            index=archivematica.search.constants.AIP_FILES_INDEX,
            doc_type=archivematica.search.constants.DOC_TYPE,
            body={
                "properties": {
                    "accessionid": {"type": "keyword"},
                    archivematica.search.constants.ES_FIELD_STATUS: {"type": "keyword"},
                    "filePath": {
                        "type": "text",
                        "analyzer": "file_path_and_name",
                        "fields": {"raw": {"type": "keyword"}},
                    },
                }
            },
        )

        # Perform an update by query on the aipfiles index to populate
        # the filePath.raw subfield from existing text values. We do
        # not specify a query to ensure that all documents are updated.
        es_client.update_by_query(archivematica.search.constants.AIP_FILES_INDEX)
