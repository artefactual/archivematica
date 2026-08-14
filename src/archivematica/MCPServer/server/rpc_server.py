"""Archivematica MCPServer API (Gearman RPC).

We have plans to replace this server with gRPC.

TODO(sevein): methods with `raise_exc` enabled should be updated so they don't
need it, but it needs to be tested further. The main thing to check is whether
the client is ready to handle application-level exceptions.
"""

import calendar
import configparser
import inspect
import logging
import os
import re
import time
from collections import OrderedDict
from datetime import timezone as datetime_timezone
from io import StringIO
from socket import gethostname
from typing import Literal

import gearman
from django.conf import settings as django_settings
from django.db import connection
from django.db.models import Count
from django.db.models import Exists
from django.db.models import FloatField
from django.db.models import Func
from django.db.models import JSONField
from django.db.models import Max
from django.db.models import Min
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.db.models.functions import JSONObject
from django.utils import translation
from django.utils.translation import gettext as _
from gearman import GearmanWorker
from lxml import etree

from archivematica.archivematicaCommon.dbconns import auto_close_old_connections
from archivematica.archivematicaCommon.gearman_encoder import JSONDataEncoder
from archivematica.dashboard.main.idempotency import IdempotencyKeyConflictError
from archivematica.dashboard.main.idempotency import IdempotencyRequestInProgressError
from archivematica.dashboard.main.models import PACKAGE_STATUS_FAILED
from archivematica.dashboard.main.models import PACKAGE_STATUS_PROCESSING
from archivematica.dashboard.main.models import SIP
from archivematica.dashboard.main.models import UNIT_VARIABLE_PROCESSING_CONFIGURATION
from archivematica.dashboard.main.models import Job
from archivematica.dashboard.main.models import Transfer
from archivematica.dashboard.main.models import UnitVariable
from archivematica.MCPServer.server.jobs.chain import get_job_class_for_link
from archivematica.MCPServer.server.packages import create_package
from archivematica.MCPServer.server.packages import get_approve_transfer_chain_id
from archivematica.MCPServer.server.processing_config import get_processing_fields
from archivematica.MCPServer.server.workflow import TERMINAL_PACKAGE_STATUS_FAILED

logger = logging.getLogger("archivematica.mcp.server.rpc_server")

# Unit-level state exposed by getUnitsStatuses when job rows do not yet exist.
# Keep this intentionally narrow: today, monitor state still comes from
# Job.currentstep once jobs have been created. The single current value covers a
# transfer accepted into processing that is waiting in PackageQueue before its
# first Job row can be written. A future persisted lifecycle model should widen
# this type, or replace it with a shared enum, instead of adding free-form
# labels here.
ProcessingUnitState = Literal["waiting_for_processing"]
PROCESSING_STATE_WAITING_FOR_PROCESSING: ProcessingUnitState = "waiting_for_processing"
INGEST_START_TIME_MARKER_GROUP = "Assign file UUIDs and checksums"

UNIT_TYPES = {
    "SIP": (SIP, ("unitSIP", "unitDIP")),
    "Transfer": (Transfer, ("unitTransfer",)),
}


def _transfer_directory_name(transfer: Transfer) -> str:
    unnamed = _("(Unnamed)")
    current_location = transfer.currentlocation.rstrip("/")
    if not current_location:
        return unnamed
    return os.path.basename(current_location) or unnamed


def _datetime_to_unix_timestamp(value) -> float:
    """Convert a datetime to the epoch-seconds format used by the monitor.

    This helper exists because getUnitsStatuses combines timestamps from two
    sources: SQL rows already converted with UNIX_TIMESTAMP and ORM
    DateTimeField values from UnitVariable. Keeping the ORM conversion here
    makes that contract explicit and preserves microsecond precision.

    With USE_TZ enabled, Django supplies aware UTC datetimes from the database.
    Aware values are normalized to UTC before conversion; naive values are
    treated as UTC to match the existing MySQL/UNIX_TIMESTAMP monitor behavior.
    """
    if value.utcoffset() is not None:
        value = value.astimezone(datetime_timezone.utc)
    return calendar.timegm(value.timetuple()) + (value.microsecond / 1000000)


def _transfer_processing_start_timestamps(transfer_uuids) -> dict[str, float]:
    """Return processing-start marker timestamps keyed by transfer UUID."""
    if not transfer_uuids:
        return {}

    markers = (
        UnitVariable.objects.filter(
            unittype="Transfer",
            unituuid__in=transfer_uuids,
            variable=UNIT_VARIABLE_PROCESSING_CONFIGURATION,
        )
        .values("unituuid")
        .annotate(createdtime=Min("createdtime"))
    )
    return {
        str(marker["unituuid"]): _datetime_to_unix_timestamp(marker["createdtime"])
        for marker in markers
    }


def _get_unit_type(payload):
    try:
        type_ = payload["type"]
        model, job_unit_types = UNIT_TYPES[type_]
        lang = payload["lang"]
    except KeyError as err:
        raise UnexpectedPayloadError(f"Missing parameter: {err}")
    return type_, model, job_unit_types, lang


class RPCServerError(Exception):
    """Base exception of RPCServer.

    This exception and its subclasses are meant to be raised by RPC handlers.
    """


class UnexpectedPayloadError(RPCServerError):
    """Missing parameters in payload."""


class NotFoundError(RPCServerError):
    """Generic NotFound exception."""


class RPCServer(GearmanWorker):
    """RPCServer is the API server implemented as a Gearman worker.

    Handlers are implemented as methods in this class. They have access to
    shared state in this class, e.g. ``self.workflow``. For a method to be
    promoted as handler it needs to meet the following conditions:

    1. The name of the method starts with an underscore (``_``) and ends with
       the string ``_handler``, e.g. ``_do_something_handler``.

    2. The method docstrings ends with a configuration snippet in INI format,
       e.g.::

           [config]
           name = doSomething
           raise_exc = yes

       Supported configuration attributes:

       - ``name`` (string) is the name of the function name or ability as
         Gearman refers to the type of a job in its protocol.

       - ``raise_exc`` (boolean) - when enabled, exceptions that occur inside
         the handler are not caught which causes the Gearman worker library to
         report the error to Gearman which results in terminating the job as
         failed. The Gearman client (in our context, the API consumer) will not
         receive additional information about the error other than its status.
         Disable ``raise_exc`` when you want the client to receive a detailed
         error.

    3. Handler methods have at least three arguments:

       - ``self``: instance of the RPCServer class.

       - ``worker``: instance of the worker class which is a subclass of
         ``gearman.job.GearmanWorker``.

       - ``job``: instance of ``gearman.job.GearmanJob``.

       Additionally, a method handler can have an argument named ``payload``.
       If present, it will carry the data embedded in the payload of the job
       already unserialized. This is useful when the handler wants to read
       data sent by the client.

    """

    data_encoder = JSONDataEncoder

    # Regular expression to match handler configurations in method docstrings.
    ability_regex = re.compile(
        r"(?P<docstring>.*)(?P<config>\[config\].*)$", re.DOTALL | re.MULTILINE
    )

    # To some extent, application logic in Archivematica is coupled to certain
    # values in our workflow data. This is mostly true to things related to
    # types of transfers and its approvals. This value in particular supports
    # the partial approval of AIP reingest.
    APPROVE_AIP_REINGEST_CHAIN_ID = "260ef4ea-f87d-4acf-830d-d0de41e6d2af"

    def __init__(self, workflow, shutdown_event, package_queue, executor):
        super().__init__(host_list=[django_settings.GEARMAN_SERVER])
        self.workflow = workflow
        self.shutdown_event = shutdown_event
        self.package_queue = package_queue
        self.executor = executor
        self._register_tasks()
        client_id = f"{gethostname()}_MCPServer".encode()
        self.set_client_id(client_id)

    def after_poll(self, any_activity):
        """Stop the work loop if the shutdown event is set."""
        if self.shutdown_event.is_set():
            return False

        return True

    def _register_tasks(self):
        for ability, handler in self._handlers():
            logger.debug("Registering ability %s", ability)
            self.register_task(ability.encode(), handler)

    def _handlers(self):
        members = inspect.getmembers(self, predicate=inspect.ismethod)
        for name, handler in members:
            if name[0] != "_":
                continue
            if not name.endswith("_handler"):
                continue
            name, opts = self._get_ability_details(handler)
            yield name, self._wrap_handler_method(name, handler, **opts)

    def _get_ability_details(self, handler):
        docstring = str(inspect.getdoc(handler))
        match = self.ability_regex.search(docstring)
        err = ValueError(f"Unexpected docstring format: {docstring}")
        if match is None:
            raise err
        try:
            config = match.group("config")
        except IndexError:
            raise err
        parser = configparser.RawConfigParser({"name": None, "raise_exc": False})
        parser.read_file(StringIO(config))
        name = parser.get("config", "name")
        if name is None:
            raise ValueError(
                "handler {} is missing the `name` attribute", handler.__name__
            )
        return (
            name,
            {
                "raise_exc": parser.getboolean("config", "raise_exc"),
                "expect_payload": "payload" in inspect.getfullargspec(handler).args,
            },
        )

    def _wrap_handler_method(self, name, handler, **opts):
        @auto_close_old_connections()
        def wrap(worker, job):
            args = [worker, job]
            if opts["expect_payload"]:
                if not isinstance(job.data, dict):
                    raise UnexpectedPayloadError("Payload is not a dictionary")
                args.append(job.data)
            try:
                resp = handler(*args)
            except Exception as err:
                # Errors that are familiar will not be logged in detail.
                known_err = isinstance(err, RPCServerError)
                logger.error(
                    "Exception raised by handler %s: %s",
                    name,
                    err,
                    exc_info=not known_err,
                )
                if opts["raise_exc"]:
                    raise  # So GearmanWorker knows that it failed.
                resp = {"error": True, "handler": name, "message": str(err)}
            return resp

        return wrap

    #
    # Handlers
    #

    def _job_approve_handler(self, worker, job, payload):
        """Approve a job awaiting for approval.

        [config]
        name = approveJob
        raise_exc = True
        """
        job_id = payload["jobUUID"]
        chain = payload["chain"]
        user_id = str(payload["user_id"])
        logger.debug("Approving: %s %s %s", job_id, chain, user_id)
        job_chain = self.package_queue.decide(job_id, chain, user_id=user_id)
        if job_chain:
            self.package_queue.schedule_job(next(job_chain))
        return "approving: ", job_id, chain

    def _job_awaiting_approval_handler(self, worker, job):
        """List jobs awaiting for approval.

        [config]
        name = getJobsAwaitingApproval
        raise_exc = True
        """
        ret = etree.Element("choicesAvailableForUnits")
        for choice in self.package_queue.jobs_awaiting_decisions().values():
            unit_choices = etree.SubElement(ret, "choicesAvailableForUnit")
            etree.SubElement(unit_choices, "UUID").text = str(choice.uuid)
            unit = etree.SubElement(unit_choices, "unit")
            etree.SubElement(unit, "type").text = choice.package.__class__.__name__
            unitXML = etree.SubElement(unit, "unitXML")
            etree.SubElement(unitXML, "UUID").text = str(choice.package.uuid)
            etree.SubElement(
                unitXML, "currentPath"
            ).text = choice.package.current_path_for_db
            choices = etree.SubElement(unit_choices, "choices")
            for id_, description in choice.get_choices().items():
                choice = etree.SubElement(choices, "choice")
                etree.SubElement(choice, "chainAvailable").text = str(id_)
                etree.SubElement(choice, "description").text = str(description)

        return etree.tostring(ret, pretty_print=True, encoding="utf8")

    def _package_create_handler(self, worker, job, payload):
        """Create a new package.

        When auto-approving a transfer, create_package delegates to
        _start_package_transfer_with_auto_approval. That bootstrap records the
        linkAfterTransferSourceRetrieval UnitVariable before queueing the first
        job, giving getUnitsStatuses a persisted timestamp while the transfer
        has no Job rows yet.

        [config]
        name = packageCreate
        raise_exc = True
        """
        args = (
            self.package_queue,
            self.executor,
            payload.get("name"),
            payload.get("type"),
            payload.get("accession"),
            payload.get("access_system_id"),
            payload.get("path"),
            payload.get("metadata_set_id"),
            payload.get("user_id"),
            self.workflow,
        )
        kwargs = {"auto_approve": payload.get("auto_approve", True)}
        processing_config = payload.get("processing_config")
        if processing_config is not None:
            kwargs["processing_config"] = processing_config
        idempotency_key = payload.get("idempotency_key")
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        try:
            result = create_package(*args, **kwargs)
        except IdempotencyRequestInProgressError as err:
            return {
                "error": True,
                "message": str(err),
                "status_code": 409,
                "code": "idempotency_key_in_progress",
            }
        except IdempotencyKeyConflictError as err:
            return {
                "error": True,
                "message": str(err),
                "status_code": 422,
                "code": "idempotency_key_reused",
            }
        if isinstance(result, Transfer):
            return result.pk
        return result

    def _approve_transfer_by_path_handler(self, worker, job, payload):
        """Approve a transfer matched by its path.

        [config]
        name = approveTransferByPath
        raise_exc = False
        """
        db_transfer_path = payload.get("db_transfer_path")
        transfer_type = payload.get("transfer_type", "standard")
        user_id = payload.get("user_id")
        job = Job.objects.filter(
            directory=db_transfer_path, currentstep=Job.STATUS_AWAITING_DECISION
        ).first()
        if not job:
            raise NotFoundError("There is no job awaiting a decision.")
        chain_id = get_approve_transfer_chain_id(transfer_type)
        try:
            job_chain = self.package_queue.decide(job.pk, chain_id, user_id=user_id)
        except KeyError:
            raise NotFoundError("Could not find choice for unit")
        else:
            if job_chain:
                self.package_queue.schedule_job(next(job_chain))
        return job.sipuuid

    def _approve_partial_reingest_handler(self, worker, job, payload):
        """Approve a partial reingest.

        TODO: (from the old api/views.py function) this is just a temporary way
        of getting the API to do the equivalent of clicking "Approve AIP
        reingest" in the dashboard when faced with "Approve AIP reingest". This
        is non-dry given ``approve_transfer_by_path_handler`` above.

        [config]
        name = approvePartialReingest
        raise_exc = False
        """
        sip_uuid = payload.get("sip_uuid")
        user_id = payload.get("user_id")
        job = Job.objects.filter(
            sipuuid=sip_uuid,
            microservicegroup="Reingest AIP",
            currentstep=Job.STATUS_AWAITING_DECISION,
        ).first()
        if not job:  # No job to be found.
            raise NotFoundError(
                f'There is no "Reingest AIP" job awaiting a decision for SIP {sip_uuid}'
            )
        not_found = NotFoundError("Could not find choice for approve AIP reingest")
        try:
            chain = self.workflow.get_chain(self.APPROVE_AIP_REINGEST_CHAIN_ID)
        except KeyError:
            raise not_found
        try:
            job_chain = self.package_queue.decide(job.pk, chain.id, user_id=user_id)
        except KeyError:
            raise not_found

        if job_chain:
            self.package_queue.schedule_job(next(job_chain))

    def _get_processing_config_fields_handler(self, worker, job, payload):
        """List processing configuration fields.

        [config]
        name = getProcessingConfigFields
        raise_exc = False
        """
        return get_processing_fields(self.workflow, payload.get("lang"))

    def _units_summary_handler(self, worker, job, payload):
        """Return lightweight monitor summaries for SIPs or Transfers.

        Unlike ``getUnitsStatuses``, this response never embeds Job rows. It
        includes only the latest Job fields needed to reproduce the unit status
        icon, the timestamp shown in the monitor, and the UUIDs of Jobs awaiting
        decisions so delayed detail responses cannot restore obsolete choices.

        [config]
        name = getUnitsSummary
        raise_exc = False
        """
        type_, model, job_unit_types, lang = _get_unit_type(payload)
        latest_jobs = Job.objects.filter(
            sipuuid=OuterRef("uuid"), unittype__in=job_unit_types
        ).order_by("-createdtime", "-jobuuid")
        latest_jobs = latest_jobs.annotate(
            data=JSONObject(
                uuid="jobuuid",
                type="jobtype",
                group="microservicegroup",
                link="microservicechainlink",
                status="currentstep",
                timestamp=Func(
                    "createdtime",
                    function="UNIX_TIMESTAMP",
                    output_field=FloatField(),
                ),
                directory="directory",
            )
        )
        oldest_jobs = Job.objects.filter(
            sipuuid=OuterRef("uuid"), unittype__in=job_unit_types
        ).order_by("createdtime", "jobuuid")
        start_marker_jobs = Job.objects.filter(
            sipuuid=OuterRef("uuid"),
            unittype__in=job_unit_types,
            microservicegroup=INGEST_START_TIME_MARKER_GROUP,
        ).order_by("-createdtime", "-jobuuid")
        units = model.objects.filter(hidden=False).annotate(
            has_jobs=Exists(
                Job.objects.filter(
                    sipuuid=OuterRef("uuid"), unittype__in=job_unit_types
                )
            ),
            latest_job=Subquery(
                latest_jobs.values("data")[:1], output_field=JSONField()
            ),
            oldest_job_time=Subquery(oldest_jobs.values("createdtime")[:1]),
            start_marker_time=Subquery(start_marker_jobs.values("createdtime")[:1]),
        )
        if type_ == "Transfer":
            units = units.filter(
                Q(has_jobs=True)
                | Q(status__in=(PACKAGE_STATUS_PROCESSING, PACKAGE_STATUS_FAILED))
            )
        else:
            units = units.filter(has_jobs=True)

        units = list(units)
        # Fetch decision identities in one batch, with stable ordering for
        # changed-aware polling. Derive the flag from these same rows so the
        # two fields cannot disagree if a decision changes between queries.
        awaiting_job_uuids: dict[str, list[str]] = {}
        for unit_id, job_id in (
            Job.objects.filter(
                sipuuid__in=[unit.uuid for unit in units],
                unittype__in=job_unit_types,
                currentstep=Job.STATUS_AWAITING_DECISION,
            )
            .order_by("jobuuid")
            .values_list("sipuuid", "jobuuid")
        ):
            awaiting_job_uuids.setdefault(str(unit_id), []).append(str(job_id))

        processing_start_times = {}
        if type_ == "Transfer":
            queued_unit_ids = [unit.uuid for unit in units if not unit.has_jobs]
            processing_start_times = _transfer_processing_start_timestamps(
                queued_unit_ids
            )

        access_system_ids = {}
        if type_ == "SIP":
            for sip_id, access_system_id in (
                Transfer.objects.filter(file__sip_id__in=[unit.uuid for unit in units])
                .values_list("file__sip_id", "access_system_id")
                .distinct()
            ):
                access_system_ids.setdefault(str(sip_id), access_system_id)

        results = []
        for unit in units:
            unit_id = str(unit.uuid)
            latest_job = unit.latest_job
            if latest_job is None:
                if unit.status == PACKAGE_STATUS_FAILED and unit.completed_at:
                    timestamp = _datetime_to_unix_timestamp(unit.completed_at)
                else:
                    timestamp = processing_start_times.get(unit_id, 0)
            else:
                timestamp = float(latest_job["timestamp"])

            if latest_job is None:
                started_timestamp = processing_start_times.get(unit_id, timestamp)
            else:
                started_at = unit.start_marker_time or unit.oldest_job_time
                if started_at is None:
                    started_timestamp = timestamp
                else:
                    started_timestamp = _datetime_to_unix_timestamp(started_at)

            if latest_job is None:
                directory = _transfer_directory_name(unit)
                if unit.status == PACKAGE_STATUS_FAILED:
                    with translation.override(lang):
                        failure_type = _("Failed before processing started")
                    status = {
                        "currentstep": Job.STATUS_FAILED,
                        "type": failure_type,
                        "microservicegroup": "",
                    }
                else:
                    status = None
            else:
                directory_job = Job(
                    directory=latest_job["directory"],
                    sipuuid=unit.uuid,
                )
                directory = str(directory_job.get_directory_name())
                terminal_package_status = None
                try:
                    link = self.workflow.get_link(latest_job["link"])
                except KeyError:
                    job_type = latest_job["type"]
                    group = latest_job["group"]
                else:
                    job_type = link.get_label("description", lang)
                    group = link.get_label("group", lang)
                    terminal_package_status = link.package_status
                status = {
                    "currentstep": latest_job["status"],
                    "type": job_type,
                    "microservicegroup": group,
                }
                # Legacy packages may already be persisted as Done because a
                # failure branch ended with a successful cleanup Job. Preserve
                # their declared workflow outcome in monitor summaries too.
                if (
                    unit.status == PACKAGE_STATUS_FAILED
                    or terminal_package_status == TERMINAL_PACKAGE_STATUS_FAILED
                ):
                    status["currentstep"] = Job.STATUS_FAILED

            item = {
                "uuid": unit_id,
                "directory": directory,
                "timestamp": timestamp,
                "started_at": started_timestamp,
                "active": unit.active,
                "status": status,
                "has_awaiting_decision": bool(awaiting_job_uuids.get(unit_id)),
                "awaiting_job_uuids": awaiting_job_uuids.get(unit_id, []),
            }
            if (
                type_ == "Transfer"
                and not unit.has_jobs
                and unit.status == PACKAGE_STATUS_PROCESSING
            ):
                item["processing_state"] = PROCESSING_STATE_WAITING_FOR_PROCESSING
            if type_ == "SIP":
                item["access_system_id"] = access_system_ids.get(unit_id)
            results.append(item)

        results.sort(key=lambda item: item["timestamp"], reverse=True)
        return results

    def _unit_job_groups_handler(self, worker, job, payload):
        """Return aggregated Job rows for one SIP or Transfer.

        Completed and executing Jobs are grouped by workflow link and status.
        Jobs awaiting decisions remain individual because their UUID and
        choices are actionable processing state.

        [config]
        name = getUnitJobGroups
        raise_exc = False
        """
        _type, model, job_unit_types, lang = _get_unit_type(payload)
        try:
            unit_id = payload["id"]
        except KeyError as err:
            raise UnexpectedPayloadError(f"Missing parameter: {err}")
        if not model.objects.filter(pk=unit_id, hidden=False).exists():
            raise NotFoundError("Unit not found")

        jobs = Job.objects.filter(sipuuid=unit_id, unittype__in=job_unit_types)
        representative_jobs = Job.objects.filter(
            sipuuid=unit_id,
            unittype__in=job_unit_types,
            microservicechainlink=OuterRef("microservicechainlink"),
            currentstep=OuterRef("currentstep"),
        ).order_by("-createdtime", "-jobuuid")
        aggregate_rows = (
            jobs.exclude(currentstep=Job.STATUS_AWAITING_DECISION)
            .values("microservicechainlink", "currentstep")
            .annotate(
                count=Count("jobuuid"),
                first_time=Min("createdtime"),
                latest_time=Max("createdtime"),
            )
            # Add the representative after all aggregates so Django does not
            # group by the subquery and evaluate it for every input Job.
            .annotate(
                job_uuid=Subquery(representative_jobs.values("jobuuid")[:1]),
            )
        )
        waiting_rows = jobs.filter(currentstep=Job.STATUS_AWAITING_DECISION).order_by(
            "-createdtime", "-jobuuid"
        )
        jobs_awaiting_decisions = self.package_queue.jobs_awaiting_decisions()

        rows = []
        for aggregate in aggregate_rows:
            link_id = aggregate["microservicechainlink"]
            try:
                link = self.workflow.get_link(link_id)
            except KeyError:
                continue
            count = aggregate["count"]
            row = {
                "key": f"{link_id}:{aggregate['currentstep']}",
                "link_id": str(link_id),
                "currentstep": aggregate["currentstep"],
                "timestamp": _datetime_to_unix_timestamp(aggregate["latest_time"]),
                "first_timestamp": _datetime_to_unix_timestamp(aggregate["first_time"]),
                "microservicegroup": link.get_label("group", lang),
                "type": link.get_label("description", lang),
                "count": count,
                "uuid": str(aggregate["job_uuid"]),
                "produces_tasks": False,
            }
            try:
                row["produces_tasks"] = get_job_class_for_link(link).produces_tasks
            except ValueError:
                pass
            rows.append(row)

        for waiting_job in waiting_rows:
            link_id = waiting_job.microservicechainlink
            try:
                link = self.workflow.get_link(link_id)
            except KeyError:
                continue
            job_id = str(waiting_job.jobuuid)
            row = {
                "key": f"job:{job_id}",
                "uuid": job_id,
                "link_id": str(link_id),
                "currentstep": waiting_job.currentstep,
                "timestamp": _datetime_to_unix_timestamp(waiting_job.createdtime),
                "first_timestamp": _datetime_to_unix_timestamp(waiting_job.createdtime),
                "microservicegroup": link.get_label("group", lang),
                "type": link.get_label("description", lang),
                "count": 1,
                "produces_tasks": False,
            }
            try:
                row["produces_tasks"] = get_job_class_for_link(link).produces_tasks
            except ValueError:
                pass
            try:
                row["choices"] = _pull_choices(job_id, lang, jobs_awaiting_decisions)
            except JobNotWaitingForApprovalError:
                pass
            rows.append(row)

        rows.sort(key=lambda item: item["timestamp"], reverse=True)
        groups = OrderedDict()
        for row in rows:
            groups.setdefault(row["microservicegroup"], []).append(row)
        return [
            {"name": group_name, "jobs": group_jobs}
            for group_name, group_jobs in groups.items()
        ]

    def _units_statuses_handler(self, worker, job, payload):
        """Returns the status of units that are of type SIP or Transfer.

        It returns a JSON-encoded objects. Its ``objects`` attribute is an
        array of objects, each of which represents a single unit. Each unit
        has a ``jobs`` attribute whose value is an array of objects, each of
        which represents a job of the unit.

        For Transfer status responses, processing transfers may briefly have no
        Job rows because PackageQueue has accepted the transfer but the first
        job has not run far enough to persist itself yet. Those transfers are
        included with a unit-level waiting state. API-created transfers persist
        the processingConfiguration UnitVariable in create_package before being
        marked as processing. Its createdTime is used as the unit timestamp so
        the monitor can sort the waiting transfer with other active work instead
        of treating it as epoch zero.

        [config]
        name = getUnitsStatuses
        raise_exc = False
        """
        unit_types = {"SIP": (SIP, "unitSIP"), "Transfer": (Transfer, "unitTransfer")}
        try:
            model_attrs = unit_types[payload["type"]]
            lang = payload["lang"]
        except KeyError as err:
            raise UnexpectedPayloadError(f"Missing parameter: {err}")
        model = model_attrs[0]
        if payload["type"] == "SIP":
            sql = """
            SELECT Jobs.SIPUUID,
                   MAX(UNIX_TIMESTAMP(Jobs.createdTime)) AS timestamp
                FROM Jobs
                JOIN SIPs
                    ON Jobs.SIPUUID = SIPs.sipUUID
                WHERE
                    Jobs.unitType=%s
                    AND NOT Jobs.SIPUUID LIKE '%%None%%'
                    AND NOT SIPs.hidden
                GROUP BY Jobs.SIPUUID;"""
        else:
            sql = """
            SELECT Jobs.SIPUUID,
                   MAX(UNIX_TIMESTAMP(Jobs.createdTime)) AS timestamp
                FROM Jobs
                JOIN Transfers
                    ON Jobs.SIPUUID = Transfers.transferUUID
                WHERE
                    Jobs.unitType=%s
                    AND NOT Jobs.SIPUUID LIKE '%%None%%'
                    AND NOT Transfers.hidden
                GROUP BY Jobs.SIPUUID;"""
        with connection.cursor() as cursor:
            cursor.execute(sql, (model_attrs[1],))
            sipuuids_and_timestamps = list(cursor.fetchall())
        if payload["type"] == "Transfer":
            # TODO: Replace this UnitVariable timestamp workaround with an
            # explicit package lifecycle timestamp, e.g. Transfer.processing_started_at.
            # API-created transfers can be processing before PackageQueue has
            # created their first Job. Until we have that direct field, use the
            # processingConfiguration UnitVariable, written before the public
            # processing status change, as the unit timestamp so the monitor can
            # show them as waiting without sorting active transfers behind old
            # completed transfers.
            transfer_jobs = Job.objects.filter(
                sipuuid=OuterRef("uuid"), unittype=model_attrs[1]
            )
            queued_transfer_uuids = list(
                Transfer.objects.filter(status=PACKAGE_STATUS_PROCESSING, hidden=False)
                .filter(~Exists(transfer_jobs))
                .values_list("uuid", flat=True)
            )
            queued_timestamps = _transfer_processing_start_timestamps(
                queued_transfer_uuids
            )
            sipuuids_and_timestamps.extend(
                (
                    str(transfer_uuid),
                    queued_timestamps.get(str(transfer_uuid), 0),
                )
                for transfer_uuid in queued_transfer_uuids
            )
        jobs_awaiting_for_approval = self.package_queue.jobs_awaiting_decisions()
        objects = []
        for unit_id, timestamp in sipuuids_and_timestamps:
            unit = model.objects.get(pk=unit_id)
            item = {
                "id": unit_id,
                "uuid": unit_id,
                "timestamp": float(timestamp),
                "active": unit.active,
                "jobs": [],
            }
            jobs = Job.objects.filter(sipuuid=unit_id).order_by(
                "-createdtime", "-jobuuid"
            )
            if jobs:
                item["directory"] = jobs[0].get_directory_name()
            elif model is Transfer:
                item["directory"] = _transfer_directory_name(unit)
                item["processing_state"] = PROCESSING_STATE_WAITING_FOR_PROCESSING
            # Embed "Access System ID" in status data (used in Upload DIP).
            # `access_system_id` is a property of the Transfer model - the
            # only way we have at the moment to look up the Transfer is by
            # using the files in common.
            if model is SIP:
                try:
                    trfs = Transfer.objects.filter(file__sip_id=item["uuid"]).distinct()
                    if trfs:
                        item["access_system_id"] = trfs[0].access_system_id
                except Exception:
                    pass
            # Append jobs
            for job_ in jobs:
                try:
                    link = self.workflow.get_link(job_.microservicechainlink)
                except KeyError:
                    continue
                new_job = {}
                new_job["uuid"] = str(job_.jobuuid)
                new_job["link_id"] = str(job_.microservicechainlink)
                new_job["currentstep"] = job_.currentstep
                new_job["timestamp"] = (
                    f"{calendar.timegm(job_.createdtime.timetuple())}.{job_.createdtime.microsecond:06d}"
                )
                new_job["microservicegroup"] = link.get_label("group", lang)
                new_job["type"] = link.get_label("description", lang)
                try:
                    new_job["produces_tasks"] = get_job_class_for_link(
                        link
                    ).produces_tasks
                except ValueError:
                    new_job["produces_tasks"] = False
                try:
                    new_job["choices"] = _pull_choices(
                        str(job_.jobuuid), lang, jobs_awaiting_for_approval
                    )
                except JobNotWaitingForApprovalError:
                    pass
                item["jobs"].append(new_job)
            objects.append(item)
        # The response combines SQL-derived job timestamps with UnitVariable
        # timestamps for transfers that are processing but have no Job rows yet.
        # Sort after both sources have been merged so API clients and the
        # monitor receive active work newest-first regardless of database row
        # order from either source.
        objects.sort(key=lambda item: item["timestamp"], reverse=True)
        return objects

    def _unit_status_handler(self, worker, job, payload):
        """Retrieve status information about a unit.

        The returned value is a dictionary with the name of the unit and a list
        of jobs recorded. It could be easily extended to incorporate more
        details.

        [config]
        name = getUnitStatus
        raise_exc = False
        """
        try:
            id_ = payload["id"]
            lang = payload["lang"]
        except KeyError as err:
            raise UnexpectedPayloadError(f"Missing parameter: {err}")
        jobs_qs = Job.objects.filter(sipuuid=id_)
        if not jobs_qs:
            if not Transfer.objects.filter(
                pk=id_, status=PACKAGE_STATUS_PROCESSING
            ).exists():
                raise NotFoundError("Unit not found")
            return {"name": jobs_qs.get_directory_name(), "jobs": []}
        microservices = jobs_qs.values(
            "jobuuid", "currentstep", "microservicechainlink"
        )
        jobs = []
        for item in microservices:
            try:
                link = self.workflow.get_link(item.get("microservicechainlink"))
            except KeyError:
                continue
            jobs.append(
                {
                    "id": item.get("jobuuid"),
                    "description": link.get_label("description", lang),
                    "status": item.get("currentstep"),
                    "group": link.get_label("group", lang),
                }
            )
        return {"name": jobs_qs.get_directory_name(), "jobs": jobs}


class JobNotWaitingForApprovalError(Exception):
    """When a job is not waiting for a decision to be made."""


def _pull_choices(job_id, lang, jobs_awaiting_for_approval):
    """Look up choices available in a job awaiting for approval.

    The choices (dict ``jobs_awaiting_for_approval``) must be provided so the
    caller can read it only once and use it many times, to minimize access to
    it as it in shared memory.

    The value returned is a dict ultimately used to hydrate a dropdown. The
    keys can be either IDs or indices depending on the underlying link manager.
    The value is the label that we want to show in the user interface, which
    is extracted from the instance of ``workflow.TranslationLabel`` hold by
    the link manager, given the ``lang`` of the user that made the request.

    The caller should expect ``JobNotWaitingForApprovalError`` to be raised
    when the job does not need a decision to be made.
    """
    ret = OrderedDict()
    try:
        choices = jobs_awaiting_for_approval[job_id].get_choices()
    except (KeyError, AttributeError):
        raise JobNotWaitingForApprovalError
    for item in choices.items():
        id_, label = item
        ret[id_] = label[lang]
    return ret


def start(workflow, shutdown_event, package_queue, executor):
    worker = RPCServer(workflow, shutdown_event, package_queue, executor)
    logger.debug("Started RPC server.")

    fail_max_sleep = 30
    fail_sleep_incrementor = 2

    while not shutdown_event.is_set():
        fail_sleep = 1
        try:
            worker.work(poll_timeout=5.0)
        except gearman.errors.ServerUnavailable as inst:
            logger.error(
                "Gearman server is unavailable: %s. Retrying in %d seconds.",
                inst.args,
                fail_sleep,
            )
            time.sleep(fail_sleep)
            if fail_sleep < fail_max_sleep:
                fail_sleep += fail_sleep_incrementor
