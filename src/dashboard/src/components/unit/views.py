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
from components import helpers
from contrib.mcp.client import MCPClient
from django.shortcuts import render
from main import models

LOGGER = logging.getLogger("archivematica.dashboard")


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
