"""Package management."""

import abc
import collections
import functools
import json
import logging
import os
from datetime import timedelta
from tempfile import mkdtemp
from uuid import UUID
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

import archivematica.archivematicaCommon.storageService as storage_service
from archivematica.archivematicaCommon.dbconns import auto_close_old_connections
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    TransferSourceRetrievalError,
)
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    copy_transfer_source_files,
)
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    move_to_internal_shared_dir,
)
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    plan_transfer_source_paths,
)
from archivematica.dashboard.main import idempotency
from archivematica.dashboard.main import models
from archivematica.MCPServer.server.jobs import JobChain
from archivematica.MCPServer.server.processing_config import (
    processing_configuration_file_exists,
)
from archivematica.MCPServer.server.utils import uuid_from_path

logger = logging.getLogger("archivematica.mcp.server.packages")


StartingPoint = collections.namedtuple("StartingPoint", "watched_dir chain link")

# API-created transfers enter this chain before their type-specific workflow.
RETRIEVE_TRANSFER_SOURCE_CHAIN_ID = "2e12b4bd-06f1-4362-905f-ef9ce5f7cd5d"
# The unit variable stores the type-specific link selected after retrieval.
LINK_AFTER_TRANSFER_SOURCE_RETRIEVAL = "linkAfterTransferSourceRetrieval"
PACKAGE_CREATE_OPERATION = "package.create"


def _get_setting(name):
    """Retrieve a Django setting decoded as a unicode string."""
    return getattr(settings, name)


def _shared_path_location(path):
    """Return a shared-directory path in the database location form."""
    shared_directory = _get_setting("SHARED_DIRECTORY")
    if not shared_directory.endswith(os.sep):
        shared_directory = f"{shared_directory}{os.sep}"
    return path.replace(shared_directory, r"%sharedPath%", 1)


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
# the workflow data but in the first iteration we've decided to do it this way.
# There is also the hope that the watched directories can be deprecated in the
# near future.
PACKAGE_TYPE_STARTING_POINTS = {
    "standard": StartingPoint(
        watched_dir=os.path.join(
            _get_setting("WATCH_DIRECTORY"), "activeTransfers/standardTransfer"
        ),
        chain="6953950b-c101-4f4c-a0c3-0cd0684afe5e",
        link="045c43ae-d6cf-44f7-97d6-c8a602748565",
    ),
    "zipfile": StartingPoint(
        watched_dir=os.path.join(
            settings.WATCH_DIRECTORY, "activeTransfers/zippedDirectory"
        ),
        chain="f3caceff-5ad5-4bad-b98c-e73f8cd03450",
        link="541f5994-73b0-45bb-9cb5-367c06a21be7",
    ),
    "unzipped bag": StartingPoint(
        watched_dir=os.path.join(
            _get_setting("WATCH_DIRECTORY"), "activeTransfers/baggitDirectory"
        ),
        chain="c75ef451-2040-4511-95ac-3baa0f019b48",
        link="154dd501-a344-45a9-97e3-b30093da35f5",
    ),
    "zipped bag": StartingPoint(
        watched_dir=os.path.join(
            _get_setting("WATCH_DIRECTORY"), "activeTransfers/baggitZippedDirectory"
        ),
        chain="167dc382-4ab1-4051-8e22-e7f1c1bf3e6f",
        link="3229e01f-adf3-4294-85f7-4acb01b3fbcf",
    ),
    "dspace": StartingPoint(
        watched_dir=os.path.join(
            _get_setting("WATCH_DIRECTORY"), "activeTransfers/Dspace"
        ),
        chain="1cb2ef0e-afe8-45b5-8d8f-a1e120f06605",
        link="bda96b35-48c7-44fc-9c9e-d7c5a05016c1",
    ),
    "maildir": StartingPoint(
        watched_dir=os.path.join(
            _get_setting("WATCH_DIRECTORY"), "activeTransfers/maildir"
        ),
        chain="d381cf76-9313-415f-98a1-55c91e4d78e0",
        link="da2d650e-8ce3-4b9a-ac97-8ca4744b019f",
    ),
    "TRIM": StartingPoint(
        watched_dir=os.path.join(
            _get_setting("WATCH_DIRECTORY"), "activeTransfers/TRIM"
        ),
        chain="e4a59e3e-3dba-4eb5-9cf1-c1fb3ae61fa9",
        link="2483c25a-ade8-4566-a259-c6c37350d0d6",
    ),
    "dataverse": StartingPoint(
        watched_dir=os.path.join(
            _get_setting("WATCH_DIRECTORY"), "activeTransfers/dataverseTransfer"
        ),
        # Approve Dataverse Transfer Chain
        chain="10c00bc8-8fc2-419f-b593-cf5518695186",
        # Chain link setting transfer-type: Dataverse
        link="0af6b163-5455-4a76-978b-e35cc9ee445f",
    ),
}

BASE_REPLACEMENTS = {
    r"%tmpDirectory%": os.path.join(_get_setting("SHARED_DIRECTORY"), "tmp", ""),
    r"%processingDirectory%": _get_setting("PROCESSING_DIRECTORY"),
    r"%watchDirectoryPath%": _get_setting("WATCH_DIRECTORY"),
    r"%rejectedDirectory%": _get_setting("REJECTED_DIRECTORY"),
}


def get_approve_transfer_chain_id(transfer_type):
    """Return chain ID to approve a transfer given its type."""
    try:
        item = PACKAGE_TYPE_STARTING_POINTS[transfer_type]
    except KeyError:
        raise ValueError("Unknown transfer type")
    return item.chain


_default_location_uuid = None


@auto_close_old_connections()
def _default_transfer_source_location_uuid():
    global _default_location_uuid
    if _default_location_uuid is not None:
        return _default_location_uuid
    location = storage_service.get_default_location("TS")
    _default_location_uuid = location["uuid"]
    return _default_location_uuid


@auto_close_old_connections()
def _copy_from_transfer_sources(paths, relative_destination):
    """Copy files from source locations to the currently processing location.

    Any files in locations not associated with this pipeline will be ignored.

    :param list paths: List of paths. Each path should be formatted
                       <uuid of location>:<full path in location>
    :param str relative_destination: Path relative to the currently processing
                                     space to move the files to.
    """
    try:
        copy_transfer_source_files(
            paths,
            relative_destination,
            storage_service,
            default_location_uuid_factory=_default_transfer_source_location_uuid,
        )
    except TransferSourceRetrievalError as err:
        raise Exception(str(err))


@auto_close_old_connections()
def _move_to_internal_shared_dir(filepath, dest, transfer):
    """Move package to an internal Archivematica directory.

    The side effect of this function is to update the transfer object with the
    final location. This is important so other components can continue the
    processing. When relying on watched directories to start a transfer (see
    _start_package_transfer), this also matters because Transfer is going
    to look up the object in the database based on the location.
    """
    try:
        result = move_to_internal_shared_dir(
            filepath, dest, _get_setting("SHARED_DIRECTORY")
        )
    except TransferSourceRetrievalError as err:
        raise Exception(str(err))
    transfer.currentlocation = result.current_location
    transfer.save()


def _mark_transfer_failed(transfer: models.Transfer) -> None:
    """Record a terminal bootstrap failure before a workflow job may exist."""
    models.Transfer.objects.filter(pk=transfer.pk).update(
        status=models.PACKAGE_STATUS_FAILED,
        completed_at=timezone.now(),
    )


def _submission_fingerprint(
    *,
    name,
    type_,
    accession,
    access_system_id,
    path,
    metadata_set_id,
    auto_approve,
    processing_config,
):
    """Return a stable digest of the inputs that define a submission."""
    return idempotency.fingerprint(
        {
            "access_system_id": access_system_id,
            "accession": accession,
            "auto_approve": auto_approve,
            "metadata_set_id": metadata_set_id,
            "name": name,
            "path": path,
            "processing_config": processing_config,
            "type": type_,
        }
    )


def _create_transfer(
    *,
    accession,
    access_system_id,
    metadata_set,
    processing_config,
    user_id,
):
    kwargs = {"uuid": str(uuid4())}
    if accession is not None:
        kwargs["accessionid"] = accession
    if access_system_id is not None:
        kwargs["access_system_id"] = access_system_id
    if metadata_set is not None:
        kwargs["transfermetadatasetrow"] = metadata_set
    transfer = models.Transfer.objects.create(**kwargs)
    transfer.set_processing_configuration(processing_config)
    transfer.update_active_agent(user_id)
    logger.debug("Transfer object created: %s", transfer.pk)
    return transfer


@auto_close_old_connections()
def create_package(
    package_queue,
    executor,
    name,
    type_,
    accession,
    access_system_id,
    path,
    metadata_set_id,
    user_id,
    workflow,
    auto_approve=True,
    processing_config=None,
    idempotency_key=None,
):
    """Launch a transfer and return its accepted identity immediately.

    ``auto_approve`` changes significantly the way that the transfer is
    initiated. See ``_start_package_transfer_with_auto_approval`` and
    ``_start_package_transfer`` for more details. Unkeyed calls retain the
    historical ``Transfer`` return value; keyed calls return a stable UUID.
    """
    if not name:
        raise ValueError("No transfer name provided.")
    if type_ is None or type_ == "disk image":
        type_ = "standard"
    if type_ not in PACKAGE_TYPE_STARTING_POINTS:
        raise ValueError(f"Unexpected type of package provided '{type_}'")
    if not path:
        raise ValueError("No path provided.")
    if isinstance(auto_approve, bool) is False:
        raise ValueError("Unexpected value in auto_approve parameter")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise ValueError("Unexpected value in user_id parameter")
    if idempotency_key is not None and not idempotency.is_valid_key(idempotency_key):
        raise ValueError("Unexpected value in idempotency_key parameter")

    submission_fingerprint = None
    if idempotency_key is not None:
        submission_fingerprint = _submission_fingerprint(
            name=name,
            type_=type_,
            accession=accession,
            access_system_id=access_system_id,
            path=path,
            metadata_set_id=(
                str(metadata_set_id) if metadata_set_id is not None else None
            ),
            auto_approve=auto_approve,
            processing_config=processing_config,
        )

    metadata_set = None
    if metadata_set_id is not None:
        try:
            metadata_set = models.TransferMetadataSet.objects.get(id=metadata_set_id)
        except (models.TransferMetadataSet.DoesNotExist, ValidationError):
            pass
    if not processing_configuration_file_exists(processing_config):
        processing_config = "default"

    transfer_kwargs = {
        "accession": accession,
        "access_system_id": access_system_id,
        "metadata_set": metadata_set,
        "processing_config": processing_config,
        "user_id": user_id,
    }
    reservation = None
    if idempotency_key is None:
        transfer = _create_transfer(**transfer_kwargs)
        transfer_uuid = str(transfer.pk)
    else:
        reservation = idempotency.reserve_or_replay(
            user_id=user_id,
            operation=PACKAGE_CREATE_OPERATION,
            key=idempotency_key,
            request_fingerprint=submission_fingerprint,
            retention=timedelta(days=_get_setting("IDEMPOTENCY_KEY_RETENTION_DAYS")),
            create_result=lambda: {
                "id": str(_create_transfer(**transfer_kwargs).pk),
            },
        )
        transfer_uuid = reservation.result["id"]
        if not reservation.created:
            logger.info("Replaying transfer submission %s", transfer_uuid)
            return transfer_uuid
        transfer = models.Transfer.objects.get(pk=transfer_uuid)

    # TODO: Clean up this staging directory after successful transfer-source
    # retrieval. TemporaryDirectory cannot own it because retrieval is asynchronous.
    tmpdir = None
    try:
        tmpdir = mkdtemp(dir=os.path.join(_get_setting("SHARED_DIRECTORY"), "tmp"))
        starting_point = PACKAGE_TYPE_STARTING_POINTS.get(type_)
        logger.debug(
            "Package %s: starting transfer (%s)",
            transfer.pk,
            (name, type_, path, tmpdir),
        )
        params = (transfer, name, path, tmpdir, starting_point)
        if auto_approve:
            transfer.status = models.PACKAGE_STATUS_PROCESSING
            transfer.save(update_fields=["status"])
            params = params + (workflow, package_queue)
            result = executor.submit(
                _start_package_transfer_with_auto_approval, *params
            )
        else:
            result = executor.submit(_start_package_transfer, *params)
    except Exception:
        if auto_approve or idempotency_key is not None:
            if reservation is None:
                _mark_transfer_failed(transfer)
            else:
                try:
                    _mark_transfer_failed(transfer)
                except Exception:
                    logger.exception(
                        "Unable to mark transfer %s failed after handoff failure",
                        transfer_uuid,
                    )
        if tmpdir is not None:
            try:
                os.rmdir(tmpdir)
            except OSError:
                logger.warning(
                    "Unable to remove unused transfer staging directory %s",
                    tmpdir,
                    exc_info=True,
                )
        if reservation is not None:
            try:
                idempotency.release(reservation)
            except Exception:
                logger.exception(
                    "Unable to release the pending idempotency reservation "
                    "for transfer %s",
                    transfer_uuid,
                )
            logger.exception(
                "Transfer %s could not be handed off",
                transfer_uuid,
            )
        raise

    result.add_done_callback(lambda f: os.chmod(tmpdir, 0o770))

    if reservation is None:
        return transfer
    idempotency.complete(reservation)
    return transfer_uuid


def _capture_transfer_failure(fn=None, *, mark_transfer_failed=False):
    """Guard transfer-start worker connections and capture their failures."""

    def decorator(wrapped):
        @auto_close_old_connections()
        @functools.wraps(wrapped)
        def wrap(*args, **kwargs):
            try:
                return wrapped(*args, **kwargs)
            except Exception as err:
                if isinstance(err, (models.Transfer.DoesNotExist, ValidationError)):
                    raise

                logger.exception("Exception occurred during transfer processing")
                if (
                    mark_transfer_failed
                    and args
                    and isinstance(args[0], models.Transfer)
                ):
                    _mark_transfer_failed(args[0])

        return wrap

    if fn is None:
        return decorator
    return decorator(fn)


def _determine_transfer_paths(
    name: str, path: str, tmpdir: str
) -> tuple[str, str, str]:
    """Adapt the shared path plan to the legacy tuple used in this module."""
    plan = plan_transfer_source_paths(
        name, path, tmpdir, _get_setting("SHARED_DIRECTORY")
    )
    return plan.copy_destination_relative, plan.copied_path, plan.copy_source


@_capture_transfer_failure(mark_transfer_failed=True)
def _start_package_transfer_with_auto_approval(
    transfer, name, path, tmpdir, starting_point, workflow, package_queue
):
    """Queue retrieval before continuing at the accepted-transfer workflow.

    No transfer content exists yet. This bootstrap only persists the planned
    staging path and queues the API-only retrieval chain; MCPClient performs
    the Storage Service and filesystem work.
    """
    transfer_rel, filepath, path = _determine_transfer_paths(name, path, tmpdir)
    logger.debug(
        "Package %s: determined vars transfer_rel=%s, filepath=%s, path=%s",
        transfer.pk,
        transfer_rel,
        filepath,
        path,
    )

    logger.debug(
        "Package %s: scheduling transfer-source retrieval (from=%s, to=%s)",
        transfer.pk,
        path,
        transfer_rel,
    )
    currentlocation = _shared_path_location(filepath)
    transfer.currentlocation = currentlocation
    transfer.save(update_fields=["currentlocation"])
    unit = Transfer(filepath, transfer.pk)
    unit.mark_as_processing()
    unit.set_variable(
        LINK_AFTER_TRANSFER_SOURCE_RETRIEVAL,
        None,
        starting_point.link,
    )
    job_chain = JobChain(
        unit,
        workflow.get_chain(RETRIEVE_TRANSFER_SOURCE_CHAIN_ID),
        workflow,
    )
    job_chain.context.update(
        {
            r"%transferSourcePath%": path,
            r"%transferSourceDestination%": transfer_rel,
            r"%transferSourceCopiedPath%": filepath,
            r"%sharedPath%": _get_setting("SHARED_DIRECTORY"),
        }
    )
    package_queue.schedule_job(next(job_chain))


@_capture_transfer_failure
def _start_package_transfer(transfer, name, path, tmpdir, starting_point):
    """Start a new transfer the old way.

    This means copying the transfer into one of the standard watched dirs.
    MCPServer will continue the processing and prompt the user once the
    contents in the watched directory are detected by the watched directory
    observer.
    """
    transfer_rel, filepath, path = _determine_transfer_paths(name, path, tmpdir)
    logger.debug(
        "Package %s: determined vars transfer_rel=%s, filepath=%s, path=%s",
        transfer.pk,
        transfer_rel,
        filepath,
        path,
    )

    logger.debug(
        "Package %s: copying chosen contents from transfer sources (from=%s, to=%s)",
        transfer.pk,
        path,
        transfer_rel,
    )
    _copy_from_transfer_sources([path], transfer_rel)

    logger.debug(
        "Package %s: moving package to activeTransfers dir (from=%s, to=%s)",
        transfer.pk,
        filepath,
        starting_point.watched_dir,
    )
    _move_to_internal_shared_dir(filepath, starting_point.watched_dir, transfer)


def get_file_replacement_mapping(file_obj, unit_directory):
    mapping = BASE_REPLACEMENTS.copy()
    dirname = os.path.dirname(file_obj.currentlocation.decode())
    name, ext = os.path.splitext(file_obj.currentlocation.decode())
    name = os.path.basename(name)

    absolute_path = file_obj.currentlocation.decode().replace(
        r"%SIPDirectory%", unit_directory
    )
    absolute_path = absolute_path.replace(r"%transferDirectory%", unit_directory)

    mapping.update(
        {
            r"%fileUUID%": str(file_obj.pk),
            r"%originalLocation%": file_obj.originallocation.decode(),
            r"%currentLocation%": file_obj.currentlocation.decode(),
            r"%fileGrpUse%": file_obj.filegrpuse,
            r"%fileDirectory%": dirname,
            r"%fileName%": name,
            r"%fileExtension%": ext[1:],
            r"%fileExtensionWithDot%": ext,
            r"%relativeLocation%": absolute_path,
            # TODO: standardize duplicates
            r"%inputFile%": absolute_path,
            r"%fileFullName%": absolute_path,
        }
    )

    return mapping


class Package(metaclass=abc.ABCMeta):
    """A `Package` can be a Transfer, a SIP, or a DIP."""

    # Limit file rows held in memory while avoiding long-lived DB cursors.
    FILE_QUERYSET_BATCH_SIZE = 1000

    def __init__(self, current_path, uuid):
        self._current_path = current_path.replace(
            r"%sharedPath%", _get_setting("SHARED_DIRECTORY")
        )
        if uuid and not isinstance(uuid, UUID):
            uuid = UUID(uuid)
        self.uuid = uuid

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.current_path}", {self.uuid})'

    @classmethod
    @auto_close_old_connections()
    def cleanup_old_db_entries(cls):
        """Update the status of any in progress package.

        This command is run on startup.
        TODO: we could try to recover, instead of just failing.
        """
        completed_at = timezone.now()
        statuses = (models.PACKAGE_STATUS_UNKNOWN, models.PACKAGE_STATUS_PROCESSING)
        models.Transfer.objects.filter(status__in=statuses).update(
            status=models.PACKAGE_STATUS_FAILED,
            completed_at=completed_at,
        )
        models.SIP.objects.filter(status__in=statuses).update(
            status=models.PACKAGE_STATUS_FAILED,
            completed_at=completed_at,
        )

    @abc.abstractmethod
    def queryset(self):
        raise NotImplementedError

    def change_status(self, status, **defaults):
        """Change the status of the package.

        Use one of the possible values in ``models.PACKAGE_STATUS_CHOICES``.
        """
        with auto_close_old_connections():
            self.queryset().update(status=status, **defaults)

    def mark_as_done(self):
        """Change the status of the package to Done."""
        self.change_status(models.PACKAGE_STATUS_DONE, completed_at=timezone.now())

    def mark_as_failed(self):
        """Change the status of the package to Failed."""
        self.change_status(models.PACKAGE_STATUS_FAILED, completed_at=timezone.now())

    def mark_as_processing(self):
        """Change the status of the package to Processing."""
        self.change_status(models.PACKAGE_STATUS_PROCESSING)

    @property
    def current_path(self):
        return self._current_path

    @current_path.setter
    def current_path(self, value):
        """The real (no shared dir vars) path to the package."""
        self._current_path = value.replace(
            r"%sharedPath%", _get_setting("SHARED_DIRECTORY")
        )

    @property
    def current_path_for_db(self):
        """The path to the package, as stored in the database."""
        return self.current_path.replace(
            _get_setting("SHARED_DIRECTORY"), r"%sharedPath%", 1
        )

    @property
    def package_name(self):
        basename = os.path.basename(self.current_path.rstrip("/"))
        return basename.replace("-" + str(self.uuid), "")

    @property
    @auto_close_old_connections()
    def base_queryset(self):
        return models.File.objects.filter(sip_id=self.uuid)

    @property
    def context(self):
        """Returns a `PackageContext` for this package."""
        # This needs to be reloaded from the db every time, because new values
        # could have been added by a client script.
        # TODO: pass context changes back from client
        return PackageContext.load_from_db(self.uuid)

    @abc.abstractmethod
    def reload(self):
        pass

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = BASE_REPLACEMENTS.copy()
        mapping.update(
            {
                r"%SIPUUID%": str(self.uuid),
                r"%SIPName%": self.package_name,
                r"%SIPLogsDirectory%": os.path.join(self.current_path, "logs", ""),
                r"%SIPObjectsDirectory%": os.path.join(
                    self.current_path, "objects", ""
                ),
                r"%SIPDirectory%": self.current_path,
                r"%SIPDirectoryBasename%": os.path.basename(
                    os.path.abspath(self.current_path)
                ),
                r"%relativeLocation%": self.current_path_for_db,
            }
        )

        return mapping

    def _database_file_replacement_mappings(self, queryset):
        """Yield file mappings without holding a database cursor open."""
        queryset = queryset.order_by("uuid")
        last_uuid = None

        while True:
            with auto_close_old_connections():
                page_queryset = queryset
                if last_uuid is not None:
                    page_queryset = page_queryset.filter(uuid__gt=last_uuid)
                file_objs = list(page_queryset[: self.FILE_QUERYSET_BATCH_SIZE])

            if not file_objs:
                break

            for file_obj in file_objs:
                last_uuid = file_obj.uuid
                yield get_file_replacement_mapping(file_obj, self.current_path)

    def files(self, filter_filename_end=None, filter_subdir=None):
        """Generator that yields all files associated with the package or that
        should be associated with a package.
        """
        with auto_close_old_connections():
            queryset = self.base_queryset

            if filter_filename_end:
                queryset = queryset.filter(
                    currentlocation__endswith=filter_filename_end
                )
            if filter_subdir:
                filter_path = "".join([self.REPLACEMENT_PATH_STRING, filter_subdir])
                queryset = queryset.filter(currentlocation__startswith=filter_path)

            start_path = self.current_path
            if filter_subdir:
                start_path = start_path + filter_subdir

        files_returned_already = set()

        for file_obj_mapped in self._database_file_replacement_mappings(queryset):
            if not os.path.exists(file_obj_mapped.get("%inputFile%")):
                continue
            files_returned_already.add(file_obj_mapped.get("%inputFile%"))
            yield file_obj_mapped

        for basedir, _, files in os.walk(start_path):
            for file_name in files:
                if filter_filename_end and not file_name.endswith(filter_filename_end):
                    continue
                file_path = os.path.join(basedir, file_name)
                if file_path not in files_returned_already:
                    yield {
                        r"%relativeLocation%": file_path,
                        r"%fileUUID%": "None",
                        r"%fileGrpUse%": "",
                    }

    @auto_close_old_connections()
    def set_variable(self, key, value, chain_link_id):
        """Sets a UnitVariable, which tracks choices made by users during processing."""
        # TODO: refactor this concept
        if not value:
            value = ""
        else:
            value = str(value)

        unit_var, created = models.UnitVariable.objects.update_or_create(
            unittype=self.UNIT_VARIABLE_TYPE,
            unituuid=self.uuid,
            variable=key,
            defaults={"variablevalue": value, "microservicechainlink": chain_link_id},
        )
        if created:
            message = "New UnitVariable %s created for %s: %s (MSCL: %s)"
        else:
            message = "Existing UnitVariable %s for %s updated to %s (MSCL %s)"

        logger.info(message, key, self.uuid, value, chain_link_id)


class SIPDIP(Package):
    """SIPDIP captures behavior shared between SIP- and DIP-type packages that
    share the same model in Archivematica.
    """

    def queryset(self):
        return models.SIP.objects.filter(pk=self.uuid)

    @classmethod
    @auto_close_old_connections()
    def get_or_create_from_db_by_path(cls, path, watched_dir_path=None):
        """Matches a directory to a database SIP by its appended UUID, or path."""
        path = path.replace(_get_setting("SHARED_DIRECTORY"), r"%sharedPath%", 1)
        package_type = cls.UNIT_VARIABLE_TYPE
        sip_uuid = uuid_from_path(path)
        created = True
        if sip_uuid:
            sip_obj, created = models.SIP.objects.get_or_create(
                uuid=sip_uuid,
                defaults={
                    "sip_type": package_type,
                    "currentpath": path,
                    "diruuids": False,
                },
            )
            # TODO: we thought this path was unused but some tests have proved
            # us wrong (see issue #1141) - needs to be investigated.
            if package_type == "SIP" and (not created and sip_obj.currentpath != path):
                sip_obj.currentpath = path
                sip_obj.save()
        else:
            try:
                sip_obj = models.SIP.objects.get(currentpath=path)
                created = False
            except models.SIP.DoesNotExist:
                sip_obj = models.SIP.objects.create(
                    uuid=uuid4(),
                    currentpath=path,
                    sip_type=package_type,
                    diruuids=False,
                )
        if package_type == "SIP" and watched_dir_path == "/system/reingestAIP/":
            # SIP package is a partial (objects or metadata-only) reingest.
            # Full reingests use a different workflow chain.
            sip_obj.set_partial_reingest()
        logger.info(
            "%s %s %s (%s)",
            package_type,
            sip_obj.uuid,
            "created" if created else "updated",
            path,
        )
        return cls(path, sip_obj.uuid)


class DIP(SIPDIP):
    REPLACEMENT_PATH_STRING = r"%SIPDirectory%"
    UNIT_VARIABLE_TYPE = "DIP"
    JOB_UNIT_TYPE = "unitDIP"

    def reload(self):
        # reload is a no-op for DIPs
        pass

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = super().get_replacement_mapping(filter_subdir_path=filter_subdir_path)
        mapping[r"%unitType%"] = "DIP"

        if filter_subdir_path:
            relative_location = filter_subdir_path.replace(
                _get_setting("SHARED_DIRECTORY"), r"%sharedPath%", 1
            )
            mapping[r"%relativeLocation%"] = relative_location

        return mapping


class Transfer(Package):
    REPLACEMENT_PATH_STRING = r"%transferDirectory%"
    UNIT_VARIABLE_TYPE = "Transfer"
    JOB_UNIT_TYPE = "unitTransfer"

    def queryset(self):
        return models.Transfer.objects.filter(pk=self.uuid)

    @classmethod
    @auto_close_old_connections()
    def get_or_create_from_db_by_path(cls, path, watched_dir_path=None):
        """Matches a directory to a database Transfer by its appended UUID, or path."""
        path = path.replace(_get_setting("SHARED_DIRECTORY"), r"%sharedPath%", 1)

        transfer_uuid = uuid_from_path(path)
        created = True
        if transfer_uuid:
            transfer_obj, created = models.Transfer.objects.get_or_create(
                uuid=transfer_uuid, defaults={"currentlocation": path}
            )
            # TODO: we thought this path was unused but some tests have proved
            # us wrong (see issue #1141) - needs to be investigated.
            if not created and transfer_obj.currentlocation != path:
                transfer_obj.currentlocation = path
                transfer_obj.save()
        else:
            try:
                transfer_obj = models.Transfer.objects.get(currentlocation=path)
                created = False
            except models.Transfer.DoesNotExist:
                transfer_obj = models.Transfer.objects.create(
                    uuid=uuid4(), currentlocation=path
                )
        logger.info(
            "Transfer %s %s (%s)",
            transfer_obj.uuid,
            "created" if created else "updated",
            path,
        )

        return cls(path, transfer_obj.uuid)

    @property
    @auto_close_old_connections()
    def base_queryset(self):
        return models.File.objects.filter(transfer_id=self.uuid)

    @auto_close_old_connections()
    def reload(self):
        transfer = models.Transfer.objects.get(uuid=self.uuid)
        self.current_path = transfer.currentlocation
        self.processing_configuration = transfer.processing_configuration

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = super().get_replacement_mapping(filter_subdir_path=filter_subdir_path)

        mapping.update(
            {
                self.REPLACEMENT_PATH_STRING: self.current_path,
                r"%unitType%": "Transfer",
                r"%processingConfiguration%": self.processing_configuration,
            }
        )

        return mapping


class SIP(SIPDIP):
    REPLACEMENT_PATH_STRING = r"%SIPDirectory%"
    UNIT_VARIABLE_TYPE = "SIP"
    JOB_UNIT_TYPE = "unitSIP"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.aip_filename = None
        self.sip_type = None

    @auto_close_old_connections()
    def reload(self):
        sip = models.SIP.objects.get(uuid=self.uuid)
        self.current_path = sip.currentpath
        self.aip_filename = sip.aip_filename or ""
        self.sip_type = sip.sip_type

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = super().get_replacement_mapping(filter_subdir_path=filter_subdir_path)

        mapping.update(
            {
                r"%unitType%": "SIP",
                r"%AIPFilename%": self.aip_filename,
                r"%SIPType%": self.sip_type,
            }
        )

        return mapping


class PackageContext:
    """Package context tracks choices made previously while processing"""

    def __init__(self, *items):
        self._data = collections.OrderedDict()
        for key, value in items:
            self._data[key] = value

    def __repr__(self):
        return f"PackageContext({dict(self._data.items())!r})"

    def __iter__(self):
        yield from self._data.items()

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    @classmethod
    @auto_close_old_connections()
    def load_from_db(cls, uuid):
        """
        Loads a context from the UnitVariable table.
        """
        context = cls()

        # TODO: we shouldn't need one UnitVariable per chain, with all the same values
        unit_vars_queryset = models.UnitVariable.objects.filter(
            unituuid=uuid, variable="replacementDict"
        )
        # Distinct helps here, at least
        unit_vars_queryset = unit_vars_queryset.values_list("variablevalue").distinct()
        for unit_var_value in unit_vars_queryset:
            try:
                unit_var = json.loads(unit_var_value[0])
            except (ValueError, TypeError):
                logger.exception(
                    "Failed to eval unit variable value %s", unit_var_value[0]
                )
            else:
                context.update(unit_var)

        return context

    def copy(self):
        clone = PackageContext()
        clone._data = self._data.copy()

        return clone

    def update(self, mapping):
        for key, value in mapping.items():
            self._data[key] = value
