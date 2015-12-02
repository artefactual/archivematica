# -*- coding: UTF-8 -*-
import os
import sys

import pytest
import vcr

from archivesspace.client import ArchivesSpaceClient, ArchivesSpaceError, CommunicationError

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
    assert len(collections) == 2
    assert collections[0]['title'] == 'Test fonds'
    assert collections[0]['type'] == 'resource'


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_listing_collections_search.yaml'))
def test_listing_collections_search():
    client = ArchivesSpaceClient(**AUTH)
    collections = client.find_collections(search_pattern='Test fonds')
    assert len(collections) == 1
    assert collections[0]['title'] == 'Test fonds'
    assert collections[0]['type'] == 'resource'

    no_results = client.find_collections(search_pattern='No such fonds')
    assert len(no_results) == 0


@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_listing_collections_sort.yaml'))
def test_listing_collections_sort():
    client = ArchivesSpaceClient(**AUTH)
    asc = client.find_collections(sort_by='asc')
    assert len(asc) == 2
    assert asc[0]['title'] == 'Some other fonds'
    assert asc[0]['type'] == 'resource'

    desc = client.find_collections(sort_by='desc')
    assert len(desc) == 2
    assert desc[0]['title'] == 'Test fonds'
    assert desc[0]['type'] == 'resource'


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
    assert data['type'] == 'resource'

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_find_resource_children_recursion.yaml'))
def test_find_resource_children_recursion_level():
    client = ArchivesSpaceClient(**AUTH)
    data = client.get_resource_component_and_children('/repositories/2/resources/1',
                                                      recurse_max_level=1)
    assert data['children'] == []

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

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_find_by_id_refid.yaml'))
def test_find_by_id_refid():
    client = ArchivesSpaceClient(**AUTH)
    data = client.find_by_id('archival_objects', 'ref_id', 'a118514fab1b2ee6a7e9ad259e1de355')
    assert len(data) == 1
    item = data[0]
    assert item['identifier'] == 'a118514fab1b2ee6a7e9ad259e1de355'
    assert item['id'] == '/repositories/2/archival_objects/752250'
    assert item['type'] == 'resource_component'
    assert item['title'] == 'Test AO'
    assert item['levelOfDescription'] == 'file'

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_augment_ids.yaml'))
def test_augment_ids():
    client = ArchivesSpaceClient(**AUTH)
    data = client.augment_resource_ids(['/repositories/2/resources/1', '/repositories/2/resources/2'])
    assert len(data) == 2
    assert data[0]['title'] == 'Test fonds'
    assert data[0]['type'] == 'resource'
    assert data[1]['title'] == 'Some other fonds'
    assert data[1]['type'] == 'resource'

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_resource_type.yaml'))
def test_get_resource_type():
    client = ArchivesSpaceClient(**AUTH)
    assert client.resource_type('/repositories/2/resources/2') == 'resource'
    assert client.resource_type('/repositories/2/archival_objects/3') == 'resource_component'

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_resource_type.yaml'))
def test_get_resource_type_raises_on_invalid_input():
    client = ArchivesSpaceClient(**AUTH)
    with pytest.raises(ArchivesSpaceError):
        client.resource_type('invalid')

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_identifier_exact_match.yaml'))
def test_identifier_search_exact_match():
    client = ArchivesSpaceClient(**AUTH)
    assert client.find_collection_ids(identifier='F1') == ['/repositories/2/resources/1']
    assert client.count_collections(identifier='F1') == 1
    assert len(client.find_collections(identifier='F1')) == 1

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_identifier_wildcard.yaml'))
def test_identifier_search_wildcard():
    client = ArchivesSpaceClient(**AUTH)
    # Searching for an identifier prefix with no wildcard returns nothing
    assert client.find_collection_ids(identifier='F') == []
    assert client.count_collections(identifier='F') == 0
    assert len(client.find_collections(identifier='F')) == 0

    assert client.find_collection_ids(identifier='F*') == ['/repositories/2/resources/1', '/repositories/2/resources/2']
    assert client.count_collections(identifier='F*') == 2
    assert len(client.find_collections(identifier='F*')) == 2

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_add_child_resource.yaml'))
def test_add_child_resource():
    client = ArchivesSpaceClient(**AUTH)
    uri = client.add_child('/repositories/2/resources/2', title='Test child', level='item')
    assert uri == '/repositories/2/archival_objects/3'

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_add_child_resource_component.yaml'))
def test_add_child_resource_component():
    client = ArchivesSpaceClient(**AUTH)
    uri = client.add_child('/repositories/2/archival_objects/1', title='Test child', level='item')
    assert uri == '/repositories/2/archival_objects/5'

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_delete_record_resource.yaml'))
def test_delete_record_resource():
    client = ArchivesSpaceClient(**AUTH)
    record_id = '/repositories/2/resources/3'
    assert client.get_record(record_id)
    r = client.delete_record(record_id)
    assert r['status'] == 'Deleted'
    with pytest.raises(CommunicationError):
        client.get_record(record_id)

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_delete_record_archival_object.yaml'))
def test_delete_record_archival_object():
    client = ArchivesSpaceClient(**AUTH)
    record_id = '/repositories/2/archival_objects/4'
    assert client.get_record(record_id)
    r = client.delete_record(record_id)
    assert r['status'] == 'Deleted'
    with pytest.raises(CommunicationError):
        client.get_record(record_id)

@vcr.use_cassette(os.path.join(THIS_DIR, 'fixtures', 'test_edit_archival_object.yaml'))
def test_edit_archival_object():
    client = ArchivesSpaceClient(**AUTH)
    original = client.get_record('/repositories/2/archival_objects/3')
    assert original['title'] == 'Test subseries'
    assert original['dates'][0]['end'] == '2015-01-01'
    assert not original['notes']
    new_record = {
        'id': '/repositories/2/archival_objects/3',
        'title': 'Test edited subseries',
        'start_date': '2014-11-01',
        'end_date': '2015-11-01',
        'date_expression': 'November, 2014 to November, 2015',
        'notes': [{
            'type': 'odd',
            'content': 'This is a test note'
        }],
    }
    client.edit_record(new_record)
    updated = client.get_record('/repositories/2/archival_objects/3')
    assert updated['title'] == new_record['title']
    assert updated['dates'][0]['begin'] == new_record['start_date']
    assert updated['dates'][0]['end'] == new_record['end_date']
    assert updated['dates'][0]['expression'] == new_record['date_expression']
    assert updated['notes'][0]['type'] == new_record['notes'][0]['type']
    assert updated['notes'][0]['subnotes'][0]['content'] == new_record['notes'][0]['content']
