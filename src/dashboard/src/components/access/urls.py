from django.conf.urls import url, patterns
from components.access import views

urlpatterns = patterns('',
    url(r'(?P<system>archivesspace|atk)/$', views.all_records),
    url(r'(?P<system>archivesspace|atk)/levels/$', views.get_levels_of_description),
    url(r'(?P<system>archivesspace|atk)/(?P<record_id>[A-Za-z0-9-_]+)/$', views.record),
    url(r'(?P<system>archivesspace|atk)/(?P<record_id>[A-Za-z0-9-_]+)/contents/arrange/$', views.access_arrange_contents),
    url(r'(?P<system>archivesspace|atk)/(?P<record_id>[A-Za-z0-9-_]+)/copy_to_arrange/$', views.access_copy_to_arrange),
    url(r'(?P<system>archivesspace|atk)/(?P<record_id>[A-Za-z0-9-_]+)/move_within_arrange/$', views.access_move_within_arrange),
    url(r'(?P<system>archivesspace|atk)/(?P<record_id>[A-Za-z0-9-_]+)/copy_from_arrange/$', views.access_arrange_start_sip),
    url(r'(?P<system>archivesspace|atk)/(?P<record_id>[A-Za-z0-9-_]+)/create_directory_within_arrange/$', views.access_create_directory),
    url(r'(?P<system>archivesspace|atk)/accession/(?P<accession>.+)/$', views.get_records_by_accession),
    url(r'(?P<system>archivesspace|atk)/(?P<record_id>.+)/children/$', views.record_children),
)
