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
import os, sys, MySQLdb
from components import helpers
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions, databaseInterface, databaseFunctions

def ingest_upload_atk_db_connection():
    # TODO: where to store config?
    return MySQLdb.connect(
        host="localhost",
        user="root",
        passwd="",
        db="MCP"
    )

def ingest_upload_atk(request, uuid):
    try:
        query = request.GET.get('query', '')
        resources = ingest_upload_atk_get_collections(query)

        page = helpers.pager(resources, 20, request.GET.get('page', 1))

    except MySQLdb.ProgrammingError:
        return HttpResponse('Database error. Please contact an administrator.')

    return render(request, 'ingest/atk/resource_list.html', locals())

def ingest_upload_atk_resource(request, uuid, resource_id):
    db = ingest_upload_atk_db_connection()
    try:
        query = request.GET.get('query', '')
        resource_data = ingest_upload_atk_get_resource_component_and_children(
            db,
            resource_id,
            'collection',
            recurse_max_level=2,
            search_pattern=query
        )
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

    cursor.execute("SELECT resourceId, parentResourceComponentId FROM atk_description WHERE resourceComponentId=%s", (resource_component_id))

    row = cursor.fetchone()

    if row[0] != None:
        return row[0]
    else:
        return ingest_upload_atk_determine_resource_component_resource_id(row[1])

def ingest_upload_atk_resource_component(request, uuid, resource_component_id):
    db = ingest_upload_atk_db_connection()
    try:
        query = request.GET.get('query', '')
        resource_component_data = ingest_upload_atk_get_resource_component_and_children(
            db,
            resource_component_id,
            'description',
            recurse_max_level=2,
            search_pattern=query
        )
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
      "SELECT resourceId, title, dateExpression FROM atk_collection WHERE title LIKE %s ORDER BY title",
      ('%' + search_pattern + '%')
    )

    for row in cursor.fetchall():
        collections.append({
          'id':    row[0],
          'title': row[1],
          'dates': row[2]
        })

    return collections

def ingest_upload_atk_match_dip_objects_to_resource_levels(request, uuid, resource_id):
    # load object relative paths
    object_path_json = simplejson.JSONEncoder().encode(
        ingest_upload_atk_get_dip_object_paths(uuid)
    )

    try:
        # load resource and child data
        resource_data_json = simplejson.JSONEncoder().encode(
            ingest_upload_atk_get_resource_children(resource_id)
        )
    except:
        return HttpResponse('Database error. Please contact an administrator.')

    return render(request, 'ingest/atk/match.html', locals())

def ingest_upload_atk_get_dip_object_paths(uuid):
    return [
      'dog.jpg',
      'images/cat.jpg'
    ]

def ingest_upload_atk_match_dip_objects_to_resource_component_levels(request, uuid, resource_component_id):
    # load object relative paths
    object_path_json = simplejson.JSONEncoder().encode(
        ingest_upload_atk_get_dip_object_paths(uuid)
    )

    try:
        # load resource and child data
        resource_data_json = simplejson.JSONEncoder().encode(
            ingest_upload_atk_get_resource_component_children(resource_component_id)
        )
    except:
        return HttpResponse('Database error. Please contact an administrator.')

    return render(request, 'ingest/atk/match.html', locals())

def ingest_upload_atk_get_resource_children(resource_id):
    db = ingest_upload_atk_db_connection()
    return ingest_upload_atk_get_resource_component_and_children(db, resource_id)

def ingest_upload_atk_get_resource_component_children(resource_component_id):
    db = ingest_upload_atk_db_connection()
    return ingest_upload_atk_get_resource_component_and_children(db, resource_component_id, 'resource')

def ingest_upload_atk_get_resource_component_and_children(db, resource_id, resource_type='collection', level=1, sort_data={}, **kwargs):
    # we pass the sort position as a dict so it passes by reference and we
    # can use it to share state during recursion

    recurse_max_level = kwargs.get('recurse_max_level', False)
    query             = kwargs.get('search_pattern', '')

    # intialize sort position if this is the beginning of recursion
    if level == 1:
        sort_data['position'] = 0

    sort_data['position'] = sort_data['position'] + 1

    resource_data = {}

    cursor = db.cursor() 

    if resource_type == 'collection':
        cursor.execute("SELECT title, dateExpression FROM atk_collection WHERE resourceid=%s", (resource_id))

        for row in cursor.fetchall():
            resource_data['id']                 = resource_id
            resource_data['sortPosition']       = sort_data['position']
            resource_data['title']              = row[0]
            resource_data['dates']              = row[1]
            resource_data['levelOfDescription'] = 'Fonds'
    else:
        cursor.execute("SELECT title, dateExpression, persistentId, resourceLevel FROM atk_description WHERE resourceComponentId=%s", (resource_id))

        for row in cursor.fetchall():
            resource_data['id']                 = resource_id
            resource_data['sortPosition']       = sort_data['position']
            resource_data['title']              = row[0]
            resource_data['dates']              = row[1]
            resource_data['identifier']         = row[2]
            resource_data['levelOfDescription'] = row[3]

    resource_data['children'] = False

    # fetch children if we haven't reached the maximum recursion level
    if (not recurse_max_level) or level < recurse_max_level:
        if resource_type == 'collection':
            cursor.execute("SELECT resourceComponentId FROM atk_description WHERE parentResourceComponentId IS NULL AND resourceId=%s AND title LIKE %s ORDER BY FIND_IN_SET(resourceLevel, 'subseries,file'), title ASC", (resource_id, '%' + query + '%'))
        else:
            cursor.execute("SELECT resourceComponentId FROM atk_description WHERE parentResourceComponentId=%s AND title LIKE %s ORDER BY FIND_IN_SET(resourceLevel, 'subseries,file'), title ASC", (resource_id, '%' + query + '%'))

        rows = cursor.fetchall()

        if len(rows):
            resource_data['children'] = []

            for row in rows:
                resource_data['children'].append(
                    ingest_upload_atk_get_resource_component_and_children(
                        db,
                        row[0],
                        'description',
                        level + 1,
                        sort_data
                    )
                 )

    return resource_data

    """
    Example data:

    return {
      'id': '31',
      'sortPosition': '1',
      'identifier': 'PR01',
      'title': 'Parent',
      'levelOfDescription': 'Fonds',
      'dates': '1880-1889',
      'children': [{
        'id': '23',
        'sortPosition': '2',
        'identifier': 'CH01',
        'title': 'Child A',
        'levelOfDescription': 'Sousfonds',
        'dates': '1880-1888',
        'children': [{
          'id': '24',
          'sortPosition': '3',
          'identifier': 'GR01',
          'title': 'Grandchild A',
          'levelOfDescription': 'Item',
          'dates': '1880-1888',
          'children': False
        },
        {
          'id': '25',
          'sortPosition': '4',
          'identifier': 'GR02',
          'title': 'Grandchild B',
          'levelOfDescription': 'Item',
          'children': False
        }]
      },
      {
        'id': '26',
        'sortPosition': '5',
        'identifier': 'CH02',
        'title': 'Child B',
        'levelOfDescription': 'Sousfonds',
        'dates': '1889',
        'children': False
      }]
    }
    """
