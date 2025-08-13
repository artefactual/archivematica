"""Reindex Elasticsearch data from remote cluster.

Creates the Elasticsearch 6.x indexes based on the configuration and reindexes
the data from earlier AM versions from a remote cluster using the 1.x version.
This task deletes the "aips", "aipfiles", "transfers" and "transferfiles"
indexes by default before recreating them with the new mappings and settings.

Execution example:

./manage.py reindex_from_remote_cluster \
    https://192.168.168.196:9200 \
    -u test -p 1234
"""

import json
import sys

from django.conf import settings

import archivematica.search.constants
from archivematica.dashboard.main.management.commands import DashboardCommand
from archivematica.search.service import setup_search_service


class Command(DashboardCommand):
    help = __doc__

    def add_arguments(self, parser):
        """Entry point to add custom arguments."""
        parser.add_argument(
            "host",
            help="URL from the Elasticsearch cluster to be reindexed. "
            "It must contain a scheme, host, port and optional path "
            "(e.g. https://otherhost:9200/proxy).",
        )
        parser.add_argument(
            "-u", "--username", default="", help="Optional username for basic auth."
        )
        parser.add_argument(
            "-p", "--password", default="", help="Optional password for basic auth."
        )
        parser.add_argument(
            "-s",
            "--size",
            type=int,
            default=10,
            help="Batch size, reduce it to limit request chunk size. Default: 10.",
        )
        parser.add_argument(
            "-t",
            "--timeout",
            type=int,
            default=30,
            help="Timeout for both connections, in seconds. Default: 30.",
        )

    def handle(self, *args, **options):
        # Check search enabled configuration
        if len(settings.SEARCH_ENABLED) == 0:
            self.error(
                "The Elasticsearch indexes are not enabled. Please, make sure "
                "to set the *_SEARCH_ENABLED environment variables to `true` "
                "to enable the AIPs and Transfers indexes, to `aips` "
                "to only enable the AIPs indexes or to `transfers` "
                "to only enable the Transfers indexes."
            )
            sys.exit(1)

        # Setup new cluster connection. Do not pass SEARCH_ENABLED
        # setting to avoid the creation of the indexes on setup,
        # and use the timeout passed to the command.
        search_service = setup_search_service(
            settings.ELASTICSEARCH_SERVER, options["timeout"], ()
        )

        # Get enabled indexes based on setting
        indexes = []
        if "aips" in settings.SEARCH_ENABLED:
            indexes.extend(["aips", "aipfiles"])
        if "transfers" in settings.SEARCH_ENABLED:
            indexes.extend(["transfers", "transferfiles"])

        # Delete all indexes and create enabled ones in new cluster
        self.info("Creating new indexes.")
        try:
            search_service.delete_indexes(archivematica.search.constants.INDEXES)
            search_service.ensure_indexes_exist(indexes)
        except Exception as e:
            self.error(
                f"The Elasticsearch indexes could not be recreated in {settings.ELASTICSEARCH_SERVER}. "
                f"Error: {e}"
            )
            sys.exit(1)

        # Remote configuration for reindex requests
        remote_config = {
            "host": options["host"],
            "socket_timeout": "{}s".format(options["timeout"]),
            "connect_timeout": "{}s".format(options["timeout"]),
            "size": options["size"],
        }

        # Add basic auth
        if options["username"] != "":
            remote_config["username"] = options["username"]
            if options["password"] != "":
                remote_config["password"] = options["password"]

        # Indexes and types to reindex
        index_mappings = [
            {"dest_index": "aips", "source_index": "aips"},
            {
                "dest_index": "aipfiles",
                "source_index": "aipfiles",
            },
            {
                "dest_index": "transfers",
                "source_index": "transfers",
            },
            {
                "dest_index": "transferfiles",
                "source_index": "transferfiles",
            },
        ]

        # Filter index mappings to only include enabled indexes
        enabled_mappings = [
            mapping for mapping in index_mappings if mapping["dest_index"] in indexes
        ]

        # Reindex documents from remote cluster
        results = search_service.reindex_from_remote(remote_config, enabled_mappings)

        # Report results
        for success in results["successful"]:
            self.info(f"Reindexing {success['index']}:")
            self.info("Response:\n%s" % json.dumps(success["response"], indent=4))

        for failure in results["failed"]:
            self.error(f"Error reindexing {failure['index']}: {failure['error']}")

        if results["failed"]:
            self.error(f"{len(results['failed'])} reindex request(s) failed!")
        else:
            self.success("All reindex requests ended successfully!")
