import angular from 'angular';
import 'lodash';
import 'restangular';

// Interacts with the Archivematica API to retrieve transfer source locations.
class SourceLocations {
  constructor(Restangular) {
    this.locations = Restangular.one('transfer').one('locations');
  }

  // Lists all transfer source locations in the Storage Service instance paired with this installation of Archivematica.
  // Returns a promise which resolves to a list of objects; each object has the following keys:
  //   * uuid - The UUID of the location, as a string.
  //   * description - A human-readable description associated with this location in the Storage Service.
  list() {
    return this.locations.getList();
  }
}

export default angular.module('services.source_locations', ['restangular']).
  service('SourceLocations', SourceLocations).
  name;

SourceLocations.$inject = ['Restangular'];
