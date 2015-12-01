from django.conf.urls import url, patterns
from django.conf import settings
from components.transfer import views

urlpatterns = patterns('',
    url(r'^$', views.grid),

    # Transfer metadata set functions
    url(r'^create_metadata_set_uuid/$', views.create_metadata_set_uuid),
    url(r'^rename_metadata_set/(?P<set_uuid>' + settings.UUID_REGEX + ')/(?P<placeholder_id>[\w\-]+)/$', views.rename_metadata_set),
    url(r'^cleanup_metadata_set/(?P<set_uuid>' + settings.UUID_REGEX + ')/$', views.cleanup_metadata_set),

    url(r'component/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.component),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/$', views.detail),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/delete/$', views.delete),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/microservices/$', views.microservices),
    url(r'status/$', views.status),
    url(r'status/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.status),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/$', views.transfer_metadata_list),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/add/$', views.transfer_metadata_edit),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/(?P<id>\d+)/$', views.transfer_metadata_edit),
)
