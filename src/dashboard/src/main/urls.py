from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template, redirect_to

UUID_REGEX = '[\w]{8}(-[\w]{4}){3}-[\w]{12}'

urlpatterns = patterns('main.views',

    # Index
    (r'^$', 'home'),

    # Forbidden
    (r'forbidden/$', 'forbidden'),

    # Jobs and tasks (is part of ingest)
    (r'jobs/(?P<uuid>' + UUID_REGEX + ')/explore/$', 'jobs_explore'),
    (r'jobs/(?P<uuid>' + UUID_REGEX + ')/list-objects/$', 'jobs_list_objects'),
    (r'tasks/(?P<uuid>' + UUID_REGEX + ')/$', 'tasks'),
    (r'task/(?P<uuid>' + UUID_REGEX + ')/$', 'task'),

    # Access
    (r'access/$', 'access_list'),
    (r'access/(?P<id>\d+)/delete/$', 'access_delete'),

    # Lookup
#    (r'lookup/rightsholder/(?P<id>\d+)/$', 'rights_holders_lookup'),

    # Autocomplete
#    (r'autocomplete/rightsholders$', 'rights_holders_autocomplete'),

    # Disabled until further development can be done
    #(r'administration/search/$', 'administration_search'),
    #(r'administration/search/flush/aips/$', 'administration_search_flush_aips'),

    # JSON feeds
    (r'status/$', 'status'),
    (r'formdata/(?P<type>\w+)/(?P<parent_id>\d+)/(?P<delete_id>\d+)/$', 'formdata_delete'),
    (r'formdata/(?P<type>\w+)/(?P<parent_id>\d+)/$', 'formdata'),
)
