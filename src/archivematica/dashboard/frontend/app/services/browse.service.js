import angular from 'angular';
import Base64 from 'base64-helpers';
import 'lodash';
import 'restangular';

import {decode_browse_response, format_entries} from 'archivematica-browse-helpers';

// Interacts with the Archivematica API to allow transfer source locations to be browsed.
class Browse {
  constructor(Restangular) {
    this.browser = Restangular.one('filesystem').one('children').one('location');
  }

  // Browses the contents of `path` at `location_uuid`.
  // * location_uuid - The UUID of the location in the given Storage Service instance.
  // * path - The directory whose contents should be retrieved.
  //
  // Returns a promise which resolves to an array of objects formatted in the format defined by archivematica-browse-helpers.
  browse(location_uuid, path) {
    let params = {'path': Base64.encode(path)};
    return this.browser.one(location_uuid).get(params).then(decode_browse_response).then(response => {
      return format_entries(response, path);
    }).then(entries => {
      entries.forEach(entry => entry.location = location_uuid);
      return entries;
    });
  }
}

export default angular.module('services.browse', ['restangular']).
  service('Browse', Browse).
  name;

Browse.$inject = ['Restangular'];
