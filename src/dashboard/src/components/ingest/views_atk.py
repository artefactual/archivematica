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

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.utils import simplejson
import os, sys, MySQLdb, ast
from main import models
from components import helpers
from components import advanced_search
import xml.etree.ElementTree as ElementTree
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivistsToolkit.atk as atk
import elasticSearchFunctions, databaseFunctions

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

def ingest_upload_atk_db_connection():
    dict = models.MicroServiceChoiceReplacementDic.objects.get(description='Archivists Toolkit Config')
    config = ast.literal_eval(dict.replacementdic)

    return MySQLdb.connect(
        host=config['%host%'],
        port=int(config['%port%']),
        user=config['%dbuser%'],
        passwd=config['%dbpass%'],
        db=config['%dbname%']
    )

def ingest_upload_atk(request, uuid):
    try:
        query = request.GET.get('query', '').strip()

        db = ingest_upload_atk_db_connection()

        try:
            resources = ingest_upload_atk_get_collection_ids(db, query)
        except MySQLdb.OperationalError:
            return HttpResponseServerError('Database connection error. Please contact an administration.')

        page = helpers.pager(resources, 10, request.GET.get('page', 1))

        page['objects'] = augment_resource_data(db, page['objects'])

    except (MySQLdb.ProgrammingError, MySQLdb.OperationalError) as e:
        return HttpResponseServerError(
          'Database error {0}. Please contact an administrator.'.format(str(e))
        )

    search_params = advanced_search.extract_url_search_params_from_request(request)
    return render(request, 'ingest/atk/resource_list.html', locals())

def ingest_upload_atk_save(request, uuid):
    pairs_saved = ingest_upload_atk_save_to_db(request, uuid)

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

def ingest_upload_atk_save_to_db(request, uuid):
    saved = 0

    # delete existing mapping, if any, for this DIP
    models.AtkDIPObjectResourcePairing.objects.filter(dipuuid=uuid).delete()

    pairs = getDictArray(request.POST, 'pairs')

    keys = pairs.keys()
    keys.sort()

    for key in keys:
        pairing = models.AtkDIPObjectResourcePairing.objects.create(
            dipuuid=pairs[key]['DIPUUID'],
            fileuuid=pairs[key]['objectUUID']
        )
        if pairs[key]['resourceLevelOfDescription'] == 'collection':
            pairing.resourceid = pairs[key]['resourceId']
        else:
            pairing.resourcecomponentid = pairs[key]['resourceId']
        pairing.save()
        saved = saved + 1

    return saved

def augment_resource_data(db, resource_ids):
    resources_augmented = []
    for id in resource_ids:
        resources_augmented.append(
            atk.get_resource_component_and_children(db, id, recurse_max_level=2)
        )
    return resources_augmented

def ingest_upload_atk_resource(request, uuid, resource_id):
    db = ingest_upload_atk_db_connection()
    try:
        query = request.GET.get('query', '').strip()
        resource_data = atk.get_resource_component_and_children(
            db,
            resource_id,
            'collection',
            recurse_max_level=2,
            search_pattern=query
        )
        if resource_data['children']:
             page = helpers.pager(resource_data['children'], 10, request.GET.get('page', 1))
    except MySQLdb.ProgrammingError:
        return HttpResponseServerError('Database error. Please contact an administrator.')

    if not resource_data['children'] and query == '':
        return HttpResponseRedirect(
            reverse('components.ingest.views_atk.ingest_upload_atk_match_dip_objects_to_resource_levels', args=[uuid, resource_id])
        )
    else:
        search_params = advanced_search.extract_url_search_params_from_request(request)
        return render(request, 'ingest/atk/resource_detail.html', locals())

def ingest_upload_atk_determine_resource_component_resource_id(resource_component_id):
    db = ingest_upload_atk_db_connection()

    cursor = db.cursor()

    cursor.execute("SELECT resourceId, parentResourceComponentId FROM ResourcesComponents WHERE resourceComponentId=%s", (resource_component_id))

    row = cursor.fetchone()

    if row[0] != None:
        return row[0]
    else:
        return ingest_upload_atk_determine_resource_component_resource_id(row[1])

def ingest_upload_atk_resource_component(request, uuid, resource_component_id):
    db = ingest_upload_atk_db_connection()
    try:
        query = request.GET.get('query', '').strip()
        resource_component_data = atk.get_resource_component_and_children(
            db,
            resource_component_id,
            'description',
            recurse_max_level=2,
            search_pattern=query
        )
        if resource_component_data['children']:
            page = helpers.pager(resource_component_data['children'], 10, request.GET.get('page', 1))
    except MySQLdb.ProgrammingError:
        return HttpResponseServerError('Database error. Please contact an administrator.')

    resource_id = ingest_upload_atk_determine_resource_component_resource_id(resource_component_id)

    if not resource_component_data['children'] and query == '':
        return HttpResponseRedirect(
            reverse('components.ingest.views_atk.ingest_upload_atk_match_dip_objects_to_resource_component_levels', args=[uuid, resource_component_id])
        )
    else:
	search_params = advanced_search.extract_url_search_params_from_request(request)
        return render(request, 'ingest/atk/resource_component.html', locals())

def ingest_upload_atk_get_collection_ids(db, search_pattern=''):
    collections = []

    cursor = db.cursor()

    if search_pattern != '':
        cursor.execute(
            "SELECT resourceId FROM Resources WHERE (title LIKE %s OR resourceid LIKE %s) AND resourceLevel in ('recordgrp', 'collection') ORDER BY title",
            ('%' + search_pattern + '%', '%' + search_pattern + '%')
        )
    else:
        cursor.execute("SELECT resourceId FROM Resources WHERE resourceLevel = 'collection' ORDER BY title")

    for row in cursor.fetchall():
        collections.append(row[0])

    return collections

def ingest_upload_atk_match_dip_objects_to_resource_levels(request, uuid, resource_id):
    # load object relative paths
    object_path_json = simplejson.JSONEncoder().encode(
        ingest_upload_atk_get_dip_object_paths(uuid)
    )

    try:
        # load resource and child data
        db = ingest_upload_atk_db_connection()
        resource_data_json = simplejson.JSONEncoder().encode(
            atk.get_resource_children(db, resource_id)
        )
    except:
        return HttpResponseServerError('Database error. Please contact an administrator.')

    return render(request, 'ingest/atk/match.html', locals())

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

def ingest_upload_atk_match_dip_objects_to_resource_component_levels(request, uuid, resource_component_id):
    # load object relative paths
    object_path_json = simplejson.JSONEncoder().encode(
        ingest_upload_atk_get_dip_object_paths(uuid)
    )

    try:
        # load resource and child data
        db = ingest_upload_atk_db_connection()
        resource_data_json = simplejson.JSONEncoder().encode(
            atk.get_resource_component_children(db, resource_component_id)
        )
    except:
        return HttpResponseServerError('Database error. Please contact an administrator.')

    return render(request, 'ingest/atk/match.html', locals())
