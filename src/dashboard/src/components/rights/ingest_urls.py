from django.conf.urls import url, patterns
from components.rights import views

urlpatterns = patterns('',
    url(r'^$', views.ingest_rights_list),
    url(r'add/$', views.ingest_rights_edit),
    url(r'delete/(?P<id>\d+)/$', views.ingest_rights_delete),
    url(r'grants/(?P<id>\d+)/delete/$', views.ingest_rights_grant_delete),
    url(r'grants/(?P<id>\d+)/$', views.ingest_rights_grants_edit),
    url(r'(?P<id>\d+)/$', views.ingest_rights_edit)
)
