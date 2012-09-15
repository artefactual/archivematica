from django.conf.urls.defaults import patterns

urlpatterns = patterns('components.archival_storage.views',
    (r'page/(?P<page>\d+)/$', 'archival_storage_page'),
    (r'search/json/file/(?P<document_id_modified>\w+)/$', 'archival_storage_file_json'),
    (r'search/$', 'archival_storage_search'),
    (r'(?P<path>AIPsStore/[0-9a-z]{4}/[0-9a-z]{3}/[0-9a-z]{4}/[0-9a-z]{4}/[0-9a-z]{4}/[0-9a-z]{4}/[0-9a-z]{4}/.*\.(7z|zip))/$', 'archival_storage_sip_download'),
    (r'$', 'archival_storage')
)
