'use strict';

import '../../app/arrangement/arrangement.controller.js';

describe('Arrangement', function() {
    var $scope, Transfer, createController;
    beforeEach(angular.mock.module('arrangementController', function($provide) {
        $provide.value('gettextCatalog', { getString: function(){}});
        $provide.value('Alert', { remove: function(){}});
    }));
    beforeEach(angular.mock.module('transferService'));
    beforeEach(inject(function($rootScope, $controller) {
        $scope = $rootScope.$new();
        createController = function() {
            return $controller('ArrangementController', {
                '$scope': $scope,
            });
        };
    }));

    it('should update data elements with tags update', function() {
        var controller = createController();
        controller.data = [
            {'properties': {'file_uuid': 'file1', 'tags': []}},
            {'properties': {'file_uuid': 'file2', 'tags': ['t2']}}
        ];
        controller.update_element_tags(controller.data, {
            'file1': ['t1', 't2'],
            'file2': ['t1']
        });
        expect(controller.data).toEqual([
            {'properties': {'file_uuid': 'file1', 'tags': ['t1', 't2']}},
            {'properties': {'file_uuid': 'file2', 'tags': ['t1']}}
        ]);
        controller.update_element_tags(controller.data, {
            'file1': ['t3'],
            'file3': ['t1', 't2'],
        });
        expect(controller.data).toEqual([
            {'properties': {'file_uuid': 'file1', 'tags': ['t3']}},
            {'properties': {'file_uuid': 'file2', 'tags': ['t1']}}
        ]);
    });
});
