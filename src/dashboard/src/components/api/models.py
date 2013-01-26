import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
from tastypie.resources import ModelResource
from main import models

class AIPResource(ModelResource):
    class Meta:
        queryset = models.AIP.objects.all()
        resource_name = 'aip'

class SIPResource(ModelResource):
    class Meta:
        queryset = models.SIP.objects.all()
        resource_name = 'sip'
