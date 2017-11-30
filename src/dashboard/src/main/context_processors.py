from django.conf import settings


def disable_search_indexing(request):
    return {'DISABLE_SEARCH_INDEXING': settings.DISABLE_SEARCH_INDEXING}
