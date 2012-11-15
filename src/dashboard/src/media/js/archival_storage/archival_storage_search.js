$(document).ready(function() {

  // create new form instance, providing a single row of default data
  var search = new advancedSearch.AdvancedSearchView({
    el: $('#search_form_container'),
//    allowAdd: false,
    rows: [{
      'op': '',
      'query': '',
      'field': ''
    }]
  });

  // define op field
  var opAttributes = {
    title: 'boolean operator',
    class: 'search_op_selector'
  }
  search.addSelect('op', 'boolean operator', opAttributes, {
    'or': 'or',
    'and': 'and',
    'not': 'not'
  });

  // define query field
  search.addInput('query', 'search query', {title: 'search query', 'class': 'span11'});

  // default field name field
  search.addSelect('field', 'field name', {title: 'field name'}, {
    '': 'Any',
    'AIPUUID': 'UUID',
    'filePath': 'File path',
    'fileExtension': 'File extension'
  });

  // don't show first op field
  search.fieldVisibilityCheck = function(rowIndex, fieldName) {
    return rowIndex > 0 || fieldName != 'op';
  };

  // override default search state if URL parameters set
  if (search.urlParamsToData()) {
    search.rows = search.urlParamsToData();
  }

  search.render();

  // submit logic
  $('#search_submit').click(function() {
    window.location = '/archival-storage/search/' + '?' + search.toUrlParams();
  });

  $('#search_form').submit(function() {
    window.location = '/archival-storage/search/' + '?' + search.toUrlParams();
    return false;
  });
});
