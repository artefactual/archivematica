"""Recreate the Elasticsearch index from AIPs stored on disk.

This is a copy of: https://github.com/artefactual/archivematica-devtools/blob/1fd49faf2b415a4f4229da832445d22b35c262f4/tools/rebuild-elasticsearch-aip-index-from-files.

This is useful if the Elasticsearch index has been deleted or damaged, but you
still have access to the AIPs in a local filesystem. This is not intended for
AIPs not stored in a local filesystem, for example Duracloud.

This must be run on the same system that Archivematica is installed on, since
it uses code from the Archivematica codebase.

The one required parameter is the path to the directory where the AIPs are
stored. In a default Archivematica installation, this is
``/var/archivematica/sharedDirectory/www/AIPsStore/``.

An optional parameter ``-u`` or ``--uuid`` may be passed to only reindex the
AIP that has the matching UUID.

``--delete`` will delete any data found in Elasticsearch with a matching
UUID before re-indexing. This is useful if only some AIPs are missing from
the index, since AIPs that already exist will not have their information
duplicated.

``--delete-all`` will delete the entire AIP Elasticsearch index before
starting. This is useful if there are AIPs indexed that have been deleted. This
should not be used if there are AIPs stored that are not locally accessible.
"""

from __future__ import print_function

from __future__ import absolute_import
import shutil
import os
import re
import subprocess
import sys
import time
import tempfile

from django.conf import settings as django_settings
from lxml import etree

from main.management.commands import DashboardCommand
import storageService as storage_service
import elasticSearchFunctions
import namespaces as ns


def extract_file(archive_path, destination_dir, relative_path):
    """Extract `relative_path` from `archive_path` into `destination_dir`."""
    if os.path.isdir(archive_path):
        output_path = os.path.join(destination_dir, os.path.basename(relative_path))
        shutil.copy(os.path.join(archive_path, relative_path), output_path)
    else:
        command_data = [
            "unar",
            "-force-overwrite",
            "-o",
            destination_dir,
            archive_path,
            relative_path,
        ]

        print("Command to run:", command_data)
        subprocess.call(command_data)
        output_path = os.path.join(destination_dir, relative_path)

    return output_path


def get_aips_in_aic(mets_root, archive_path, temp_dir):
    """Return the number of AIPs in the AIC, extracted from AIC METS file."""
    # Find name of AIC METS file
    try:
        # aic_mets_filename includes metadata/
        aic_mets_filename = ns.xml_find_premis(
            mets_root,
            "mets:fileSec/mets:fileGrp[@USE='metadata']/mets:file/mets:FLocat",
        ).get("{" + ns.NSMAP["xlink"] + "}href")
        aip_dirname = ns.xml_find_premis(mets_root, "mets:structMap/mets:div").get(
            "LABEL"
        )
    except Exception:
        # Catch any parsing errors
        return None

    # Extract AIC METS file
    aic_mets_path = extract_file(
        archive_path=archive_path,
        destination_dir=temp_dir,
        relative_path=os.path.join(aip_dirname, "data", aic_mets_filename),
    )

    # Parse for number of AIPs
    aic_root = etree.parse(aic_mets_path)
    extent = ns.xml_find_premis(
        aic_root,
        "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore/dcterms:extent",
    )

    try:
        aips_in_aic = re.search("\d+", extent.text).group()
    except AttributeError:
        # Probably because extent was None
        # Or the search returned None
        return None

    return aips_in_aic


def processAIPThenDeleteMETSFile(path, temp_dir, es_client, delete_existing_data=False):
    archive_file = os.path.basename(path)

    # Regex match the UUID - AIP might end with .7z, .tar.bz2, or
    # something else.
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", archive_file
    )
    if match is not None:
        aip_uuid = match.group()
    else:
        return -1

    print("Processing AIP", aip_uuid)

    if delete_existing_data is True:
        print("Deleting AIP", aip_uuid, "from aips/aip and aips/aipfile.")
        elasticSearchFunctions.delete_aip(es_client, aip_uuid)
        elasticSearchFunctions.delete_aip_files(es_client, aip_uuid)

    # AIP filenames are <name>-<uuid><extension>
    # Index of match end is right before the extension
    subdir = archive_file[: match.end()]
    aip_name = subdir[:-37]
    mets_file = "METS." + aip_uuid + ".xml"
    mets_file_relative_path = os.path.join("data", mets_file)
    if os.path.isfile(path):
        mets_file_relative_path = os.path.join(subdir, mets_file_relative_path)
    path_to_mets = extract_file(
        archive_path=path,
        destination_dir=temp_dir,
        relative_path=mets_file_relative_path,
    )

    # If AIC, need to extract number of AIPs in AIC to index as well
    aips_in_aic = None
    root = etree.parse(path_to_mets)
    try:
        aip_type = ns.xml_find_premis(
            root, "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore/dcterms:type"
        ).text
    except AttributeError:
        pass
    else:
        if aip_type == "Archival Information Collection":
            aips_in_aic = get_aips_in_aic(root, path, temp_dir)

    aip_info = storage_service.get_file_info(uuid=aip_uuid)

    if not aip_info:
        print("Information not found in Storage Service for AIP UUID: ", aip_uuid)
        return 1

    return elasticSearchFunctions.index_aip_and_files(
        client=es_client,
        uuid=aip_uuid,
        aip_stored_path=path,
        mets_staging_path=path_to_mets,
        name=aip_name,
        aip_size=aip_info[0]["size"],
        aips_in_aic=aips_in_aic,
        identifiers=[],  # TODO get these
    )


def is_hex(string):
    try:
        int(string, 16)
    except ValueError:
        return False
    return True


class Command(DashboardCommand):

    help = __doc__

    def add_arguments(self, parser):
        """Entry point to add custom arguments."""
        parser.add_argument(
            "-d",
            "--delete",
            action="store_true",
            help="Delete AIP-related Elasticsearch data before" " indexing AIP data",
        )
        parser.add_argument(
            "--delete-all",
            action="store_true",
            help="Delete all AIP information in the index before starting."
            " This will remove Elasticsearch entries for AIPS that do not"
            " exist in the provided directory.",
        )
        parser.add_argument(
            "-u",
            "--uuid",
            action="store",
            default="",
            help="Specify a single AIP by UUID to process",
        )
        parser.add_argument(
            "rootdir", help="Path to the directory containing the AIPs", metavar="PATH"
        )

    def handle(self, *args, **options):
        # Check that the `aips` part of the search is enabled
        if "aips" not in django_settings.SEARCH_ENABLED:
            print(
                "The AIPs indexes are not enabled. Please, make sure to "
                "set the *_SEARCH_ENABLED environment variables to `true` "
                "to enable the AIPs and Transfers indexes, or to `aips` "
                "to only enable the AIPs indexes."
            )
            sys.exit(1)

        # Check root directory exists
        if not os.path.isdir(options["rootdir"]):
            print("AIP store location doesn't exist.")
            sys.exit(1)

        # Verify ES is accessible
        elasticSearchFunctions.setup_reading_from_conf(django_settings)
        es_client = elasticSearchFunctions.get_client()

        try:
            es_client.info()
        except Exception:
            print("Error: Elasticsearch may not be running.")
            sys.exit(1)

        # Delete existing data also clears AIPS not found in the
        # provided directory
        if options["delete_all"]:
            print("Deleting all AIPs in the AIP index")
            time.sleep(3)  # Time for the user to panic and kill the process
            indexes = ["aips", "aipfiles"]
            es_client.indices.delete(",".join(indexes), ignore=404)
            elasticSearchFunctions.create_indexes_if_needed(es_client, indexes)

        if not options["uuid"]:
            print("Rebuilding AIPS index from AIPS in", options["rootdir"])
        else:
            print("Rebuilding AIP UUID", options["uuid"])

        temp_dir = tempfile.mkdtemp()
        count = 0
        name_regex = r"-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        dir_regex = r"-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

        for root, directories, files in os.walk(options["rootdir"]):
            # Ignore top-level directories inside ``rootdir`` that are not hex,
            # e.g. we walk ``0771`` but we're ignoring ``transferBacklog``.
            if root == options["rootdir"]:
                directories[:] = [d for d in directories if is_hex(d) and len(d) == 4]

            # Uncompressed AIPs
            for directory in directories:
                # Check if dir name matches AIP name format
                match = re.search(dir_regex, directory)
                if not match:
                    continue
                # If running on a single AIP, skip all others
                if options["uuid"] and options["uuid"].lower() not in directory.lower():
                    continue
                ret = processAIPThenDeleteMETSFile(
                    path=os.path.join(root, directory),
                    temp_dir=temp_dir,
                    es_client=es_client,
                    delete_existing_data=options["delete"],
                )
                # Don't recurse into this directory
                directories = directories.remove(directory)
                # Update count on successful index
                if ret == 0:
                    count += 1

            # Compressed AIPs
            for filename in files:
                # Check if filename matches AIP name format
                match = re.search(name_regex, filename)
                if not match:
                    continue
                # If running on a single AIP, skip all others
                if options["uuid"] and options["uuid"].lower() not in filename.lower():
                    continue
                ret = processAIPThenDeleteMETSFile(
                    path=os.path.join(root, filename),
                    temp_dir=temp_dir,
                    es_client=es_client,
                    delete_existing_data=options["delete"],
                )
                # Update count on successful index
                if ret == 0:
                    count += 1

        print("Cleaning up")

        shutil.rmtree(temp_dir)

        print("Indexing complete. Indexed", count, "AIP(s).")
