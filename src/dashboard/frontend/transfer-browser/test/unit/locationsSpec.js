'use strict';

import '../../app/services/source_locations.service';

describe('SourceLocations', () => {
  beforeEach(angular.mock.module('services.source_locations'));
  beforeEach(angular.mock.inject((_$httpBackend_) => {
    _$httpBackend_.when('GET', '/transfer/locations').respond([
    {
      'description': '/home/artefactual',
      'enabled': true,
      'path': '/home/artefactual',
      'pipeline': ['/api/v2/pipeline/fa18d06b-192c-4655-9e5d-8ef9ed3b82b9/'],
      'purpose': 'TS',
      'quota': null,
      'relative_path': 'home/vagrant/archivematica-sampledata',
      'resource_uri': '/api/v2/location/55989059-7b96-4857-92da-ebcdaa2525b4/',
      'space': '/api/v2/space/f3f114e5-d5dc-4684-bcc3-0a87d1046d30/',
      'used': '0',
      'uuid': '55989059-7b96-4857-92da-ebcdaa2525b4',
    },
    ]);
  }));

  it('should be able to fetch a list of transfer source locations', angular.mock.inject((SourceLocations, _$httpBackend_) => {
    SourceLocations.list().then((locations) => {
      expect(locations.length).toEqual(1);
      expect(locations[0].description).toEqual('/home/artefactual');
    });
    _$httpBackend_.flush();
  }));
});
