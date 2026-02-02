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
import json
import logging
import os
import re
import shutil
import uuid
from urllib.parse import urljoin

import requests
from django.conf import settings as django_settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms.models import modelformset_factory
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.generic import View

from archivematica.archivematicaCommon import storageService as storage_service
from archivematica.dashboard.components import decorators
from archivematica.dashboard.components import helpers
from archivematica.dashboard.components.ingest import forms as ingest_forms
from archivematica.dashboard.components.ingest.views_NormalizationReport import (
    getNormalizationReportQuery,
)
from archivematica.dashboard.contrib.mcp.client import MCPClient
from archivematica.dashboard.main import forms
from archivematica.dashboard.main import models

logger = logging.getLogger("archivematica.dashboard")

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Ingest
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def ingest_grid(request):
    try:
        storage_service.get_location(purpose="BL")
    except Exception:
        messages.warning(
            request,
            _(
                "Error retrieving originals directory locations: is the storage server running? Please contact an administrator."
            ),
        )
    return render(
        request,
        "ingest/grid.html",
        {
            "polling_interval": django_settings.POLLING_INTERVAL,
            "microservices_help": django_settings.MICROSERVICES_HELP,
            "job_statuses": dict(models.Job.STATUS),
        },
    )


class SipsView(View):
    def post(self, request):
        """
        Creates a new stub SIP object, and returns its UUID in a JSON response.
        """
        sip = models.SIP.objects.create(uuid=str(uuid.uuid4()), currentpath=None)
        return helpers.json_response({"success": True, "id": sip.uuid})


def ingest_status(request, uuid=None):
    response = {"objects": {}, "mcp": False}
    try:
        client = MCPClient(request.user)
        response["objects"] = client.get_sips_statuses()
    except Exception:
        pass
    else:
        response["mcp"] = True
    return HttpResponse(json.dumps(response), content_type="application/json")


def ingest_sip_metadata_type_id():
    return helpers.get_metadata_type_id_by_description("SIP")


@decorators.load_jobs  # Adds jobs, name
def ingest_metadata_list(request, uuid, jobs, name):
    # See MetadataAppliesToTypes table
    metadata = models.DublinCore.objects.filter(
        metadataappliestotype=ingest_sip_metadata_type_id(),
        metadataappliestoidentifier__exact=uuid,
    )

    return render(request, "ingest/metadata_list.html", locals())


def ingest_metadata_edit(request, uuid, id=None):
    if id:
        # If we have the ID of the DC object, use that - Edit
        dc = models.DublinCore.objects.get(pk=id)
    else:
        # Otherwise look for a SIP with the provided UUID, creating a new one
        # if needed.  Not using get_or_create because that save the empty
        # object, even if the form is not submitted.
        sip_type_id = ingest_sip_metadata_type_id()
        try:
            dc = models.DublinCore.objects.get(
                metadataappliestotype=sip_type_id, metadataappliestoidentifier=uuid
            )
            id = dc.id
        except (models.DublinCore.DoesNotExist, ValidationError):
            dc = models.DublinCore(
                metadataappliestotype=sip_type_id, metadataappliestoidentifier=uuid
            )

    # If the SIP is an AIC, use the AIC metadata form
    if "AIC" in models.SIP.objects.get(uuid=uuid).sip_type:
        form = ingest_forms.AICDublinCoreMetadataForm(request.POST or None, instance=dc)
        dc_type = "Archival Information Collection"
    else:
        form = ingest_forms.DublinCoreMetadataForm(request.POST or None, instance=dc)
        dc_type = "Archival Information Package"

    if form.is_valid():
        dc = form.save()
        dc.type = dc_type
        dc.save()
        return redirect("ingest:ingest_metadata_list", uuid)
    jobs = models.Job.objects.filter(sipuuid=uuid)
    name = jobs.get_directory_name()

    return render(request, "ingest/metadata_edit.html", locals())


def ingest_metadata_add_files(request, sip_uuid):
    source_directories = []
    try:
        source_directories = storage_service.get_location(purpose="TS")
    except Exception:
        messages.warning(
            request,
            _(
                "Error retrieving source directories: is the storage server running? Please contact an administrator."
            ),
        )
    else:
        logging.debug(f"Source directories found: {source_directories}")
        if not source_directories:
            messages.warning(
                request,
                _(
                    "No transfer source locations are available. Please contact an administrator."
                ),
            )
    # Get name of SIP from directory name of most recent job
    jobs = models.Job.objects.filter(sipuuid=sip_uuid)
    name = jobs.get_directory_name()

    editor_payload = None
    if source_directories:
        dirs = {}
        for directory in source_directories:
            dir_uuid = directory.get("uuid")
            dir_path = directory.get("path")
            if dir_uuid and dir_path:
                dirs[dir_uuid] = dir_path
        if dirs:
            editor_payload = {
                "sipUUID": sip_uuid,
                "sourceDirectories": dirs,
            }

    context = {
        "name": name,
        "sip_uuid": sip_uuid,
        "editor_payload": editor_payload,
    }
    return render(request, "ingest/metadata_add_files.html", context)


def aic_metadata_add(request, uuid):
    sip_type_id = ingest_sip_metadata_type_id()
    try:
        dc = models.DublinCore.objects.get(
            metadataappliestotype=sip_type_id, metadataappliestoidentifier=uuid
        )
        id = dc.id
    except (models.DublinCore.DoesNotExist, ValidationError):
        dc = models.DublinCore(
            metadataappliestotype=sip_type_id, metadataappliestoidentifier=uuid
        )

    form = ingest_forms.AICDublinCoreMetadataForm(request.POST or None, instance=dc)
    if form.is_valid():
        # Save the metadata
        dc = form.save()
        dc.type = "Archival Information Collection"
        dc.save()

        # Start the MicroServiceChainLink for the AIC
        shared_dir = django_settings.SHARED_DIRECTORY
        source = os.path.join(shared_dir, "tmp", uuid)

        watched_dir = django_settings.WATCH_DIRECTORY
        name = dc.title if dc.title else dc.identifier
        name = slugify(name).replace("-", "_")
        dir_name = f"{name}-{uuid}"
        destination = os.path.join(watched_dir, "system", "createAIC", dir_name)

        destination_db = destination.replace(shared_dir, "%sharedPath%") + "/"
        models.SIP.objects.filter(uuid=uuid).update(currentpath=destination_db)
        shutil.move(source, destination)
        return redirect("ingest:ingest_index")

    name = dc.title or "New AIC"
    aic = True
    return render(request, "ingest/metadata_edit.html", locals())


def ingest_metadata_event_detail(request, uuid):
    EventDetailFormset = modelformset_factory(
        models.Event, form=forms.EventDetailForm, extra=0
    )
    manual_norm_files = models.File.objects.filter(sip=uuid).filter(
        originallocation__icontains="manualNormalization/preservation"
    )
    events = models.Event.objects.filter(
        derivation__derived_file__in=manual_norm_files
    ).order_by("file_uuid__currentlocation")
    formset = EventDetailFormset(request.POST or None, queryset=events)

    if formset.is_valid():
        formset.save()
        return redirect("unit:detail", unit_type="ingest", unit_uuid=uuid)

    # Add path for original and derived files to each form
    for form in formset:
        form.original_file = form.instance.file_uuid.originallocation.decode().replace(
            "%transferDirectory%objects/", "", 1
        )
        form.derived_file = (
            form.instance.file_uuid.derived_file_set.filter(
                derived_file__filegrpuse="preservation"
            )
            .get()
            .derived_file.originallocation.decode()
            .replace("%transferDirectory%objects/", "", 1)
        )

    # Get name of SIP from directory name of most recent job
    jobs = models.Job.objects.filter(sipuuid=uuid)
    name = jobs.get_directory_name()
    return render(request, "ingest/metadata_event_detail.html", locals())


def delete_context(request, uuid, id):
    cancel_url = reverse("ingest:ingest_metadata_list", args=[uuid])
    return {
        "action": "Delete",
        "prompt": _("Are you sure you want to delete this metadata?"),
        "cancel_url": cancel_url,
    }


@decorators.confirm_required("simple_confirm.html", delete_context)
def ingest_metadata_delete(request, uuid, id):
    try:
        models.DublinCore.objects.get(pk=id).delete()
        messages.info(request, _("Deleted."))
        return redirect("ingest:ingest_metadata_list", uuid)
    except Exception:
        raise Http404


def ingest_upload_destination_url_check(request):
    settings = models.DashboardSetting.objects.get_dict("upload-qubit_v0.0")
    url = settings.get("url")

    # add target to URL
    url = urljoin(url, request.GET.get("target", ""))

    # make request for URL
    response = requests.request(
        "GET", url, timeout=django_settings.AGENTARCHIVES_CLIENT_TIMEOUT
    )

    # return resulting status code from request
    return HttpResponse(response.status_code)


def ingest_upload(request, uuid):
    """
    The upload DIP is actually not executed here, but some data is storaged
    in the database (permalink, ...), used later by upload-qubit.py
    - GET = It could be used to obtain DIP size
    - POST = Create Accesses tuple with permalink
    """
    if not models.SIP.objects.filter(uuid__exact=uuid).exists():
        raise Http404

    if request.method == "POST":
        if "target" in request.POST:
            try:
                access = models.Access.objects.get(sipuuid=uuid)
            except Exception:
                access = models.Access(sipuuid=uuid)
            access.target = request.POST["target"]
            access.save()
            response = {"ready": True}
            return helpers.json_response(response)
    elif request.method == "GET":
        try:
            access = models.Access.objects.get(sipuuid=uuid)
        except Exception:
            raise Http404
        return helpers.json_response({"target": access.target})

    return HttpResponseNotAllowed(["GET", "POST"])


def derivative_validation_report(obj):
    """Return a 4-tuple indicating whether
    i.   preservation derivative validation was attempted,
    ii.  preservation derivative validation failed,
    iii. access derivative validation was attempted,
    iv.  access derivative validation failed,
    ::param dict obj:: encodes information about a specific file and any
        normalization and derivative validation events performed on it.
    """
    file_id = obj["fileID"]
    (
        preservation_failed,
        preservation_attempted,
    ) = derivative_validation_report_by_purpose(
        obj["preservation_derivative_validation_task_exitCode"], file_id
    )
    access_failed, access_attempted = derivative_validation_report_by_purpose(
        obj["access_derivative_validation_task_exitCode"], file_id
    )
    return (
        preservation_attempted,
        preservation_failed,
        access_attempted,
        access_failed,
    )


def derivative_validation_report_by_purpose(exit_code, file_id):
    """Return a 2-tuple indicating whether derivative validation failed and was
    attempted, respectively.
    """
    if file_id:
        if exit_code == 0:
            return 0, 1
        elif exit_code == 1:
            return 1, 1
        elif exit_code in (2, None):
            return 0, 0
        else:
            raise ValueError(
                "Derivative validation client script returned an"
                " exit code not in 0, 1, 2: %s" % exit_code
            )
    else:
        return 0, 0


def ingest_normalization_report(request, uuid, current_page=None):
    jobs = models.Job.objects.filter(sipuuid=uuid)
    sipname = jobs.get_directory_name()

    objects = getNormalizationReportQuery(sipUUID=uuid)
    for o in objects:
        (
            o["preservation_derivative_validation_attempted"],
            o["preservation_derivative_validation_failed"],
            o["access_derivative_validation_attempted"],
            o["access_derivative_validation_failed"],
        ) = derivative_validation_report(o)

    results_per_page = 10

    if current_page is None:
        current_page = 1

    page = helpers.pager(objects, results_per_page, current_page)
    hit_count = len(objects)

    return render(request, "ingest/normalization_report.html", locals())


def ingest_browse(request, browse_type, jobuuid):
    watched_dir = django_settings.WATCH_DIRECTORY
    if browse_type == "normalization":
        title = _("Review normalization")
        directory = os.path.join(watched_dir, "approveNormalization")
    elif browse_type == "aip":
        title = _("Review AIP")
        directory = os.path.join(watched_dir, "storeAIP")
    elif browse_type == "dip":
        title = _("Review DIP")
        directory = os.path.join(watched_dir, "uploadedDIPs")
    else:
        raise Http404

    jobs = models.Job.objects.filter(jobuuid=jobuuid)
    name = jobs.get_directory_name()

    return render(request, "ingest/aip_browse.html", locals())


_REGEX_BAGIT_MANIFESTS = re.compile(
    r"""^(
           (tag)?manifest-\w+ |
           bag(it|-info)
         )\.txt$
    """,
    re.VERBOSE,
)


def transfer_file_download(request, uuid):
    # get file basename
    try:
        file = models.File.objects.get(uuid=uuid)
    except Exception:
        raise Http404

    shared_directory_path = django_settings.SHARED_DIRECTORY
    transfer = models.Transfer.objects.get(uuid=file.transfer.uuid)
    path_to_transfer = transfer.currentlocation.replace(
        "%sharedPath%", shared_directory_path
    )
    path_to_file = file.currentlocation.decode().replace(
        "%transferDirectory%", path_to_transfer
    )
    return helpers.send_file(request, path_to_file)
