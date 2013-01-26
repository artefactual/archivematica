from django.conf.urls.defaults import *
from components.api.models import AIPResource
from components.api.models import SIPResource

aip_resource = AIPResource()
sip_resource = SIPResource()

urlpatterns = patterns('components.archival_storage.views',
    (r'', include(aip_resource.urls)),
    (r'', include(sip_resource.urls)),
)
