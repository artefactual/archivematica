$(document).ready(function() {

  // activate completion buttons
  $('.creation').each(function() {
    var url = $(this).attr('href');
    $(this).removeAttr('href');
    this.url = url;
    this.fired = false;
    $(this).click(function() {
      if (this.fired == false) {
        this.fired = true;
        // remove all button with same url
        $('.creation').each(function() {
          if (this.url == url) {
            $(this).attr('disabled', 'disabled');
          }
        });

        // complete SIP
        $.ajax({
          type: "POST",
          url: url,
          error: function(error) {
            $('.creation').each(function() {
              if (this.url == url) {
                alert(error.statusText);
                $(this).removeAttr('disabled');
                this.fired = false;
              }
            });
          },
          success: function(result) {
            alert(result.message);
            $('.creation').each(function() {
              if (this.url == url) {
                $(this).parent().parent().fadeOut();
              }
            });
          }
        });
      }
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

  function backlogSearchSubmit() {
    var destination = '/ingest/backlog/' + '?' + search.toUrlParams();
    if($('#search_mode').is(':checked')) {
      destination += '&mode=file';
    }
    window.location = destination;
  }

  // submit logic
  $('#search_submit').click(function() {
    backlogSearchSubmit();
  });

  $('#search_form').submit(function() {
    backlogSearchSubmit();
    return false;
  });
});
