
from elasticsearch import Elasticsearch
import os
import sys
import unittest
import vcr

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class TestElasticSearchFunctions(unittest.TestCase):

    def setUp(self):
        self.conn = Elasticsearch('127.0.0.1:9200')
        self.aip_uuid = 'a1ee611a-a4f5-4ba9-b7ce-b92695746514'

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_delete_aip.yaml'))
    def test_delete_aip(self):
        # Verify AIP exists
        results = self.conn.search(
            index='aips',
            doc_type='aip',
            body={'query': {'term': {'uuid': self.aip_uuid}}},
            fields='uuid',
        )
        assert results['hits']['total'] == 1
        assert results['hits']['hits'][0]['fields']['uuid'] == [self.aip_uuid]
        # Delete AIP
        success = elasticSearchFunctions.delete_aip(self.aip_uuid)
        # Verify AIP gone
        assert success is True
        results = self.conn.search(
            index='aips',
            doc_type='aip',
            body={'query': {'term': {'uuid': self.aip_uuid}}},
            fields='uuid',
        )
        assert results['hits']['total'] == 0

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_delete_aip_files.yaml'))
    def test_delete_aip_files(self):
        # Verify AIP exists
        results = self.conn.search(
            index='aips',
            doc_type='aipfile',
            body={'query': {'term': {'AIPUUID': self.aip_uuid}}},
            fields='AIPUUID,FILEUUID',
            sort='FILEUUID:desc',
        )
        assert results['hits']['total'] == 3
        assert results['hits']['hits'][0]['fields']['AIPUUID'] == [self.aip_uuid]
        assert results['hits']['hits'][0]['fields']['FILEUUID'] == ['b8bd3cdd-f224-4237-b0d7-99c217ff8e67']
        assert results['hits']['hits'][1]['fields']['AIPUUID'] == [self.aip_uuid]
        assert results['hits']['hits'][1]['fields']['FILEUUID'] == ['68babd3e-7e6b-40e5-99f6-00ea724d4ce8']
        assert results['hits']['hits'][2]['fields']['AIPUUID'] == [self.aip_uuid]
        assert results['hits']['hits'][2]['fields']['FILEUUID'] == ['547bbd92-d8a0-4624-a9d3-69ba706eacee']
        # Delete AIP
        success = elasticSearchFunctions.connect_and_delete_aip_files(self.aip_uuid)
        # Verify AIP gone
        assert success is True
        results = self.conn.search(
            index='aips',
            doc_type='aipfile',
            body={'query': {'term': {'AIPUUID': self.aip_uuid}}},
            fields='AIPUUID,FILEUUID',
        )
        assert results['hits']['total'] == 0
