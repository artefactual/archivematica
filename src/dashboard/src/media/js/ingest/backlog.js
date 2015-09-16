function renderBacklogSearchForm(search_uri, on_success, on_error) {
  // create new form instance, providing a single row of default data
  var search = new advancedSearch.AdvancedSearchView({
    el: $('#search_form_container'),
    rowTemplate: {
      'op': '',
      'query': '',
      'field': '',
      'type': 'term'
    },
    'deleteHandleHtml': '<img src="/media/images/delete.png" style="margin-left: 5px"/>',
    'addHandleHtml': '<a>Add New</a>'
  });

  // define op field
  var opAttributes = {
    title: 'boolean operator',
    class: 'search_op_selector'
  }
  search.addSelect('op', opAttributes, {
    'or': 'or',
    'and': 'and',
    'not': 'not'
  });

  // define query field
  search.addInput('query', {title: 'search query', 'class': 'aip-search-query-input'});

  // default field name field
  search.addSelect('field', {title: 'field name'}, {
    ''             : 'Any',
    'filename'     : 'File name',
    'file_extension': 'File extension',
    'accessionid'  : 'Accession number',
    'ingestdate'   : 'Ingest date (YYYY-MM-DD)',
    'sipuuid'      : 'SIP UUID'
  });

  // default field name field
  search.addSelect('type', {title: 'query type'}, {
    'term': 'Keyword',
    'string': 'Phrase'
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

  function backlogSearchSubmit() {
    // Query Django, which queries ElasticSearch, to get the backlog file info
    var query_url = search_uri + '?' + search.toUrlParams();
    $.ajax({
      type: 'GET',
      url: query_url,
      data: null,
      success: on_success,
      error: function(jqXHR, textStatus, errorThrown) {
        on_error(query_url, jqXHR, textStatus, errorThrown);
      },
    });
  }

  // submit logic
  $('#search_submit').click(function() {
    backlogSearchSubmit();
  });

  $('#search_form').submit(function() {
    backlogSearchSubmit();
    return false;
  });
}
