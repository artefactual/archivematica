# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.urls import re_path
from django.conf import settings

from components.file import views

app_name = "file"
urlpatterns = [
    re_path(r"(?P<fileuuid>" + settings.UUID_REGEX + ")/$", views.file_details),
    re_path(
        r"(?P<fileuuid>" + settings.UUID_REGEX + ")/tags/$",
        views.TransferFileTags.as_view(),
    ),
    re_path(
        r"(?P<fileuuid>" + settings.UUID_REGEX + ")/bulk_extractor/$",
        views.bulk_extractor,
    ),
]
