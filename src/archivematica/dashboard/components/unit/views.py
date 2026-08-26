# This file is part of Archivematica.
#
# Copyright 2010-2016 Artefactual Systems Inc. <http://artefactual.com>
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

import django.http
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Exists
from django.db.models import OuterRef
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_GET

from archivematica.dashboard.components import helpers
from archivematica.dashboard.contrib.mcp.client import MCPClient
from archivematica.dashboard.contrib.mcp.client import RPCGearmanClientError
from archivematica.dashboard.main import models

LOGGER = logging.getLogger("archivematica.dashboard")

PROCESSING_UNIT_TYPES = {
    "transfer": (models.Transfer, "Transfer"),
    "ingest": (models.SIP, "SIP"),
}

JOB_HISTORY_UNIT_TYPES = {
    "transfer": ("unitTransfer",),
    "ingest": ("unitSIP", "unitDIP"),
}
JOB_HISTORY_PAGE_SIZE = 50


def _processing_error(message, status_code):
    return helpers.json_response(
        {"error": True, "message": message}, status_code=status_code
    )


def processing_units(request, unit_type):
    """Return lightweight summaries for the Dashboard processing monitor."""
    if request.method != "GET":
        return django.http.HttpResponseNotAllowed(["GET"])

    _, rpc_type = PROCESSING_UNIT_TYPES[unit_type]
    try:
        results = MCPClient(request.user).get_units_summary(rpc_type)
    except RPCGearmanClientError:
        LOGGER.exception("Unable to fetch %s processing summaries", rpc_type)
        return _processing_error("Unable to fetch processing summaries.", 503)
    return helpers.json_response({"results": results})


def processing_unit_job_groups(request, unit_type, unit_uuid):
    """Return aggregated Job rows for one Dashboard processing unit."""
    if request.method != "GET":
        return django.http.HttpResponseNotAllowed(["GET"])

    unit_model, rpc_type = PROCESSING_UNIT_TYPES[unit_type]
    try:
        unit_exists = unit_model.objects.filter(uuid=unit_uuid, hidden=False).exists()
    except ValidationError:
        unit_exists = False
    if not unit_exists:
        return _processing_error(
            f"Unit with UUID {unit_uuid} does not exist",
            404,
        )

    try:
        results = MCPClient(request.user).get_unit_job_groups(rpc_type, str(unit_uuid))
    except RPCGearmanClientError:
        LOGGER.exception("Unable to fetch Job groups for unit %s", unit_uuid)
        return _processing_error("Unable to fetch Job groups.", 503)
    return helpers.json_response({"results": results})


@login_required
@require_GET
def job_history(request, unit_type, unit_uuid, link_uuid):
    """List all Jobs for a workflow link, including earlier attempts and statuses."""
    unit_model, _ = PROCESSING_UNIT_TYPES[unit_type]
    get_object_or_404(unit_model, uuid=unit_uuid, hidden=False)
    jobs = (
        models.Job.objects.filter(
            sipuuid=unit_uuid,
            unittype__in=JOB_HISTORY_UNIT_TYPES[unit_type],
            microservicechainlink=link_uuid,
        )
        .only(
            "jobuuid", "jobtype", "createdtime", "currentstep", "directory", "sipuuid"
        )
        .annotate(has_tasks=Exists(models.Task.objects.filter(job_id=OuterRef("pk"))))
        .order_by("-createdtime", "-jobuuid")
    )
    page = Paginator(jobs, JOB_HISTORY_PAGE_SIZE).get_page(request.GET.get("page"))
    # Evaluate only the requested page; Task output is loaded by each Job's
    # existing Tasks page, never by the monitor or this history listing.
    page.object_list = list(page.object_list)
    if not page.object_list:
        raise django.http.Http404("No Jobs found for this workflow link")
    first_job = page.object_list[0]
    return render(
        request,
        "unit/job_history.html",
        {
            "unit_type": unit_type,
            "uuid": unit_uuid,
            "name": first_job.get_directory_name(),
            "job_type": first_job.jobtype,
            "page": page,
        },
    )


def detail(request, unit_type, unit_uuid):
    """
    Display detailed information about the unit.

    :param unit_type: 'transfer' or 'ingest' for a Transfer or SIP respectively
    :param unit_uuid: UUID of the Transfer or SIP
    """
    jobs = models.Job.objects.filter(sipuuid=unit_uuid)
    name = jobs.get_directory_name()
    is_waiting = jobs.filter(currentstep=models.Job.STATUS_AWAITING_DECISION).exists()
    context = {
        "name": name,
        "is_waiting": is_waiting,
        "uuid": unit_uuid,
        "unit_type": unit_type,
    }
    if unit_type == "transfer":
        set_uuid = models.Transfer.objects.get(uuid=unit_uuid).transfermetadatasetrow_id
        context["set_uuid"] = set_uuid
    return render(request, unit_type + "/detail.html", context)


def microservices(request, unit_type, unit_uuid):
    """
    Display information about what microservices have run.

    :param unit_type: 'transfer' or 'ingest' for a Transfer or SIP respectively
    :param unit_uuid: UUID of the Transfer or SIP

    """
    client = MCPClient(request.user)
    resp = client.get_unit_status(unit_uuid)
    return render(
        request,
        unit_type + "/microservices.html",
        {
            "uuid": unit_uuid,
            "unit_type": unit_type,
            "name": resp.get("name"),
            "jobs": resp.get("jobs"),
        },
    )


UNIT_MODELS = {
    "transfer": models.Transfer,
    "ingest": models.SIP,
}


def mark_hidden(request, unit_type, unit_uuid):
    """
    Marks the unit as hidden to delete it.

    This endpoint assumes you are already logged in.

    :param unit_type: 'transfer' or 'ingest' for a Transfer or SIP respectively
    :param unit_uuid: UUID of the Transfer or SIP
    """
    if request.method not in ("DELETE",):
        return django.http.HttpResponseNotAllowed(["DELETE"])
    try:
        unit_model = UNIT_MODELS.get(unit_type)
    except AttributeError:
        return django.http.HttpResponseBadRequest("Unknown unit_type")
    try:
        count = (
            unit_model.objects.done()
            .filter(pk=unit_uuid, hidden=False)
            .update(hidden=True)
        )
        if not count:
            return django.http.JsonResponse({"removed": False}, status=409)
    except Exception:
        LOGGER.error(
            "Error setting %s %s to hidden", unit_type, unit_uuid, exc_info=True
        )
        return django.http.JsonResponse({"removed": False}, status=500)

    return helpers.json_response({"removed": True})


def mark_completed_hidden(request, unit_type):
    """Marks all units of type ``unit_type`` as hidden, if and only if the unit
    is completed or failed. This is what happens when the user clicks the
    "Remove all completed" button in the dashboard GUI.

    This endpoint assumes you are already logged in.

    :param unit_type: 'transfer' or 'ingest' for hiding of Transfers or SIPs,
        respectively
    """
    if request.method not in ("DELETE",):
        return django.http.HttpResponseNotAllowed(["DELETE"])
    try:
        unit_model = UNIT_MODELS.get(unit_type)
    except AttributeError:
        return django.http.HttpResponseBadRequest("Unknown unit_type")
    try:
        completed = helpers.completed_units_efficient(unit_type=unit_type)
        if completed:
            unit_model.objects.filter(uuid__in=completed).update(hidden=True)
        response = {"removed": completed}
        return helpers.json_response(response)
    except Exception:
        LOGGER.error(
            "Error setting completed %s units to hidden", unit_type, exc_info=True
        )
        return django.http.JsonResponse({"removed": False}, status=500)
