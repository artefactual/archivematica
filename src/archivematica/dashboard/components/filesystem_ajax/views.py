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
import logging
import os
import re
import shutil
import tempfile
import uuid

import django.http
import django.template.defaultfilters
from django.conf import settings as django_settings
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

import archivematica.dashboard.components.filesystem_ajax.helpers as filesystem_ajax_helpers
from archivematica.archivematicaCommon import storageService as storage_service
from archivematica.archivematicaCommon.archivematicaFunctions import b64decode_string
from archivematica.archivematicaCommon.archivematicaFunctions import b64encode_string
from archivematica.dashboard.components import helpers
from archivematica.dashboard.main import models

logger = logging.getLogger("archivematica.dashboard")

SHARED_DIRECTORY_ROOT = django_settings.SHARED_DIRECTORY
ACTIVE_TRANSFER_DIR = os.path.join(
    SHARED_DIRECTORY_ROOT, "watchedDirectories", "activeTransfers"
)

DEFAULT_BACKLOG_PATH = "originals/"

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
                prop["display_string"] = ngettext(
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
        try:
            destination = _copy_to_start_transfer(
                filepath=filepath,
                type=transfer_type,
                accession=accession,
                access_id=access_id,
                transfer_metadata_set_row_uuid=row_id,
            )
        except Exception as e:
            logger.exception(f"Error starting transfer {filepath}: {e}")
            raise Exception(f"Error starting transfer {filepath}: {e}")

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
            ACTIVE_TRANSFER_DIR, type_subdir, f"{basename}-{temp_uuid}"
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
    sip_path = sip.currentpath.replace("%sharedPath%", "", 1)
    metadata_directory_path = os.path.join(sip_path, sip.get_metadata_directory_path())

    error, message = _copy_from_transfer_sources(paths, metadata_directory_path)

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
        source = path.replace(str(files[location]["location"]["path"]), "", 1).lstrip(
            "/"
        )
        # Use the last segment of the path for the destination - basename for a
        # file, or the last folder if not. Keep the trailing / for folders.
        last_segment = (
            os.path.basename(source.rstrip("/")) + "/"
            if source.endswith("/")
            else os.path.basename(source)
        )
        destination = os.path.join(
            str(processing_location["path"]),
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
