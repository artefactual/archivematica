from contrib.mcp.client import MCPClient
import sys
from lxml import etree
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
from tastypie.resources import ModelResource
from tastypie.resources import Resource
from tastypie import fields
from tastypie.bundle import Bundle
from main import models
#useful references: 
# https://docs.djangoproject.com/en/dev/topics/db/models/
# http://www.youtube.com/watch?v=Zv26xHYlc8s
# http://django-tastypie.readthedocs.org/en/latest/non_orm_data_sources.html
# http://stackoverflow.com/questions/13094835/how-to-use-tastypie-to-wrap-internal-functions
# http://django-tastypie.readthedocs.org/en/v0.9.11/cookbook.html#adding-search-functionality
# http://django-tastypie.readthedocs.org/en/latest/resources.html

#http://localhost/api/SelectionAvailable/?format=json
#http://localhost/api/SelectionAPI/?format=json

mcpClient = MCPClient()

class SelectionAPIObject(object):
    def __init__(self, initial=None):
        self.__dict__['_data'] = {}

        if hasattr(initial, 'items'):
            self.__dict__['_data'] = initial

    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        self.__dict__['_data'][name] = value

    def to_dict(self):
        return self._data

class SelectionAPIResource(Resource):
    # Just like a Django ``Form`` or ``Model``, we're defining all the
    # fields we're going to handle with the API here.
    unitType = fields.CharField(attribute='unitType')
    unitUUID = fields.CharField(attribute='unitUUID')
    currentPath = fields.CharField(attribute='currentPath') 
    selectionMade = fields.CharField(attribute='selectionMade') 

    class Meta:
        resource_name = 'SelectionAPI'
        object_class = SelectionAPIObject
        #authorization = Authorization()

    # Specific to this resource, just to get the needed Riak bits.
    def _client(self):
        return None

    def _bucket(self):
        client = self._client()
        # Note that we're hard-coding the bucket to use. Fine for
        # example purposes, but you'll want to abstract this.
        return client.bucket('messages')

    # The following methods will need overriding regardless of your
    # data source.
    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {"pk":bundle_or_obj}
        #if isinstance(bundle_or_obj, Bundle):
        #    kwargs['pk'] = bundle_or_obj.obj.uuid
        #else:
        #    kwargs['pk'] = bundle_or_obj.uuid

        return kwargs

    def get_object_list(self, request):
        results = []
        XML = mcpClient.list()
        root = etree.fromstring(XML)
        #<choicesAvailableForUnits>\n  <choicesAvailableForUnit>\n    <UUID>b2da33eb-d388-4c5c-ae43-b7af33dc1b48</UUID>\n    <unit>\n      <type>Transfer</type>\n      <unitXML>\n        <UUID>52471b20-7fd1-46bc-9db2-7d81cea83fbb</UUID>
        print XML
        for unit in root.findall("choicesAvailableForUnit"):
            uuid = unit.find("UUID").text
            unitType = unit.find("unit/type").text
            unitUUID = unit.find("unit/unitXML/UUID").text
            unitCurrentPath = unit.find("unit/unitXML/currentPath").text
            entry = SelectionAPIObject({"uuid":uuid, "currentPath":unitCurrentPath, "unitType": unitType, "unitUUID":unitUUID, "selectionMade":"None"})
            results.append(entry)
        return results

    def obj_get_list(self, request=None, **kwargs):
        # Filtering disabled for brevity...
        return self.get_object_list(request)

    def obj_get(self, request=None, **kwargs):
        return
        bucket = self._bucket()
        message = bucket.get(kwargs['pk'])
        return RiakObject(initial=message.get_data())

    def obj_create(self, bundle, request=None, **kwargs):
        return
        bundle.obj = RiakObject(initial=kwargs)
        bundle = self.full_hydrate(bundle)
        bucket = self._bucket()
        new_message = bucket.new(bundle.obj.uuid, data=bundle.obj.to_dict())
        new_message.store()
        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        return
        return self.obj_create(bundle, request, **kwargs)

    def obj_delete_list(self, request=None, **kwargs):
        return
        bucket = self._bucket()

        for key in bucket.get_keys():
            obj = bucket.get(key)
            obj.delete()

    def obj_delete(self, request=None, **kwargs):
        return
        bucket = self._bucket()
        obj = bucket.get(kwargs['pk'])
        obj.delete()

    def rollback(self, bundles):
        pass

#---------------------------------------------------------------------------

class SelectionAvailableObject(object):
    def __init__(self, initial=None):
        self.__dict__['_data'] = {}

        if hasattr(initial, 'items'):
            self.__dict__['_data'] = initial

    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        self.__dict__['_data'][name] = value

    def to_dict(self):
        return self._data

class SelectionAvailableResource(Resource):
    # Just like a Django ``Form`` or ``Model``, we're defining all the
    # fields we're going to handle with the API here.
    chainAvailable = fields.CharField(attribute='chainAvailable')
    description = fields.CharField(attribute='description')
    unitSelectionAvailable = fields.ForeignKey(SelectionAPIResource, 'unitSelectionAPIAvailable')
    
    class Meta:
        resource_name = 'SelectionAvailable'
        object_class = SelectionAvailableObject
        #authorization = Authorization()

    # Specific to this resource, just to get the needed Riak bits.
    def _client(self):
        return None

    def _bucket(self):
        client = self._client()
        # Note that we're hard-coding the bucket to use. Fine for
        # example purposes, but you'll want to abstract this.
        return client.bucket('messages')

    # The following methods will need overriding regardless of your
    # data source.
    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        #if isinstance(bundle_or_obj, Bundle):
        kwargs['pk'] = bundle_or_obj.obj.uuid
        #else:
        #    kwargs['pk'] = bundle_or_obj.uuid

        return kwargs

    def get_object_list(self, request):
        results = []
        XML = mcpClient.list()
        root = etree.fromstring(XML)
        #<choicesAvailableForUnits>\n  <choicesAvailableForUnit>\n    <UUID>b2da33eb-d388-4c5c-ae43-b7af33dc1b48</UUID>\n    <unit>\n      <type>Transfer</type>\n      <unitXML>\n        <UUID>52471b20-7fd1-46bc-9db2-7d81cea83fbb</UUID>
        print XML
        for unit in root.findall("choicesAvailableForUnit"):
            uuid = unit.find("UUID").text
            unitType = unit.find("unit/type").text
            unitUUID = unit.find("unit/unitXML/UUID").text
            unitCurrentPath = unit.find("unit/unitXML/currentPath").text
            for choice in unit.find("choices").findall("choice"):
                chainAvailable = choice.find("chainAvailable").text
                description = choice.find("description").text
                entry = SelectionAvailableObject({"unitSelectionAPIAvailable":unitUUID, "unitType": unitType, "unitUUID":unitUUID, "chainAvailable": chainAvailable, "description": description})
                results.append(entry)
        return results

    def obj_get_list(self, request=None, **kwargs):
        # Filtering disabled for brevity...
        return self.get_object_list(request)

    def obj_get(self, request=None, **kwargs):
        return
        bucket = self._bucket()
        message = bucket.get(kwargs['pk'])
        return RiakObject(initial=message.get_data())

    def obj_create(self, bundle, request=None, **kwargs):
        return
        bundle.obj = RiakObject(initial=kwargs)
        bundle = self.full_hydrate(bundle)
        bucket = self._bucket()
        new_message = bucket.new(bundle.obj.uuid, data=bundle.obj.to_dict())
        new_message.store()
        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        return
        return self.obj_create(bundle, request, **kwargs)

    def obj_delete_list(self, request=None, **kwargs):
        return
        bucket = self._bucket()

        for key in bucket.get_keys():
            obj = bucket.get(key)
            obj.delete()

    def obj_delete(self, request=None, **kwargs):
        return
        bucket = self._bucket()
        obj = bucket.get(kwargs['pk'])
        obj.delete()

    def rollback(self, bundles):
        pass
