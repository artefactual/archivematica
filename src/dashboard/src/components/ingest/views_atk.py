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

from django.http import HttpResponseServerError
import sys, MySQLdb, ast
from main import models
from components import advanced_search
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from archivistsToolkit.client import ArchivistsToolkitClient

import pair_matcher

def get_atk_system_client():
    dict = models.MicroServiceChoiceReplacementDic.objects.get(description='Archivists Toolkit Config')
    config = ast.literal_eval(dict.replacementdic)

    return ArchivistsToolkitClient(
        host=config['%host%'],
        user=config['%dbuser%'],
        passwd=config['%dbpass%'],
        db=config['%dbname%']
    )

def ingest_upload_atk(request, uuid):
    try:
        client = get_atk_system_client()
        query = request.GET.get('query', '').strip()
        page = request.GET.get('page', 1)
        search_params = advanced_search.extract_url_search_params_from_request(request)

        return pair_matcher.list_records(client, request, query, page,
                                         search_params,
                                         'ingest/atk/resource_list.html',
                                         uuid)
    except (MySQLdb.ProgrammingError, MySQLdb.OperationalError) as e:
        return HttpResponseServerError(
          'Database error {0}. Please contact an administrator.'.format(str(e))
        )

def ingest_upload_atk_save(request, uuid):
    return pair_matcher.pairs_saved_response(ingest_upload_atk_save_to_db(request, uuid))

def ingest_upload_atk_save_to_db(request, uuid):
    saved = 0

    # delete existing mapping, if any, for this DIP
    models.AtkDIPObjectResourcePairing.objects.filter(dipuuid=uuid).delete()

    pairs = pair_matcher.getDictArray(request.POST, 'pairs')

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

def ingest_upload_atk_resource(request, uuid, resource_id):
    client = get_atk_system_client()
    try:
        query = request.GET.get('query', '').strip()
        page = request.GET.get('page', 1)
        search_params = advanced_search.extract_url_search_params_from_request(request)

        return pair_matcher.render_resource(client, request, resource_id,
                                            query, page, search_params,
                                            'components.ingest.views_atk.ingest_upload_atk_match_dip_objects_to_resource_levels',
                                            'ingest/atk/resource_detail.html',
                                            uuid)
    except MySQLdb.ProgrammingError:
        return HttpResponseServerError('Database error. Please contact an administrator.')

def ingest_upload_atk_resource_component(request, uuid, resource_component_id):
    client = get_atk_system_client()
    try:
        query = request.GET.get('query', '').strip()
        page = request.GET.get('page', 1)
        search_params = advanced_search.extract_url_search_params_from_request(request)
        return pair_matcher.render_resource_component(client, request,
                                                      resource_component_id,
                                                      query, page, search_params,
                                                      'components.ingest.views_atk.ingest_upload_atk_match_dip_objects_to_resource_component_levels',
                                                      'ingest/atk/resource_component.html',
                                                      uuid)
    except MySQLdb.ProgrammingError:
        return HttpResponseServerError('Database error. Please contact an administrator.')

def ingest_upload_atk_match_dip_objects_to_resource_levels(request, uuid, resource_id):
    try:
        # load resource and child data
        client = get_atk_system_client()
        return pair_matcher.match_dip_objects_to_resource_levels(client, request, resource_id, 'ingest/atk/match.html', uuid)
    except:
        return HttpResponseServerError('Database error. Please contact an administrator.')

def ingest_upload_atk_match_dip_objects_to_resource_component_levels(request, uuid, resource_component_id):
    # load object relative paths
    try:
        # load resource and child data
        client = get_atk_system_client()
        return pair_matcher.match_dip_objects_to_resource_component_levels(client, request, resource_component_id, 'ingest/atk/match.html', uuid)
    except:
        return HttpResponseServerError('Database error. Please contact an administrator.')
