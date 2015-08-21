
from elasticsearch import Elasticsearch
import os
import sys
import pytest
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

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_list_tags.yaml'))
    def test_list_tags(self):
        assert elasticSearchFunctions.connect_and_get_file_tags('a410501b-64ac-4b81-92ca-efa9e815366d') == ['test1']

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_list_tags_no_matches.yaml'))
    def test_list_tags_fails_when_file_cant_be_found(self):
        with pytest.raises(elasticSearchFunctions.EmptySearchResultError):
            elasticSearchFunctions.connect_and_get_file_tags('no_such_file')

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_set_tags.yaml'))
    def test_set_tags(self):
        elasticSearchFunctions.connect_and_set_file_tags('2101fa74-bc27-405b-8e29-614ebd9d5a89', ['test'])
        assert elasticSearchFunctions.connect_and_get_file_tags('2101fa74-bc27-405b-8e29-614ebd9d5a89') == ['test']

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_set_tags_no_matches.yaml'))
    def test_set_tags_fails_when_file_cant_be_found(self):
        with pytest.raises(elasticSearchFunctions.EmptySearchResultError):
            elasticSearchFunctions.connect_and_set_file_tags('no_such_file', [])
