# -*- coding: UTF-8 -*-
import os
import sys

import vcr

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from archivesspace.client import ArchivesSpaceClient

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH = {
    'host': 'http://localhost',
    'user': 'admin',
    'passwd': 'admin'
}


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_listing_collections.yaml'))
def test_listing_collections():
    client = ArchivesSpaceClient(**AUTH)
    collections = client.find_collections()
    assert len(collections) == 1
    assert collections[0]['title'] == 'Test fonds'


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_listing_collections_search.yaml'))
def test_listing_collections_search():
    client = ArchivesSpaceClient(**AUTH)
    collections = client.find_collections(search_pattern='Test fonds')
    assert len(collections) == 1
    assert collections[0]['title'] == 'Test fonds'

    no_results = client.find_collections(search_pattern='No such fonds')
    assert len(no_results) == 0


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_listing_collections_sort.yaml'))
def test_listing_collections_sort():
    client = ArchivesSpaceClient(**AUTH)
    asc = client.find_collections(sort_by='asc')
    assert len(asc) == 2
    assert asc[0]['title'] == 'Some other fonds'

    desc = client.find_collections(sort_by='desc')
    assert len(desc) == 2
    assert desc[0]['title'] == 'Test fonds'


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_find_resource_id.yaml'))
def test_find_resource_id():
    client = ArchivesSpaceClient(**AUTH)
    assert client.find_resource_id_for_component('/repositories/2/archival_objects/3') == '/repositories/2/resources/1'


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_find_component_parent.yaml'))
def test_find_component_parent():
    client = ArchivesSpaceClient(**AUTH)
    type, id = client.find_parent_id_for_component('/repositories/2/archival_objects/3')

    assert type == ArchivesSpaceClient.RESOURCE_COMPONENT
    assert id == '/repositories/2/archival_objects/1'

    type, id = client.find_parent_id_for_component('/repositories/2/archival_objects/1')
    assert type == ArchivesSpaceClient.RESOURCE
    assert id == '/repositories/2/resources/1'


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_find_resource_children.yaml'))
def test_find_resource_children():
    client = ArchivesSpaceClient(**AUTH)
    data = client.get_resource_component_and_children('/repositories/2/resources/1')

    assert type(data) == dict
    assert len(data['children']) == 2
    assert data['title'] == 'Test fonds'

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_find_resource_children_recursion.yaml'))
def test_find_resource_children_recursion_level():
    client = ArchivesSpaceClient(**AUTH)
    data = client.get_resource_component_and_children('/repositories/2/resources/1',
                                                      recurse_max_level=1)
    assert data['children'] is False

    data = client.get_resource_component_and_children('/repositories/2/resources/1',
                                                      recurse_max_level=2)
    assert len(data['children']) == 2


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_find_collection_ids.yaml'))
def test_find_collection_ids():
    client = ArchivesSpaceClient(**AUTH)
    ids = client.find_collection_ids()
    assert ids == ['/repositories/2/resources/1', '/repositories/2/resources/2']


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_find_collection_ids_search.yaml'))
def test_find_collection_ids_search():
    client = ArchivesSpaceClient(**AUTH)
    ids = client.find_collection_ids(search_pattern='Some')
    assert ids == ['/repositories/2/resources/2']

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_count_collection_ids.yaml'))
def test_count_collection_ids():
    client = ArchivesSpaceClient(**AUTH)
    ids = client.count_collections()
    assert ids == 2


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_count_collection_ids_search.yaml'))
def test_count_collection_ids_search():
    client = ArchivesSpaceClient(**AUTH)
    ids = client.count_collections(search_pattern='Some')
    assert ids == 1


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_augment_ids.yaml'))
def test_augment_ids():
    client = ArchivesSpaceClient(**AUTH)
    data = client.augment_resource_ids(['/repositories/2/resources/1', '/repositories/2/resources/2'])
    assert len(data) == 2
    assert data[0]['title'] == 'Test fonds'
    assert data[1]['title'] == 'Some other fonds'
