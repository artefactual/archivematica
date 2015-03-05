from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils import simplejson
import os
from main import models
from components import helpers
import xml.etree.ElementTree as ElementTree


# TODO: move into helpers module at some point
# From http://www.ironzebra.com/news/23/converting-multi-dimensional-form-arrays-in-django
def getDictArray(post, name):
    dic = {}
    for k in post.keys():
        if k.startswith(name):
            rest = k[len(name):]

            # split the string into different components
            parts = [p[:-1] for p in rest.split('[')][1:]
            id = int(parts[0])

            # add a new dictionary if it doesn't exist yet
            if id not in dic:
                dic[id] = {}

            # add the information to the dictionary
            dic[id][parts[1]] = post.get(k)
    return dic


def list_records(client, request, query, page, search_params, list_redirect_target, uuid):
    resources = client.find_collection_ids(query)

    page = helpers.pager(resources, 10, page)

    page['objects'] = client.augment_resource_ids(page['objects'])

    return render(request, list_redirect_target, locals())


def pairs_saved_response(pairs_saved):
    if pairs_saved > 0:
        response = {
            "message": "Submitted successfully."
        }
    else:
        response = {
            "message": "No pairs saved."
        }

    return HttpResponse(
        simplejson.JSONEncoder().encode(response),
        mimetype='application/json'
    )


def render_resource(client, request, resource_id, query, page, search_params, match_redirect_target, resource_detail_template, uuid):
    resource_data = client.get_resource_component_and_children(
        resource_id,
        'collection',
        recurse_max_level=2,
        search_pattern=query
    )

    if resource_data['children']:
        page = helpers.pager(resource_data['children'], 10, page)

    if not resource_data['children'] and query == '':
        return HttpResponseRedirect(reverse(match_redirect_target, args=[uuid, resource_id]))
    else:
        return render(request, resource_detail_template, locals())


def render_resource_component(client, request, resource_component_id, query, page, search_params, match_redirect_target, resource_detail_template, uuid):
    resource_component_data = client.get_resource_component_and_children(
        resource_component_id,
        'description',
        recurse_max_level=2,
        search_pattern=query
    )
    if resource_component_data['children']:
        page = helpers.pager(resource_component_data['children'], 10, page)

    resource_id = client.find_resource_id_for_component(resource_component_id)
    parent_id = client.find_parent_id_for_component(resource_component_id)

    if not resource_component_data['children'] and query == '':
        return HttpResponseRedirect(
            reverse(match_redirect_target, args=[uuid, resource_component_id])
        )
    else:
        return render(request, resource_detail_template, locals())


def match_dip_objects_to_resource_levels(client, request, resource_id, match_template, uuid):
    # load object relative paths
    object_path_json = simplejson.JSONEncoder().encode(
        ingest_upload_atk_get_dip_object_paths(uuid)
    )

    resource_data_json = simplejson.JSONEncoder().encode(
        client.get_resource_component_and_children(resource_id)
    )

    return render(request, match_template, locals())


def match_dip_objects_to_resource_component_levels(client, request, resource_component_id, match_template, uuid):
    # load object relative paths
    object_path_json = simplejson.JSONEncoder().encode(
        ingest_upload_atk_get_dip_object_paths(uuid)
    )

    # load resource and child data
    resource_data_json = simplejson.JSONEncoder().encode(
        client.get_resource_component_children(resource_component_id)
    )

    parent_id = client.find_parent_id_for_component(resource_component_id)

    return render(request, match_template, locals())


def ingest_upload_atk_get_dip_object_paths(uuid):
    # determine the DIP upload directory
    watch_dir = helpers.get_server_config_value('watchDirectoryPath')
    dip_upload_dir = os.path.join(watch_dir, 'uploadDIP')

    # work out directory name for DIP (should be the same as the SIP)
    try:
        sip = models.SIP.objects.get(uuid=uuid)
    except:
        raise Http404

    directory = os.path.basename(os.path.dirname(sip.currentpath))

    # work out the path to the DIP's METS file
    metsFilePath = os.path.join(dip_upload_dir, directory, 'METS.' + uuid + '.xml')

    # read file paths from METS file
    tree = ElementTree.parse(metsFilePath)
    root = tree.getroot()

    # use paths to create an array that we'll sort and store path UUIDs separately
    paths = []
    path_uuids = {}

    # in the end we'll populate this using paths and path_uuids
    files = []

    # get each object's filepath
    for item in root.findall("{http://www.loc.gov/METS/}fileSec/{http://www.loc.gov/METS/}fileGrp[@USE='original']/{http://www.loc.gov/METS/}file"):
        for item2 in item.findall("{http://www.loc.gov/METS/}FLocat"):
            object_path = item2.attrib['{http://www.w3.org/1999/xlink}href']

            # look up file's UUID
            file = models.File.objects.get(
                sip=uuid,
                currentlocation='%SIPDirectory%' + object_path
            )

            # remove "objects/" dir when storing representation
            if object_path.index('objects/') == 0:
                object_path = object_path[8:]

            paths.append(object_path)
            path_uuids[object_path] = file.uuid

    # create array of objects with object data
    paths.sort()
    for path in paths:
        files.append({
            'uuid': path_uuids[path],
            'path': path
        })

    return files

    """
    files = [{
        'uuid': '7665dc52-29f3-4309-b3fe-273c4c04df4b',
        'path': 'dog.jpg'
    },
    {
        'uuid': 'c2e41289-8280-4db9-ae4e-7730fbaa1471',
        'path': 'inages/candy.jpg'
    }]
    """
