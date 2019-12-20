import angular from 'angular';
import _ from 'lodash';

angular.module('facetFilter', []).

filter('facet', ['Facet', function(Facet) {
  var facet_filter_fn = records => Facet.filter(records);

  // The default hash function may confuse two arrays of objects
  // of the same length as the same set of records.
  var hash_fn = records => {
    return JSON.stringify(records) + JSON.stringify(Facet.facets);
  };

  return _.memoize(facet_filter_fn, hash_fn);
}]);
