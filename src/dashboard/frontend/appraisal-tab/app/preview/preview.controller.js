import angular from 'angular';

angular.module('previewController', ['route-segment', 'selectedFilesService']).

// Used to populate the preview pane, which displays:
// * the file in an iframe;
// * the filename;
// * a download link
//
// FIXME If the file being previewed belongs to a SIP that's already been started,
//       then the preview/download URL will 404. This looks really ugly to the
//       end user. It would be great to find a more elegant solution to this.
controller('PreviewController', ['$scope', 'gettextCatalog', '$routeSegment', 'Alert', 'File', 'SelectedFiles', function($scope, gettextCatalog, $routeSegment, Alert, File, SelectedFiles) {
  var vm = this;

  vm.set_file_data = file => {
    $scope.file = file;
    $scope.url = '/filesystem/' + file.id + '/download';
  };

  $scope.$routeSegment = $routeSegment;
  // The UUID of the file is located in the URL, which allows users to
  // share the URL with another user to let them preview the file.
  $scope.id = $routeSegment.$routeParams.id;
  if ($scope.id !== undefined) {
    // Try to get file from the file list first, to avoid pinging the server.
    var file = SelectedFiles.get($scope.id);
    if (file) {
      vm.set_file_data(file);
    } else {
      // If the data isn't available, contact the server to fetch file info;
      // it may not have been loaded.
      var on_failure = error => {
        Alert.alerts.push({
          type: 'danger',
          message: gettextCatalog.getString('Unable to retrieve metadata for file with UUID {{id}}', { id: $scope.id }),
        });
      };
      File.get($scope.id).then(file => {
        vm.set_file_data(file);
      }, on_failure);
    }
  }
}]);
