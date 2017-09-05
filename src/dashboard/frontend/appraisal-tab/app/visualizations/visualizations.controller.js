import angular from 'angular';

angular.module('visualizationsController', [
  'angularCharts',
  'selectedFilesService',
]).

// Feeds data into the graphs in the two visualization partials.
controller('VisualizationsController', ['$scope', 'gettextCatalog', 'Facet', 'SelectedFiles', 'Transfer', function($scope, gettextCatalog, Facet, SelectedFiles, Transfer) {
  // Displays aggregate information about file formats;
  // the selected record data is filtered/reformatted in the view.
  $scope.records = SelectedFiles;
  $scope.format_chart_type = 'pie';
  // Check angular-charts for the supported options:
  // https://github.com/chinmaymk/angular-charts
  $scope.format_config = {
    // Formats (total)
    click: record => {
      Facet.add('format', record.data.format, {name: gettextCatalog.getString('Format'), text: record.data.format});
      Transfer.filter();
    },
    tooltips: true,
    labels: false,
    legend: {
      display: true,
      position: 'right',
    },
    colors: d3.scale.category20().range(),
  };

  $scope.size_chart_type = 'pie';
  $scope.size_config = {
    // Formats (by size)
    click: record => {
      Facet.add('format', record.data.format, {name: gettextCatalog.getString('Format'), text: record.data.format});
      Transfer.filter();
    },
    tooltips: true,
    labels: false,
    legend: {
      display: true,
      position: 'right',
    },
    colors: d3.scale.category20().range(),
  };
}]);
