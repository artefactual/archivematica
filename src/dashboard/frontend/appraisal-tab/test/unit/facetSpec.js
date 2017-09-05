'use strict';

import '../../app/services/facet.service.js';

describe('Facet', function() {
  beforeEach(angular.mock.module('facetService'));

  it('should allow new facets to be defined by name', inject(function(Facet) {
    expect(Facet.get('foo')).toBe(undefined);
    Facet.add('foo', 'bar');
    expect(Facet.get('foo')).toEqual(['bar']);
  }));

  it('should allow a specific facet to be removed', inject(function(Facet) {
    Facet.add('removeOne', '1');
    Facet.add('removeOne', '2');
    expect(Facet.get('removeOne').length).toBe(2);
    Facet.remove('removeOne', '1');
    expect(Facet.get('removeOne').length).toBe(1);
  }));

  it('should remove every facet if no facet is specified', inject(function(Facet) {
    Facet.add('removeAll', '1');
    Facet.add('removeAll', '2');
    expect(Facet.get('removeAll').length).toBe(2);
    Facet.remove('removeAll');
    expect(Facet.get('removeAll')).toBe(undefined);
  }));

  it('should allow all facets to be removed', inject(function(Facet) {
    Facet.add('clearOne', '1');
    Facet.add('clearTwo', '1');
    expect(Facet.get('clearOne').length).toBe(1);
    expect(Facet.get('clearTwo').length).toBe(1);
    Facet.clear();
    expect(Facet.get('clearOne')).toBe(undefined);
    expect(Facet.get('clearTwo')).toBe(undefined);
  }));

  it('should allow facets to be defined as strings to perform exact matches', inject(function(Facet) {
    Facet.add('puid', 'fmt/256');
    expect(Facet.filter([{'puid': 'fmt/256'}, {'puid': 'fmt/128'}, {'puid': 'fmt/2560'}])).toEqual([{'puid': 'fmt/256'}]);
  }));

  it('should allow facets to be defined as regular expressions to perform fuzzy matches', inject(function(Facet) {
    Facet.add('filename', /\.jpg$/);
    expect(Facet.filter([{'filename': '1.png'}, {'filename': '2.jpg'}])).toEqual([{'filename': '2.jpg'}]);
  }));

  it('should allow facets to be defined as functions to perform custom matches', inject(function(Facet) {
    Facet.add('date', function(value) {
      var start = value.split(':')[0];
      return Date.parse(start) > Date.parse('1970');
    });
    expect(Facet.filter([{'date': '1950:1999'}, {'date': '1975:1980'}])).toEqual([{'date': '1975:1980'}]);
  }));

  it('should return all elements with no filters', inject(function(Facet) {
    expect(Facet.filter([{'puid': 'fmt/256'}, {'puid': 'fmt/128'}])).toEqual([{'puid': 'fmt/256'}, {'puid': 'fmt/128'}]);
  }));

  it('should only return elements that match the current filter', inject(function(Facet) {
    Facet.add('puid', 'fmt/256');
    expect(Facet.filter([{'puid': 'fmt/256', 'name': 'foo'}, {'puid': 'fmt/128', 'name': 'bar'}])).toEqual([{'puid': 'fmt/256', 'name': 'foo'}]);
  }));

  it('should return elements that match any filter on different attributes', inject(function(Facet) {
    Facet.add('puid', 'fmt/256');
    Facet.add('name', 'foo');
    expect(Facet.filter([
      {'puid': 'fmt/256', 'name': 'bar'},
      {'puid': 'fmt/128', 'name': 'foo'},
      {'puid': 'fmt/2560', 'name': 'baz'},
    ])).toEqual([
      {'puid': 'fmt/256', 'name': 'bar'},
      {'puid': 'fmt/128', 'name': 'foo'},
    ]);
  }));

  it('should return elements that match any filter on the same attribute', inject(function(Facet) {
    Facet.add('puid', 'fmt/256');
    Facet.add('puid', 'fmt/128');
    expect(Facet.filter([
      {'puid': 'fmt/256', 'name': 'bar'},
      {'puid': 'fmt/128', 'name': 'foo'},
      {'puid': 'fmt/2560', 'name': 'baz'},
    ])).toEqual([
      {'puid': 'fmt/256', 'name': 'bar'},
      {'puid': 'fmt/128', 'name': 'foo'},
    ]);
  }));


  it('should be able to return a boolean value when filtering a single value', inject(function(Facet) {
    Facet.add('filename', /\.jpg$/);
    expect(Facet.passes_filters({'filename': '1.png'})).toBe(false);
    expect(Facet.passes_filters({'filename': '1.jpg'})).toBe(true);
  }));

  it('should return a unique ID for each newly-added value', inject(function(Facet) {
    var id1 = Facet.add('id', '1');
    var id2 = Facet.add('id', '2');
    expect(id1).toBeDefined();
    expect(id1).not.toEqual(id2);
  }));

  it('should allow a facet ID to be specified', inject(function(Facet) {
    var id = Facet.add('manual_id', '1', {}, 'this is an ID');
    expect(id).toEqual('this is an ID');
  }));

  it('should allow a facet to be fetched by ID', inject(function(Facet) {
    var id = Facet.add('get_id', '1');
    Facet.add('get_id', '2');
    expect(Facet.get_by_id('get_id', id)).toEqual('1');
  }));

  it('should allow a facet to be removed by ID', inject(function(Facet) {
    var id = Facet.add('remove_id', '1');
    Facet.add('remove_id', '2');
    expect(Facet.get('remove_id').length).toEqual(2);
    Facet.remove_by_id('remove_id', id);
    expect(Facet.get('remove_id').length).toEqual(1);
  }));

  it('should provide a read-only flat list of every facet', inject(function(Facet) {
    Facet.add('list_a', '1');
    Facet.add('list_b', '2');
    expect(Facet.facet_list.length).toEqual(2);
  }));

  it('should apply a filter to every element in a list if the value is a list', inject(function(Facet) {
    Facet.add('key', 'test');
    expect(Facet.passes_filters({'key': ['test']})).toBe(true);
    expect(Facet.passes_filters({'key': ['this', 'should', 'fail']})).toBe(false);
    expect(Facet.passes_filters({'key': ['this', 'should', 'pass', 'test']})).toBe(true);
  }));

  it('should consider empty list values to be false', inject(function(Facet) {
    Facet.add('key', 'test');
    expect(Facet.passes_filters({'key': []})).toBe(false);
  }));

  it('should be able to only filter on a subset of filters', inject(function(Facet) {
    Facet.add('tag', 'test');
    Facet.add('format', 'jpg');
    expect(Facet.passes_filters({'tag': 'false', 'format': 'jpg'})).toBe(true);
    expect(Facet.passes_filters({'tag': 'false', 'format': 'jpg'}, ['tag'])).toBe(false);
    expect(Facet.passes_filters({'tag': 'test', 'format': 'jpg'}, ['tag'])).toBe(true);
  }));

  it('should delete the facet key if all filters for that facet have been removed', inject(function(Facet) {
    expect(Facet.facets['key']).toBeUndefined();
    Facet.add('key', 'value');
    expect(Facet.facets['key']).toBeDefined();
    Facet.remove('key', 'value');
    expect(Facet.facets['key']).toBeUndefined();
  }));
});
