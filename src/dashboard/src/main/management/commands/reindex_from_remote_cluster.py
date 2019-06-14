# -*- coding: utf-8 -*-
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
from __future__ import absolute_import, print_function

import json
import sys

import elasticsearch
from django.conf import settings

from main.management.commands import DashboardCommand
import elasticSearchFunctions


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
            help="Batch size, reduce it to limit request chunk size. " "Default: 10.",
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
        elasticSearchFunctions.setup(
            settings.ELASTICSEARCH_SERVER, options["timeout"], []
        )
        es_client = elasticSearchFunctions.get_client()

        # Get enabled indexes based on setting
        indexes = []
        if "aips" in settings.SEARCH_ENABLED:
            indexes.extend(["aips", "aipfiles"])
        if "transfers" in settings.SEARCH_ENABLED:
            indexes.extend(["transfers", "transferfiles"])

        # Delete all indexes and create enabled ones in new cluster
        self.info("Creating new indexes.")
        try:
            es_client.indices.delete(
                ",".join(elasticSearchFunctions.INDEXES), ignore=404
            )
            elasticSearchFunctions.create_indexes_if_needed(es_client, indexes)
        except Exception as e:
            self.error(
                "The Elasticsearch indexes could not be recreated in {}. "
                "Error: {}".format(settings.ELASTICSEARCH_SERVER, e)
            )
            sys.exit(1)

        # Default body for reindex requests
        body = {
            "source": {
                "remote": {
                    "host": options["host"],
                    "socket_timeout": "{}s".format(options["timeout"]),
                    "connect_timeout": "{}s".format(options["timeout"]),
                },
                "index": "",
                "type": "",
                "size": options["size"],
            },
            "dest": {"index": "", "type": elasticSearchFunctions.DOC_TYPE},
        }

        # Add basic auth
        if options["username"] != "":
            body["source"]["remote"]["username"] = options["username"]
            if options["password"] != "":
                body["source"]["remote"]["password"] = options["password"]

        # Indexes and types to reindex
        indexes_relations = [
            {"dest_index": "aips", "source_index": "aips", "source_type": "aip"},
            {
                "dest_index": "aipfiles",
                "source_index": "aips",
                "source_type": "aipfile",
            },
            {
                "dest_index": "transfers",
                "source_index": "transfers",
                "source_type": "transfer",
            },
            {
                "dest_index": "transferfiles",
                "source_index": "transfers",
                "source_type": "transferfile",
            },
        ]

        # Reindex documents from remote cluster
        fails = 0
        for indexes_relation in indexes_relations:
            # Skip not enabled indexes
            if indexes_relation["dest_index"] not in indexes:
                continue
            # Update request body
            body["dest"]["index"] = indexes_relation["dest_index"]
            body["source"]["index"] = indexes_relation["source_index"]
            body["source"]["type"] = indexes_relation["source_type"]
            # Reindex request
            self.info("Reindexing %s:" % indexes_relation["dest_index"])
            try:
                response = es_client.reindex(body=body)
            except elasticsearch.TransportError as exc:
                fails += 1
                self.error("Error: {}. Details:\n{}".format(exc, exc.info))
            except Exception as exc:
                fails += 1
                self.error("Error: {}".format(exc))
            else:
                self.info("Response:\n%s" % json.dumps(response, indent=4))

        if fails > 0:
            self.error("%s reindex request(s) failed!" % fails)
        else:
            self.success("All reindex requests ended successfully!")
