# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import os

from django.conf import settings as django_settings
from django.urls import reverse
from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseRedirect
import xml.etree.ElementTree as ElementTree

from main import models
from components import helpers

from lazy_paged_sequence import LazyPagedSequence

PAGE_SIZE = 30


def _determine_reverse_sort_direction(sort):
    if sort is None or sort == "asc":
        return "desc"
    else:
        return "asc"


# TODO: move into helpers module at some point
# From http://www.ironzebra.com/news/23/converting-multi-dimensional-form-arrays-in-django


def getDictArray(post, name):
    dic = {}
    for k in post.keys():
        if k.startswith(name):
            rest = k[len(name) :]

            # split the string into different components
            parts = [p[:-1] for p in rest.split("[")][1:]
            id = int(parts[0])

            # add a new dictionary if it doesn't exist yet
            if id not in dic:
                dic[id] = {}

            # add the information to the dictionary
            dic[id][parts[1]] = post.get(k)
    return dic


def list_records(
    client,
    request,
    query,
    identifier,
    page_number,
    sort_by,
    search_params,
    list_redirect_target,
    reset_url,
    uuid,
):
    resources = LazyPagedSequence(
        lambda page, page_size: client.find_collections(
            search_pattern=query,
            identifier=identifier,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
        ),
        PAGE_SIZE,
        client.count_collections(query, identifier),
    )
    page = helpers.pager(resources, PAGE_SIZE, page_number)

    sort_direction = _determine_reverse_sort_direction(sort_by)

    return render(request, list_redirect_target, locals())


def pairs_saved_response(pairs_saved):
    if pairs_saved > 0:
        response = {"message": "Submitted successfully."}
    else:
        response = {"message": "No pairs saved."}

    return HttpResponse(
        json.JSONEncoder().encode(response), content_type="application/json"
    )


def render_resource(
    client,
    request,
    resource_id,
    query,
    page,
    sort_by,
    search_params,
    match_redirect_target,
    resource_detail_template,
    reset_url,
    uuid,
):
    resource_data = client.get_resource_component_and_children(
        resource_id,
        "collection",
        recurse_max_level=2,
        search_pattern=query,
        sort_by=sort_by,
    )

    sort_direction = _determine_reverse_sort_direction(sort_by)

    if resource_data["children"]:
        page = helpers.pager(resource_data["children"], PAGE_SIZE, page)

    if not resource_data["children"] and query == "":
        return HttpResponseRedirect(
            reverse(match_redirect_target, args=[uuid, resource_id])
        )
    else:
        return render(request, resource_detail_template, locals())


def render_resource_component(
    client,
    request,
    resource_component_id,
    query,
    page,
    sort_by,
    search_params,
    match_redirect_target,
    resource_detail_template,
    reset_url,
    uuid,
):
    resource_component_data = client.get_resource_component_and_children(
        resource_component_id,
        "description",
        recurse_max_level=2,
        search_pattern=query,
        sort_by=sort_by,
    )

    sort_direction = _determine_reverse_sort_direction(sort_by)

    if resource_component_data["children"]:
        page = helpers.pager(resource_component_data["children"], PAGE_SIZE, page)

    if not resource_component_data["children"] and query == "":
        return HttpResponseRedirect(
            reverse(match_redirect_target, args=[uuid, resource_component_id])
        )
    else:
        return render(
            request,
            resource_detail_template,
            {
                "match_redirect_target": match_redirect_target,
                "page": page,
                "query": query,
                "reset_url": reset_url,
                "resource_component_data": resource_component_data,
                "resource_component_id": resource_component_id,
                "search_params": search_params,
                "sort_by": sort_by,
                "sort_direction": sort_direction,
                "uuid": uuid,
            },
        )


def match_dip_objects_to_resource_levels(
    client,
    request,
    resource_id,
    match_template,
    parent_id,
    parent_url,
    reset_url,
    uuid,
    matches=[],
):
    # load object relative paths
    object_path_json = json.JSONEncoder().encode(
        ingest_upload_atk_get_dip_object_paths(uuid)
    )

    resource_data_json = json.JSONEncoder().encode(
        client.get_resource_component_and_children(resource_id)
    )

    matches_json = json.JSONEncoder().encode(matches)

    return render(request, match_template, locals())


def match_dip_objects_to_resource_component_levels(
    client,
    request,
    resource_component_id,
    match_template,
    parent_id,
    parent_url,
    reset_url,
    uuid,
    matches=[],
):
    # load object relative paths
    object_path_json = json.JSONEncoder().encode(
        ingest_upload_atk_get_dip_object_paths(uuid)
    )

    # load resource and child data
    resource_data_json = json.JSONEncoder().encode(
        client.get_resource_component_children(resource_component_id)
    )

    matches_json = json.JSONEncoder().encode(matches)

    return render(request, match_template, locals())


def remove_prefix(string, prefix):
    if string.startswith(prefix):
        return string[len(prefix) :]
    return string


def remove_objects_prefix(path):
    return remove_prefix(path, "objects/")


def remove_sip_dir_prefix(path):
    return remove_prefix(path, "%SIPDirectory%")


def remove_review_matches_prefixes(path):
    return remove_objects_prefix(remove_sip_dir_prefix(path))


def review_matches(client, request, template, uuid, matches=[]):
    object_paths = {
        file_.uuid: remove_review_matches_prefixes(file_.currentlocation)
        for file_ in models.File.objects.filter(sip=uuid)
    }
    for match in matches:
        try:
            match["object_path"] = object_paths[match["file_uuid"]]
        except KeyError:
            match["object_path"] = "Unable to locate a path for file {}".format(
                match["file_uuid"]
            )
    return render(request, template, {"uuid": uuid, "matches": matches})


def ingest_upload_atk_get_dip_object_paths(uuid):
    """Parse the DIP METS for original files and return a list of dicts with
    'uuid' and 'path' keys which valuate to the UUID of an original file and
    the relative path to that file, minus the 'objects/' prefix.
    """
    watch_dir = django_settings.WATCH_DIRECTORY
    dip_upload_dir = os.path.join(watch_dir, "uploadDIP")
    try:
        sip = models.SIP.objects.get(uuid=uuid)
    except:
        raise Http404
    directory = os.path.basename(os.path.dirname(sip.currentpath))
    metsFilePath = os.path.join(dip_upload_dir, directory, "METS." + uuid + ".xml")
    tree = ElementTree.parse(metsFilePath)
    root = tree.getroot()
    paths = []
    path_uuids = {}
    files = []
    for item in root.findall(
        "{http://www.loc.gov/METS/}fileSec"
        "/{http://www.loc.gov/METS/}fileGrp[@USE='original']"
        "/{http://www.loc.gov/METS/}file"
    ):
        for item2 in item.findall("{http://www.loc.gov/METS/}FLocat"):
            object_path = item2.attrib["{http://www.w3.org/1999/xlink}href"]
            file = models.File.objects.get(
                sip=uuid, currentlocation="%SIPDirectory%" + object_path
            )
            object_path = remove_objects_prefix(object_path)
            paths.append(object_path)
            path_uuids[object_path] = file.uuid
    paths.sort()
    for path in paths:
        files.append({"uuid": path_uuids[path], "path": path})
    return files
