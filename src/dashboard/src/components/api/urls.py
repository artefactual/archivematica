from django.conf.urls.defaults import *
from components.api.models import AIPResource
from components.api.models import SelectionAPIResource

aip_resource = AIPResource()
selectionAPI = SelectionAPIResource()

urlpatterns = patterns('components.archival_storage.views',
    (r'', include(aip_resource.urls)),
    (r'', include(selectionAPI.urls)),
)
