import angular from 'angular';

angular.module('searchController', ['alertService', 'transferService']).

controller('SearchController', ['$scope', 'gettextCatalog', 'Alert', 'Transfer', function($scope, gettextCatalog, Alert, Transfer) {
  var on_request = data => {
    $scope.$apply(() => {
      Transfer.resolve(data);
    });
  };

  var on_error = () => {
    $scope.$apply(() => {
      Alert.alerts.push({
        type: 'danger',
        message: gettextCatalog.getString('Unable to retrieve transfer data from Archivematica.'),
      });
    });
  };

  // This function comes from Archivematica's backlog.js, not from the appraisal tab itself.
  // The on_request and on_error callbacks are provided to a jQuery.ajax call.
  renderBacklogSearchForm('/ingest/appraisal_list/', on_request, on_error);
}]);
