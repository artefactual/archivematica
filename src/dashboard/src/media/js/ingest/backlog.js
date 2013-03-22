$(document).ready(function() {

  // activate completion buttons
  $('.creation').each(function() {
    var url = $(this).attr('href');
    $(this).removeAttr('href');
    this.url = url;
    $(this).click(function() {
      console.log(this.url);
      // remove all button with same url
      $('.creation').each(function() {
        if (this.url == url) {
          $(this).remove();
        }
      });

      // complete SIP
      $.ajax({
        type: "POST",
        url: url,
        success: function(result) {
          console.log(result);
        }
      });
    });
  });

  // create new form instance, providing a single row of default data
  var search = new advancedSearch.AdvancedSearchView({
    el: $('#search_form_container'),
    rows: [{
      'op': '',
      'query': '',
      'field': '',
      'type': ''
    }]
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
    'fileExtension': 'File extension',
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

  // submit logic
  $('#search_submit').click(function() {
    window.location = '/ingest/backlog/' + '?' + search.toUrlParams();
  });

  $('#search_form').submit(function() {
    window.location = '/ingest/backlog/' + '?' + search.toUrlParams();
    return false;
  });
});
