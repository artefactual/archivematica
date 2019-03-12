import angular from 'angular';
import 'restangular';

angular.module('fileService', ['restangular']).

// Provides functions to return metadata about individual files from the Archivematica API.
factory('File', ['Restangular', function(Restangular) {
  var File = Restangular.one('file');
  return {
    // Given a file's UUID, fetches metadata about a file from Archivematica.
    // The file metadata uses a format identical to the Elasticsearch metadata
    // returned by the Transfer API.
    get: function(uuid) {
      return File.one(uuid).get();
    },
    // Returns parsed Bulk Extractor reports for the file with `uuid`.
    // If an array of report types is passed to `reports`, limits the results to
    // those reports; otherwise, returns the default set of reports defined by the API.
    // Consult Archivematica's GET /file/:uuid/bulk_extractor/ API for the format.
    bulk_extractor_info: function(uuid, reports) {
      reports = reports || [];
      reports = reports.join(',');
      return File.one(uuid).one('bulk_extractor').get({reports: reports});
    },
  };
}]);
