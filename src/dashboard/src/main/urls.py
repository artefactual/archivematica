from django.conf.urls import url, patterns
from django.conf import settings
from main import views

urlpatterns = patterns('',
    # Index
    url(r'^$', views.home),

    # Forbidden
    url(r'forbidden/$', views.forbidden),

    # Elasticsearch check
    url(r'elasticsearch/$', views.elasticsearch_login_check),

    # Jobs and tasks (is part of ingest)
    url(r'jobs/(?P<uuid>' + settings.UUID_REGEX + ')/explore/$', views.jobs_explore),
    url(r'jobs/(?P<uuid>' + settings.UUID_REGEX + ')/list-objects/$', views.jobs_list_objects),
    url(r'tasks/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.tasks),
    url(r'task/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.task),

    # Access
    url(r'access/$', views.access_list),
    url(r'access/(?P<id>\d+)/delete/$', views.access_delete),

    # JSON feeds
    url(r'status/$', views.status),
    url(r'formdata/(?P<type>\w+)/(?P<parent_id>\d+)/(?P<delete_id>\d+)/$', views.formdata_delete),
    url(r'formdata/(?P<type>\w+)/(?P<parent_id>\d+)/$', views.formdata),
)
