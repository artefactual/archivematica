from django.conf.urls import url, patterns
from components.access import views

urlpatterns = patterns('',
    url(r'(?P<system>archivesspace|atk)/$', views.all_records),
    url(r'(?P<system>archivesspace|atk)/levels/$', views.get_levels_of_description),
    url(r'(?P<system>archivesspace|atk)/(?P<record_id>[A-Za-z0-9-_]+)/$', views.record),
    url(r'(?P<system>archivesspace|atk)/accession/(?P<accession>.+)/$', views.get_records_by_accession),
    url(r'(?P<system>archivesspace|atk)/(?P<record_id>.+)/children/$', views.record_children),
)
