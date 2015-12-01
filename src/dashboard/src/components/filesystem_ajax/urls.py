from django.conf.urls import url, patterns
from django.conf import settings
from components.filesystem_ajax import views


urlpatterns = patterns('',
    url(r'^download_ss/$', views.download_ss),
    url(r'^download_fs/$', views.download_fs),
    url(r'^(?P<uuid>' + settings.UUID_REGEX + ')/download/$', views.download_by_uuid),
    url(r'^contents/arrange/$', views.arrange_contents),
    url(r'^contents/$', views.contents),
    url(r'^children/location/(?P<location_uuid>' + settings.UUID_REGEX + ')/$', views.directory_children_proxy_to_storage_server),
    url(r'^delete/arrange/$', views.delete_arrange),
    url(r'^create_directory_within_arrange/$', views.create_directory_within_arrange),
    url(r'^copy_to_arrange/$', views.copy_to_arrange),
    url(r'^transfer/$', views.start_transfer_logged_in),
    url(r'^copy_from_arrange/$', views.copy_from_arrange_to_completed),
    url(r'^copy_metadata_files/$', views.copy_metadata_files),
)
