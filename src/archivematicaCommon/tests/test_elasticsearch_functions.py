import os

import mock
import pytest
import unittest
import vcr

import elasticSearchFunctions

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestElasticSearchFunctions(unittest.TestCase):

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_elasticsearch_setup.yaml'))
    def setUp(self):
        hosts = os.environ.get('ELASTICSEARCH_SERVER', '127.0.0.1:9200')
        elasticSearchFunctions.setup(hosts)
        self.client = elasticSearchFunctions.get_client()
        self.aip_uuid = 'a1ee611a-a4f5-4ba9-b7ce-b92695746514'

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_delete_aip.yaml'))
    def test_delete_aip(self):
        # Verify AIP exists
        results = self.client.search(
            index='aips',
            doc_type='aip',
            body={'query': {'term': {'uuid': self.aip_uuid}}},
            fields='uuid',
        )
        assert results['hits']['total'] == 1
        assert results['hits']['hits'][0]['fields']['uuid'] == [self.aip_uuid]
        # Delete AIP
        success = elasticSearchFunctions.delete_aip(self.client, self.aip_uuid)
        # Verify AIP gone
        assert success is True
        results = self.client.search(
            index='aips',
            doc_type='aip',
            body={'query': {'term': {'uuid': self.aip_uuid}}},
            fields='uuid',
        )
        assert results['hits']['total'] == 0

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_delete_aip_files.yaml'))
    def test_delete_aip_files(self):
        # Verify AIP exists
        results = self.client.search(
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
        success = elasticSearchFunctions.delete_aip_files(self.client, self.aip_uuid)
        # Verify AIP gone
        assert success is True
        results = self.client.search(
            index='aips',
            doc_type='aipfile',
            body={'query': {'term': {'AIPUUID': self.aip_uuid}}},
            fields='AIPUUID,FILEUUID',
        )
        assert results['hits']['total'] == 0

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_list_tags.yaml'))
    def test_list_tags(self):
        assert elasticSearchFunctions.get_file_tags(self.client, 'a410501b-64ac-4b81-92ca-efa9e815366d') == ['test1']

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_list_tags_no_matches.yaml'))
    def test_list_tags_fails_when_file_cant_be_found(self):
        with pytest.raises(elasticSearchFunctions.EmptySearchResultError):
            elasticSearchFunctions.get_file_tags(self.client, 'no_such_file')

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_set_tags.yaml'))
    def test_set_tags(self):
        elasticSearchFunctions.set_file_tags(self.client, '2101fa74-bc27-405b-8e29-614ebd9d5a89', ['test'])
        assert elasticSearchFunctions.get_file_tags(self.client, '2101fa74-bc27-405b-8e29-614ebd9d5a89') == ['test']

    @vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_set_tags_no_matches.yaml'))
    def test_set_tags_fails_when_file_cant_be_found(self):
        with pytest.raises(elasticSearchFunctions.EmptySearchResultError):
            elasticSearchFunctions.set_file_tags(self.client, 'no_such_file', [])

    @mock.patch('elasticSearchFunctions.get_dashboard_uuid')
    @mock.patch('elasticSearchFunctions.wait_for_cluster_yellow_status')
    @mock.patch('elasticSearchFunctions.try_to_index')
    def test_index_mets_file_metadata(
            self,
            dummy_try_to_index,
            dummy_wait_for_cluster_yellow_status,
            dummy_get_dashboard_uuid,
    ):
        # Set up mocked functions
        dummy_get_dashboard_uuid.return_value = 'test-uuid'
        indexed_data = {}

        def get_dublincore_metadata(client, indexData, index, type_):
            try:
                dmd_section = indexData['METS']['dmdSec']
                metadata_container = dmd_section['ns0:xmlData_dict_list'][0]
                dc = metadata_container['ns1:dublincore_dict_list'][0]
            except (KeyError, IndexError):
                dc = None
            indexed_data[indexData['filePath']] = dc
        dummy_try_to_index.side_effect = get_dublincore_metadata

        # This METS file is a cut-down version of the AIP METS produced
        # using the SampleTransfers/DemoTransfer
        mets_file_path = os.path.join(
            THIS_DIR, 'fixtures', 'test_index_metadata-METS.xml'
        )
        mets_object_id = '771aa252-7930-4e68-b73e-f91416b1d4a4'
        index = 'aips'
        type_ = 'aipfile'
        uuid = 'f42a260a-9b53-4555-847e-8a4329c81662'
        sipName = 'DemoTransfer-{}'.format(uuid)
        identifiers = []
        indexed_files_count = elasticSearchFunctions.index_mets_file_metadata(
            client=self.client,
            uuid=uuid,
            metsFilePath=mets_file_path,
            index=index,
            type_=type_,
            sipName=sipName,
            identifiers=identifiers,
        )

        # ES should have indexed 12 files
        # - 5 content files
        # - 5 checksum and csv files in the metadata directory
        # - 2 files generated in the transfer process
        assert indexed_files_count == 12
        assert dummy_try_to_index.call_count == 12

        # Metadata should have been indexed only for these content
        # files because they are listed in the metadata.csv file
        content_files_with_metadata = (
            {
                'path': ('objects/View_from_lookout_over_Queenstown_'
                         'towards_the_Remarkables_in_spring.jpg'),
                'title': ('Morning view from lookout over Queenstown '
                          'towards the Remarkables in spring'),
                'creator': 'Pseudopanax at English Wikipedia',
            },
            {
                'path': 'objects/beihai.tif',
                'title': 'Beihai, Guanxi, China, 1988',
                'creator': ('NASA/GSFC/METI/ERSDAC/JAROS and U.S./Japan '
                            'ASTER Science Team'),
            },
            {
                'path': 'objects/bird.mp3',
                'title': '14000 Caen, France - Bird in my garden',
                'creator': 'Nicolas Germain',
            },
            {
                'path': 'objects/ocr-image.png',
                'title': 'OCR image',
                'creator': 'Tesseract',
            },
        )
        for file_metadata in content_files_with_metadata:
            dc = indexed_data[file_metadata['path']]
            assert dc['dc:title'] == file_metadata['title']
            assert dc['dc:creator'] == file_metadata['creator']

        # There is no metadata for this content file because
        # it was not listed in the metadata.csv file
        assert indexed_data['objects/piiTestDataCreditCardNumbers.txt'] is None

        # Checksum and csv files in the metadata directory
        # won't have dublin core metadata indexed
        files_in_metadata_directory = (
            'checksum.md5',
            'checksum.sha1',
            'checksum.sha256',
            'metadata.csv',
            'rights.csv',
        )
        for filename in files_in_metadata_directory:
            path = 'objects/metadata/transfers/DemoTransfer-{}/{}'.format(
                mets_object_id, filename
            )
            assert indexed_data[path] is None

        # Neither will the generated files during the transfer process
        generated_files = (
            'dc.json',
            'directory_tree.txt',
        )
        for filename in generated_files:
            path = 'objects/metadata/transfers/DemoTransfer-{}/{}'.format(
                mets_object_id, filename
            )
            assert indexed_data[path] is None
