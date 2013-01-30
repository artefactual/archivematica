from django.conf.urls.defaults import *
from components.api.models import SelectionAvailableResource
from components.api.models import SelectionAPIResource

selectionAvailable = SelectionAvailableResource()
selectionAPI = SelectionAPIResource()

urlpatterns = patterns('components.archival_storage.views',
    (r'', include(selectionAvailable.urls)),
    (r'', include(selectionAPI.urls)),
)
