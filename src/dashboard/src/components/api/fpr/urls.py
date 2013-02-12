from django.conf.urls.defaults import *
from components.api.fpr.models import FPRFileIDResource
from tastypie.api import Api

# add version to FPR resources
api = Api(api_name='v1')
api.register(FPRFileIDResource())

urlpatterns = patterns('components.archival_storage.views',
    (r'', include(api.urls)),
)
