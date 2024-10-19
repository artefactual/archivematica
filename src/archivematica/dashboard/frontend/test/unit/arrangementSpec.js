'use strict';

import '../../app/arrangement/arrangement.controller.js';

describe('Arrangement', function() {
    var $scope, createController, $uibModalService, Alert;
    beforeEach(angular.mock.module('arrangementController', function($provide) {
        var Alert = {
            'alerts': []
        };
        $provide.value('gettextCatalog', { getString: function(message){
            return message;
        }});
        $provide.value('Alert', Alert);
    }));
    beforeEach(angular.mock.module('transferService'));
    beforeEach(angular.mock.inject(function(_$httpBackend_) {
        _$httpBackend_.whenGET('/filesystem/contents/arrange?path=').respond({
            "directories": [], "properties": {}, "entries": []
        });
        _$httpBackend_.whenGET('arrangement/edit_metadata_form.html').respond(
            '<form></form>'
        );
    }));
    beforeEach(inject(function($rootScope, $controller, $uibModal) {
        $scope = $rootScope.$new();
        $uibModalService = $uibModal;
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

    it("shows an error alert when AtoM's levels of description aren't available", inject(function(_$httpBackend_, SipArrange, Alert) {
        _$httpBackend_.whenGET(
            '/api/filesystem/administration/dips/atom/levels'
        ).respond(503);
        var controller = createController();
        spyOn(controller, 'refresh');
        // call the function under test
        controller.edit_metadata({});
        _$httpBackend_.flush();
        // check that an error alert was raised
        expect(Alert.alerts).toEqual([{
            'type': 'danger',
            'message': 'Error fetching levels of description',
        }]);
        // the arrangement tree is refreshed after the error
        expect(controller.refresh).toHaveBeenCalled();
    }));

    it('should open a modal form for editing metadata', inject(function(_$httpBackend_, SipArrange, Alert) {
        _$httpBackend_.whenGET(
            '/api/filesystem/administration/dips/atom/levels'
        ).respond([
            {'level1': 'Level 1'},
            {'level2': 'Level 2'},
            {'level3': 'Level 3'}
        ]);
        var controller = createController();
        var node = {
            'title': 'My node',
            'path': '/my/node',
            'properties': {
                'levelOfDescription': 'Level 2'
            }
        };
        // spy all the functions of the controller used to render the modal
        spyOn(SipArrange, 'get_atom_levels_of_description').and.callThrough();
        spyOn(controller, 'edit_metadata_handler').and.callThrough();
        spyOn(controller, 'open_edit_metadata_modal').and.callThrough();
        spyOn($uibModalService, 'open').and.callThrough();
        // call the function under test
        controller.edit_metadata(node);
        _$httpBackend_.flush();
        // check that all the spies were called with expected parameters
        expect(SipArrange.get_atom_levels_of_description).toHaveBeenCalled();
        expect(controller.edit_metadata_handler).toHaveBeenCalled();
        expect(controller.edit_metadata_handler).toHaveBeenCalledWith(node);
        expect(controller.open_edit_metadata_modal).toHaveBeenCalled();
        expect(controller.open_edit_metadata_modal).toHaveBeenCalledWith(
            [
                { value: 'level1', label: 'Level 1' },
                { value: 'level2', label: 'Level 2' },
                { value: 'level3', label: 'Level 3' }
            ],
            { value: 'level2', label: 'Level 2' }
        );
        expect($uibModalService.open).toHaveBeenCalled();
    }));

});
