'use strict';

import '../../app/tree/tree.controller.js';

describe('Tree', function() {
    var scope, Transfer, createController;
    beforeEach(angular.mock.module('treeController'));
    beforeEach(angular.mock.module('selectedFilesService'));
    beforeEach(angular.mock.module('transferService'));
    beforeEach(inject(function($rootScope, $controller) {
        scope = $rootScope.$new();
        Transfer = jasmine.createSpyObj('Transfer', ['remove_tag']);
        createController = function() {
            return $controller('TreeController', {
                '$scope': scope,
                'Transfer': Transfer
            });
        };
    }));

    it('should stop event propagation after removing a tag', function() {
        var event = jasmine.createSpyObj('event', ['stopPropagation']);
        createController();
        scope.remove_tag(event, 'file-id', 'tag1');
        expect(Transfer.remove_tag).toHaveBeenCalled();
        expect(Transfer.remove_tag).toHaveBeenCalledWith('file-id', 'tag1');
        expect(event.stopPropagation).toHaveBeenCalled();
    });
});
