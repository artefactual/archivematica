'use strict';

import '../../app/services/tag.service.js';

describe('Tag', function() {
  beforeEach(angular.mock.module('tagService'));
  beforeEach(angular.mock.inject(function(_$httpBackend_) {
    _$httpBackend_.when('GET', '/file/e9010578-e065-4fa1-91c8-a105665037d6/tags').respond(function() {
      return [
        'fetched_tag_1', 'fetched_tag_2',
      ];
    });
    _$httpBackend_.when('PUT', '/file/f5e06285-10e7-4996-b184-1c07951dc75e/tags').respond({'success': true});
    _$httpBackend_.when('DELETE', '/file/51228e59-f9c5-4e79-9b2c-73ac8d217147/tags').respond({'success': true});
  }));

  it('should be able to fetch a list of file tags by UUID', inject(function(_$httpBackend_, Tag) {
    Tag.get('e9010578-e065-4fa1-91c8-a105665037d6').then(function(tags) {
      expect(tags.slice(0)).toEqual(['fetched_tag_1', 'fetched_tag_2']);
    });
    _$httpBackend_.flush();
  }));

  it('should be able to add tags to a file by UUID', inject(function(_$httpBackend_, Tag) {
    Tag.submit('f5e06285-10e7-4996-b184-1c07951dc75e', ['test1', 'test2']);
    _$httpBackend_.flush();
  }));

  it('should be able to remove tags from a file by UUID', inject(function(_$httpBackend_, Tag) {
    Tag.remove('51228e59-f9c5-4e79-9b2c-73ac8d217147');
    _$httpBackend_.flush();
  }));
});
