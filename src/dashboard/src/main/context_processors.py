from django.conf import settings


def search_enabled(request):
    return {
        "search_transfers_enabled": "transfers" in settings.SEARCH_ENABLED,
        "search_aips_enabled": "aips" in settings.SEARCH_ENABLED,
    }
