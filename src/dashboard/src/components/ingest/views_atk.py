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
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.utils import simplejson
import os, sys, MySQLdb, ast
from main import models
from components import helpers
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivistsToolkit.atk as atk
import elasticSearchFunctions, databaseInterface, databaseFunctions

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
    if request.method == 'GET':
        try:
            query = request.GET.get('query', '')
            resources = ingest_upload_atk_get_collections(query)

            page = helpers.pager(resources, 20, request.GET.get('page', 1))

        except MySQLdb.ProgrammingError:
            return HttpResponse('Database error. Please contact an administrator.')

        return render(request, 'ingest/atk/resource_list.html', locals())
    else:
        pairs = getDictArray(request.POST, 'pairs')

        keys = pairs.keys()
        keys.sort()

        for key in keys:
            # TODO: write data in pairs[key] to DB
            pass

        response = {
            "message": "Submitted successfully."
        }

        return HttpResponse(
            simplejson.JSONEncoder().encode(response),
            mimetype='application/json'
        )

def ingest_upload_atk_resource(request, uuid, resource_id):
    db = ingest_upload_atk_db_connection()
    try:
        query = request.GET.get('query', '')
        resource_data = atk.get_resource_component_and_children(
            db,
            resource_id,
            'collection',
            recurse_max_level=2,
            search_pattern=query
        )
        if resource_data['children']:
             page = helpers.pager(resource_data['children'], 20, request.GET.get('page', 1))
    except MySQLdb.ProgrammingError:
        return HttpResponse('Database error. Please contact an administrator.')

    if not resource_data['children'] and query == '':
        return HttpResponseRedirect(
            reverse('components.ingest.views_atk.ingest_upload_atk_match_dip_objects_to_resource_levels', args=[uuid, resource_id])
        )
    else:
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
        query = request.GET.get('query', '')
        resource_component_data = atk.get_resource_component_and_children(
            db,
            resource_component_id,
            'description',
            recurse_max_level=2,
            search_pattern=query
        )
        if resource_component_data['children']:
            page = helpers.pager(resource_component_data['children'], 20, request.GET.get('page', 1))
    except MySQLdb.ProgrammingError:
        return HttpResponse('Database error. Please contact an administrator.')

    resource_id = ingest_upload_atk_determine_resource_component_resource_id(resource_component_id)

    if not resource_component_data['children'] and query == '':
        return HttpResponseRedirect(
            reverse('components.ingest.views_atk.ingest_upload_atk_match_dip_objects_to_resource_component_levels', args=[uuid, resource_component_id])
        )
    else:
        return render(request, 'ingest/atk/resource_component.html', locals())

def ingest_upload_atk_get_collections(search_pattern=''):
    collections = []

    db = ingest_upload_atk_db_connection()

    cursor = db.cursor()

    cursor.execute(
      "SELECT resourceId FROM Resources WHERE title LIKE %s OR resourceid LIKE %s ORDER BY title",
      ('%' + search_pattern + '%', '%' + search_pattern + '%')
    )

    for row in cursor.fetchall():
        collections.append(
            atk.get_resource_component_and_children(db, row[0])
        )

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
        return HttpResponse('Database error. Please contact an administrator.')

    return render(request, 'ingest/atk/match.html', locals())

def ingest_upload_atk_get_dip_object_paths(uuid):
    paths = [
      'dog.jpg',
      'budget.xls',
      'book.doc',
      'manual.pdf',
      'hats.png',
      'demons.jpg',
      'goat.png',
      'celery.png',
      'owls.jpg',
      'candyman.jpg',
      'clown.jpg',
      'taxes.xls',
      'stats.xls',
      'donut.jpg',
      'hamburger.jpg',
      'goose.png',
      'chicken.png',
      'crayons.png',
      'hammer.jpg',
      'banana.jpg',
      'minutes.doc',
      'revised.pdf',
      'carrot.jpg',
      'hinge.jpg',
      'hatrack.png',
      'images/cat.jpg',
      'images/racoon.jpg'
    ]

    paths.sort()

    return paths

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
        return HttpResponse('Database error. Please contact an administrator.')

    return render(request, 'ingest/atk/match.html', locals())
