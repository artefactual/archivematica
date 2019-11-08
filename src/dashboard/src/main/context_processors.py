# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings


def search_enabled(request):
    return {
        "search_transfers_enabled": "transfers" in settings.SEARCH_ENABLED,
        "search_aips_enabled": "aips" in settings.SEARCH_ENABLED,
    }


def auth_methods(request):
    return {"oidc_enabled": settings.OIDC_AUTHENTICATION}
