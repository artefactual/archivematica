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

import archivematica.search.constants
from archivematica.dashboard.main.management.commands import DashboardCommand
from archivematica.search.service import SearchServiceError
from archivematica.search.service import setup_search_service_from_conf


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
            search_service = setup_search_service_from_conf(settings)
        except SearchServiceError:
            self.error("Error: the search service may not be running.")
            sys.exit(1)

        # Update the AIPs index mappings.
        aips_mappings = {
            "properties": {
                archivematica.search.constants.ES_FIELD_ACCESSION_IDS: {
                    "type": "keyword"
                },
                archivematica.search.constants.ES_FIELD_STATUS: {"type": "keyword"},
                archivematica.search.constants.ES_FIELD_FILECOUNT: {"type": "integer"},
                archivematica.search.constants.ES_FIELD_LOCATION: {"type": "keyword"},
            }
        }
        search_service.update_index_mappings(
            archivematica.search.constants.AIPS_INDEX, aips_mappings
        )

        # Update the AIP files index mapping.
        aip_files_mappings = {
            "properties": {
                "accessionid": {"type": "keyword"},
                archivematica.search.constants.ES_FIELD_STATUS: {"type": "keyword"},
                "filePath": {
                    "type": "text",
                    "analyzer": "file_path_and_name",
                    "fields": {"raw": {"type": "keyword"}},
                },
            }
        }
        search_service.update_index_mappings(
            archivematica.search.constants.AIP_FILES_INDEX, aip_files_mappings
        )

        # Perform an update by query on the aipfiles index to populate
        # the filePath.raw subfield from existing text values. We do
        # not specify a query to ensure that all documents are updated.
        search_service.update_all_documents(
            archivematica.search.constants.AIP_FILES_INDEX
        )
