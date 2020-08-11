# -*- coding: utf-8 -*-
"""Update Elasticsearch mappings for Archivematica 1.12

This command updates the Elasticsearch mappings for the aips and
aipfiles indices for Archivematica 1.12 to enable sorting on all fields
displayed in the new Archival Storage DataTable and populates the new
filePath.raw subfield in the aipfiles index using an Update By Query.

Execution example:

./manage.py update_elasticsearch_mappings
"""
from __future__ import absolute_import, print_function

import sys

from django.conf import settings
from elasticsearch import ElasticsearchException

from main.management.commands import DashboardCommand
import elasticSearchFunctions as es


class Command(DashboardCommand):

    help = __doc__

    def handle(self, *args, **options):
        # Check that the AIPs index is enabled before proceeding.
        if es.AIPS_INDEX not in settings.SEARCH_ENABLED:
            self.error(
                "The AIPs indexes are not enabled. Please, make sure to "
                "set the *_SEARCH_ENABLED environment variables to `true` "
                "to enable the AIPs and Transfers indexes, or to `aips` "
                "to only enable the AIPs indexes."
            )
            sys.exit(1)

        try:
            es.setup_reading_from_conf(settings)
            es_client = es.get_client()
        except ElasticsearchException:
            self.error("Error: Elasticsearch may not be running.")
            sys.exit(1)

        # Update the AIPs index mappings.
        es_client.indices.put_mapping(
            index=es.AIPS_INDEX,
            doc_type=es.DOC_TYPE,
            body={
                "properties": {
                    es.ES_FIELD_ACCESSION_IDS: {"type": "keyword"},
                    es.ES_FIELD_STATUS: {"type": "keyword"},
                    es.ES_FIELD_FILECOUNT: {"type": "integer"},
                    es.ES_FIELD_LOCATION: {"type": "keyword"},
                }
            },
        )

        # Update the AIP files index mapping.
        es_client.indices.put_mapping(
            index=es.AIP_FILES_INDEX,
            doc_type=es.DOC_TYPE,
            body={
                "properties": {
                    "accessionid": {"type": "keyword"},
                    es.ES_FIELD_STATUS: {"type": "keyword"},
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
        es_client.update_by_query(es.AIP_FILES_INDEX)
