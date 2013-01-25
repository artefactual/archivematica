import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
from tastypie.resources import ModelResource
from main.models import AIP

class AIPResource(ModelResource):
    class Meta:
        queryset = AIP.objects.all()
        resource_name = 'aip'
