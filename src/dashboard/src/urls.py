from django.conf.urls import url, include, patterns
from django.conf import settings

urlpatterns = patterns('',
    url(r'^mcp/', include('components.mcp.urls')),
    url(r'^installer/', include('installer.urls')),
    url(r'^administration/accounts/', include('components.accounts.urls')),
    url(r'^archival-storage/', include('components.archival_storage.urls')),
    url(r'^fpr/', include('fpr.urls')),
    url(r'^transfer/(?P<uuid>' + settings.UUID_REGEX + ')/rights/', include('components.rights.transfer_urls')),
    url(r'^transfer/', include('components.transfer.urls')),
    url(r'^appraisal/', include('components.appraisal.urls')),
    url(r'^ingest/(?P<uuid>' + settings.UUID_REGEX + ')/rights/', include('components.rights.ingest_urls')),
    url(r'^ingest/', include('components.ingest.urls')),
    url(r'^administration/', include('components.administration.urls')),
    url(r'^filesystem/', include('components.filesystem_ajax.urls')),
    url(r'^api/', include('components.api.urls')),
    url(r'^file/', include('components.file.urls')),
    url(r'^access/', include('components.access.urls')),
    url(r'^backlog/', include('components.backlog.urls')),
    url(r'', include('main.urls'))
)
