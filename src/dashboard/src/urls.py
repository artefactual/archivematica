from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^mcp/', include('mcp.urls')),
    (r'^installer/', include('installer.urls')),
    (r'^administration/accounts/', include('components.accounts.urls')),
    (r'^archival-storage/', include('components.archival_storage.urls')),
    (r'^preservation-planning/', include('components.preservation_planning.urls')),
    (r'', include('main.urls'))
)
