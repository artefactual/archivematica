'use strict';

import '../../app/services/sip_arrange.service.js';
import '../../app/vendor/angular-tree-control/demo/jquery.2.0.3.js';

describe('SipArrange', function() {
  beforeEach(angular.mock.module('sipArrangeService'));
  beforeEach(angular.mock.inject(function(_$httpBackend_) {
    _$httpBackend_.when('POST', '/filesystem/create_directory_within_arrange', 'paths%5B%5D=L2FycmFuZ2UvYS9mdWxsL25ld19wYXRo').respond({'success': true});
    _$httpBackend_.when('GET', '/filesystem/contents/arrange?path=').respond({
      'entries': [
        'VGVzdA==',
      ],
      'directories': [
        'VGVzdA==',
      ],
      'properties': [],
    });
    _$httpBackend_.when('GET', '/filesystem/contents/arrange?path=L2FycmFuZ2UvY2hpbGQv').respond({
      'entries': ['ZmlsZQ==', 'ZGlyZWN0b3J5'],
      'directories': ['ZGlyZWN0b3J5'],
      'properties': [],
    });
    _$httpBackend_.when('POST', '/filesystem/delete/arrange', 'filepath=dGFyZ2V0').respond({
      'message': 'Delete successful.',
    });
    _$httpBackend_.when('POST', '/filesystem/copy_to_arrange', 'filepath=c291cmNl&destination=ZGVzdGluYXRpb24%3D').respond({
      'message': 'Files added to the SIP.',
    });
    _$httpBackend_.when('POST', '/filesystem/copy_to_arrange', 'filepath%5B%5D=cGF0aDE%3D&filepath%5B%5D=cGF0aDI%3D&destination%5B%5D=ZGVzdDE%3D&destination%5B%5D=ZGVzdDI%3D').respond({
      'message': 'Files added to the SIP.',
    });
    _$httpBackend_.when('POST', '/filesystem/copy_from_arrange', 'filepath=dGFyZ2V0').respond({
      'message': 'SIP created.',
    });
  }));

  it('should be able to create SIP arrange directories', inject(function(_$httpBackend_, SipArrange) {
    var parent = {title: 'parent'};
    SipArrange.create_directory('/arrange/a/full/new_path', 'new_path', parent).then(function(directory) {
      expect(directory.title).toEqual('new_path');
      expect(directory.path).toEqual('a/full/new_path');
      expect(directory.parent).toBe(parent);
    });
    _$httpBackend_.flush();
  }));

  it('should be able to list arrange contents', inject(function(_$httpBackend_, SipArrange) {
    SipArrange.list_contents().then(function(directories) {
      expect(directories.length).toEqual(1);
      expect(directories[0].title).toEqual('Test');
      expect(directories[0].has_children).toBe(true);
    });
    _$httpBackend_.flush();
  }));

  it('should be able to list arrange contents within a given directory', inject(function(_$httpBackend_, SipArrange) {
    var parent = {title: '/a/parent/node'};
    SipArrange.list_contents('/arrange/child/', parent).then(function(entries) {
      expect(entries.length).toEqual(2);
      // directories are listed before files
      // https://github.com/artefactual-labs/archivematica-browse-helpers/pull/2
      expect(entries[0].has_children).toBe(true);
      expect(entries[1].has_children).toBe(false);
      expect(entries[1].title).toEqual('file');
    });
    _$httpBackend_.flush();
  }));

  it('should be able to delete contents within arrange', inject(function(_$httpBackend_, SipArrange) {
    SipArrange.remove('target').then(function(response) {
      expect(response.message).toEqual('Delete successful.');
    });
    _$httpBackend_.flush();
  }));

  it('should be able to add files to a SIP', inject(function(_$httpBackend_, SipArrange) {
    SipArrange.copy_to_arrange('source', 'destination').then(function(response) {
      expect(response.message).toEqual('Files added to the SIP.');
    });
    _$httpBackend_.flush();
  }));
  it('should be able to add a list of files to a SIP', inject(function(_$httpBackend_, SipArrange) {
    SipArrange.copy_to_arrange(['path1', 'path2'], ['dest1', 'dest2']).then(function(response) {
      expect(response.message).toEqual('Files added to the SIP.');
    });
    _$httpBackend_.flush();
  }));

  it('should be able to start a SIP', inject(function(_$httpBackend_, SipArrange) {
    SipArrange.start_sip('target').then(function(response) {
      expect(response.message).toEqual('SIP created.');
    });
    _$httpBackend_.flush();
  }));
});
