from django.conf.urls.defaults import patterns



UUID_REGEX = '[\w]{8}(-[\w]{4}){3}-[\w]{12}'

urlpatterns = patterns('components.archival_storage.views',
    (r'page/(?P<page>\d+)/$', 'archival_storage_page'),
    (r'search/json/file/(?P<document_id_modified>\w+)/$', 'archival_storage_file_json'),
    (r'search/$', 'archival_storage_search'),
    (r'download/(?P<uuid>' + UUID_REGEX + ')/$', 'archival_storage_sip_download'),
    (r'$', 'archival_storage')
)
