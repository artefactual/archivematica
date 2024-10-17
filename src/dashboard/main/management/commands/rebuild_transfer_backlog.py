"""Recreate the ``transfers`` Elasticsearch index from the Transfer Backlog.

This is useful if the Elasticsearch index has been deleted or damaged
or during software upgrades where the document schema has changed.

It also requests the Storage Service to reindex the transfers.

This must be run on the same system that Archivematica is installed on, since
it uses code from the Archivematica codebase.

Based on https://git.io/vN6v6.

Optional parameters:

``--transfer-backlog-dir [storage_location_path]`` : path where the Transfer
Backlog storage location is located in the local filesystem.
Default: /var/archivematica/sharedDirectory/www/AIPsStore/transferBacklog.

``--no-prompt`` : do not ask for confirmation.

``--from-storage-service`` : uses the Storage Service API to determine
which stored transfers need to be re-indexed. Temporarily downloads a
copy of each transfer via the API for indexing. This enables reindexing
of packages stored in encrypted locations as well as some remote locations.

``--delete-all`` : will delete the entire AIP Elasticsearch index and create
an empty index before starting to reindex

``-u`` or ``--uuid`` : only reindex the transfer that has the matching UUID.

``--skip-to``: starts reindexing from the specified uuid. Useful if a previous
reindex attempt was interrupted for some reason. Mutually exclusive
with ``--uuid`` option

``--delete``: before re-reindexing a transfer, will delete any data found in Elasticsearch with a matching UUID. In contrast with the ``--delete-all``, it does not delete the entire index.

"""

import logging
import multiprocessing
import os
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path
from subprocess import CalledProcessError

import archivematicaFunctions as am
import bagit
import elasticSearchFunctions as es
import metsrw
import storageService
from components.rights.load import load_rights
from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from fileOperations import addFileToTransfer
from fileOperations import extract_package
from fpr.models import FormatVersion
from main.management.commands import DashboardCommand
from main.management.commands import boolean_input
from main.models import Agent
from main.models import FileFormatVersion
from main.models import FileID
from main.models import Transfer

logger = logging.getLogger("archivematica.dashboard")


def _elasticsearch_noop_printfn(*args, **kwargs):
    pass


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
        parser.add_argument(
            "--from-storage-service",
            help="Import packages from Storage Service",
            action="store_true",
        )
        parser.add_argument(
            "--pipeline",
            help="Pipeline UUID to use when filtering packages from Storage Service",
            default=am.get_dashboard_uuid(),
        )
        parser.add_argument(
            "--delete-all",
            action="store_true",
            help="Delete all transfers information in the index before starting.",
        )
        parser.add_argument(
            "-u",
            "--uuid",
            action="store",
            default=None,
            help="Specify a single transfer by UUID to process",
        )
        parser.add_argument(
            "--skip-to",
            action="store",
            default=None,
            help="Specify starting transfer UUID to process. Mutually exclusive with --uuid option",
        )
        parser.add_argument(
            "-d",
            "--delete",
            action="store_true",
            help="Delete AIP-related Elasticsearch data before indexing AIP data",
        )

    def handle(self, *args, **options):
        """Entry point of the rebuild_transfer_backlog command."""
        # Check that the `transfers` part of the search is enabled
        if es.TRANSFERS_INDEX not in django_settings.SEARCH_ENABLED:
            print(
                "The Transfers indexes are not enabled. Please, make sure to "
                "set the *_SEARCH_ENABLED environment variables to `true` "
                "to enable the Transfers and AIPs indexes, or to `transfers` "
                "to only enable the Transfers indexes."
            )
            sys.exit(1)

        if not self.confirm(options["no_prompt"]):
            sys.exit(0)

        if options["uuid"] and options["skip_to"]:
            raise CommandError("Arguments --uuid and --skip-to are mutually exclusive.")

        # Ignore elasticsearch-py logging events unless they're errors.
        logging.getLogger("elasticsearch").setLevel(logging.ERROR)
        logging.getLogger("archivematica.common").setLevel(logging.ERROR)

        transfer_backlog_dir = self.prepdir(options["transfer_backlog_dir"])
        if options["from_storage_service"]:
            self.info('Rebuilding "transfers" index from packages in Storage Service.')
        else:
            if not os.path.exists(transfer_backlog_dir):
                raise CommandError(
                    "Directory does not exist: %s" % transfer_backlog_dir
                )
            self.info(f'Rebuilding "transfers" index from {transfer_backlog_dir}.')

        # Connect to Elasticsearch.
        es.setup_reading_from_conf(django_settings)
        es_client = es.get_client()
        try:
            es_info = es_client.info()
        except Exception as err:
            raise CommandError("Unable to connect to Elasticsearch: %s" % err)
        else:
            self.info(
                "Connected to Elasticsearch node {} (v{}).".format(
                    es_info["name"], es_info["version"]["number"]
                )
            )

        if options["delete_all"]:
            indexes = [es.TRANSFERS_INDEX, es.TRANSFER_FILES_INDEX]
            self.delete_indexes(es_client, indexes)
            self.create_indexes(es_client, indexes)

        if options["from_storage_service"]:
            pipeline_uuid = options["pipeline"]
            self.populate_data_from_storage_service(
                es_client,
                pipeline_uuid,
                uuid=options["uuid"],
                skip_to=options["skip_to"],
                delete=options["delete"],
            )
        else:
            self.populate_data_from_files(
                es_client,
                transfer_backlog_dir,
                uuid=options["uuid"],
                skip_to=options["skip_to"],
                delete=options["delete"],
            )

    def confirm(self, no_prompt):
        """Ask user to confirm the operation."""
        if no_prompt:
            return True
        self.warning(
            "WARNING: This script will overwrite your current"
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
            'in the "transfers" and "transferfiles" indexes...'
        )
        time.sleep(3)  # Time for the user to panic and kill the process.
        es_client.indices.delete(",".join(indexes), ignore=404)

    def create_indexes(self, es_client, indexes):
        """Create search indexes."""
        self.stdout.write("Creating indexes...")
        es.create_indexes_if_needed(es_client, indexes)

    def populate_data_from_files(
        self, es_client, transfer_backlog_dir, uuid=None, skip_to=None, delete=False
    ):
        """Populate indices and/or database from files."""
        transfer_backlog_dir = Path(transfer_backlog_dir)
        processed = 0
        skip_found = False
        for transfer_dir in transfer_backlog_dir.glob("*"):
            if transfer_dir.name == ".gitignore" or transfer_dir.is_file():
                continue
            try:
                bag = bagit.Bag(str(transfer_dir))
                bag.validate(
                    processes=multiprocessing.cpu_count(), completeness_only=True
                )
            except bagit.BagError:
                bag = None
            transfer_uuid = transfer_dir.name[-36:]
            # If skip_to option specified, skip until uuid found
            if skip_to and (skip_to.lower() == transfer_uuid.lower()):
                skip_found = True
            if skip_to and (not skip_found):
                self.info(f"Skipping {transfer_uuid}")
                continue
            # If specified a single transfer uuid, skip all others
            if uuid and (uuid.lower() != transfer_uuid.lower()):
                continue
            # if delete option specified delete before reindexing
            if delete:
                self.info(f"Deleting index data of {transfer_uuid}")
                es.remove_backlog_transfer(es_client, transfer_uuid)
                es.remove_backlog_transfer_files(es_client, transfer_uuid)

            if bag and "External-Identifier" in bag.info:
                self.info(f"Importing self-describing transfer {transfer_uuid}.")
                size = am.get_bag_size(bag, str(transfer_dir))

                _import_self_describing_transfer(
                    self, es_client, self.stdout, transfer_dir, transfer_uuid, size
                )
            else:
                self.info(f"Rebuilding known transfer {transfer_uuid}.")
                if bag:
                    size = am.get_bag_size(bag, str(transfer_dir))
                else:
                    size = am.walk_dir(str(transfer_dir))

                _import_pipeline_dependant_transfer(
                    self, es_client, self.stdout, transfer_dir, transfer_uuid, size
                )
            processed += 1
        self.success(f"{processed} transfers indexed!")

    def populate_data_from_storage_service(
        self, es_client, pipeline_uuid, uuid=None, skip_to=None, delete=False
    ):
        """Populate indices and/or database from Storage Service.

        :param es_client: Elasticsearch client.
        :param pipeline_uuid: UUID of origin pipeline for transfers to
        reindex.

        :returns: None
        """
        transfers = storageService.get_file_info(package_type="transfer")
        filtered_transfers = storageService.filter_packages(
            transfers, pipeline_uuid=pipeline_uuid
        )
        processed = 0
        skip_found = False
        for transfer in filtered_transfers:
            transfer_uuid = transfer["uuid"]
            # If skip_to option specified, skip until uuid found
            if skip_to and (skip_to.lower() == transfer_uuid.lower()):
                skip_found = True
            if skip_to and (not skip_found):
                self.info(f"Skipping {transfer_uuid}")
                continue
            # If specified a single transfer uuid, skip all others
            if uuid and (uuid.lower() != transfer_uuid.lower()):
                continue
            # if delete option specified delete before reindexing
            if delete:
                self.info(f"Deleting index data of {transfer_uuid}")
                es.remove_backlog_transfer(es_client, transfer_uuid)
                es.remove_backlog_transfer_files(es_client, transfer_uuid)

            temp_backlog_dir = tempfile.mkdtemp()
            try:
                local_package = storageService.download_package(
                    transfer_uuid, temp_backlog_dir
                )
            except storageService.Error:
                self.error(
                    f"Transfer {transfer_uuid} not indexed. Unable to download from Storage Service."
                )
                continue
            # Transfers are downloaded as .tar files, so we extract files
            # before indexing.
            try:
                extract_package(local_package, temp_backlog_dir)
            except CalledProcessError as err:
                self.error(
                    f"Transfer {transfer_uuid} not indexed. File extraction from tar failed: {err}."
                )
                continue
            local_package_without_extension = am.package_name_from_path(local_package)
            transfer_indexed = False
            for entry in os.scandir(temp_backlog_dir):
                if entry.is_dir() and entry.name == local_package_without_extension:
                    transfer_path = entry.path
                    self.info(
                        f"Importing transfer {transfer_uuid} from temporarily downloaded copy."
                    )
                    _import_self_describing_transfer(
                        self,
                        es_client,
                        self.stdout,
                        Path(transfer_path),
                        transfer_uuid,
                        transfer["size"],
                    )
                    transfer_indexed = True
            shutil.rmtree(temp_backlog_dir)
            if transfer_indexed:
                processed += 1
            else:
                self.error(
                    f"Transfer {transfer_uuid} not indexed. Unable to find files extracted from tar."
                )
        self.success(f"{processed} transfers indexed!")


def _import_dir_from_fsentry(cmd, fsentry, transfer_uuid):
    pass
    """
    Directory.objects.create(
        uuid=uuid.uuid4(),  # TODO: what goes here?
        transfer_id=transfer_uuid,
        originallocation=b"TODO",
        currentlocation=b"TODO")
    """


def _import_file_from_fsentry(cmd, fsentry, transfer_uuid):
    premis_events = fsentry.get_premis_events()

    ingestion_date = None
    for evt in fsentry.get_premis_events():
        if evt.event_type == "ingestion":
            ingestion_date = evt.event_date_time
            break

    file_obj = addFileToTransfer(
        f"%transferDirectory%{fsentry.path}",
        fsentry.file_uuid,
        transfer_uuid,
        None,
        ingestion_date,
        sourceType="ingestion",
        use="original",
    )

    for rights_statement in fsentry.get_premis_rights():
        load_rights(file_obj, rights_statement)

    for event in premis_events:
        _load_event(file_obj, event)

    try:
        premis_object = fsentry.get_premis_objects()[0]
    except IndexError:
        return

    # Populate extra attributes in the File object.
    file_obj.checksum = premis_object.message_digest
    file_obj.checksumtype = _convert_checksum_algo(
        premis_object.message_digest_algorithm
    )
    file_obj.size = premis_object.size
    file_obj.save()

    # Populate format details of the File object.
    if premis_object.format_registry_name != "PRONOM":
        return
    try:
        format_version = FormatVersion.active.get(
            pronom_id=premis_object.format_registry_key
        )
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


def _load_event(file_obj, event):
    create_kwargs = {
        "event_id": event.event_identifier_value,
        "event_type": event.event_type,
        "event_datetime": event.event_date_time,
    }

    event_detail = None
    if event.premis_version == "3.0":
        event_detail_attr = "event_detail_information__event_detail"
    else:
        event_detail_attr = "event_detail"
    try:
        event_detail = getattr(event, event_detail_attr)
    except AttributeError:
        raise
    if isinstance(event_detail, str):
        create_kwargs["event_detail"] = event.event_detail

    try:
        event_outcome_information = event.event_outcome_information[0]
    except (AttributeError, IndexError):
        pass
    else:
        event_outcome = event_outcome_information.event_outcome
        if isinstance(event_outcome, str):
            create_kwargs["event_outcome"] = event_outcome
        event_outcome_note = event_outcome_information.event_outcome_detail_note
        if isinstance(event_outcome_note, str):
            create_kwargs["event_outcome_detail"] = event_outcome_note

    event_obj = file_obj.event_set.create(**create_kwargs)

    try:
        identifiers = event.linking_agent_identifier
    except AttributeError:
        return
    for item in identifiers:
        try:
            # Is this cached?
            agent = Agent.objects.get(
                identifiertype=item.linking_agent_identifier_type,
                identifiervalue=item.linking_agent_identifier_value,
            )
        except Agent.DoesNotExist:
            continue
        event_obj.agents.add(agent)


def _convert_checksum_algo(algo):
    """Convert hash function names to the internal form expected.

    This may be good enough at least for the vocab at:
    http://id.loc.gov/vocabulary/preservation/cryptographicHashFunctions.
    """
    return algo.replace("-", "").lower()


def _get_transfer_mets_path(transfer_dir):
    mets_relative_path = "metadata/submissionDocumentation/METS.xml"
    try:
        bagit.Bag(str(transfer_dir))
        return str(transfer_dir / "data" / mets_relative_path)
    except bagit.BagError:
        return str(transfer_dir / mets_relative_path)


def _import_self_describing_transfer(
    cmd, es_client, stdout, transfer_dir, transfer_uuid, size
):
    """Import a self-describing transfer.

    Knowledge of this transfer is not required in the database. If
    missing, this function will populate the necessary state so
    arrangement and ingest work as expected.

    :param cmd: Command object
    :param es_client: Elasticsearch client.
    :param stdout: stdout handler.
    :param transfer_dir: Path to transfer.
    :param transfer_uuid: Transfer UUID.
    :param size: Transfer size.

    :returns: None.
    """
    transfer, created = Transfer.objects.get_or_create(
        uuid=transfer_uuid,
        defaults={
            "type": "Standard",
            "diruuids": False,
            "currentlocation": f"%sharedPath%www/AIPsStore/transferBacklog/originals/{transfer_dir.name}/",
        },
    )

    # The transfer did not exist, we need to populate everything else.
    if created:
        mets = metsrw.METSDocument.fromfile(_get_transfer_mets_path(transfer_dir))

        try:
            alt_id = mets.alternate_ids[0]
        except IndexError:
            pass
        else:
            if alt_id.type == "Accession ID":
                transfer.accessionid = alt_id.text
            transfer.save()

        for fsentry in mets.all_files():
            try:
                if fsentry.type == "Directory":
                    _import_dir_from_fsentry(cmd, fsentry, transfer_uuid)
                else:
                    _import_file_from_fsentry(cmd, fsentry, transfer_uuid)
            except Exception as err:
                cmd.warning(
                    f"There was an error processing file {fsentry.file_uuid} (transfer {transfer_uuid}): {err}"
                )
                if django_settings.DEBUG:
                    traceback.print_exc()

    es.index_transfer_and_files(
        es_client,
        transfer_uuid,
        str(transfer_dir) + "/",
        size,
        printfn=_elasticsearch_noop_printfn,
    )


def _import_pipeline_dependant_transfer(
    cmd, es_client, stdout, transfer_dir, transfer_uuid, size
):
    """Import a pipeline-dependant transfer.

    We can only import pipeline-dependant transfers from backlog if the
    pipeline has records of it, e.g. the Transfer object exists in the
    database.
    """
    try:
        Transfer.objects.get(uuid=transfer_uuid)
    except (Transfer.DoesNotExist, ValidationError):
        cmd.warning(f"Skipping transfer {transfer_uuid} - not found in the database!")
        return
    es.index_transfer_and_files(
        es_client,
        transfer_uuid,
        str(transfer_dir) + "/",
        size,
        printfn=_elasticsearch_noop_printfn,
    )
    try:
        storageService.reindex_file(transfer_uuid)
    except Exception as err:
        cmd.warning(
            "Could not reindex Transfer in the Storage Service, UUID: %s (%s)"
            % (transfer_uuid, err)
        )
