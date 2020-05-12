# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from functools import wraps
import json
import logging

from django.contrib import messages
from django.urls import reverse
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    HttpResponseServerError,
)
from django.utils.translation import ugettext as _

from contrib.mcp.client import MCPClient
from components import advanced_search
from main import models

from agentarchives.archivesspace import (
    ArchivesSpaceError,
    ArchivesSpaceClient,
    AuthenticationError,
    ConnectionError,
)

from components.ingest import pair_matcher

logger = logging.getLogger("archivematica.dashboard")


def get_as_system_client():
    config = models.DashboardSetting.objects.get_dict("upload-archivesspace_v0.0")

    config_err = ArchivesSpaceError(
        "ArchivesSpace has not been configured properly" " - base URL is missing"
    )
    try:
        base_url = config["base_url"]
    except KeyError:
        raise config_err
    if not base_url:
        raise config_err

    return ArchivesSpaceClient(
        host=base_url,
        user=config["user"],
        passwd=config["passwd"],
        repository=config["repository"],
    )


def _get_reset_view(uuid):
    if (
        models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(
            dipuuid=uuid
        ).count()
        > 0
    ):
        return "ingest:ingest_upload_as_reset"


def _authenticate_to_archivesspace(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            client = get_as_system_client()
        except AuthenticationError:
            return HttpResponseServerError(
                "Unable to authenticate to ArchivesSpace server using the default user! Check administrative settings."
            )
        except ConnectionError:
            return HttpResponseServerError(
                "Unable to connect to ArchivesSpace server at the default location! Check administrative settings."
            )

        return func(client, *args, **kwargs)

    return wrapper


@_authenticate_to_archivesspace
def ingest_upload_as(client, request, uuid):
    query = request.GET.get("query", "").strip()
    identifier = request.GET.get("identifier", "").strip()
    page = request.GET.get("page", 1)
    sort = request.GET.get("sort")
    search_params = advanced_search.extract_url_search_params_from_request(request)

    return pair_matcher.list_records(
        client,
        request,
        query,
        identifier,
        page,
        sort,
        search_params,
        "ingest/as/resource_list.html",
        _get_reset_view(uuid),
        uuid,
    )


def ingest_upload_as_save(request, uuid):
    return pair_matcher.pairs_saved_response(ingest_upload_as_save_to_db(request, uuid))


def ingest_upload_as_reset(request, uuid):
    models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(dipuuid=uuid).delete()
    return HttpResponseRedirect(reverse("ingest:ingest_upload_as", args=[uuid]))


def ingest_upload_as_save_to_db(request, uuid):
    saved = 0

    # delete existing mapping, if any, for this DIP
    models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(dipuuid=uuid).delete()

    pairs = pair_matcher.getDictArray(request.POST, "pairs")

    keys = sorted(pairs.keys())

    for key in keys:
        models.ArchivesSpaceDIPObjectResourcePairing.objects.create(
            dipuuid=pairs[key]["DIPUUID"],
            fileuuid=pairs[key]["objectUUID"],
            resourceid=pairs[key]["resourceId"],
        )
        saved = saved + 1

    return saved


@_authenticate_to_archivesspace
def ingest_upload_as_resource(client, request, uuid, resource_id):
    query = request.GET.get("query", "").strip()
    page = request.GET.get("page", 1)
    sort = request.GET.get("sort")
    search_params = advanced_search.extract_url_search_params_from_request(request)

    return pair_matcher.render_resource(
        client,
        request,
        resource_id,
        query,
        page,
        sort,
        search_params,
        "ingest:ingest_upload_as_match_dip_objects_to_resource_levels",
        "ingest/as/resource_detail.html",
        _get_reset_view(uuid),
        uuid,
    )


@_authenticate_to_archivesspace
def ingest_upload_as_resource_component(client, request, uuid, resource_component_id):
    query = request.GET.get("query", "").strip()
    page = request.GET.get("page", 1)
    sort = request.GET.get("sort")
    search_params = advanced_search.extract_url_search_params_from_request(request)

    return pair_matcher.render_resource_component(
        client,
        request,
        resource_component_id,
        query,
        page,
        sort,
        search_params,
        "ingest:ingest_upload_as_match_dip_objects_to_resource_component_levels",
        "ingest/as/resource_component.html",
        _get_reset_view(uuid),
        uuid,
    )


def _format_pair(client, resourceid, fileuuid):
    return {
        "resource_id": resourceid,
        "file_uuid": fileuuid,
        # Returns verbose details about the resource/component, required
        # in order to populate the pair matching UI.
        "resource": client.get_resource_component_children(resourceid),
    }


@_authenticate_to_archivesspace
def ingest_upload_as_match_dip_objects_to_resource_levels(
    client, request, uuid, resource_id
):
    # Locate existing matches for display in the "Pairs" panel
    pairs = models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(dipuuid=uuid)
    matches = [_format_pair(client, pair.resourceid, pair.fileuuid) for pair in pairs]

    parent_type, parent_id = client.find_parent_id_for_component(resource_id)
    if parent_type == type(client).RESOURCE:
        parent_url = "ingest:ingest_upload_as_resource"
    else:
        parent_url = "ingest:ingest_upload_as_resource_component"

    return pair_matcher.match_dip_objects_to_resource_levels(
        client,
        request,
        resource_id,
        "ingest/as/match.html",
        parent_id,
        parent_url,
        _get_reset_view(uuid),
        uuid,
        matches=matches,
    )


@_authenticate_to_archivesspace
def ingest_upload_as_match_dip_objects_to_resource_component_levels(
    client, request, uuid, resource_component_id
):
    # Locate existing matches for display in the "Pairs" panel
    pairs = models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(dipuuid=uuid)
    matches = [_format_pair(client, pair.resourceid, pair.fileuuid) for pair in pairs]

    parent_type, parent_id = client.find_parent_id_for_component(resource_component_id)
    if parent_type == type(client).RESOURCE:
        parent_url = "ingest:ingest_upload_as_resource"
    else:
        parent_url = "ingest:ingest_upload_as_resource_component"

    return pair_matcher.match_dip_objects_to_resource_component_levels(
        client,
        request,
        resource_component_id,
        "ingest/as/match.html",
        parent_id,
        parent_url,
        _get_reset_view(uuid),
        uuid,
        matches=matches,
    )


@_authenticate_to_archivesspace
def ingest_upload_as_review_matches(client, request, uuid):
    pairs = models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(dipuuid=uuid)
    matches = [_format_pair(client, pair.resourceid, pair.fileuuid) for pair in pairs]

    return pair_matcher.review_matches(
        client, request, "ingest/as/review_matches.html", uuid, matches=matches
    )


def ingest_upload_as_match(request, uuid):
    try:
        payload = json.load(request)
    except ValueError:
        payload = {}
    resource_id = payload.get("resource_id")
    file_uuid = payload.get("file_uuid")

    if not resource_id or not file_uuid:
        return HttpResponseBadRequest(
            "Both a resource_id and file_uuid must be specified."
        )

    if request.method == "POST":
        criteria = {"dipuuid": uuid, "fileuuid": file_uuid}
        # Ensure that this file hasn't already been matched before saving to the DB
        records = models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(
            **criteria
        )
        if records.count() < 1:
            models.ArchivesSpaceDIPObjectResourcePairing.objects.create(
                dipuuid=uuid, resourceid=resource_id, fileuuid=file_uuid
            )
            return HttpResponse(status=201)
        else:
            return HttpResponse(status=409)
    elif request.method == "DELETE":
        rows = models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(
            dipuuid=uuid, resourceid=resource_id, fileuuid=file_uuid
        )
        with open("/tmp/delete.log", "a") as log:
            print(
                "Resource",
                resource_id,
                "File",
                "file_uuid",
                "matches",
                rows.count(),
                file=log,
            )
        models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(
            dipuuid=uuid, resourceid=resource_id, fileuuid=file_uuid
        ).delete()

        return HttpResponse(status=204)
    else:
        return HttpResponse(status=405)


def complete_matching(request, uuid):
    """Complete the process by moving to the ArchivesSpace upload chain.

    This is the final step that we execute when the user has reviewed the
    matchings and submits the form. It only accepts POST because the action
    performed is not idempotent.
    """
    if request.method != "POST":
        return HttpResponse(status=405)
    try:
        client = MCPClient(request.user)
        client.execute_unit(
            uuid,
            # Microservice: Upload DIP
            mscl_id="92879a29-45bf-4f0b-ac43-e64474f0f2f9",
            # Chain: Upload DIP to ArchivesSpace
            choice="3572f844-5e69-4000-a24b-4e32d3487f82",
        )
    except Exception as err:
        messages.error(
            request,
            _(
                "Operation failed, please try again later"
                " or contact your administrator."
            ),
        )
        logger.error("Upload DIP to ArchivesSpace failed: %s", err)
        return HttpResponseRedirect(
            reverse("ingest:ingest_upload_as_review_matches", args=[uuid])
        )
    return HttpResponseRedirect(reverse("ingest:ingest_index"))
