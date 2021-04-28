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

import json
import logging
import os
import re
import requests
import shutil
import uuid

from django.conf import settings as django_settings
from django.contrib import messages
from django.urls import reverse
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.utils.text import slugify
from django.utils.translation import ugettext as _
from django.views.generic import View
import six.moves.cPickle
from six.moves.urllib.parse import urljoin

from contrib.mcp.client import MCPClient
from components import advanced_search
from components import helpers
from components import decorators
from components.ingest import forms as ingest_forms
from components.ingest.views_NormalizationReport import getNormalizationReportQuery
from main import forms, models

from archivematicaFunctions import b64encode_string, escape
import elasticSearchFunctions
import storageService as storage_service

logger = logging.getLogger("archivematica.dashboard")

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Ingest
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def _any_draggable(nodes):
    for node in nodes:
        children = node.get("children", [])
        if not node["not_draggable"] or _any_draggable(children):
            return True
    return False


def _adjust_directories_draggability(nodes):
    """Make directories not draggable only if all their children are not draggable."""
    for node in nodes:
        # Make directory nodes draggable by default
        if "relative_path" not in node:
            node["not_draggable"] = False
        children = node.get("children", [])
        if children:
            node["not_draggable"] = not _any_draggable(children)
            _adjust_directories_draggability(children)


def ingest_grid(request):
    try:
        storage_service.get_location(purpose="BL")
    except:
        messages.warning(
            request,
            _(
                "Error retrieving originals/arrange directory locations: is the storage server running? Please contact an administrator."
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
        except models.DublinCore.DoesNotExist:
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
    try:
        source_directories = storage_service.get_location(purpose="TS")
    except:
        messages.warning(
            request,
            _(
                "Error retrieving source directories: is the storage server running? Please contact an administrator."
            ),
        )
    else:
        logging.debug("Source directories found: {}".format(source_directories))
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

    return render(request, "ingest/metadata_add_files.html", locals())


def aic_metadata_add(request, uuid):
    sip_type_id = ingest_sip_metadata_type_id()
    try:
        dc = models.DublinCore.objects.get(
            metadataappliestotype=sip_type_id, metadataappliestoidentifier=uuid
        )
        id = dc.id
    except models.DublinCore.DoesNotExist:
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
        dir_name = "{name}-{uuid}".format(name=name, uuid=uuid)
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
        form.original_file = form.instance.file_uuid.originallocation.replace(
            "%transferDirectory%objects/", "", 1
        )
        form.derived_file = (
            form.instance.file_uuid.derived_file_set.filter(
                derived_file__filegrpuse="preservation"
            )
            .get()
            .derived_file.originallocation.replace("%transferDirectory%objects/", "", 1)
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
    except:
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
            except:
                access = models.Access(sipuuid=uuid)
            access.target = six.moves.cPickle.dumps(
                {"target": request.POST["target"]}, protocol=0
            )
            access.save()
            response = {"ready": True}
            return helpers.json_response(response)
    elif request.method == "GET":
        try:
            access = models.Access.objects.get(sipuuid=uuid)
            data = six.moves.cPickle.loads(str(access.target))
        except:
            raise Http404
        return helpers.json_response(data)

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
        o["location"] = escape(o["location"])
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


def _is_hidden(part):
    """Return whether a string must be hidden in the treeview."""
    if part in ("logs", "metadata"):
        return True
    if _REGEX_BAGIT_MANIFESTS.match(part):
        return True
    if part == "README.html":
        return True
    return False


def _es_results_to_directory_tree(path, return_list, not_draggable=False):
    # Helper function for transfer_backlog
    # Paths MUST be input in sorted order
    # Otherwise the same directory might end up with multiple entries
    parts = path.split("/", 1)
    if _is_hidden(parts[0]):
        not_draggable = True
    if len(parts) == 1:  # path is a file
        return_list.append(
            {
                "name": b64encode_string(parts[0]),
                "properties": {"not_draggable": not_draggable},
            }
        )
    else:
        node, others = parts
        node = b64encode_string(node)
        if not return_list or return_list[-1]["name"] != node:
            return_list.append(
                {
                    "name": node,
                    "properties": {"not_draggable": not_draggable, "object count": 0},
                    "children": [],
                }
            )
        this_node = return_list[-1]
        # Populate children list
        _es_results_to_directory_tree(
            others, this_node["children"], not_draggable=not_draggable
        )

        # Generate count of all non-directory objects in this tree
        object_count = sum(
            e["properties"].get("object count", 0) for e in this_node["children"]
        )
        object_count += len([e for e in this_node["children"] if not e.get("children")])

        this_node["properties"]["object count"] = object_count
        this_node["properties"]["display_string"] = "{} objects".format(object_count)
        # If any children of a dir are draggable, the whole dir should be
        # Otherwise, directories have the draggability of their first child
        this_node["properties"]["not_draggable"] = (
            this_node["properties"]["not_draggable"] and not_draggable
        )


def _is_draggable(parts):
    if parts[1] == "data":
        # the transfer is a bag (contains a "data" directory)
        if len(parts) > 2:
            # check if the child of "data" is hidden
            result = not _is_hidden(parts[2])
        else:
            # data is the final part and it's draggable
            result = True
    else:
        # the transfer is not a bag
        # check if the child of the transfer is hidden
        result = not _is_hidden(parts[1])
    return result


def _es_results_to_appraisal_tab_format(
    record, record_map, directory_list, not_draggable=False
):
    """
    Given a set of records from Elasticsearch, produces a list of records suitable for use with the appraisal tab.
    This function mutates a provided `directory_list`; it does not return a value.

    Elasticsearch results index only files; directories are inferred by splitting the filename and generating directory entries for each presumed directory.

    :param dict record: A record from Elasticsearch.
        This must be in the new format defined for Archivematica 1.6.
    :param dict record_map: A dictionary to be used to track created directory objects.
        This ensures that duplicate directories aren't created when processing multiple files.
    :param dict directory_list: A list of top-level directories to return in the results.
        This only contains directories which are not themselves contained within any other directories, e.g. transfers.
        This will be appended to by this function in lieu of returning a value.
    :param bool not_draggable: This property determines whether or not a given file should be able to be dragged in the user interface; passing this will override the default logic for determining if a file is draggable.
    """
    dir, fn = record["relative_path"].rsplit("/", 1)

    # Recursively create elements for this item's parent directory,
    # if not already present in the record map
    components = dir.split("/")
    directories = []
    while len(components) > 0:
        directories.insert(0, "/".join(components))
        components.pop(-1)

    parent = None
    for node in directories:
        node_parts = node.split("/")
        is_transfer = len(node_parts) == 1
        draggable = not not_draggable and (
            _is_draggable(node_parts) if not is_transfer else not not_draggable
        )
        if node not in record_map:
            dir_record = {
                "type": "transfer" if is_transfer else "directory",
                # have to artificially create directory IDs, since we don't assign those
                "id": str(uuid.uuid4()),
                "title": b64encode_string(os.path.basename(node)),
                "relative_path": b64encode_string(node),
                "not_draggable": not draggable,
                "object_count": 0,
                "children": [],
            }
            record_map[node] = dir_record
            # directory_list should consist only of top-level records
            if is_transfer:
                directory_list.append(dir_record)
        else:
            dir_record = record_map[node]

        if parent is not None and dir_record not in parent["children"]:
            parent["children"].append(dir_record)
            parent["object_count"] += 1

        parent = dir_record

    dir_parts = dir.split("/")
    draggable = not not_draggable and (
        _is_draggable(dir_parts) if (len(dir_parts) > 1) else not not_draggable
    )

    child = {
        "type": "file",
        "id": record["fileuuid"],
        "title": b64encode_string(fn),
        "relative_path": b64encode_string(record["relative_path"]),
        "size": record["size"],
        "tags": record["tags"],
        "bulk_extractor_reports": record["bulk_extractor_reports"],
        "not_draggable": _is_hidden(fn) or not draggable,
    }

    if record["modification_date"]:
        child["last_modified"] = record["modification_date"]

    if record["format"]:
        format = record["format"][0]  # TODO handle multiple format identifications
        child["format"] = format["format"]
        child["group"] = format["group"]
        child["puid"] = format["puid"]

    record_map[dir]["children"].append(child)
    record_map[dir]["object_count"] += 1


def transfer_backlog(request, ui):
    """
    AJAX endpoint to query for and return transfer backlog items.
    """
    es_client = elasticSearchFunctions.get_client()
    results = None

    # Return files which are in the backlog
    backlog_filter = {"bool": {"must": {"term": {"status": "backlog"}}}}
    # Omit files without UUIDs (metadata and logs directories):
    # - When the `hidemetadatalogs` param is sent from SIP arrange.
    if request.GET.get("hidemetadatalogs"):
        backlog_filter["bool"]["must_not"] = {"term": {"fileuuid": ""}}

    # Get search parameters from request
    if "query" not in request.GET:
        # Use backlog boolean filter as boolean query
        query = {"query": backlog_filter}
    else:
        queries, ops, fields, types = advanced_search.search_parameter_prep(request)

        try:
            query = advanced_search.assemble_query(
                queries, ops, fields, types, filters=[backlog_filter]
            )
        except:
            logger.exception("Error accessing index.")
            return HttpResponse("Error accessing index.")

    # perform search
    try:
        results = elasticSearchFunctions.search_all_results(
            es_client, body=query, index="transferfiles"
        )
    except:
        logger.exception("Error accessing index.")
        return HttpResponse("Error accessing index.")

    # Convert results into a more workable form
    results = elasticSearchFunctions.augment_raw_search_results(results)

    # Convert to a form JS can use:
    # [{'name': <filename>,
    #   'properties': {'not_draggable': False}},
    #  {'name': <directory name>,
    #   'properties': {'not_draggable': True, 'object count': 3, 'display_string': '3 objects'},
    #   'children': [
    #    {'name': <filename>,
    #     'properties': {'not_draggable': True}},
    #    {'name': <directory name>,
    #     'children': [...]
    #    }
    #   ]
    #  },
    # ]
    return_list = []
    directory_map = {}
    # _es_results_to_directory_tree requires that paths MUST be sorted
    results.sort(key=lambda x: x["relative_path"])
    for path in results:
        # If a path is in SIPArrange.original_path, then it shouldn't be draggable
        not_draggable = False
        if models.SIPArrange.objects.filter(
            original_path__endswith=path["relative_path"]
        ).exists():
            not_draggable = True
        if ui == "legacy":
            _es_results_to_directory_tree(
                path["relative_path"], return_list, not_draggable=not_draggable
            )
        else:
            _es_results_to_appraisal_tab_format(
                path, directory_map, return_list, not_draggable=not_draggable
            )

    if ui == "legacy":
        response = return_list
    else:
        _adjust_directories_draggability(return_list)
        response = {"formats": [], "transfers": return_list}  # TODO populate this

    # return JSON response
    return helpers.json_response(response)


def transfer_file_download(request, uuid):
    # get file basename
    try:
        file = models.File.objects.get(uuid=uuid)
    except:
        raise Http404

    shared_directory_path = django_settings.SHARED_DIRECTORY
    transfer = models.Transfer.objects.get(uuid=file.transfer.uuid)
    path_to_transfer = transfer.currentlocation.replace(
        "%sharedPath%", shared_directory_path
    )
    path_to_file = file.currentlocation.replace("%transferDirectory%", path_to_transfer)
    return helpers.send_file(request, path_to_file)
