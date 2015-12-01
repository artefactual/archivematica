from django.conf.urls import url, patterns
from components.rights import views

urlpatterns = patterns('',
    url(r'^$', views.transfer_rights_list),
    url(r'add/$', views.transfer_rights_edit),
    url(r'delete/(?P<id>\d+)/$', views.transfer_rights_delete),
    url(r'grants/(?P<id>\d+)/delete/$', views.transfer_rights_grant_delete),
    url(r'grants/(?P<id>\d+)/$', views.transfer_rights_grants_edit),
    url(r'(?P<id>\d+)/$', views.transfer_rights_edit)
)
