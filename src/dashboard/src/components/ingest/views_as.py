import ast
from functools import wraps
import sys

from django.http import HttpResponseServerError

from components import advanced_search
from main import models

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from archivesspace.client import ArchivesSpaceClient, AuthenticationError, ConnectionError

from components.ingest import pair_matcher


def get_as_system_client():
    dict = models.MicroServiceChoiceReplacementDic.objects.get(description='ArchivesSpace Config')
    config = ast.literal_eval(dict.replacementdic)

    return ArchivesSpaceClient(
        host=config['%host%'],
        port=config['%port%'],
        user=config['%user%'],
        passwd=config['%passwd%']
    )


def _authenticate_to_archivesspace(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            client = get_as_system_client()
        except AuthenticationError:
            return HttpResponseServerError("Unable to authenticate to ArchivesSpace server using the default user! Check administrative settings.")
        except ConnectionError:
            return HttpResponseServerError("Unable to connect to ArchivesSpace server at the default location! Check administrative settings.")

        return func(client, *args, **kwargs)
    return wrapper


@_authenticate_to_archivesspace
def ingest_upload_as(client, request, uuid):
    query = request.GET.get('query', '').strip()
    page = request.GET.get('page', 1)
    search_params = advanced_search.extract_url_search_params_from_request(request)

    return pair_matcher.list_records(client, request, query, page,
                                     search_params,
                                     'ingest/as/resource_list.html',
                                     uuid)


def ingest_upload_as_save(request, uuid):
    return pair_matcher.pairs_saved_response(ingest_upload_as_save_to_db(request, uuid))


def ingest_upload_as_save_to_db(request, uuid):
    saved = 0

    # delete existing mapping, if any, for this DIP
    models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(dipuuid=uuid).delete()

    pairs = pair_matcher.getDictArray(request.POST, 'pairs')

    keys = pairs.keys()
    keys.sort()

    for key in keys:
        models.ArchivesSpaceDIPObjectResourcePairing.objects.create(
            dipuuid=pairs[key]['DIPUUID'],
            fileuuid=pairs[key]['objectUUID'],
            resourceid=pairs[key]['resourceId']
        )
        saved = saved + 1

    return saved


@_authenticate_to_archivesspace
def ingest_upload_as_resource(client, request, uuid, resource_id):
    query = request.GET.get('query', '').strip()
    page = request.GET.get('page', 1)
    search_params = advanced_search.extract_url_search_params_from_request(request)

    return pair_matcher.render_resource(client, request, resource_id,
                                        query, page, search_params,
                                        'components.ingest.views_as.ingest_upload_as_match_dip_objects_to_resource_levels',
                                        'ingest/as/resource_detail.html',
                                        uuid)


@_authenticate_to_archivesspace
def ingest_upload_as_resource_component(client, request, uuid, resource_component_id):
    query = request.GET.get('query', '').strip()
    page = request.GET.get('page', 1)
    search_params = advanced_search.extract_url_search_params_from_request(request)

    return pair_matcher.render_resource_component(client, request,
                                                  resource_component_id,
                                                  query, page, search_params,
                                                  'components.ingest.views_as.ingest_upload_as_match_dip_objects_to_resource_component_levels',
                                                  'ingest/as/resource_component.html',
                                                  uuid)


@_authenticate_to_archivesspace
def ingest_upload_as_match_dip_objects_to_resource_levels(client, request, uuid, resource_id):
    # Locate existing matches for display in the "Pairs" panel
    pairs = models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(dipuuid=uuid)
    matches = [{"resource_id": pair.resourceid, "file_uuid": pair.fileuuid} for pair in pairs]

    return pair_matcher.match_dip_objects_to_resource_levels(client, request, resource_id, 'ingest/as/match.html', uuid, matches=matches)


@_authenticate_to_archivesspace
def ingest_upload_as_match_dip_objects_to_resource_component_levels(client, request, uuid, resource_component_id):
    # Locate existing matches for display in the "Pairs" panel
    pairs = models.ArchivesSpaceDIPObjectResourcePairing.objects.filter(
        dipuuid=uuid)
    matches = [{"resource_id": pair.resourceid, "file_uuid": pair.fileuuid} for pair in pairs]

    return pair_matcher.match_dip_objects_to_resource_component_levels(client, request, resource_component_id, 'ingest/as/match.html', uuid, matches=matches)
