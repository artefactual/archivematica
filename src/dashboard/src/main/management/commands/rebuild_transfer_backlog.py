"""Recreate the ``transfers`` Elasticsearch index from the Transfer Backlog.

This is useful if the Elasticsearch index has been deleted or damaged
or during software upgrades where the document schema has changed.

It also requests the Storage Service to reindex the transfers.

This must be run on the same system that Archivematica is installed on, since
it uses code from the Archivematica codebase.

The one required parameter is the path to the directory where Transfer Backlog
location is stored.

Copied from https://git.io/vN6v6.
"""

import logging
import os
import sys
import time

from django.conf import settings as django_settings
from django.core.management.base import CommandError

import elasticSearchFunctions
import storageService
from main.management.commands import boolean_input, DashboardCommand
from main.models import Transfer


logger = logging.getLogger("archivematica.dashboard")


class Command(DashboardCommand):
    """Recreate the ``transfers`` Elasticsearch index from the Transfer Backlog."""

    help = __doc__

    DEFAULT_TRANSFER_BACKLOG_DIR = (
        "/var/archivematica/sharedDirectory/www/AIPsStore/transferBacklog"
    )

    CHECKSUM_TYPE = "sha256"
    CHECKSUM_UTIL = "sha256sum"

    def add_arguments(self, parser):
        """Entry point to add custom arguments."""
        parser.add_argument(
            "--transfer-backlog-dir", default=self.DEFAULT_TRANSFER_BACKLOG_DIR
        )
        parser.add_argument("--no-prompt", action="store_true")

    def handle(self, *args, **options):
        """Entry point of the rebuild_transfer_backlog command."""
        # Check that the `transfers` part of the search is enabled
        if "transfers" not in django_settings.SEARCH_ENABLED:
            print(
                "The Transfers indexes are not enabled. Please, make sure to "
                "set the *_SEARCH_ENABLED environment variables to `true` "
                "to enable the Transfers and AIPs indexes, or to `transfers` "
                "to only enable the Transfers indexes."
            )
            sys.exit(1)

        if not self.confirm(options["no_prompt"]):
            sys.exit(0)

        transfer_backlog_dir = self.prepdir(options["transfer_backlog_dir"])
        if not os.path.exists(transfer_backlog_dir):
            raise CommandError("Directory does not exist: %s", transfer_backlog_dir)
        self.success(
            'Rebuilding "transfers" index from {}.'.format(transfer_backlog_dir)
        )

        # Connect to Elasticsearch.
        elasticSearchFunctions.setup_reading_from_conf(django_settings)
        es_client = elasticSearchFunctions.get_client()
        try:
            es_info = es_client.info()
        except Exception as err:
            raise CommandError("Unable to connect to Elasticsearch: %s" % err)
        else:
            self.success(
                "Connected to Elasticsearch node {} (v{}).".format(
                    es_info["name"], es_info["version"]["number"]
                )
            )

        indexes = ["transfers", "transferfiles"]
        self.delete_indexes(es_client, indexes)
        self.create_indexes(es_client, indexes)
        self.populate_indexes(es_client, transfer_backlog_dir)
        self.success("Indexing complete!")

    def confirm(self, no_prompt):
        """Ask user to confirm the operation."""
        if no_prompt:
            return True
        self.warning(
            "WARNING: This script will delete your current"
            " Elasticsearch transfer data, rebuilding it using"
            " files."
        )
        return boolean_input("Are you sure you want to continue?")

    def prepdir(self, path):
        """Append ''originals'' to the path if it's missing."""
        tail = os.path.basename(os.path.normpath(path))
        suffix = "originals"
        if tail != suffix:
            return os.path.join(path, suffix)

    def delete_indexes(self, es_client, indexes):
        """Delete search indexes."""
        self.stdout.write(
            "Deleting all transfers and transfer files "
            'in the "transfers" and "transferfiles" indexes ...'
        )
        time.sleep(3)  # Time for the user to panic and kill the process.
        es_client.indices.delete(",".join(indexes), ignore=404)

    def create_indexes(self, es_client, indexes):
        """Create search indexes."""
        self.stdout.write("Creating indexes ...")
        elasticSearchFunctions.create_indexes_if_needed(es_client, indexes)

    def populate_indexes(self, es_client, transfer_backlog_dir):
        """Populate search indexes."""
        for directory in os.listdir(transfer_backlog_dir):
            if directory == ".gitignore":
                continue

            transfer_uuid = directory[-36:]
            transfer_dir = os.path.basename(directory)

            try:
                Transfer.objects.get(uuid=transfer_uuid)
            except Transfer.DoesNotExist:
                self.warning("Skipping transfer {}: not found!".format(transfer_uuid))
                continue

            self.stdout.write("Indexing {} ({})".format(transfer_uuid, transfer_dir))

            elasticSearchFunctions.index_transfer_and_files(
                es_client,
                transfer_uuid,
                os.path.join(transfer_backlog_dir, directory, ""),
                status="backlog",
            )

            try:
                storageService.reindex_file(transfer_uuid)
            except Exception:
                self.warning(
                    "Could not reindex Transfer in the Storage Service, "
                    "UUID: %s" % transfer_uuid
                )
