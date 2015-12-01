from django.conf.urls import url, patterns
from django.conf import settings
from components.archival_storage import views


urlpatterns = patterns('',
    url(r'search/json/file/(?P<document_id_modified>\w+)/$', views.file_json),
    url(r'search/json/aip/(?P<document_id_modified>\w+)/$', views.aip_json),
    url(r'search/create_aic/$', views.create_aic,
        name='create_aic'),
    url(r'search/$', views.search,
        name='archival_storage_search'),
    url(r'delete/aip/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.aip_delete,
        name='aip_delete'),
    url(r'(?P<package_uuid>' + settings.UUID_REGEX + ')/reingest/$', views.reingest_aip,
        name='reingest_aip'),
    url(r'download/aip/file/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.aip_file_download),
    url(r'download/aip/(?P<uuid>' + settings.UUID_REGEX + ')/pointer_file/$', views.aip_pointer_file_download),
    url(r'download/aip/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.aip_download),
    url(r'thumbnail/(?P<fileuuid>' + settings.UUID_REGEX + ')/$', views.send_thumbnail),
    url(r'^$', views.overview,
        name='archival_storage_index')
)
