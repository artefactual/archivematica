import angular from 'angular';
import {decode_browse_response, format_entries} from 'archivematica-browse-helpers';
// lodash is used by restangular
import 'lodash';
import 'restangular';

angular.module('archivesSpaceService', ['restangular']).

// This service allows access to ArchivesSpace, as proxied via Archivematica.
// The data format used is documented in agentarchives:
// https://github.com/artefactual-labs/agentarchives
factory('ArchivesSpace', ['Restangular', function(Restangular) {
    var id_to_urlsafe = id => {
      return id.replace(/\//g, '-');
    };

    var ArchivesSpace = Restangular.all('access').all('archivesspace');
    return {
      // Returns all records at the top level of description in a repository.
      all: function() {
        return ArchivesSpace.getList();
      },
      search: function(opts) {
        return ArchivesSpace.getList({'title': opts.title, 'identifier': opts.identifier});
      },
      // Returns a single record, given its ID (e.g., /repositories/2/resources/1)
      get: function(id) {
        var url_fragment = id_to_urlsafe(id);
        return ArchivesSpace.one(url_fragment).get();
      },
      // Fetches all children of the specified record.
      get_children: function(id) {
        var url_fragment = id_to_urlsafe(id);
        return ArchivesSpace.one(url_fragment).one('children').getList();
      },
      // Returns a list of all the levels of description.
      // The returned values are the strings used internally by ArchivesSpace,
      // not the prettily-formatted versions displayed in the ArchivesSpace UI.
      get_levels_of_description: function() {
        return ArchivesSpace.one('levels').getList();
      },
      // Submits edits to the record with the specified ID.
      // `record` is a copy of the record in the same format returned by the
      // `get` methods.
      edit: function(id, record) {
        var url_fragment = id_to_urlsafe(id);
        return ArchivesSpace.one(url_fragment).customPUT(record);
      },
      // Creates a new archival object as a child to the given record.
      // `record` uses a similar format to the record returned by the `get` methods.
      add_child: function(id, record) {
        var url_fragment = id_to_urlsafe(id);
        return ArchivesSpace.one(url_fragment).one('children').customPOST(record);
      },
      // Lists all of the digital object components associated with a given record.
      // This returns digital object components tracked by Archivematica in its
      // database - not necessarily components which have been submitted to
      // ArchivesSpace yet. These may not be created remotely until after the SIP
      // finishes processing.
      digital_object_components: function(id) {
        var url_fragment = id_to_urlsafe(id);
        return ArchivesSpace.one(url_fragment).one('digital_object_components').get();
      },
      // Creates a new digital object component parented to the given record.
      // `record` uses the same format returned by `digital_object_components`.
      create_digital_object_component: function(id, record) {
        var url_fragment = id_to_urlsafe(id);
        return ArchivesSpace.one(url_fragment).one('digital_object_components').customPOST(record);
      },
      // Lists the files inside a digital object component, given the ID of both
      // the digital object component and its parent record.
      // The returned format is the same format used by the `SipArrange` service.
      list_digital_object_component_contents: function(id, component_id) {
        var id_fragment = id_to_urlsafe(id);
        return ArchivesSpace.one(id_fragment).one('digital_object_components').one(String(component_id)).one('files').get().then(decode_browse_response).then(format_entries);
      },
      // Removes the ArchivesSpace record with the given ID.
      // The deletion occurs immediately on the remote ArchivesSpace server.
      remove: function(id) {
        var url_fragment = id_to_urlsafe(id);
        return ArchivesSpace.one(url_fragment).remove();
      },
      // Starts a new SIP from the ArchivesSpace record with the given ID.
      // The contents of the SIP will use all of the digital object components
      // associated with the specified record; each component will be created
      // as a directory within the new SIP.
      start_sip: function(node) {
        var url_fragment = id_to_urlsafe(node.id);
        return ArchivesSpace.one(url_fragment).one('copy_from_arrange').customPOST({ sip_name: node.display_title });
      },
    };
}]);
