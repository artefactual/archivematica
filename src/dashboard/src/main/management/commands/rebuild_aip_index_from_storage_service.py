# -*- coding: utf-8 -*-
"""Recreate the Elasticsearch AIPs indices from the Storage Service.

This is useful if the Elasticsearch index has been deleted or damaged, but you
still have access to the AIPs and AICs via the Archivematica Storage Service.
This script is not limited to AIPs stored in a local filesystem or to unencrypted
locations, as it uses the Storage Service's "extract_file" API endpoint to
download the METS file for each package to reindex.

This must be run on the same system that Archivematica is installed on, since
it uses code from the Archivematica codebase.

By default, the script will reindex every AIP and AIC in the Storage Service
that has an origin pipeline that matches where the script is run from, and a
status other than "DELETED".

An optional parameter ``--pipeline`` may be passed to reindex packages from
a different pipeline than the current dashboard.

An optional parameter ``-u`` or ``--uuid`` may be passed to only reindex the
AIP that has the matching UUID.

``--delete`` will delete any data found in Elasticsearch with a matching
UUID before re-indexing. This is useful if only some AIPs are missing from
the index, since AIPs that already exist will not have their information
duplicated.

``--delete-all`` will delete the entire AIP Elasticsearch index before
starting. This is useful if there are AIPs indexed that have been deleted, or
if you would like to delete the 'aips' and 'aipfiles' indices entirely and
recreate them using the most recent version of the ES mappings.

Execution example:
./manage.py rebuild_aip_index_from_storage_service --delete-all
"""
from __future__ import absolute_import, print_function

import logging
from lxml import etree
import os
import shutil
import tempfile

from elasticsearch import ElasticsearchException

import archivematicaFunctions as am
import elasticSearchFunctions as es
from main.management.commands import DashboardCommand, setup_es_for_aip_reindexing
import storageService


def get_aips_in_aic(mets_root, temp_dir, uuid):
    """Return the number of AIPs in the AIC as found in the AIP METS.

    :param mets_root: AIP METS document root.
    :param temp_dir: Path to tempdir where we'll write AIC METS file.
    :param uuid: AIC UUID.

    :returns: Count of AIPs in AIC or None.
    """
    # Find the name of AIC METS file from within the AIP METS file.
    aic_mets_filename = am.find_aic_mets_filename(mets_root)
    aip_dirname = am.find_aip_dirname(mets_root)
    if aic_mets_filename is None or aip_dirname is None:
        return None

    # Download a copy of the AIC METS file.
    mets_relative_path = os.path.join(aip_dirname, "data", aic_mets_filename)
    aic_mets_filename = os.path.basename(aic_mets_filename)
    mets_download_path = os.path.join(temp_dir, aic_mets_filename)
    storageService.extract_file(uuid, mets_relative_path, mets_download_path)
    if not os.path.isfile(mets_download_path):
        return None

    # Find number of AIPs in the AIC in AIC METS file.
    aic_root = etree.parse(mets_download_path)
    aips_in_aic = am.find_aips_in_aic(aic_root)
    return aips_in_aic


class Command(DashboardCommand):

    help = __doc__

    def add_arguments(self, parser):
        """Entry point to add custom arguments."""
        parser.add_argument(
            "-d",
            "--delete",
            action="store_true",
            help="Delete AIP-related Elasticsearch data for AIPs with matching"
            " UUIDS before indexing AIP data",
        )
        parser.add_argument(
            "--delete-all",
            action="store_true",
            help="Delete all AIP information in the index before starting.",
        )
        parser.add_argument(
            "-u",
            "--uuid",
            action="store",
            default="",
            help="Specify a single AIP by UUID to process",
        )
        parser.add_argument(
            "--pipeline",
            help="Pipeline UUID to use when filtering packages",
            default=am.get_dashboard_uuid(),
        )

    def handle(self, *args, **options):
        # Ignore elasticsearch-py logging events unless they're errors.
        logging.getLogger("elasticsearch").setLevel(logging.ERROR)
        logging.getLogger("archivematica.common").setLevel(logging.ERROR)

        # Setup es_client and delete indices if required.
        es_client = setup_es_for_aip_reindexing(self, options["delete_all"])

        # Create temporary directory for downloaded METS files.
        temp_dir = tempfile.mkdtemp()

        # Set pipeline UUID to use for filtering packages to reindex.
        pipeline_uuid = options["pipeline"]

        delete_before_reindexing = False
        if options["delete"] is True:
            delete_before_reindexing = True

        # Index a single package and return if uuid option is enabled.
        if options["uuid"]:
            package_uuid = options["uuid"]
            self.info("Reindexing package {}".format(package_uuid))
            package_info = storageService.get_file_info(uuid=package_uuid)

            is_aic = False
            package_type = package_info.get("package_type")
            if package_type and package_type == "AIC":
                is_aic = True

            (index_success, error_message) = self.process_package(
                es_client,
                package_info,
                temp_dir,
                delete_before_reindexing,
                is_aic=is_aic,
            )
            if index_success is True:
                self.info("Successfully reindexed package {}".format(package_uuid))
            else:
                self.error(
                    "Error indexing package {0}. Details: {1}".format(
                        package_uuid, error_message
                    )
                )

            self.info("Cleaning up")
            shutil.rmtree(temp_dir)
            self.info("Indexing complete.")
            return

        self.info("Rebuilding 'aips' and 'aipfiles' indices")

        packages_not_indexed = []

        # Index non-deleted AIPs associated with this pipeline.
        aips = storageService.get_file_info(package_type="AIP")
        filtered_aips = am.filter_packages_by_status_and_pipeline(
            aips, pipeline_uuid=pipeline_uuid
        )
        filtered_aip_count = len(filtered_aips)

        aip_indexed_count = 0
        for aip in filtered_aips:
            index_success = self.process_package(
                es_client, aip, temp_dir, delete_before_reindexing
            )
            if index_success is True:
                aip_indexed_count += 1
            else:
                packages_not_indexed.append(aip["uuid"])

        # Index non-deleted AICs associated with this pipeline.
        aics = storageService.get_file_info(package_type="AIC")
        filtered_aics = am.filter_packages_by_status_and_pipeline(
            aics, pipeline_uuid=pipeline_uuid
        )
        filtered_aic_count = len(filtered_aics)

        aic_indexed_count = 0
        for aic in filtered_aics:
            index_success = self.process_package(
                es_client, aic, temp_dir, delete_before_reindexing, is_aic=True
            )
            if index_success is True:
                aic_indexed_count += 1
            else:
                packages_not_indexed.append(aic["uuid"])

        # Clean up and report on packages indexed.
        self.info("Cleaning up")
        shutil.rmtree(temp_dir)

        if packages_not_indexed:
            indexing_stats = "{0} of {1} AIPs and {2} of {3} AICs".format(
                aip_indexed_count,
                filtered_aip_count,
                aic_indexed_count,
                filtered_aic_count,
            )
            self.info(
                "Indexing complete. Indexed {0}. Packages not indexed: {1}.".format(
                    indexing_stats, ", ".join(packages_not_indexed)
                )
            )
        else:
            self.info(
                "Indexing complete. Indexed {0} AIPs and {1} AICs".format(
                    aip_indexed_count, aic_indexed_count
                )
            )

    def process_package(
        self, es_client, package_info, temp_dir, delete_before_reindexing, is_aic=False
    ):
        """Index package in 'aips' and 'aipfiles' indices.

        :param es_client: Elasticsearch client.
        :param package_info: Package info dict returned by Storage
        Service.
        :param temp_dir: Path to tempdir for downloaded METS files.
        :param delete_before_reindexing: Boolean of whether to delete
        package from indices prior to reindexing.
        :is_aic: Optional boolean to indicate if package being indexed
        is an AIC.

        :returns: Boolean indicating success.
        """
        uuid = package_info["uuid"]

        # Download the AIP METS file to a temporary directory.
        mets_relative_path = am.relative_path_to_aip_mets_file(
            package_info["uuid"], package_info["current_path"]
        )
        mets_filename = os.path.basename(mets_relative_path)
        mets_download_path = os.path.join(temp_dir, mets_filename)
        storageService.extract_file(uuid, mets_relative_path, mets_download_path)

        if not os.path.isfile(mets_download_path):
            error_message = "Unable to download AIP METS file from Storage Service"
            self.error(
                "Error indexing package {0}. Details: {1}".format(uuid, error_message)
            )
            return False

        aips_in_aic = None
        if is_aic is True:
            mets_root = etree.parse(mets_download_path)
            aips_in_aic = get_aips_in_aic(mets_root, temp_dir, uuid)

        package_name = am.package_name_from_path(
            package_info["current_path"], remove_uuid_suffix=True
        )

        if delete_before_reindexing is True:
            self.info(
                "Deleting package {} from 'aips' and 'aipfiles' indices.".format(uuid)
            )
            es.delete_aip(es_client, uuid)
            es.delete_aip_files(es_client, uuid)

        # Index the AIP and then immediately delete the METS file.
        try:
            es.index_aip_and_files(
                client=es_client,
                uuid=uuid,
                aip_stored_path=package_info["current_full_path"],
                mets_staging_path=mets_download_path,
                name=package_name,
                aip_size=package_info["size"],
                aips_in_aic=aips_in_aic,
                encrypted=package_info.get("encrypted", False),
            )
            self.info("Successfully indexed package {}".format(uuid))
            os.remove(mets_download_path)
            return True
        except ElasticsearchException as err:
            self.error("Error indexing package {0}. Details: {1}".format(uuid, err))
            os.remove(mets_download_path)
            return False
