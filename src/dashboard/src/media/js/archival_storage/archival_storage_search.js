$(document).ready(function() {

  // create new form instance, providing a single row of default data
  var search = new advancedSearch.AdvancedSearchView({
    el: $('#search_form_container'),
    allowAdd: false,
    rows: [{
      'op': '',
      'query': ''
    }]
  });

  // override default search state if URL parameters set
  if (search.urlParamsToData()) {
    search.rows = search.urlParamsToData();
  }

  // define op field
  var opAttributes = {
    title: 'boolean operator',
    class: 'search_op_selector'
  }
  search.addSelect('op', 'boolean operator', opAttributes, {
    'and': 'and',
    'or':  'or',
    'not': 'not'
  });

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
    return search.rows.length > 1 || fieldName != 'op';
  };

  search.render();
  $('.search_op_selector').css('width', '50px');
  $('.search_op_selector').css('margin-right', '5px');

  // submit logic
  $('#search_submit').click(function() {
    window.location = '/archival-storage/search/' + '?' + search.toUrlParams();
  });

  $('#search_form').submit(function() {
    window.location = '/archival-storage/search/' + '?' + search.toUrlParams();
    return false;
  });
});
