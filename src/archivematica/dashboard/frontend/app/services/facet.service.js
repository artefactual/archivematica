import angular from 'angular';

angular.module('facetService', []).

// Provides the ability to filter sets of data via various criteria.
// The Facet service operates on lists of objects, and filters them
// according to criteria which evaluates specific keys in those
// objects.
// Facets provide several different ways of matching:
// * string   - if the test value is a string, then the facet only matches if
//              the object has a value at that key which is an exact match.
// * regexp   - if the test value is a regexp, then the facet matches if
//              the object has a value at that key which passes value.match(regexp).
// * function - if the test value is a function, then the facet matches if
//              the function passes true when passed the value at that key from the object.
factory('Facet', function() {
  // Adds a new facet.
  // * name - the key this function should match.
  // * value - the value to match against the object's value; see above.
  // * data - an object with arbitrary keys/values which can be useful to outside
  //          systems querying the tag list.
  //          For example, the facet selector controller uses the `data` property to
  //          track display-formatted strings which are used in the UI when reading
  //          data from Facet.facet_list.
  // * id - if provided, a unique ID for the facet, which allows it to be removed
  //        by ID in the future.
  var add = function(name, value, data, id) {
    data = data || {};

    if (undefined === this.facets[name]) {
      this.facets[name] = [];
    }
    // Don't add the same filter more than once
    if (this.facets[name].indexOf(value) !== -1) {
      return;
    }
    data.id = id || generate_id();
    data.value = value;
    data.facet = name;
    this.facets[name].push(data);
    this.facet_list.push(data);

    return data.id;
  };

  // If `value` is provided, returns a facet with this `name` and `value`,
  // or `undefined` if no matching facet is tracked.
  // If `value` is not provided, returns all facets with this `name`,
  // or `undefined` if no matching facet is tracked.
  var get = function(name, value) {
    // If the facet doesn't exist, just return nothing
    if (undefined === this.facets[name]) {
      return;
    }
    // If no value is requested, return all facets for this field
    if (undefined === value) {
      return this.facets[name].map(function(element) {
        return element.value;
      });
    }
    // Return undefined if the requested facet isn't present
    var facets = this.facets[name].filter(function(element) {
      return element.value === value;
    });
    if (facets.length === 0) {
      return;
    } else {
      return facets[0].value;
    }
  };

  // Returns a facet with this `name` and `id`,
  // or undefined if no matching facet is tracked.
  var get_by_id = function(name, id) {
    var facets = this.facets[name].filter(function(element) {
      return element.id === id;
    });
    return facets[0].value;
  };

  // Removes one or more facets.
  // If `value` is provided, removes a facet that matches both `name` and `value`;
  // otherwise, removes every facet with `name`.
  var remove = function(name, value) {
    // If no value is provided, delete all values
    if (undefined === value) {
      delete this.facets[name];
      this.facet_list = this.facet_list.filter(function(element) {
        return element.facet !== name;
      });
    } else if (undefined !== this.facets[name]) {
      var filter_fn = function(element) {
        return element.facet !== name || element.value !== value;
      };
      // TODO: filtering over two arrays is unnecessarily expensive;
      //       see about ways to optimize this later
      this.facets[name] = this.facets[name].filter(filter_fn);
      if (this.facets[name].length === 0) {
        delete this.facets[name];
      }
      this.facet_list = this.facet_list.filter(filter_fn);
    }
  };

  // Returns a facet with this `name` and `id`.
  var remove_by_id = function(name, id) {
    var filter_fn = function(element) {
      return element.id !== id;
    };
    this.facets[name] = this.facets[name].filter(filter_fn);
    if (this.facets[name].length === 0) {
      delete this.facets[name];
    }
    this.facet_list = this.facet_list.filter(filter_fn);
  };

  // Removes every facet.
  var clear = function() {
    this.facets = {};
    this.facet_list = [];
  };

  // Filters an array of objects.
  // Each object is tested against the full list of defined facets
  // using `passes_filters()`, and is only included in the output array
  // if that returns true.
  // Returns a copy of the array with only the matching entries.
  var filter = function(values) {
    var self = this; // needs to be defined outside the filter function
    return values.filter(function(element, index, array) {
      return self.passes_filters(element);
    });
  };

  // Tests `object` against the currently-defined facets.
  // The object is not matched against facets defined against keys
  // which the object doesn't have.
  // Returns true if the object passes at least one facet defined for its
  // keys, false otherwise.
  // Optionally, keys can be passed, and it will only check filters for those keys.
  var passes_filters = function(object, keys = Object.keys(this.facets)) {
    var key, value;
    // If no filters, everything passes
    if (keys.length === 0) {
      return true;
    }
    for (var i = 0; i < keys.length; i++) {
      key = keys[i];
      value = object[key];
      if (filter_value.apply(this, [key, value]) === true) {
        return true;
      }
    }
    return false;
  };

  // private

  var filter_value = function(key, value) {
    if (undefined === this.facets[key] || undefined === value) {
      // no facet for this key
      return true;
    }
    // if this is a collection, test to see if any of the matches are false
    if (value.map !== undefined) {
      // if the collection is empty it cannot possibly match anything
      if (value.length === 0) {
        return false;
      }

      var self = this;
      var results = value.map(function(element) {
        return filter_value.apply(self, [key, element]);
      });
      // if there are any true elements, return true
      return results.indexOf(true) !== -1;
    }

    for (var i in this.facets[key]) {
      var result;
      var filter = this.facets[key][i].value;
      // filter is a function
      if (filter.call) {
        result = filter(value);
      } else if (typeof filter === 'string') {
        result = value === filter;
      } else {
        result = !!value.match(filter);
      }
      // return immediately if any filter returns true,
      // otherwise keep going
      if (result === true) {
        return true;
      }
    }

    return false;
  };

  var generate_id = function() {
    var s = '';
    for (var i = 0; i < 16; i++) {
      s += String.fromCharCode(Math.random() * 255);
    }

    return s;
  };

  return {
    facets: {},
    facet_list: [],
    add: add,
    get: get,
    get_by_id: get_by_id,
    remove: remove,
    remove_by_id: remove_by_id,
    clear: clear,
    filter: filter,
    passes_filters: passes_filters,
  };
});
