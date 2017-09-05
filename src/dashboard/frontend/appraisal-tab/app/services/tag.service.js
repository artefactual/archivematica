import angular from 'angular';
import 'restangular';

angular.module('tagService', ['restangular']).

// Provides functions to retrieve and manipulate file tag data via the Archivematica API.
factory('Tag', ['$log', 'Restangular', function($log, Restangular) {
  var Tag = Restangular.all('file');

  // public

  // Returns an array of tags for the file with the specified UUID.
  var get = function(id) {
    return Tag.one(id).one('tags').getList();
  };

  // Updates the list of tags associated with the file with the specified `uuid`.
  var submit = function(id, tags) {
    Tag.one(id).one('tags').customPUT(tags).then(null, response => {
      // TODO display error handling
      $log.error(`Submitting tags for file ${String(id)} failed with response: ${response.status}`);
    });
  };

  // Removes all tags from the file with the specified `uuid`.
  var remove = function(id) {
    Tag.one(id).one('tags').remove().then(null, response => {
      $log.error(`Deleting tags for file ${String(id)} failed with response: ${response.status}`);
    });
  };

  return {
    get: get,
    submit: submit,
    remove: remove,
  };
}]);
