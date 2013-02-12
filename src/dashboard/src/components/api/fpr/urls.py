from django.conf.urls.defaults import *
from components.api.fpr.models import FPRFileIDResource

file_id_resource = FPRFileIDResource()

urlpatterns = patterns('components.archival_storage.views',
    (r'', include(file_id_resource.urls)),
)
