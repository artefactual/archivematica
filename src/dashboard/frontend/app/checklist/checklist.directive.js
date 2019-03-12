import angular from 'angular';

angular.module('checklistDirective', []).

// The checklist directive simplifies tracking the state of a series of
// checkboxes, and whether every checkbox in the set is checked.
//
// The "ng-element" attribute is a record associated with the checkbox.
// Its `id` attribute will be pushed onto or removed from the list of
// selected items when the checkbox is clicked.
// The "selected-list" attribute is an array which will contain the IDs
// of selected records.
// The "all-selected" attribute will be set to true or false depending
// on whether or not all checkboxes in the checklist are checked.
// The "record-count" attribute is the total count of records, used to
// determine whether all records are selected or not.
directive('checklist', ['$compile', '$parse', function($compile, $parse) {
  return {
    restrict: 'A',
    link: function($scope, element, attrs) {
      var get_record = $parse(attrs.ngElement);
      var get_selected = $parse(attrs.selectedList);
      var set_all_selected = $parse(attrs.allSelected).assign;
      var get_record_count = $parse(attrs.recordCount);

      element.bind('click', () => {
        var selected = get_selected($scope);
        var record = get_record($scope);

        var index = selected.indexOf(record.id);
        $scope.$apply(() => {
          // remove from selection
          if (index > -1) {
            selected.splice(index, 1);
          } else {
            selected.push(record.id);
          }

          set_all_selected($scope, !(selected.length < get_record_count($scope)));
        });
      });
    },
  };
}]);
