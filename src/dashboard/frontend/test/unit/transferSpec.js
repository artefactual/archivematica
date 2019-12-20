'use strict';

import '../../app/services/transfer.service.js';

describe('Transfer', function() {
  beforeEach(angular.mock.module('transferService'));
  beforeEach(angular.mock.inject(function(Transfer) {
    Transfer.resolve({
      'formats': [
        {
          'label': 'Powerpoint 97-2002',
          'puid': 'fmt/126',
        },
      ],
      'transfers': [
        {
          'id': 'd5700e44-68f1-4eec-a7e4-c5a5c7da2373',
          'title': 'SW1hZ2VzLTQ5YzQ3MzE5LTEzODctNDhjNC1hYWI3LTM4MTkyM2YwN2Y3Yw==',
          'relative_path': 'SW1hZ2VzLTQ5YzQ3MzE5LTEzODctNDhjNC1hYWI3LTM4MTkyM2YwN2Y3Yw==',
          'children': [
            {
              'id': '042340ba-e682-4454-aa26-a9230de79c5f',
              'title': 'cnVieS5yYg==',
              'relative_path': 'SW1hZ2VzLTQ5YzQ3MzE5LTEzODctNDhjNC1hYWI3LTM4MTkyM2YwN2Y3Yy9ydWJ5LnJi',
              'tags': [],
            },
            {
              'id': 'c3908e0d-3ac7-4603-8d0b-9b26a0df9c64',
              'title': 'c2FwcGhpcmUuY2xq',
              'relative_path': 'SW1hZ2VzLTQ5YzQ3MzE5LTEzODctNDhjNC1hYWI3LTM4MTkyM2YwN2Y3Yy9zYXBwaGlyZS5jbGo=',
              'tags': [],
            },
          ],
        },
        {
          'id': 'd5700e44-68f1-4eec-a7e4-c5a5c7da2374',
          'title': 'SW1hZ2VzLTQ5YzQ3MzE5LTEzODctNDhjNC1hYWI3LTM4MTkyM2YwN2Y3Yw==',
          'relative_path': 'SW1hZ2VzLTQ5YzQ3MzE5LTEzODctNDhjNC1hYWI3LTM4MTkyM2YwN2Y3Yw==',
          'children': [
            {
              'id': 'SW1hZ2VzLTQ5YzQ3MzE5LTEzODctNDhjNC1hYWI3LTM4MTkyM2YwN2Y3Yy9ydWJ5LnJi',
              'title': 'cnVieS5yYg==',
              'relative_path': 'SW1hZ2VzLTQ5YzQ3MzE5LTEzODctNDhjNC1hYWI3LTM4MTkyM2YwN2Y3Yy9ydWJ5LnJi',
              'tags': [],
            },
          ],
        },
      ],
    });
  }));

  it('should be able to track a copy of fetched transfers on itself', inject(function(Transfer) {
    expect(Transfer.data.length).toEqual(2);
    expect(Transfer.data[0].id).toEqual('d5700e44-68f1-4eec-a7e4-c5a5c7da2373');
    expect(Transfer.data[1].id).toEqual('d5700e44-68f1-4eec-a7e4-c5a5c7da2374');
  }));

  it('should provide a flat map of all stored transfers using IDs as keys', inject(function(Transfer) {
    expect(Transfer.id_map['d5700e44-68f1-4eec-a7e4-c5a5c7da2373'].title).toEqual('Images-49c47319-1387-48c4-aab7-381923f07f7c');
  }));

  it('should be able to track a copy of the fetched transfers\' formats on itself', inject(function(Transfer) {
    expect(Transfer.formats.length).toEqual(1);
    expect(Transfer.formats[0].puid).toEqual('fmt/126');
  }));

  it('should be able to add tags to files', inject(function(Transfer) {
    var ruby = Transfer.id_map['042340ba-e682-4454-aa26-a9230de79c5f'];
    expect(ruby.tags.length).toEqual(0);
    Transfer.add_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test', true);
    expect(ruby.tags.length).toEqual(1);
  }));

  it('should be able to remove tags for a given file', inject(function(Transfer) {
    var ruby = Transfer.id_map['042340ba-e682-4454-aa26-a9230de79c5f'];
    Transfer.add_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test1', true);
    Transfer.add_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test2', true);
    Transfer.add_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test3', true);
    expect(ruby.tags.length).toEqual(3);
    Transfer.remove_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test2', true);
    expect(ruby.tags.length).toEqual(2);
    expect(ruby.tags).toEqual(['test1', 'test3']);
  }));

  it('should be able to remove all tags for a given file if no tag is specified', inject(function(Transfer) {
    var ruby = Transfer.id_map['042340ba-e682-4454-aa26-a9230de79c5f'];
    Transfer.add_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test1', true);
    Transfer.add_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test2', true);
    expect(ruby.tags.length).toEqual(2);
    Transfer.remove_tag('042340ba-e682-4454-aa26-a9230de79c5f', null, true);
    expect(ruby.tags.length).toEqual(0);
  }));

  it('should track a flat list of all applied tags', inject(function(Transfer) {
    expect(Transfer.tags).toEqual([]);
    Transfer.add_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test1');
    Transfer.add_tag('c3908e0d-3ac7-4603-8d0b-9b26a0df9c64', 'test2');
    expect(Transfer.tags).toEqual(['test1', 'test2']);
  }));

  it('should track an object with tag updates', inject(function(Transfer) {
    expect(Transfer.tag_updates).toEqual({});
    Transfer.add_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test1', true);
    expect(Transfer.tag_updates).toEqual({
      '042340ba-e682-4454-aa26-a9230de79c5f': ['test1']
    });
    Transfer.add_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test2', true);
    expect(Transfer.tag_updates).toEqual({
      '042340ba-e682-4454-aa26-a9230de79c5f': ['test1', 'test2']
    });
    Transfer.add_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test2', true);
    Transfer.add_tag('c3908e0d-3ac7-4603-8d0b-9b26a0df9c64', 'test2', true);
    expect(Transfer.tag_updates).toEqual({
      '042340ba-e682-4454-aa26-a9230de79c5f': ['test1', 'test2'],
      'c3908e0d-3ac7-4603-8d0b-9b26a0df9c64': ['test2']
    });
    Transfer.remove_tag('042340ba-e682-4454-aa26-a9230de79c5f', 'test1', true);
    expect(Transfer.tag_updates).toEqual({
      '042340ba-e682-4454-aa26-a9230de79c5f': ['test2'],
      'c3908e0d-3ac7-4603-8d0b-9b26a0df9c64': ['test2']
    });
    Transfer.remove_tag('042340ba-e682-4454-aa26-a9230de79c5f', null, true);
    expect(Transfer.tag_updates).toEqual({
      '042340ba-e682-4454-aa26-a9230de79c5f': [],
      'c3908e0d-3ac7-4603-8d0b-9b26a0df9c64': ['test2']
    });
  }));

  it('should not tag metadata files', inject(function(Transfer) {
    var ruby = Transfer.id_map['SW1hZ2VzLTQ5YzQ3MzE5LTEzODctNDhjNC1hYWI3LTM4MTkyM2YwN2Y3Yy9ydWJ5LnJi'];
    expect(ruby.tags.length).toEqual(0);
    Transfer.add_tag('SW1hZ2VzLTQ5YzQ3MzE5LTEzODctNDhjNC1hYWI3LTM4MTkyM2YwN2Y3Yy9ydWJ5LnJi', 'test', true);
    expect(ruby.tags.length).toEqual(0);
  }));
});
