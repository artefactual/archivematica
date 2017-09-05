'use strict';

import '../../app/services/file.service.js';

describe('File', function() {
  beforeEach(angular.mock.module('fileService'));
  beforeEach(angular.mock.inject(function(_$httpBackend_) {
    _$httpBackend_.when('GET', '/file/054a0f2c-79bb-4051-b82b-4b0f14564811').respond({'id': '054a0f2c-79bb-4051-b82b-4b0f14564811', 'parent': '0e3bd878-069d-49e2-b270-46b0b40cba5b', 'text': 'lion.svg', 'icon': 'file', 'puid': 'fmt/91', 'size': '5'});
    _$httpBackend_.when('GET', '/file/cf02698a-3185-45b6-bdaa-af484d5ede5b/bulk_extractor?reports=').respond({
      'ppi': [
        {
          'offset': '0x0100',
          'content': 'something',
          'context': 'This record contains something',
        },
      ],
    });
    _$httpBackend_.when('GET', '/file/40896729-e2c2-4c06-989b-5e95d3031baf/bulk_extractor?reports=ccn').respond({
      'ccn': [
        {
          'offset': '0xabad1d3a',
          'content': 'something',
          'context': 'This record contains something',
        },
      ],
    });
  }));

  it('should be able to fetch a file given its UUID', inject(function(_$httpBackend_, File) {
    File.get('054a0f2c-79bb-4051-b82b-4b0f14564811').then(function(file) {
        expect(file.id).toEqual('054a0f2c-79bb-4051-b82b-4b0f14564811');
    });
    _$httpBackend_.flush();
  }));

  it('should be able to fetch Bulk Extractor logs given a file UUID', inject(function(_$httpBackend_, File) {
    File.bulk_extractor_info('cf02698a-3185-45b6-bdaa-af484d5ede5b').then(function(file) {
      expect(file.ppi.length).toEqual(1);
      expect(file.ppi[0].offset).toEqual('0x0100');
    });
    _$httpBackend_.flush();
  }));

  it('should be able to specify which reports to fetch', inject(function(_$httpBackend_, File) {
    File.bulk_extractor_info('40896729-e2c2-4c06-989b-5e95d3031baf', ['ccn']).then(function(file) {
      expect(file.ccn.length).toEqual(1);
      expect(file.ccn[0].offset).toEqual('0xabad1d3a');
    });
    _$httpBackend_.flush();
  }));
});
