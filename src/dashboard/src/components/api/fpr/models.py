import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
from tastypie.resources import ModelResource
from main import models

class FPRFileIDResource(ModelResource):
    class Meta:
        queryset = models.FPRFileID.objects.all()
        resource_name = 'file_id'
