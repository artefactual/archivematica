# -*- coding: utf-8 -*-
# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import

import errno
import os
import logging
import re
import shutil
import tempfile
import uuid

from django.conf import settings as django_settings
import django.http
import django.template.defaultfilters
from django.utils.translation import ugettext as _, ungettext
import six
from six.moves import map, zip

from components import helpers
import components.filesystem_ajax.helpers as filesystem_ajax_helpers
from main import models

import archivematicaFunctions
import databaseFunctions
import elasticSearchFunctions
import storageService as storage_service
from archivematicaFunctions import b64encode_string, b64decode_string


logger = logging.getLogger("archivematica.dashboard")

SHARED_DIRECTORY_ROOT = django_settings.SHARED_DIRECTORY
ACTIVE_TRANSFER_DIR = os.path.join(
    SHARED_DIRECTORY_ROOT, "watchedDirectories", "activeTransfers"
)
ORIGINAL_DIR = os.path.join(
    SHARED_DIRECTORY_ROOT, "www", "AIPsStore", "transferBacklog", "originals"
)

DEFAULT_BACKLOG_PATH = "originals/"
DEFAULT_ARRANGE_PATH = "/arrange/"

TRANSFER_TYPE_DIRECTORIES = {
    "standard": "standardTransfer",
    "zipfile": "zippedDirectory",
    "unzipped bag": "baggitDirectory",
    "zipped bag": "baggitZippedDirectory",
    "dspace": "Dspace",
    "maildir": "maildir",
    "TRIM": "TRIM",
    "dataverse": "dataverseTransfer",
}


def _prepare_browse_response(response):
    """
    Additional common processing before passing a browse response back to JS.

    Input should be a dictionary with keys 'entries', 'directories' and 'properties'.

    'entries' is a list of strings, one for each entry in that directory, both file-like and folder-like.
    'directories' is a list of strings for each folder-like entry. Each entry should also be listed in 'entries'.
    'properties' is an optional dictionary that may contain additional information for the entries.  Keys are the entry name found in 'entries', values are a dictionary containing extra information. 'properties' may not contain all values from 'entries'.

    Output will be the input dictionary with the following transforms applied:
    * All filenames will be base64 encoded
    * 'properties' dicts may have a new entry of 'display_string' with relevant information to display to the user.

    :param dict response: Dict response from a browse call. See above.
    :return: Dict response ready to be returned to file-browser JS.
    """
    # Generate display string based on properties
    for entry, prop in response.get("properties", {}).items():
        logger.debug("Properties for %s: %s", entry, prop)
        if "levelOfDescription" in prop:
            prop["display_string"] = prop["levelOfDescription"]
        elif "verbose name" in prop:
            prop["display_string"] = prop["verbose name"].strip()
        elif "object count" in prop:
            try:
                prop["display_string"] = ungettext(
                    "%(count)d object", "%(count)d objects", prop["object count"]
                ) % {"count": prop["object count"]}
            except TypeError:  # 'object_count' val can be a string, see SS:space.py
                prop["display_string"] = _("%(count)s objects") % {
                    "count": prop["object count"]
                }
        elif "size" in prop:
            prop["display_string"] = django.template.defaultfilters.filesizeformat(
                prop["size"]
            )

    response["entries"] = list(map(b64encode_string, response["entries"]))
    response["directories"] = list(map(b64encode_string, response["directories"]))
    response["properties"] = {
        b64encode_string(k): v for k, v in response.get("properties", {}).items()
    }

    return response


def directory_children_proxy_to_storage_server(request, location_uuid, basePath=False):
    path = ""
    if basePath:
        path = b64decode_string(basePath)
    path = path + b64decode_string(request.GET.get("base_path", ""))
    path = path + b64decode_string(request.GET.get("path", ""))

    response = storage_service.browse_location(location_uuid, path)
    response = _prepare_browse_response(response)

    return helpers.json_response(response)


def contents(request):
    path = request.GET.get("path", "/home")
    response = filesystem_ajax_helpers.directory_to_dict(path)
    return helpers.json_response(response)


def arrange_contents(request, path=None):
    if path is None:
        path = request.GET.get("path", "")
        try:
            base_path = b64decode_string(path)
        except TypeError:
            response = {
                "success": False,
                "message": _("Could not base64-decode provided path: %(path)s")
                % {"path": path},
            }
            return helpers.json_response(response, status_code=400)
    else:
        base_path = path

    # Must indicate that base_path is a folder by ending with /
    if not base_path.endswith("/"):
        base_path += "/"

    if not base_path.startswith(DEFAULT_ARRANGE_PATH):
        base_path = DEFAULT_ARRANGE_PATH

    # Query SIP Arrangement for results
    # Get all the paths that are not in SIPs and start with base_path.  We don't
    # need the objects, just the arrange_path
    paths = (
        models.SIPArrange.objects.filter(sip_created=False)
        .filter(aip_created=False)
        .filter(arrange_path__startswith=base_path)
        .order_by("arrange_path")
    )

    if len(paths) == 0 and base_path != DEFAULT_ARRANGE_PATH:
        response = {
            "success": False,
            "message": _("No files or directories found under path: %(path)s")
            % {"path": base_path},
        }
        return helpers.json_response(response, status_code=404)

    # Convert the response into an entries [] and directories []
    # 'entries' contains everything (files and directories)
    entries = set()
    directories = set()
    properties = {}
    for item in paths:
        # Strip common prefix
        path_parts = item.arrange_path.replace(base_path, "", 1).split("/")
        entry = path_parts[0]
        if not entry:
            continue
        entries.add(entry)
        # Specify level of description if set
        if item.level_of_description:
            properties[entry] = properties.get(entry, {})  # Default empty dict
            # Don't overwrite if already exists
            properties[entry]["levelOfDescription"] = (
                properties[entry].get("levelOfDescription") or item.level_of_description
            )
        if item.file_uuid:
            properties[entry] = properties.get(entry, {})  # Default empty dict
            properties[entry]["file_uuid"] = item.file_uuid
        if len(path_parts) > 1:  # Path is a directory
            directories.add(entry)
            # Don't add directories to the object count
            if path_parts[-1]:
                properties[entry] = properties.get(entry, {})  # Default empty dict
                properties[entry]["object count"] = (
                    properties[entry].get("object count", 0) + 1
                )  # Increment object count

    response = {
        "entries": list(entries),
        "directories": list(directories),
        "properties": properties,
    }
    response = _prepare_browse_response(response)

    return helpers.json_response(response)


def delete_arrange(request, filepath=None):
    if filepath is None:
        try:
            filepath = b64decode_string(request.POST["filepath"])
        except KeyError:
            response = {
                "success": False,
                "message": _("No filepath to delete was provided!"),
            }
            return helpers.json_response(response, status_code=400)

    # Delete access mapping if found
    models.SIPArrangeAccessMapping.objects.filter(arrange_path=filepath).delete()
    models.SIPArrange.objects.filter(arrange_path__startswith=filepath).delete()
    return helpers.json_response({"message": _("Delete successful.")})


def start_transfer(transfer_name, transfer_type, accession, access_id, paths, row_ids):
    """
    Start a new transfer.

    :param str transfer_name: Name of new transfer.
    :param str transfer_type: Type of new transfer. From TRANSFER_TYPE_DIRECTORIES.
    :param str accession: Accession number of new transfer.
    :param str access_id: Access system identifier for the new transfer.
    :param list paths: List of <location_uuid>:<relative_path> to be copied into the new transfer. Location UUIDs should be associated with this pipeline, and relative path should be relative to the location.
    :param list row_ids: ID of the associated TransferMetadataSet for disk image ingest.
    :returns: Dict with {'message': <message>, ['error': True, 'path': <path>]}.  Error is a boolean, present and True if there is an error.  Message describes the success or failure. Path is populated if there is no error.
    """
    if not transfer_name:
        raise ValueError("No transfer name provided.")
    if not paths:
        raise ValueError("No path provided.")

    # Create temp directory that everything will be copied into
    temp_base_dir = os.path.join(SHARED_DIRECTORY_ROOT, "tmp")
    temp_dir = tempfile.mkdtemp(dir=temp_base_dir)
    os.chmod(temp_dir, 0o770)  # Needs to be writeable by the SS

    for i, path in enumerate(paths):
        index = i + 1  # so transfers start from 1, not 0
        # Don't suffix the first transfer component, only subsequent ones
        if index > 1:
            target = transfer_name + "_" + str(index)
        else:
            target = transfer_name
        row_id = row_ids[i]

        if helpers.file_is_an_archive(path):
            transfer_dir = temp_dir
            p = path.split(":", 1)[1]
            logger.debug("found a zip file, splitting path " + p)
            filepath = os.path.join(temp_dir, os.path.basename(p))
        else:
            path = os.path.join(path, ".")  # Copy contents of dir but not dir
            transfer_dir = os.path.join(temp_dir, target)
            filepath = os.path.join(temp_dir, target)

        transfer_relative = transfer_dir.replace(SHARED_DIRECTORY_ROOT, "", 1)
        _copy_from_transfer_sources([path], transfer_relative)
        filepath = archivematicaFunctions.unicodeToStr(filepath)
        try:
            destination = _copy_to_start_transfer(
                filepath=filepath,
                type=transfer_type,
                accession=accession,
                access_id=access_id,
                transfer_metadata_set_row_uuid=row_id,
            )
        except Exception as e:
            logger.exception("Error starting transfer {}: {}".format(filepath, e))
            raise Exception("Error starting transfer {}: {}".format(filepath, e))

    shutil.rmtree(temp_dir)
    return {"message": _("Copy successful."), "path": destination}


def _copy_to_start_transfer(
    filepath="", type="", accession="", access_id="", transfer_metadata_set_row_uuid=""
):
    error = filesystem_ajax_helpers.check_filepath_exists(filepath)

    if error is None:
        temp_uuid = str(uuid.uuid4())

        # confine destination to subdir of originals
        basename = os.path.basename(filepath)

        # default to standard transfer
        type_subdir = TRANSFER_TYPE_DIRECTORIES.get(type, "standardTransfer")
        destination = os.path.join(
            ACTIVE_TRANSFER_DIR, type_subdir, "{}-{}".format(basename, temp_uuid)
        )
        destination = helpers.pad_destination_filepath_if_it_already_exists(destination)

        # Ensure directories end with a trailing /
        if os.path.isdir(filepath):
            destination = os.path.join(destination, "")

        mcp_destination = destination.replace(
            os.path.join(SHARED_DIRECTORY_ROOT, ""), "%sharedPath%"
        )
        kwargs = {
            "uuid": temp_uuid,
            "accessionid": accession,
            "access_system_id": access_id,
            "currentlocation": mcp_destination,
        }

        # Even if a UUID is passed, there might not be a row with
        # that UUID yet - for instance, if the user opened an edit
        # form but did not save any metadata for that row.
        if transfer_metadata_set_row_uuid:
            try:
                row = models.TransferMetadataSet.objects.get(
                    id=transfer_metadata_set_row_uuid
                )
                kwargs["transfermetadatasetrow"] = row
            except models.TransferMetadataSet.DoesNotExist:
                pass

        # Create the Transfer here instead of letting MCPClient create it
        # Used to pass additional information to the Transfer
        models.Transfer.objects.create(**kwargs)

        try:
            shutil.move(filepath, destination)
        except (OSError, shutil.Error) as e:
            error = (
                "Error copying from "
                + filepath
                + " to "
                + destination
                + ". ("
                + str(e)
                + ")"
            )

    if error:
        raise Exception(error)
    return destination


def _source_transfers_gave_uuids_to_directories(files):
    """Returns ``True`` if any of the ``Transfer`` models (that any of the
    ``File`` models referenced in ``files`` were accessioned by) gave UUIDs to
    directories. If ``True`` is returned, we assign new UUIDs to all
    directories in the arranged SIP.
    """
    file_uuids = [_f for _f in [file_.get("uuid") for file_ in files] if _f]
    return models.Transfer.objects.filter(
        file__uuid__in=file_uuids, diruuids=True
    ).exists()


def _create_arranged_sip(staging_sip_path, files, sip_uuid):
    shared_dir = django_settings.SHARED_DIRECTORY
    staging_sip_path = staging_sip_path.lstrip("/")
    staging_abs_path = os.path.join(shared_dir, staging_sip_path)

    # If an arranged SIP contains a single file that comes from a
    # transfer wherein UUIDs were assigned to directories, then assign new
    # UUIDs to all directories in the arranged SIP.
    diruuids = _source_transfers_gave_uuids_to_directories(files)  # boolean

    # Create SIP object
    sip_name = staging_sip_path.split("/")[1]
    sip_path = os.path.join(
        shared_dir,
        "watchedDirectories",
        "SIPCreation",
        "SIPsUnderConstruction",
        sip_name,
    )
    currentpath = sip_path.replace(shared_dir, "%sharedPath%", 1) + "/"
    sip_path = helpers.pad_destination_filepath_if_it_already_exists(sip_path)
    try:
        sip = models.SIP.objects.get(uuid=sip_uuid)
    except models.SIP.DoesNotExist:
        # Create a SIP object if none exists
        path = os.path.join(sip_path.replace(shared_dir, "%sharedPath%", 1), "")
        databaseFunctions.createSIP(path, sip_uuid, diruuids=diruuids)
        sip = models.SIP.objects.get(uuid=sip_uuid)
    else:
        # Update the already-created SIP with its path
        if sip.currentpath is not None:
            return _(
                "Provided SIP UUID (%(uuid)s) belongs to an already-started SIP!"
            ) % {"uuid": sip_uuid}
        sip.currentpath = currentpath
        sip.diruuids = diruuids
        sip.save()

    # Update currentLocation of files
    # Also get all directory paths implicit in all of the file paths
    directories = set()
    for file_ in files:
        if file_.get("uuid"):
            # Strip 'arrange/sip_name' from file path
            in_sip_path = "/".join(file_["destination"].split("/")[2:])
            currentlocation = "%SIPDirectory%" + in_sip_path
            models.File.objects.filter(uuid=file_["uuid"]).update(
                sip=sip_uuid, currentlocation=currentlocation
            )
            # Get all ancestor directory paths of the file's destination.
            subdir = os.path.dirname(currentlocation)
            while subdir:
                directory = subdir.replace("%SIPDirectory%", "%SIPDirectory%objects/")
                directories.add(directory)
                subdir = os.path.dirname(subdir)

    if diruuids:
        # Create new Directory models for all subdirectories in the newly
        # arranged SIP. Because the user can arbitrarily modify the directory
        # structure, it doesn't make sense to reuse any directory models that
        # were created during transfer.
        models.Directory.create_many(
            archivematicaFunctions.get_dir_uuids(directories, logger),
            sip,
            unit_type="sip",
        )

    # Create directories for logs and metadata, if they don't exist
    for directory in (
        "logs",
        "metadata",
        os.path.join("metadata", "submissionDocumentation"),
    ):
        try:
            os.mkdir(os.path.join(staging_abs_path, directory))
        except os.error as exception:
            if exception.errno != errno.EEXIST:
                raise

    # Add log of original location and new location of files
    arrange_log = os.path.join(staging_abs_path, "logs", "arrange.log")
    with open(arrange_log, "w") as f:
        log = (
            "%s -> %s\n" % (file_["source"], file_["destination"])
            for file_ in files
            if file_.get("uuid")
        )
        f.writelines(log)

    # Move to watchedDirectories/SIPCreation/SIPsUnderConstruction
    logger.info("_create_arranged_sip: move from %s to %s", staging_abs_path, sip_path)
    shutil.move(src=staging_abs_path, dst=sip_path)


def copy_from_arrange_to_completed(
    request, filepath=None, sip_uuid=None, sip_name=None
):
    """Create a SIP from the information stored in the SIPArrange table.

    Get all the files in the new SIP, and all their associated metadata, and
    move to the processing space.  Create needed database entries for the SIP
    and start the microservice chain.
    """
    if filepath is None:
        filepath = b64decode_string(request.POST.get("filepath", ""))
    logger.info(
        "copy_from_arrange_to_completed: filepath: %s, sip_uuid: %s", filepath, sip_uuid
    )
    # can optionally pass in the UUID to an unstarted SIP entity
    if sip_uuid is None:
        sip_uuid = request.POST.get("uuid")

    status_code, response = copy_from_arrange_to_completed_common(
        filepath, sip_uuid, sip_name
    )
    return helpers.json_response(response, status_code=status_code)


def copy_from_arrange_to_completed_common(filepath, sip_uuid, sip_name):
    """Create a SIP from SIPArrange table.

    Get all the files in the new SIP, and all their associated metadata, and
    move to the processing space.
    Create needed database entries for the SIP and start the microservice chain.
    """
    error = None
    # if sip_uuid is None here, it will be created later,
    # but we want to sanity-check provided values at this point.
    if sip_uuid is not None:
        try:
            uuid.UUID(sip_uuid)
        except ValueError:
            response = {
                "message": _("Provided UUID (%(uuid)s) is not a valid UUID!")
                % {"uuid": sip_uuid},
                "error": True,
            }
            status_code = 400
            return status_code, response

    # Error checking
    if not filepath.startswith(DEFAULT_ARRANGE_PATH):
        # Must be in DEFAULT_ARRANGE_PATH
        error = _("%(path1)s is not in %(path2)s") % {
            "path1": filepath,
            "path2": DEFAULT_ARRANGE_PATH,
        }
    elif not filepath.endswith("/"):
        # Must be a directory (end with /)
        error = _("%(path)s is not a directory") % {"path": filepath}
    else:
        if not sip_name:
            # Filepath is prefix on arrange_path in SIPArrange
            sip_name = os.path.basename(filepath.rstrip("/"))
        staging_sip_path = os.path.join("staging", sip_name, "")
        logger.debug(
            "copy_from_arrange_to_completed: staging_sip_path: %s", staging_sip_path
        )
        # Fetch all files with 'filepath' as prefix, and have a source path
        arrange = models.SIPArrange.objects.filter(sip_created=False).filter(
            arrange_path__startswith=filepath
        )
        arrange_files = arrange.filter(original_path__isnull=False)

        # Collect file and directory information. Change path to be in staging, not arrange
        files = []
        for arranged_file in arrange_files:
            destination = arranged_file.arrange_path.replace(
                filepath, staging_sip_path, 1
            )
            files.append(
                {
                    "source": arranged_file.original_path.lstrip("/"),
                    "destination": destination,
                    "uuid": arranged_file.file_uuid,
                }
            )
            # Get transfer folder name
            transfer_parts = arranged_file.original_path.replace(
                DEFAULT_BACKLOG_PATH, "", 1
            ).split("/", 1)
            transfer_name = transfer_parts[0]
            # Determine if the transfer is a BagIt package
            is_bagit = transfer_parts[1].startswith(u"data/")
            # Copy metadata & logs to tmp/, where later scripts expect
            for directory in ("logs", "metadata"):
                source = [DEFAULT_BACKLOG_PATH, transfer_name, directory, "."]
                if is_bagit:
                    source.insert(2, "data")
                file_ = {
                    "source": os.path.join(*source),
                    "destination": os.path.join(
                        "tmp",
                        "transfer-{}".format(arranged_file.transfer_uuid),
                        directory,
                        ".",
                    ),
                }
                if file_ not in files:
                    files.append(file_)

        if not files:
            status_code = 400
            response = {
                "message": _("No files were selected"),
                "code": "ERR_NO_FILES",
                "error": True,
            }
            return status_code, response

        logger.debug("copy_from_arrange_to_completed: files: %s", files)
        # Move files from backlog to local staging path
        (sip, error) = storage_service.get_files_from_backlog(files)

        if error is None:
            # Create SIP object
            if sip_uuid is None:
                sip_uuid = str(uuid.uuid4())
            error = _create_arranged_sip(staging_sip_path, files, sip_uuid)

        if error is None:
            for arranged_entry in arrange:
                # Update arrange_path to be relative to new SIP's objects
                # Use normpath to strip trailing / from directories
                relative_path = arranged_entry.arrange_path.replace(filepath, "", 1)
                if relative_path == "objects/":
                    # If objects directory created manually, delete it as we
                    # don't want the LoD for it, and it's not needed elsewhere
                    arranged_entry.delete()
                    continue
                relative_path = relative_path.replace("objects/", "", 1)
                relative_path = os.path.normpath(relative_path)
                arranged_entry.arrange_path = relative_path
                arranged_entry.sip_id = sip_uuid
                arranged_entry.sip_created = True
                arranged_entry.save()

    if error is not None:
        response = {"message": str(error), "error": True}
        status_code = 400
    else:
        response = {"message": _("SIP created."), "sip_uuid": sip_uuid}
        status_code = 201

    return status_code, response


def create_arrange_directories(paths):
    for path in paths:
        if not path.startswith(DEFAULT_ARRANGE_PATH):
            raise ValueError(_("All directories must be within the arrange directory."))
    arranges = [
        models.SIPArrange(
            original_path=None,
            arrange_path=os.path.join(path, ""),  # ensure ends with /
            file_uuid=None,
        )
        for path in paths
    ]
    models.SIPArrange.create_many(arranges)


def create_directory_within_arrange(request):
    """Creates directory entries in the SIPArrange table.

    paths: POST parameter, a list of paths of directories in
    DEFAULT_ARRANGE_PATH to create.
    """
    error = None

    paths = list(map(b64decode_string, request.POST.getlist("paths[]", [])))

    if paths:
        try:
            create_arrange_directories(paths)
        except ValueError as e:
            error = str(e)

    if error is not None:
        response = {"message": error, "error": True}
        status_code = 409
    else:
        response = {"message": _("Creation successful.")}
        status_code = 201

    return helpers.json_response(response, status_code=status_code)


def _move_files_within_arrange(sourcepath, destination):
    if not (
        sourcepath.startswith(DEFAULT_ARRANGE_PATH)
        and destination.startswith(DEFAULT_ARRANGE_PATH)
    ):
        raise ValueError(
            _("%(src)s and %(dst)s must be inside %(path)s")
            % {"src": sourcepath, "dst": destination, "path": DEFAULT_ARRANGE_PATH}
        )
    elif destination.endswith("/"):  # destination is a directory
        if sourcepath.endswith("/"):  # source is a directory
            folder_contents = models.SIPArrange.objects.filter(
                arrange_path__startswith=sourcepath
            )
            # Strip the last folder off sourcepath, but leave a trailing /, so
            # we retain the folder name when we move the files.
            source_parent = "/".join(sourcepath.split("/")[:-2]) + "/"
            for entry in folder_contents:
                entry.arrange_path = entry.arrange_path.replace(
                    source_parent, destination, 1
                )
                entry.save()
        else:  # source is a file
            models.SIPArrange.objects.filter(arrange_path=sourcepath).update(
                arrange_path=destination + os.path.basename(sourcepath)
            )
    else:  # destination is a file (this should have been caught by JS)
        raise ValueError(_("You cannot drag and drop onto a file."))


def _get_arrange_directory_tree(backlog_uuid, original_path, arrange_path):
    """Fetches all the children of original_path from backlog_uuid and creates
    an identical tree in arrange_path.

    Helper function for copy_to_arrange.
    """
    # TODO Use ElasticSearch, since that's where we're getting the original info from now?  Could be easier to get file UUID that way
    ret = []
    browse = storage_service.browse_location(backlog_uuid, original_path)

    # Add everything that is not a directory (ie that is a file)
    entries = [e for e in browse["entries"] if e not in browse["directories"]]
    for entry in entries:
        if entry not in ("processingMCP.xml"):
            path = os.path.join(original_path, entry)
            relative_path = (path.replace(DEFAULT_BACKLOG_PATH, "", 1),)
            try:
                file_info = storage_service.get_file_metadata(
                    relative_path=relative_path
                )[0]
            except storage_service.ResourceNotFound:
                logger.warning(
                    "No file information returned from the Storage Service for file at relative_path: %s",
                    relative_path,
                )
                raise
            file_uuid = file_info["fileuuid"]
            transfer_uuid = file_info["sipuuid"]
            ret.append(
                {
                    "original_path": path,
                    "arrange_path": os.path.join(arrange_path, entry),
                    "file_uuid": file_uuid,
                    "transfer_uuid": transfer_uuid,
                }
            )

    # Add directories and recurse, adding their children too
    for directory in browse["directories"]:
        original_dir = os.path.join(original_path, directory, "")
        arrange_dir = os.path.join(arrange_path, directory, "")
        # Don't fetch metadata or logs dirs
        # TODO only filter if the children of a SIP ie /arrange/sipname/metadata
        if directory not in ("metadata", "logs"):
            ret.append(
                {
                    "original_path": None,
                    "arrange_path": arrange_dir,
                    "file_uuid": None,
                    "transfer_uuid": None,
                }
            )
            ret.extend(
                _get_arrange_directory_tree(backlog_uuid, original_dir, arrange_dir)
            )

    return ret


def _copy_files_to_arrange(
    sourcepath, destination, fetch_children=False, backlog_uuid=None
):
    sourcepath = sourcepath.lstrip("/")  # starts with 'originals/', not '/originals/'
    # Insert each file into the DB

    # Lots of error checking:
    if not sourcepath or not destination:
        raise ValueError(_("GET parameter 'filepath' or 'destination' was blank."))
    if not destination.startswith(DEFAULT_ARRANGE_PATH):
        raise ValueError(
            _("%(path)s must be in arrange directory.") % {"path": destination}
        )

    try:
        leaf_dir = sourcepath.split("/")[-2]
    except IndexError:
        leaf_dir = ""
    # Files cannot go into the top level folder,
    # and neither can the "objects" directory
    if destination == DEFAULT_ARRANGE_PATH and not (
        sourcepath.endswith("/") or leaf_dir == "objects"
    ):
        raise ValueError(
            _("%(path1)s must go in a SIP, cannot be dropped onto %(path2)s")
            % {"path1": sourcepath, "path2": DEFAULT_ARRANGE_PATH}
        )

    # Create new SIPArrange entry for each object being copied over
    if not backlog_uuid:
        backlog_uuid = storage_service.get_first_location(purpose="BL")["uuid"]
    to_add = []

    # Construct the base arrange_path differently for files vs folders
    if sourcepath.endswith("/"):
        # If dragging objects/ folder, actually move the contents of (not
        # the folder itself)
        if leaf_dir == "objects":
            arrange_path = os.path.join(destination, "")
        else:
            # Strip UUID from transfer name
            uuid_regex = r"-[\w]{8}(-[\w]{4}){3}-[\w]{12}$"
            leaf_dir = re.sub(uuid_regex, "", leaf_dir)
            arrange_path = os.path.join(destination, leaf_dir) + "/"
            to_add.append(
                {
                    "original_path": None,
                    "arrange_path": arrange_path,
                    "file_uuid": None,
                    "transfer_uuid": None,
                }
            )
        if fetch_children:
            try:
                to_add.extend(
                    _get_arrange_directory_tree(backlog_uuid, sourcepath, arrange_path)
                )
            except storage_service.ResourceNotFound as e:
                raise ValueError(
                    _("Storage Service failed with the message: %(messsage)s")
                    % {"message": str(e)}
                )
    else:
        if destination.endswith("/"):
            arrange_path = os.path.join(destination, os.path.basename(sourcepath))
        else:
            arrange_path = destination
        relative_path = sourcepath.replace(DEFAULT_BACKLOG_PATH, "", 1)
        try:
            file_info = storage_service.get_file_metadata(relative_path=relative_path)[
                0
            ]
        except storage_service.ResourceNotFound:
            raise ValueError(
                _(
                    "No file information returned from the Storage Service for file at relative_path: %(path)s"
                )
                % {"path": relative_path}
            )
        file_uuid = file_info.get("fileuuid")
        transfer_uuid = file_info.get("sipuuid")
        to_add.append(
            {
                "original_path": sourcepath,
                "arrange_path": arrange_path,
                "file_uuid": file_uuid,
                "transfer_uuid": transfer_uuid,
            }
        )

    logger.info("arrange_path: %s", arrange_path)
    logger.debug("files to be added: %s", to_add)

    return to_add


def copy_to_arrange(request, sources=None, destinations=None, fetch_children=False):
    """
    Add files to in-progress SIPs being arranged.

    Files being copied can be located in either the backlog or in another SIP being arranged.

    If sources or destinations are strs not a list, they will be converted into a list and fetch_children will be set to True.

    :param list sources: List of paths relative to this pipelines backlog. If None, will look for filepath[] or filepath
    :param list destinations: List of paths within arrange folder. All paths should start with DEFAULT_ARRANGE_PATH
    :param bool fetch_children: If True, will fetch all children of the provided path(s) to copy to the destination.
    """
    if isinstance(sources, six.string_types) or isinstance(
        destinations, six.string_types
    ):
        fetch_children = True
        sources = [sources]
        destinations = [destinations]

    if sources is None or destinations is None:
        # List of sources & destinations
        if "filepath[]" in request.POST or "destination[]" in request.POST:
            sources = list(
                map(b64decode_string, request.POST.getlist("filepath[]", []))
            )
            destinations = list(
                map(b64decode_string, request.POST.getlist("destination[]", []))
            )
        # Single path representing tree
        else:
            fetch_children = True
            sources = [b64decode_string(request.POST.get("filepath", ""))]
            destinations = [b64decode_string(request.POST.get("destination", ""))]
    logger.info("sources: %s", sources)
    logger.info("destinations: %s", destinations)

    # The DEFAULT_BACKLOG_PATH constant is missing a leading slash for
    # historical reasons; TODO change this at some point.
    # External paths passed into these views are in the format
    # /originals/, whereas copy_from_arrange_to_completed constructs
    # paths without a leading slash as an implementation detail
    # (to communicate with the Storage Service).
    # Possibly the constant used to refer to externally-constructed
    # paths and the one used solely internally should be two different
    # constants.
    if sources[0].startswith("/" + DEFAULT_BACKLOG_PATH):
        action = "copy"
        backlog_uuid = storage_service.get_first_location(purpose="BL")["uuid"]
    elif sources[0].startswith(DEFAULT_ARRANGE_PATH):
        action = "move"
    else:
        logger.error(
            "Filepath %s is not in base backlog path nor arrange path", sources[0]
        )
        return helpers.json_response(
            {
                "error": True,
                "message": _("%(path)s is not in base backlog path nor arrange path")
                % {"path": sources[0]},
            }
        )

    entries_to_copy = []
    try:
        for source, dest in zip(sources, destinations):
            if action == "copy":
                entries = _copy_files_to_arrange(
                    source,
                    dest,
                    fetch_children=fetch_children,
                    backlog_uuid=backlog_uuid,
                )
                for entry in entries:
                    entries_to_copy.append(
                        models.SIPArrange(
                            original_path=entry["original_path"],
                            arrange_path=entry["arrange_path"],
                            file_uuid=entry["file_uuid"],
                            transfer_uuid=entry["transfer_uuid"],
                        )
                    )
            elif action == "move":
                _move_files_within_arrange(source, dest)
                response = {"message": _("SIP files successfully moved.")}
                status_code = 200
        if entries_to_copy:
            models.SIPArrange.create_many(entries_to_copy)
    except ValueError as e:
        logger.exception("Failed copying %s to %s", source, dest)
        response = {"message": str(e), "error": True}
        status_code = 400
    else:
        response = {"message": _("Files added to the SIP.")}
        status_code = 201

    return helpers.json_response(response, status_code=status_code)


def copy_metadata_files(request):
    """
    Copy files from list `source_paths` to sip_uuid's metadata folder.

    sip_uuid: UUID of the SIP to put files in
    paths: List of files to be copied, base64 encoded, in the format
        'source_location_uuid:full_path'
    """
    sip_uuid = request.POST.get("sip_uuid")
    paths = request.POST.getlist("source_paths[]")
    if not sip_uuid or not paths:
        response = {
            "error": True,
            "message": "sip_uuid and source_paths[] both required.",
        }
        return helpers.json_response(response, status_code=400)

    paths = [b64decode_string(p) for p in paths]
    sip = models.SIP.objects.get(uuid=sip_uuid)
    relative_path = sip.currentpath.replace("%sharedPath%", "", 1)
    relative_path = os.path.join(relative_path, "metadata")

    error, message = _copy_from_transfer_sources(paths, relative_path)

    if not error:
        message = _("Metadata files added successfully.")
        status_code = 201
    else:
        status_code = 500
    response = {"error": error, "message": message}

    return helpers.json_response(response, status_code=status_code)


def _copy_from_transfer_sources(paths, relative_destination):
    """
    Helper to copy files from transfer source locations to the currently processing location.

    Any files in locations not associated with this pipeline will be ignored.

    :param list paths: List of paths.  Each path should be formatted <uuid of location>:<full path in location>
    :param str relative_destination: Path relative to the currently processing space to move the files to.
    :returns: Tuple of (boolean error, message)
    """
    processing_location = storage_service.get_first_location(purpose="CP")
    transfer_sources = storage_service.get_location(purpose="TS")
    files = {ts["uuid"]: {"location": ts, "files": []} for ts in transfer_sources}

    for p in paths:
        try:
            location, path = p.split(":", 1)
        except ValueError:
            logger.warning("Path %s cannot be split into location:path", p)
            return True, "Path" + p + "cannot be split into location:path"
        if location not in files:
            logger.warning(
                "Location %s is not associated with this pipeline.", location
            )
            return (
                True,
                _("Location %(location)s is not associated with this pipeline")
                % {"location": location},
            )

        # ``path`` will be a UTF-8 bytestring but the replacement pattern path
        # from ``files`` will be a Unicode object. Therefore, the latter must
        # be UTF-8 encoded prior. Same reasoning applies to ``destination``
        # below. This allows transfers to be started on UTF-8-encoded directory
        # names.
        source = path.replace(
            files[location]["location"]["path"].encode("utf8"), "", 1
        ).lstrip("/")
        # Use the last segment of the path for the destination - basename for a
        # file, or the last folder if not. Keep the trailing / for folders.
        last_segment = (
            os.path.basename(source.rstrip("/")) + "/"
            if source.endswith("/")
            else os.path.basename(source)
        )
        destination = os.path.join(
            processing_location["path"].encode("utf8"),
            relative_destination,
            last_segment,
        ).replace("%sharedPath%", "")
        files[location]["files"].append({"source": source, "destination": destination})
        logger.debug("source: %s, destination: %s", source, destination)

    message = []
    for pl in files.values():
        reply, error = storage_service.copy_files(
            pl["location"], processing_location, pl["files"]
        )
        if reply is None:
            message.append(str(error))
    if message:
        return (
            True,
            _("The following errors occured: %(message)s")
            % {"message": ", ".join(message)},
        )
    else:
        return False, _("Files added successfully.")


def download_ss(request):
    filepath = b64decode_string(request.GET.get("filepath", "")).lstrip("/")
    logger.info("download filepath: %s", filepath)
    if not filepath.startswith(DEFAULT_BACKLOG_PATH):
        return django.http.HttpResponseBadRequest()
    filepath = filepath.replace(DEFAULT_BACKLOG_PATH, "", 1)

    # Get UUID
    uuid_regex = r"[\w]{8}(-[\w]{4}){3}-[\w]{12}"
    transfer_uuid = re.search(uuid_regex, filepath).group()

    # Get relative path
    # Find first /, should be at the end of the transfer name/uuid, rest is relative ptah
    relative_path = filepath[filepath.find("/") + 1 :]

    redirect_url = storage_service.extract_file_url(transfer_uuid, relative_path)
    return helpers.stream_file_from_storage_service(
        redirect_url, "Storage service returned {}; check logs?"
    )


def download_fs(request):
    shared_dir = os.path.realpath(django_settings.SHARED_DIRECTORY)
    filepath = b64decode_string(request.GET.get("filepath", ""))
    requested_filepath = os.path.realpath("/" + filepath)

    # respond with 404 if a non-Archivematica file is requested
    try:
        if requested_filepath.index(shared_dir) == 0:
            return helpers.send_file(request, requested_filepath)
        else:
            raise django.http.Http404
    except ValueError:
        raise django.http.Http404


def preview_by_uuid(request, uuid):
    """Simple wrapper to the download_by_uuid function to create a route
    through the code to enable the preview of a file in the browser, not
    automatically download.
    """
    return download_by_uuid(request, uuid, preview_file=True)


def download_by_uuid(request, uuid, preview_file=False):
    """Download a transfer file, given its UUID.

    If the file is available on the pipeline local filesystem, this view will
    stream it directly from disk. In setups with a remote Storage Service, this
    prevents needing to rsync the entire transfer to the Storage Service and
    unpack it to stream a single file.

    If the requested file is not available on disk, this view will stream it
    directly from the Storage Service. Unlike download_ss, this will work even
    if the Storage Service is not accessible to the requestor.

    It looks up the full relative path in the ``transferfiles`` search index.
    ``relative_path`` includes the ``data`` directory when the transfer package
    uses the BagIt format.

    Returns 404 if a file with the requested UUID cannot be found. Otherwise
    the status code is returned via the call to ``send_file`` or
    ``stream_file_from_storage_service`` as appropriate.

    ``preview_file`` is an instruction to be applied to the response headers
    to enable the file to be seen inside the browser if it is capable of being
    rendered. On receiving this instruction, the content-disposition header
    will be set in the stream_file_from_storage_service to 'inline'.
    """
    not_found_err = helpers.json_response(
        {
            "success": False,
            "message": _("File with UUID %(uuid)s " "could not be found")
            % {"uuid": uuid},
        },
        status_code=404,
    )

    try:
        record = elasticSearchFunctions.get_transfer_file_info(
            elasticSearchFunctions.get_client(), "fileuuid", uuid
        )
    except elasticSearchFunctions.ElasticsearchError:
        return not_found_err

    try:
        transfer_id, relpath = record["sipuuid"], record["relative_path"]
    except KeyError:
        logger.debug("Search document is missing required parameters")
        return not_found_err

    try:
        backlog = storage_service.get_first_location(purpose="BL")
    except storage_service.ResourceNotFound:
        logger.debug("No backlog location associated with this pipeline")
        return not_found_err

    file_abspath = os.path.join(backlog["path"], "originals", relpath)
    if os.path.exists(file_abspath):
        download_file = not preview_file
        return helpers.send_file(request, file_abspath, download_file)

    # Prepare relative path in format expected by Storage Service API.
    # E.g. from "<name>-<uuid>/data/objects/bird.mp3" we only need the path
    # component not including transfer name or UUID.
    try:
        relpath = relpath.split("/", 1)[1]
    except IndexError:
        logger.debug(
            "Relative path in search document has an unexpected form: %s", relpath
        )
        return not_found_err

    redirect_url = storage_service.extract_file_url(transfer_id, relpath)
    return helpers.stream_file_from_storage_service(
        redirect_url, "Storage service returned {}; check logs?", preview_file
    )
