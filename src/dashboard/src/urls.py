from django.conf.urls.defaults import *

UUID_REGEX = '[\w]{8}(-[\w]{4}){3}-[\w]{12}'

urlpatterns = patterns('',
    (r'^mcp/', include('mcp.urls')),
    (r'^installer/', include('installer.urls')),
    (r'^administration/accounts/', include('components.accounts.urls')),
    (r'^archival-storage/', include('components.archival_storage.urls')),
    (r'^preservation-planning/', include('components.preservation_planning.urls')),
    (r'transfer/(?P<uuid>' + UUID_REGEX + ')/rights/', include('components.rights.transfer_urls')),
    (r'transfer/', include('components.transfer.urls')),
    (r'ingest/(?P<uuid>' + UUID_REGEX + ')/rights/', include('components.rights.ingest_urls')),
    (r'^administration/', include('components.administration.urls')),
    (r'', include('main.urls'))
)
