$(document).ready(function() {

  // create new form instance, providing a single row of default data
  var search = new advancedSearch.AdvancedSearchView({
    el: $('#search_form'),
    allowAdd: false,
    data: [{
      'query': ''
    }]
  });

  /*
  // define op field
  search.addSelect('op[]', 'boolean operator', {title: 'boolean operator'}, {
    'and': 'and',
    'or': 'or',
    'not': 'not'
  });
  */

  // define query field
  search.addInput('query', 'search query', {title: 'search query', 'class': 'span11'});

  /*
  // default field name field
  search.addSelect('field[]', 'field name', {title: 'field name'}, {
    'aipname': 'AIP name',
    'filename': 'File name',
    'uuid': 'UUID'
  });
  */

  // don't show first op field
  search.fieldVisibilityCheck = function(rowIndex, fieldName) {
    return rowIndex > 0 || fieldName != 'op[]';
  };

  search.render();

  // submit logic
  $('#search_submit').click(function() {
    window.location = '/archival-storage/search/' + '?' + search.toUrlParams();
  });
});
