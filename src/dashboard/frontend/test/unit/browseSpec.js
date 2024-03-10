'use strict';

import '../../app/services/browse.service';

describe('Browse', () => {
  beforeEach(angular.mock.module('services.browse'));
  beforeEach(angular.mock.inject((_$httpBackend_) => {
    _$httpBackend_.when('GET', '/filesystem/children/location/772056c6-ce0c-4ba0-a4c3-8b64791ace88?path=L2hvbWUvdmFncmFudC9hcmNoaXZlbWF0aWNhLXNhbXBsZWRhdGE%3D').respond({
      "entries": [
        "T1BGIGZvcm1hdC1jb3JwdXM=",
        "UkVBRE1FLm1k",
        "U2FtcGxlVHJhbnNmZXJz",
        "VGVzdFRyYW5zZmVycw=="
      ],
      "properties": {
        "T1BGIGZvcm1hdC1jb3JwdXM=": {
          "size": 4096,
          "display_string": "1499 objects",
          "object count": 1499
        },
        "VGVzdFRyYW5zZmVycw==": {
          "size": 4096,
          "display_string": "369 objects",
          "object count": 369
        },
        "U2FtcGxlVHJhbnNmZXJz": {
          "size": 4096,
          "display_string": "95 objects",
          "object count": 95
        },
        "UkVBRE1FLm1k": {
          "size": 201,
          "display_string": "201 bytes"
        }
      },
      "directories": [
        "T1BGIGZvcm1hdC1jb3JwdXM=",
        "U2FtcGxlVHJhbnNmZXJz",
        "VGVzdFRyYW5zZmVycw=="
      ]
    });
  }));
  beforeEach(angular.mock.inject((_$httpBackend_) => {
    _$httpBackend_.when('GET', '/filesystem/children/location/772056c6-ce0c-4ba0-a4c3-8b64791ace88?path=L2hvbWUvTW9udHLDqWFsL2FyY2hpdmVtYXRpY2Etc2FtcGxlZGF0YQ%3D%3D').respond({
      "entries": [
        "T1BGIGZvcm1hdC1jb3JwdXM=",
        "UkVBRE1FLm1k"
      ],
      "properties": {
        "T1BGIGZvcm1hdC1jb3JwdXM=": {
          "size": 4096,
          "display_string": "1499 objects",
          "object count": 1499
        },
        "UkVBRE1FLm1k": {
          "size": 201,
          "display_string": "201 bytes"
        }
      },
      "directories": [
        "T1BGIGZvcm1hdC1jb3JwdXM="
      ]
    });
  }));

  it('should be able to list the contents of a path inside a location', angular.mock.inject((Browse, _$httpBackend_) => {
    Browse.browse('772056c6-ce0c-4ba0-a4c3-8b64791ace88', '/home/vagrant/archivematica-sampledata').then(entries => {
      expect(entries.length).toEqual(4);
    });
    _$httpBackend_.flush();
  }));
  it('should be able to list the contents of a path with non-ascii parts', angular.mock.inject((Browse, _$httpBackend_) => {
    Browse.browse('772056c6-ce0c-4ba0-a4c3-8b64791ace88', '/home/Montréal/archivematica-sampledata').then(entries => {
      expect(entries.length).toEqual(2);
    });
    _$httpBackend_.flush();
  }));
});
