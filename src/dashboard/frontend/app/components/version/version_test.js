'use strict';

describe('appraisalTab.version module', function() {
  beforeEach(module('appraisalTab.version'));

  describe('version service', function() {
    it('should return current version', inject(function(version) {
      expect(version).toEqual('0.1');
    }));
  });
});
