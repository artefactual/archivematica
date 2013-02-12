import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
from tastypie.resources import ModelResource
from main import models
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS

class FPRFileIDResource(ModelResource):
    class Meta:
        queryset = models.FPRFileID.objects.all()
        resource_name = 'file_id'

        filtering = {
            "uuid": ALL,
            "lastmodified": ALL
        }
