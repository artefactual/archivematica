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

from __future__ import unicode_literals

import multiprocessing
import logging
import os
import sys
import time

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

from django.conf import settings as django_settings
from django.core.management.base import CommandError

from fileOperations import addFileToTransfer
import elasticSearchFunctions
import metsrw
import storageService

from fpr.models import FormatVersion
from main.management.commands import boolean_input, DashboardCommand
from main.models import Transfer, FileFormatVersion, FileID

import bagit

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
        transfer_backlog_dir = Path(transfer_backlog_dir)
        for transfer_dir in transfer_backlog_dir.glob("*"):
            if transfer_dir.name == ".gitignore" or transfer_dir.is_file():
                continue
            try:
                bag = bagit.Bag(str(transfer_dir))
                bag.validate(
                    processes=multiprocessing.cpu_count(), completeness_only=True
                )
            except bagit.BagError:
                self.stdout.write(
                    "Skipping transfer {} - not a valid bag!".format(transfer_dir)
                )
            transfer_uuid = transfer_dir.name[-36:]
            if "External-Identifier" in bag.info:
                _import_self_describing_transfer(
                    es_client, self.stdout, transfer_dir, transfer_uuid
                )
            else:
                _import_pipeline_dependant_transfer(
                    es_client, self.stdout, transfer_dir, transfer_uuid
                )


def _import_file_from_fsentry(fsentry, transfer_uuid):
    ingestion_date = None
    for evt in fsentry.get_premis_events():
        if evt.event_type == "ingestion":
            ingestion_date = evt.event_date_time
            break

    file_obj = addFileToTransfer(
        filePathRelativeToSIP="%transferDirectory%{}".format(fsentry.path),
        fileUUID=fsentry.file_uuid,
        transferUUID=transfer_uuid,
        taskUUID=None,  # Unused?
        date=ingestion_date,
        sourceType="ingestion",
        use="original",
    )

    try:
        premis_object = fsentry.get_premis_objects()[0]
    except IndexError:
        return

    # Populate extra attributes in the File object.
    file_obj.checksum = premis_object.message_digest
    file_obj.checksumtype = premis_object.message_digest_algorithm
    file_obj.size = premis_object.size
    file_obj.save()

    # Populate format details of the File object.
    if premis_object.format_registry_name != "PRONOM":
        return
    try:
        format_version = FormatVersion.active.get(pronom_id=premis_object.format_registry_key)
    except FormatVersion.DoesNotExist:
        return
    FileFormatVersion.objects.create(file_uuid=file_obj, format_version=format_version)
    FileID.objects.create(
        file=file_obj,
        format_name=format_version.format.description,
        format_version=format_version.version or "",
        format_registry_name=premis_object.format_registry_name,
        format_registry_key=premis_object.format_registry_key,
    )


def _import_dir_from_fsentry(fsentry, transfer_uuid):
    pass


def _import_self_describing_transfer(es_client, stdout, transfer_dir, transfer_uuid):
    """Import a self-describing transfer.

    Knowledge of this transfer is not required in the transfer. If missing,
    this function will populate the necessary state so arrangement and ingest
    work as expected.

    TODO:
    - What is the active agent of a new transfer?
    - How can I determine the type of the transfer? Does it matter?
    - Transfer attributes like accessionId
    """
    transfer, created = Transfer.objects.get_or_create(
        uuid=transfer_uuid,
        defaults=dict(
            type="Standard",
            diruuids=False,
            currentlocation="%sharedPath%www/AIPsStore/originals/" + str(transfer_dir.name) + "/",
        ),
    )

    # The transfer did not exist, we need to populate everything else.
    if created:
        mets = metsrw.METSDocument.fromfile(
            str(transfer_dir / "data/metadata/submissionDocumentation/METS.xml")
        )
        for fsentry in mets.all_files():
            if fsentry.type == "Item":
                _import_file_from_fsentry(fsentry, transfer_uuid)
            elif fsentry.type == "Directory":
                _import_dir_from_fsentry(fsentry, transfer_uuid)

    elasticSearchFunctions.index_transfer_and_files(
        es_client, transfer_uuid, str(transfer_dir) + "/"
    )


def _import_pipeline_dependant_transfer(es_client, stdout, transfer_dir, transfer_uuid):
    """Import a pipeline-dependant transfer.

    We can only import pipeline-dependant transfers from backlog if the
    pipeline has records of it, e.g. the Transfer object exists in the
    database.
    """
    try:
        Transfer.objects.get(uuid=transfer_uuid)
    except Transfer.DoesNotExist:
        stdout.write(
            "Skipping transfer {} - not found in the database!".format(transfer_uuid)
        )
        return
    stdout.write("Indexing {} ({})".format(transfer_uuid, transfer_dir))
    elasticSearchFunctions.index_transfer_and_files(
        es_client, transfer_uuid, str(transfer_dir) + "/"
    )
    try:
        storageService.reindex_file(transfer_uuid)
    except Exception as err:
        self.stdout.write(
            "Could not reindex Transfer in the Storage Service, UUID: %s (%s)"
            % (transfer_uuid, err)
        )
