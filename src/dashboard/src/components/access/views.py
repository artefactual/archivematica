# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64
from functools import wraps
import json
import logging
import os
import uuid

import django.http
from django.shortcuts import redirect
from django.utils import timezone

from agentarchives.archivesspace import ArchivesSpaceError, AuthenticationError

from components import helpers
from components.ingest.views_as import get_as_system_client
import components.filesystem_ajax.views as filesystem_views
from main.models import (
    SIP,
    SIPArrange,
    SIPArrangeAccessMapping,
    ArchivesSpaceDigitalObject,
    DublinCore,
)

logger = logging.getLogger("archivematica.dashboard")

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Access
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def _authenticate_to_archivesspace(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            client = get_as_system_client()
        except AuthenticationError:
            response = {
                "success": False,
                "message": "Unable to authenticate to ArchivesSpace server using the default user! Check administrative settings.",
            }
            return django.http.HttpResponseServerError(
                json.dumps(response), content_type="application/json"
            )
        except ArchivesSpaceError:
            response = {
                "success": False,
                "message": "Unable to connect to ArchivesSpace server at the default location! Check administrative settings.",
            }
            return django.http.HttpResponseServerError(
                json.dumps(response), content_type="application/json"
            )
        return func(client, *args, **kwargs)

    return wrapper


def _normalize_record_id(record_id):
    """
    Normalizes a record ID that has been mangled for a URL.

    ArchivesSpace record IDs are URL fragments, in the format /repository/n/type/n.
    The slashes are replaced by dashes so that they can be conveniently passed in URLs within this module;
    this function transforms them back into the original format.
    """
    return record_id.replace("-", "/")


def _get_arrange_path(func):
    @wraps(func)
    def wrapper(request, record_id=""):
        try:
            mapping = SIPArrangeAccessMapping.objects.get(
                system=SIPArrangeAccessMapping.ARCHIVESSPACE,
                identifier=_normalize_record_id(record_id),
            )
            return func(request, mapping)
        except SIPArrangeAccessMapping.DoesNotExist:
            response = {
                "success": False,
                "message": "No SIP Arrange mapping exists for record {}".format(
                    record_id
                ),
            }
            return helpers.json_response(response, status_code=404)

    return wrapper


def _get_or_create_arrange_path(func):
    @wraps(func)
    def wrapper(request, record_id=""):
        mapping = create_arranged_directory(record_id)
        return func(request, mapping)

    return wrapper


def _get_sip(func):
    @wraps(func)
    def wrapper(request, mapping):
        arrange = SIPArrange.objects.get(
            arrange_path=os.path.join(mapping.arrange_path, "")
        )
        if arrange.sip is None:
            arrange.sip = SIP.objects.create(uuid=(uuid.uuid4()), currentpath=None)
            arrange.save()
        return func(request, arrange.sip)

    return wrapper


@_authenticate_to_archivesspace
def all_records(client, request):
    page = request.GET.get("page", 1)
    page_size = request.GET.get("page_size", 30)
    search_pattern = request.GET.get("title", "")
    identifier = request.GET.get("identifier", "")

    records = client.find_collections(
        search_pattern=search_pattern,
        identifier=identifier,
        page=page,
        page_size=page_size,
    )

    for i, r in enumerate(records):
        records[i] = _get_sip_arrange_children(r)

    return helpers.json_response(records)


@_authenticate_to_archivesspace
def record(client, request, record_id=""):
    if request.method == "PUT":
        try:
            new_record = json.load(request)
        except ValueError:
            response = {
                "success": False,
                "message": "No JSON object could be decoded from request body.",
            }
            return helpers.json_response(response, status_code=400)

        try:
            client.edit_record(new_record)
        except ArchivesSpaceError as e:
            return helpers.json_response(
                {"sucess": False, "message": str(e)}, status_code=500
            )
        return helpers.json_response({"success": True, "message": "Record updated."})
    elif request.method == "GET":
        record_id = _normalize_record_id(record_id)

        try:
            records = client.get_resource_component_and_children(
                record_id, recurse_max_level=3
            )
            return helpers.json_response(records)
        except ArchivesSpaceError as e:
            return helpers.json_response(
                {"success": False, "message": str(e)}, status_code=400
            )
    elif request.method == "DELETE":
        # Delete associated SIPArrange entries
        try:
            mapping = SIPArrangeAccessMapping.objects.get(
                system=SIPArrangeAccessMapping.ARCHIVESSPACE,
                identifier=_normalize_record_id(record_id),
            )
        except SIPArrangeAccessMapping.DoesNotExist:
            logger.debug("No access mapping for %s", record_id)
        else:
            filesystem_views.delete_arrange(
                request, filepath=mapping.arrange_path + "/"
            )
        # Delete in Aspace
        return helpers.json_response(
            client.delete_record(_normalize_record_id(record_id))
        )


@_authenticate_to_archivesspace
def record_children(client, request, record_id=""):
    record_id = _normalize_record_id(record_id)

    if request.method == "POST":
        new_record_data = json.load(request)
        try:
            notes = new_record_data.get("notes", [])
            new_id = client.add_child(
                record_id,
                title=new_record_data.get("title", ""),
                level=new_record_data.get("level", ""),
                start_date=new_record_data.get("start_date", ""),
                end_date=new_record_data.get("end_date", ""),
                date_expression=new_record_data.get("date_expression", ""),
                notes=notes,
            )
        except ArchivesSpaceError as e:
            response = {"success": False, "message": str(e)}
            return helpers.json_response(response, status_code=400)
        response = {
            "success": True,
            "id": new_id,
            "message": "New record successfully created",
        }
        return helpers.json_response(response)
    elif request.method == "GET":
        records = client.get_resource_component_and_children(
            record_id, recurse_max_level=3
        )
        records = _get_sip_arrange_children(records)
        return helpers.json_response(records["children"])


def get_digital_object_component_path(record_id, component_id, create=True):
    mapping = create_arranged_directory(record_id)
    component_path = os.path.join(
        mapping.arrange_path, "digital_object_component_{}".format(component_id), ""
    )
    if create:
        filesystem_views.create_arrange_directories([component_path])

    return component_path


@_authenticate_to_archivesspace
def digital_object_components(client, request, record_id=""):
    """
    List, modify or view the digital object components associated with the record `record_id`.

    GET:
    Returns a list of all digital object components in the database associated with `record_id`.
    These are returned as dictionaries containing the keys `id`, `label`, and `title`.

    POST:
    Creates a new digital object component associated with `record_id`.
    The `label` and `title` of the new object, and the `uuid` of a SIP with which the component should be associated, can be specified by including a JSON document in the request body with values in those keys.

    PUT:
    Updates an existing digital object component, using `title` and `label` values in a JSON document in the request body.
    The `component_id` to the component to edit must be specified in the request body.
    """
    if request.method == "POST":
        record = json.load(request)
        component = ArchivesSpaceDigitalObject.objects.create(
            resourceid=_normalize_record_id(record_id),
            sip_id=record.get("uuid"),
            label=record.get("label", ""),
            title=record.get("title", ""),
        )

        try:
            access_path = get_digital_object_component_path(
                record_id, component.id, create=True
            )
        except ValueError as e:
            component.delete()
            response = {"success": False, "message": str(e)}
            return helpers.json_response(response, status_code=400)

        response = {
            "success": True,
            "message": "Digital object component successfully created",
            "component_id": component.id,
            "component_path": access_path,
        }
        return helpers.json_response(response)
    elif request.method == "GET":
        components = list(
            ArchivesSpaceDigitalObject.objects.filter(
                resourceid=_normalize_record_id(record_id), started=False
            ).values("id", "resourceid", "label", "title")
        )
        for component in components:
            access_path = get_digital_object_component_path(record_id, component["id"])
            component["path"] = access_path
            component["type"] = "digital_object"
        return helpers.json_response(components)
    elif request.method == "PUT":
        record = json.load(request)
        try:
            component_id = record["component_id"]
        except KeyError:
            response = {"success": False, "message": "No component_id was specified!"}
            return helpers.json_response(response, status_code=400)

        try:
            component = ArchivesSpaceDigitalObject.objects.get(id=component_id)
        except ArchivesSpaceDigitalObject.DoesNotExist:
            response = {
                "success": False,
                "message": "No digital object component exists with the specified ID: {}".format(
                    component_id
                ),
            }
            return helpers.json_response(response, status_code=404)
        else:
            component.label = record.get("label", "")
            component.title = record.get("title", "")
            component.save()
            return django.http.HttpResponse(status=204)


def _get_sip_arrange_children(record):
    """ Recursively check for SIPArrange associations. """
    try:
        mapping = SIPArrangeAccessMapping.objects.get(
            system=SIPArrangeAccessMapping.ARCHIVESSPACE, identifier=record["id"]
        )
        record["path"] = mapping.arrange_path
        record["children"] = record["children"] or []
        record["has_children"] = True
    except (
        SIPArrangeAccessMapping.MultipleObjectsReturned,
        SIPArrangeAccessMapping.DoesNotExist,
    ):
        pass
    if record["children"]:  # record['children'] may be False
        for i, r in enumerate(record["children"]):
            record["children"][i] = _get_sip_arrange_children(r)
    record["has_children"] = (
        record["has_children"]
        or ArchivesSpaceDigitalObject.objects.filter(resourceid=record["id"]).exists()
    )
    return record


@_authenticate_to_archivesspace
def get_levels_of_description(client, request):
    levels = client.get_levels_of_description()
    return helpers.json_response(levels)


def create_arranged_directory(record_id):
    """
    Creates a directory to house an arranged SIP associated with `record_id`.

    If a mapping already exists, returns the existing mapping.
    Otherwise, creates one along with a directory in the arranged directory tree.
    """
    identifier = _normalize_record_id(record_id)
    mapping, created = SIPArrangeAccessMapping.objects.get_or_create(
        system=SIPArrangeAccessMapping.ARCHIVESSPACE, identifier=identifier
    )
    if created:
        try:
            filepath = (
                "/arrange/" + record_id + str(uuid.uuid4())
            )  # TODO: get this from the title?
            filesystem_views.create_arrange_directories([filepath])
        except ValueError:
            mapping.delete()
            return
        else:
            mapping.arrange_path = filepath
            mapping.save()

    return mapping


def access_create_directory(request, record_id=""):
    """
    Creates an arranged SIP directory for record `record_id`.
    """
    mapping = create_arranged_directory(record_id)
    if mapping is not None:
        response = {
            "success": True,
            "message": "Creation successful.",
            "path": mapping.arrange_path,
        }
        status_code = 201
    else:
        response = {"success": False, "message": "Could not create arrange directory."}
        status_code = 400
    return helpers.json_response(response, status_code=status_code)


@_get_or_create_arrange_path
@_get_sip
def access_sip_rights(request, sip):
    return redirect("rights_ingest:index", uuid=sip.uuid)


@_get_or_create_arrange_path
@_get_sip
def access_sip_metadata(request, sip):
    return redirect("ingest:ingest_metadata_list", uuid=sip.uuid)


def access_copy_to_arrange(request, record_id=""):
    """
    Copies a record from POST parameter `filepath` into the SIP arrange directory for the specified record, creating a directory if necessary.

    This should be used to copy files into the root of the SIP, while filesystem_ajax's version of this API should be used to copy deeper into the record.
    """
    mapping = create_arranged_directory(record_id)
    if mapping is None:
        response = {"success": False, "message": "Unable to create directory."}
        return helpers.json_response(response, status_code=400)
    sourcepath = base64.b64decode(request.POST.get("filepath", "")).lstrip("/")
    return filesystem_views.copy_to_arrange(
        request, sourcepath=sourcepath, destination=mapping.arrange_path + "/"
    )


@_get_arrange_path
def access_arrange_contents(request, mapping):
    """
    Lists the files in the root of the SIP arrange directory associated with this record.
    """
    return filesystem_views.arrange_contents(request, path=mapping.arrange_path + "/")


@_get_arrange_path
@_authenticate_to_archivesspace
def access_arrange_start_sip(client, request, mapping):
    """
    Starts the SIP associated with this record.
    """
    try:
        arrange = SIPArrange.objects.get(
            arrange_path=os.path.join(mapping.arrange_path, "")
        )
    except SIPArrange.DoesNotExist:
        response = {
            "success": False,
            "message": "No SIP Arrange object exists for record {}".format(
                mapping.identifier
            ),
        }
        return helpers.json_response(response, status_code=404)

    # Get metadata from ArchivesSpace
    archival_object = client.get_record(mapping.identifier)
    logger.debug("archival object %s", archival_object)
    # dc.creator is sort_name of the resource's linked_agent with role: creator
    resource = client.get_record(archival_object["resource"]["ref"])
    logger.debug("resource %s", resource)
    creators = [
        agent for agent in resource["linked_agents"] if agent["role"] == "creator"
    ]
    if creators:
        creator = client.get_record(creators[0]["ref"])
        logger.debug("creator %s", creator)
        creator = creator["display_name"]["sort_name"]
    else:
        response = {
            "success": False,
            "message": "Unable to fetch ArchivesSpace creator",
        }
        return helpers.json_response(response, status_code=502)
    # dc.description is general note's content
    notes = [n for n in archival_object["notes"] if n["type"] == "odd"]
    description = notes[0]["subnotes"][0]["content"] if notes else ""
    # dc.relation is parent archival object's display names
    relation = []
    parent = archival_object.get("parent", {}).get("ref")
    while parent:
        parent_obj = client.get_record(parent)
        parent_title = (
            parent_obj["title"]
            if parent_obj.get("title")
            else parent_obj["display_string"]
        )
        relation = [parent_title] + relation
        parent = parent_obj.get("parent", {}).get("ref")
    relation = " - ".join(relation)

    # Create digital objects in ASpace related to the resource instead of digital object components
    for do in ArchivesSpaceDigitalObject.objects.filter(
        resourceid=mapping.identifier, started=False
    ):
        new_do = client.add_digital_object(mapping.identifier, str(uuid.uuid4()))
        do.remoteid = new_do["id"]
        do.save()
    sip_uuid = arrange.sip_id
    sip_name = json.load(request).get("sip_name", "")
    status_code, response = filesystem_views.copy_from_arrange_to_completed_common(
        filepath=mapping.arrange_path + "/", sip_uuid=sip_uuid, sip_name=sip_name
    )

    if not response.get("error"):
        sip_uuid = response["sip_uuid"]
        logger.debug("New SIP UUID %s", sip_uuid)
        # Update ArchivesSpaceDigitalObject with new SIP UUID
        ArchivesSpaceDigitalObject.objects.filter(
            resourceid=mapping.identifier, started=False
        ).update(started=True, sip_id=response["sip_uuid"])
        # Create new SIP-level DC with ArchivesSpace metadata
        DublinCore.objects.create(
            metadataappliestotype_id="3e48343d-e2d2-4956-aaa3-b54d26eb9761",  # SIP
            metadataappliestoidentifier=sip_uuid,
            title=archival_object["display_string"],
            creator=creator,
            date=str(timezone.now().year),
            description=description,
            rights="This content may be under copyright. Researchers are responsible for determining the appropriate use or reuse of materials.",
            relation=relation,
        )

    return helpers.json_response(response, status_code=status_code)
