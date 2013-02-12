from django.conf.urls.defaults import *
from components.api.models import AIPResource
from components.api.models import SIPResource
from tastypie.api import Api

# add version to non-FPR resources
api = Api(api_name='v1')
api.register(AIPResource())
api.register(SIPResource())

urlpatterns = patterns('components.archival_storage.views',
    (r'', include(api.urls)),
    (r'fpr/', include('components.api.fpr.urls'))
)
