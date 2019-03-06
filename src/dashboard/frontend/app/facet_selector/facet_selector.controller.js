import angular from 'angular';

angular.module('facetController', ['tagService']).

controller('FacetController', ['$scope', 'gettextCatalog', 'Transfer', 'Facet', function($scope, gettextCatalog, Transfer, Facet) {
  $scope.remove_facet = function(name, id) {
    Facet.remove_by_id(name, id);
    Transfer.filter();
  };
  $scope.Facet = Facet;
  $scope.transfers = Transfer;

  $scope.$watch('tag_facet', function(selected) {
    if (!selected) {
      return;
    }

    Facet.add('tags', selected, {name: gettextCatalog.getString('Tag'), text: selected});
    Transfer.filter();
    $scope.tag_facet = '';
  });
}]);
