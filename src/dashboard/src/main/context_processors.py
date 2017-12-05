from django.conf import settings


def search_enabled(request):
    return {'search_enabled': settings.SEARCH_ENABLED}
