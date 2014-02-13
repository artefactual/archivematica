function renderBacklogSearchForm(openInNewTab) {
  // activate deletion buttons
  $('.creation, .deletion').each(function() {
    var url = $(this).attr('href')
      , id = $(this).attr('id');
      
    $(this).removeAttr('href');
    this.url = url;
    this.id = id;
    this.fired = false;

    $(this).click(function() {
      if (this.fired == false) {
        this.fired = true;
        // remove all button with same url
        $('.creation, .deletion').each(function() {
          if (this.id == url) {
            console.log('DISABLING...');
            $(this).attr('disabled', 'disabled');
          }
        });

        var data = {};
        if ($(this).hasClass('deletion')) {
          data['filepath'] = $(this).attr('id');
        }

        // perform action
        $.ajax({
          type: "POST",
          data: data,
          url: url,
          error: function(error) {
            $('.creation, .deletion').each(function() {
              if (this.id == id) {
                alert(error.statusText);
                $(this).removeAttr('disabled');
                this.fired = false;
              }
            });
          },
          success: function(result) {
            alert(result.message);
            $('.creation, .deletion').each(function() {
              if (this.id == id) {
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
    }],
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
    var destination = '/ingest/backlog/' + '?' + search.toUrlParams();
    if($('#search_mode').is(':checked')) {
      destination += '&mode=file';
    }

    if (openInNewTab) {
      window.open(destination, '_blank');
    } else {
      window.location = destination;
    }
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
