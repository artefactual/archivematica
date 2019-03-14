"""Package management."""

# This file is part of Archivematica.
#
# Copyright 2010-2018 Artefactual Systems Inc. <http://artefactual.com>
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

import collections
import logging
import os
import shutil
from tempfile import mkdtemp
from uuid import uuid4

from django.conf import settings as django_settings

from archivematicaFunctions import unicodeToStr
from databaseFunctions import auto_close_db
from executor import Executor
from jobChain import jobChain
from main.models import Transfer, TransferMetadataSet
import storageService as storage_service
from unitTransfer import unitTransfer


logger = logging.getLogger("archivematica.mcp.server")


StartingPoint = collections.namedtuple("StartingPoint", "watched_dir chain link")

# Each package type has its corresponding watched directory and its
# associated chain, e.g. a "standard" transfer triggers the chain with UUID
# "fffd5342-2337-463f-857a-b2c8c3778c6d". This is stored in the
# WatchedDirectory model. These starting chains all have in common that they
# prompt the user to Accept/Reject the transfer.
#
# In this module we don't want to prompt the user. Instead we want to jump
# directly into action, this is whatever happens when the transfer is
# accepted. The following dictionary points to the chains and links where
# this is happening. Presumably this could be written in a generic way querying
# the workflow data but in the first iteraiton we've decided to do it this way.
# There is also the hope that the watched directories can be deprecated in the
# near future.
PACKAGE_TYPE_STARTING_POINTS = {
    "standard": StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY, "activeTransfers/standardTransfer"
        ),
        chain="6953950b-c101-4f4c-a0c3-0cd0684afe5e",
        link="045c43ae-d6cf-44f7-97d6-c8a602748565",
    ),
    "unzipped bag": StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY, "activeTransfers/baggitDirectory"
        ),
        chain="c75ef451-2040-4511-95ac-3baa0f019b48",
        link="154dd501-a344-45a9-97e3-b30093da35f5",
    ),
    "zipped bag": StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY, "activeTransfers/baggitZippedDirectory"
        ),
        chain="167dc382-4ab1-4051-8e22-e7f1c1bf3e6f",
        link="3229e01f-adf3-4294-85f7-4acb01b3fbcf",
    ),
    "dspace": StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY, "activeTransfers/Dspace"
        ),
        chain="1cb2ef0e-afe8-45b5-8d8f-a1e120f06605",
        link="bda96b35-48c7-44fc-9c9e-d7c5a05016c1",
    ),
    "maildir": StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY, "activeTransfers/maildir"
        ),
        chain="d381cf76-9313-415f-98a1-55c91e4d78e0",
        link="da2d650e-8ce3-4b9a-ac97-8ca4744b019f",
    ),
    "TRIM": StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY, "activeTransfers/TRIM"
        ),
        chain="e4a59e3e-3dba-4eb5-9cf1-c1fb3ae61fa9",
        link="2483c25a-ade8-4566-a259-c6c37350d0d6",
    ),
    "dataverse": StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY, "activeTransfers/dataverseTransfer"
        ),
        # Approve Dataverse Transfer Chain
        chain="10c00bc8-8fc2-419f-b593-cf5518695186",
        # Chain link setting transfer-type: Dataverse
        link="0af6b163-5455-4a76-978b-e35cc9ee445f",
    ),
}


def get_approve_transfer_chain_id(transfer_type):
    """Return chain ID to approve a transfer given its type."""
    try:
        item = PACKAGE_TYPE_STARTING_POINTS[transfer_type]
    except KeyError:
        raise ValueError("Unknown transfer type")
    return item.chain


def _file_is_an_archive(filepath):
    filepath = filepath.lower()
    return (
        filepath.endswith(".zip")
        or filepath.endswith(".tgz")
        or filepath.endswith(".tar.gz")
    )


def _pad_destination_filepath_if_it_already_exists(filepath, original=None, attempt=0):
    if original is None:
        original = filepath
    attempt = attempt + 1
    if not os.path.exists(filepath):
        return filepath
    if os.path.isdir(filepath):
        return _pad_destination_filepath_if_it_already_exists(
            original + "_" + str(attempt), original, attempt
        )
    # need to work out basename
    basedirectory = os.path.dirname(original)
    basename = os.path.basename(original)
    # do more complex padding to preserve file extension
    period_position = basename.index(".")
    non_extension = basename[0:period_position]
    extension = basename[period_position:]
    new_basename = "{}_{}{}".format(non_extension, attempt, extension)
    new_filepath = os.path.join(basedirectory, new_basename)
    return _pad_destination_filepath_if_it_already_exists(
        new_filepath, original, attempt
    )


def _check_filepath_exists(filepath):
    if filepath == "":
        return "No filepath provided."
    if not os.path.exists(filepath):
        return "Filepath {} does not exist.".format(filepath)
    if ".." in filepath:  # check for trickery
        return "Illegal path."
    return None


_default_location_uuid = None


def _default_transfer_source_location_uuid():
    global _default_location_uuid
    if _default_location_uuid is not None:
        return _default_location_uuid
    location = storage_service.get_default_location("TS")
    _default_location_uuid = location["uuid"]
    return _default_location_uuid


def _copy_from_transfer_sources(paths, relative_destination):
    """Copy files from source locations to the currently processing location.

    Any files in locations not associated with this pipeline will be ignored.

    :param list paths: List of paths. Each path should be formatted
                       <uuid of location>:<full path in location>
    :param str relative_destination: Path relative to the currently processing
                                     space to move the files to.
    """
    processing_location = storage_service.get_location(purpose="CP")[0]
    transfer_sources = storage_service.get_location(purpose="TS")
    files = {l["uuid"]: {"location": l, "files": []} for l in transfer_sources}

    for item in paths:
        location, path = Path(item).parts()
        if location is None:
            location = _default_transfer_source_location_uuid()
        if location not in files:
            raise Exception(
                "Location %(location)s is not associated"
                " with this pipeline" % {"location": location}
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
    for item in files.values():
        reply, error = storage_service.copy_files(
            item["location"], processing_location, item["files"]
        )
        if reply is None:
            message.append(str(error))
    if message:
        raise Exception(
            "The following errors occured: %(message)s"
            % {"message": ", ".join(message)}
        )


def _move_to_internal_shared_dir(filepath, dest, transfer):
    """Move package to an internal Archivematica directory.

    The side effect of this function is to update the transfer object with the
    final location. This is important so other components can continue the
    processing. When relying on watched directories to start a transfer (see
    _start_package_transfer), this also matters because unitTransfer is going
    to look up the object in the database based on the location.
    """
    error = _check_filepath_exists(filepath)
    if error:
        raise Exception(error)
    # Confine destination to subdir of originals.
    basename = os.path.basename(filepath)
    dest = _pad_destination_filepath_if_it_already_exists(os.path.join(dest, basename))
    # Ensure directories end with a trailing slash.
    if os.path.isdir(filepath):
        dest = os.path.join(dest, "")
    try:
        shutil.move(filepath, dest)
    except (OSError, shutil.Error) as e:
        raise Exception("Error moving from %s to %s (%s)", filepath, dest, e)
    else:
        transfer.currentlocation = dest.replace(
            django_settings.SHARED_DIRECTORY, "%sharedPath%", 1
        )
        transfer.save()


def create_package(
    name,
    type_,
    accession,
    access_system_id,
    path,
    metadata_set_id,
    user_id,
    workflow,
    auto_approve=True,
    wait_until_complete=False,
    processing_config=None,
):
    """Launch transfer and return its object immediately.

    ``auto_approve`` changes significantly the way that the transfer is
    initiated. See ``_start_package_transfer_with_auto_approval`` and
    ``_start_package_transfer`` for more details.
    """
    if not name:
        raise ValueError("No transfer name provided.")
    name = unicodeToStr(name)
    if type_ is None or type_ == "disk image":
        type_ = "standard"
    if type_ not in PACKAGE_TYPE_STARTING_POINTS:
        raise ValueError("Unexpected type of package provided '{}'".format(type_))
    if not path:
        raise ValueError("No path provided.")
    if isinstance(auto_approve, bool) is False:
        raise ValueError("Unexpected value in auto_approve parameter")
    try:
        int(user_id)
    except (TypeError, ValueError):
        raise ValueError("Unexpected value in user_id parameter")

    # Create Transfer object.
    kwargs = {"uuid": str(uuid4())}
    if accession is not None:
        kwargs["accessionid"] = unicodeToStr(accession)
    if access_system_id is not None:
        kwargs["access_system_id"] = unicodeToStr(access_system_id)
    if metadata_set_id is not None:
        try:
            kwargs["transfermetadatasetrow"] = TransferMetadataSet.objects.get(
                id=metadata_set_id
            )
        except TransferMetadataSet.DoesNotExist:
            pass
    transfer = Transfer.objects.create(**kwargs)
    transfer.update_active_agent(user_id)
    logger.debug("Transfer object created: %s", transfer.pk)

    @auto_close_db
    def _start(transfer, name, type_, path):
        # TODO: use tempfile.TemporaryDirectory as a context manager in Py3.
        tmpdir = mkdtemp(dir=os.path.join(django_settings.SHARED_DIRECTORY, "tmp"))
        starting_point = PACKAGE_TYPE_STARTING_POINTS.get(type_)
        logger.debug(
            "Package %s: starting transfer (%s)",
            transfer.pk,
            (name, type_, path, tmpdir),
        )
        try:
            params = (transfer, name, path, tmpdir, starting_point, processing_config)
            if auto_approve:
                params = params + (workflow,)
                _start_package_transfer_with_auto_approval(*params)
            else:
                _start_package_transfer(*params)
        finally:
            os.chmod(tmpdir, 0o770)  # Needs to be writeable by the SS.

    getattr(Executor, "apply" if wait_until_complete else "apply_async")(
        _start, (transfer, name, type_, path)
    )

    return transfer


def _capture_transfer_failure(fn):
    """Detect errors during transfer/ingest."""

    def wrap(*args, **kwargs):
        try:
            # Our decorated function isn't expected to return anything.
            fn(*args, **kwargs)
        except Exception as err:
            # The main purpose of this decorator is to update the Transfer with
            # the new state (fail). If the Transfer does not exist we give up.
            if isinstance(err, Transfer.DoesNotExist):
                raise
        else:
            # No exceptions!
            return
        # At this point we know that the transfer has failed and we want to do
        # our best effort to update the state without further interruptions.
        try:
            pass
            #
            # TODO: update state once we have a FSM.
            # transfer = args[0]
            #
        except Exception:
            pass
        # Finally raised the exception and log it.
        try:
            logger.exception("Exception: %s", err, exc_info=True)
        except NameError:
            pass

    return wrap


def _determine_transfer_paths(name, path, tmpdir):
    if _file_is_an_archive(path):
        transfer_dir = tmpdir
        p = Path(path).path
        filepath = os.path.join(tmpdir, os.path.basename(p))
    else:
        path = os.path.join(path, ".")  # Copy contents of dir but not dir
        transfer_dir = filepath = os.path.join(tmpdir, name)
    return (
        transfer_dir.replace(django_settings.SHARED_DIRECTORY, "", 1),
        unicodeToStr(filepath),
        path,
    )


@_capture_transfer_failure
def _start_package_transfer_with_auto_approval(
    transfer, name, path, tmpdir, starting_point, processing_config, workflow
):
    """Start a new transfer the new way.

    This method does not rely on the activeTransfer watched directory. It
    blocks until the process completes. It does not prompt the user to accept
    the transfer because we go directly into the next chain link.
    """
    transfer_rel, filepath, path = _determine_transfer_paths(name, path, tmpdir)
    logger.debug(
        "Package %s: determined vars" " transfer_rel=%s, filepath=%s, path=%s",
        transfer.pk,
        transfer_rel,
        filepath,
        path,
    )

    logger.debug(
        "Package %s: copying chosen contents from transfer sources" " (from=%s, to=%s)",
        transfer.pk,
        path,
        transfer_rel,
    )
    _copy_from_transfer_sources([path], transfer_rel)

    _copy_processing_config(processing_config, transfer.pk, transfer_rel)

    logger.debug("Package %s: moving package to processing directory", transfer.pk)
    _move_to_internal_shared_dir(
        filepath, django_settings.PROCESSING_DIRECTORY, transfer
    )

    logger.debug("Package %s: starting workflow processing", transfer.pk)
    unit = unitTransfer(path, transfer.pk)
    jobChain(
        unit,
        workflow.get_chain(starting_point.chain),
        workflow,
        workflow.get_link(starting_point.link),
    )


@_capture_transfer_failure
def _start_package_transfer(
    transfer, name, path, tmpdir, starting_point, processing_config
):
    """Start a new transfer the old way.

    This means copying the transfer into one of the standard watched dirs.
    MCPServer will continue the processing and prompt the user once the
    contents in the watched directory are detected by the watched directory
    observer.
    """
    transfer_rel, filepath, path = _determine_transfer_paths(name, path, tmpdir)
    logger.debug(
        "Package %s: determined vars" " transfer_rel=%s, filepath=%s, path=%s",
        transfer.pk,
        transfer_rel,
        filepath,
        path,
    )

    logger.debug(
        "Package %s: copying chosen contents from transfer sources" " (from=%s, to=%s)",
        transfer.pk,
        path,
        transfer_rel,
    )
    _copy_from_transfer_sources([path], transfer_rel)

    _copy_processing_config(processing_config, transfer.pk, transfer_rel)

    logger.debug(
        "Package %s: moving package to activeTransfers dir (from=%s," " to=%s)",
        transfer.pk,
        filepath,
        starting_point.watched_dir,
    )
    _move_to_internal_shared_dir(filepath, starting_point.watched_dir, transfer)


def _copy_processing_config(processing_config, transfer_pk, transfer_rel):
    if processing_config is None:
        return
    src = os.path.join(
        django_settings.SHARED_DIRECTORY,
        "sharedMicroServiceTasksConfigs/processingMCPConfigs",
        "%sProcessingMCP.xml" % processing_config,
    )
    dest = os.path.join(
        django_settings.SHARED_DIRECTORY, transfer_rel, "processingMCP.xml"
    )
    logger.debug(
        "Package %s: copying processing configuration" " (from=%s to=%s)",
        transfer_pk,
        src,
        dest,
    )
    try:
        shutil.copyfile(src, dest)
    except IOError as err:
        logger.warning(
            "Package %s: processing configuration could not"
            " be copied: (from=%s to=%s) - %s",
            transfer_pk,
            src,
            dest,
            err,
        )


class Path(object):
    """Path wraps a path that is a pair of two values: UUID and path."""

    uuid, path = None, None

    def __init__(self, path, sep=":"):
        self.sep = sep
        parts = path.partition(self.sep)
        if parts[1] != self.sep:
            self.path = parts[0]
        else:
            self.uuid = parts[0]
            self.path = parts[2]

    def __repr__(self):
        return "%s (uuid=%r, sep=%r, path=%r)" % (
            self.__class__,
            self.uuid,
            self.sep,
            self.path,
        )

    def parts(self):
        return self.uuid, self.path
