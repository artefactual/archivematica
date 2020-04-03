# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf.urls import url

from components.access import views

app_name = "access"
urlpatterns = [
    url(r"archivesspace/$", views.all_records),
    url(r"archivesspace/levels/$", views.get_levels_of_description),
    url(r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/$", views.record),
    url(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/contents/arrange/$",
        views.access_arrange_contents,
        name="access_arrange_contents",
    ),
    url(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/copy_to_arrange/$",
        views.access_copy_to_arrange,
    ),
    url(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/copy_from_arrange/$",
        views.access_arrange_start_sip,
    ),
    url(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/create_directory_within_arrange/$",
        views.access_create_directory,
        name="access_create_directory",
    ),
    url(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/rights/$", views.access_sip_rights
    ),
    url(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/metadata/$",
        views.access_sip_metadata,
    ),
    url(r"archivesspace/(?P<record_id>.+)/children/$", views.record_children),
    url(
        r"archivesspace/(?P<record_id>.+)/digital_object_components/$",
        views.digital_object_components,
    ),
]
