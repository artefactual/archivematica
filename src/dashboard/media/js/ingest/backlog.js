//
// Render the backlog search form
// search_uri: The URI to the AJAX end point to post form data to / get results from
// on_success: Method to call when ajax request succeeds. If set to NULL, no ajax query will occur.
// on_error:   Method to call when ajax request returns an error
// returns:    The instance of AdvancedSearchView created
//
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
    'addHandleHtml': '<a>' + gettext('Add new') + '</a>'
  });

  // define op field
  search.addSelect('op', {'title': 'boolean operator', 'class': 'form-control search_op_selector'}, {
    'or': 'or',
    'and': 'and',
    'not': 'not'
  });

  // define query field
  search.addInput('query', {title: 'search query', 'class': 'form-control aip-search-query-input'});

  // default field name field
  search.addSelect('field', {title: 'field name', 'class': 'form-control'}, {
    ''             : gettext('Any'),
    'filename'     : gettext('File name'),
    'file_extension': gettext('File extension'),
    'accessionid'  : gettext('Accession number'),
    'ingestdate'   : gettext('Ingest date (YYYY-MM-DD)'),
    'sipuuid'      : gettext('Transfer UUID')
  });

  // default field name field
  search.addSelect('type', {title: 'query type', 'class': 'form-control'}, {
    'term': gettext('Keyword'),
    'string': gettext('Phrase')
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

  if (on_success !== null) {
    function backlogSearchSubmit() {
      // Query Django, which queries ElasticSearch, to get the backlog file info
      var query_url = search_uri + '?' + search.toUrlParams();
      if (!$('#id_show_metadata_logs').is(':checked')) {
          query_url = query_url + '&' + $.param({hidemetadatalogs: 1});
      }

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

  return search;
}
