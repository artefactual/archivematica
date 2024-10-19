'use strict';

describe('dashboard.version module', function() {
  beforeEach(module('dashboard.version'));

  describe('version service', function() {
    it('should return current version', inject(function(version) {
      expect(version).toEqual('0.1');
    }));
  });
});
