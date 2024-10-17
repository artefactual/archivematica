from components.access import views
from django.urls import path
from django.urls import re_path

app_name = "access"
urlpatterns = [
    path("archivesspace/", views.all_records),
    path("archivesspace/levels/", views.get_levels_of_description),
    re_path(r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/$", views.record),
    re_path(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/contents/arrange/$",
        views.access_arrange_contents,
        name="access_arrange_contents",
    ),
    re_path(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/copy_to_arrange/$",
        views.access_copy_to_arrange,
    ),
    re_path(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/copy_from_arrange/$",
        views.access_arrange_start_sip,
        name="access_arrange_start_sip",
    ),
    re_path(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/create_directory_within_arrange/$",
        views.access_create_directory,
        name="access_create_directory",
    ),
    re_path(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/rights/$", views.access_sip_rights
    ),
    re_path(
        r"archivesspace/(?P<record_id>[A-Za-z0-9-_]+)/metadata/$",
        views.access_sip_metadata,
    ),
    path("archivesspace/<path:record_id>/children/", views.record_children),
    path(
        "archivesspace/<path:record_id>/digital_object_components/",
        views.digital_object_components,
    ),
]
