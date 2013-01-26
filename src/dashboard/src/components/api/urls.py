from django.conf.urls.defaults import *
from components.api.models import AIPResource

aip_resource = AIPResource()

urlpatterns = patterns('components.archival_storage.views',
    (r'', include(aip_resource.urls)),
)
