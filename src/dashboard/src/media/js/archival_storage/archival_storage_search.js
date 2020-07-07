/*
This file is part of Archivematica.

Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>

Archivematica is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Archivematica is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
*/

function selectField(el) {
  var target = $(el.parentNode.nextSibling.firstChild);
  if (el.value == 'transferMetadataOther') {
    target.show('fade', {}, 250);
  } else {
    target.hide('fade', {}, 250);
  }
}

function renderArchivalStorageSearchForm(search_uri, on_success, on_error) {
  // create new form instance, providing a single row of default data
  var search = new advancedSearch.AdvancedSearchView({
    el: $('#search_form_container'),
    rowTemplate: {
      'op': '',
      'query': '',
      'field': '',
      'fieldName': '',
      'type': 'term'
    },
    'deleteHandleHtml': '<img src="/media/images/delete.png" style="margin-left: 5px"/>',
    'addHandleHtml': '<a>' + gettext('Add new') + '</a>'
  });

  // define op field
  var opAttributes = {
    title: 'boolean operator',
    class: 'search_op_selector form-control'
  }
  search.addSelect('op', opAttributes, {
    'or': 'or',
    'and': 'and',
    'not': 'not'
  });

  // define query field
  search.addInput('query', {title: 'search query', 'class': 'aip-search-query-input form-control'});

  // default field name field
  search.addSelect('field', {title: 'field name', 'class': 'form-control', onchange: 'selectField(this)'}, {
    '': gettext('Any'),
    'FILEUUID': gettext('File UUID'),
    'filePath': gettext('File path'),
    'fileExtension': gettext('File extension'),
    'AIPUUID': gettext('AIP UUID'),
    'sipName': gettext('AIP name'),
    'identifiers': gettext('Identifiers'),
    'isPartOf': gettext('Part of AIC'),
    'AICID': gettext('AIC Identifier'),
    'transferMetadata': gettext('Transfer metadata'),
    'transferMetadataOther': gettext('Transfer metadata (other)'),
  });

  // "Other" field name, when selecting "transfer metadata (other)"
  search.addInput('fieldName', {
    title: gettext('other field name'),
    'class': 'aip-search-query-input form-control',
    'id': 'aip-search-query-other-field-name'
  });

  // default field name field
  search.addSelect('type', {title: 'query type', 'class': 'form-control'}, {
    'term': gettext('Keyword'),
    'string': gettext('Phrase'),
    'range': gettext('Date range')
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

  // Ensure the select field name field is hidden/displayed as appropriate
  selectField($('.advanced_search_form_field_field > select')[0]);

  if (on_success !== null) {
    function aipSearchSubmit() {
      // Query Django, which queries ElasticSearch, to get the backlog file info
      var query_url = search_uri + '?' + search.toUrlParams();
      if($('#id_show_files').is(':checked')) {
        query_url += '&filemode=true';
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
      aipSearchSubmit();
    });

    $('#search_form').submit(function() {
      aipSearchSubmit();
      return false;
    });
  }

  return search;
}

$(document).ready(function() {
  // Show files is a page state. We collect that state information early for
  // use in each of the functions that then need it.
  var showFiles = $('#id_show_files').prop('checked');

  set_create_aic_visibility(showFiles);
  set_download_csv_visibility(showFiles);

  var search = renderArchivalStorageSearchForm(null, null, null);

  function render_thumbnail(file_uuid) {
    return '<img src="/archival-storage/thumbnail/' + file_uuid + '/">';
  }

  function render_filepath(filepath, type, row_data) {
    var view_raw = ' (<a href="/archival-storage/search/json/file/'
      + row_data.document_id_no_hyphens
      + '/">'
      + gettext('view raw')
      + '</a>)';
    // Remove 'objects/' from beginning of path.
    var objects_prefix = 'objects/';
    var objects_prefix_length = objects_prefix.length;
    var formatted_path = filepath.startsWith(objects_prefix)
      ? filepath.substring(objects_prefix_length)
      : filepath;
    return formatted_path + view_raw;
  }

  function render_file_aip_info(sip_name, type, row_data) {
    var aip_name_with_link = '<a href="/archival-storage/'
      + row_data.AIPUUID + '/">'
      + sip_name
      + '</a>';
    return aip_name_with_link + '<br>' + row_data.AIPUUID;
  }

  function render_file_actions(file_uuid) {
    var download_href = '/archival-storage/download/aip/file/' + file_uuid + '/';
    var text_span = '<span class="button-text-span">' + gettext('Download') + '</span>';
    return '<a class="btn btn-default fa-download fa" target="_blank" href="'
      + download_href
      + '"> '
      + text_span
      + '</a>';
  }

  function render_aip_name(name, type, row_data) {
    return '<a href="/archival-storage/' + row_data.uuid + '/">' + name + '</a>';
  }

  function render_aip_aic(aic_id, type, row_data) {
    if (row_data.type === 'AIC' && row_data.countAIPsinAIC !== null) {
      var aip_or_aips = row_data.countAIPsinAIC > 1
        ? gettext('AIPs in AIC')
        : gettext('AIP in AIC');
      return aic_id + ' (' + row_data.countAIPsinAIC + ' ' + aip_or_aips + ')';
    } else if (row_data.isPartOf !== null && row_data.isPartOf !== '') {
      return gettext('Part of') + ' ' + row_data.isPartOf;
    } else {
      return gettext('None');
    }
  }

  function render_aip_actions(uuid) {
    return '<a class="btn btn-default" href="/archival-storage/'
      + uuid + '/">'
      + gettext('View')
      + '</a>';
  }

  function render_aip_accession_ids(accession_ids) {
    return accession_ids === null ? '' : accession_ids.join(',<br>');
  }

  function render_aip_created_date(created) {
    return timestampToLocal(created);
  }

  function render_aip_encrypted(encrypted) {
    return encrypted == true ? gettext('True') : gettext('False');
  }

  function render_status(status) {
    return status == "Deletion requested" ? gettext("Deletion requested") : gettext("Stored");
  }

  // Return array consisting of column indices for columns that should be hidden
  // by default if there is no saved table state in DashboardSettings.
  function get_default_hidden_column_indices() {
    return $('#id_show_files').prop('checked') ? [4, 5] : [2, 4, 5, 9];
  }

  // Return array consisting of column indices for columns that should not sort,
  // i.e. Actions, Thumbnails.
  function get_unorderable_column_indices() {
    return $('#id_show_files').prop('checked') ? [0, 6] : [10];
  }

  function get_state_url_params() {
    return $('#id_show_files').prop('checked') ? 'aipfiles/' : 'aips/';
  }

  function get_datatable(showFiles) {
    if (showFiles) {
      var cols = [
        {sTitle: gettext('Thumbnail'), mData: 'FILEUUID', mRender: render_thumbnail },
        {sTitle: gettext('File'), mData: 'filePath', mRender: render_filepath },
        {sTitle: gettext('File UUID'), mData: 'FILEUUID'},
        {sTitle: gettext('AIP'), mData: 'sipname', mRender: render_file_aip_info },
        {sTitle: gettext('Accession number'), mData: 'accessionid', defaultContent: ''},
        {sTitle: gettext('Status'), mData: 'status', mRender: render_status },
        {sTitle: gettext('Actions'), mData: 'FILEUUID', mRender: render_file_actions }
      ];
    }
    else {
      var cols = [
        {sTitle: gettext('Name'), mData: 'name', mRender: render_aip_name },
        {sTitle: gettext('UUID'), mData: 'uuid'},
        {sTitle: gettext('AIC'), mData: 'AICID', mRender: render_aip_aic },
        {sTitle: gettext('Size'), mData: 'size'},
        {sTitle: gettext('File count'), mData: 'file_count', defaultContent: ''},
        {sTitle: gettext('Accession numbers'), mData: 'accessionids', mRender: render_aip_accession_ids},
        {sTitle: gettext('Created'), mData: 'created', mRender: render_aip_created_date },
        {sTitle: gettext('Status'), mData: 'status', mRender: render_status },
        {sTitle: gettext('Encrypted'), mData: 'encrypted', mRender: render_aip_encrypted },
        {sTitle: gettext('Location'), mData: 'location' },
        {sTitle: gettext('Actions'), mData: 'uuid', mRender: render_aip_actions }
      ];
    }

    return $('#archival-storage-entries').dataTable({
        'dom': 'rtiBp',
        'stateSave': true,
        'stateDuration': 60 * 60 * 24 * 365 * 10, // Set state duration to 10 years.
        // Don't save information other than column visibility.
        'stateSaveParams': function(settings, data) {
            delete data.search;
            delete data.start;
            delete data.order;
            delete data.length;
            for ( var i=0 ; i< data.columns.length ; i++ ) {
              delete data.columns[i].search;
            }
        },
        'stateSaveCallback': function(settings, data) {
            $.ajax({
                url: '/archival-storage/save_state/' + get_state_url_params(),
                data: JSON.stringify(data),
                dataType: 'json',
                type: 'POST',
                headers: {'X-CSRFToken': getCookie('csrftoken')},
                success: function() {}
            });
        },
        'stateLoadCallback': function (settings, callback) {
            $.ajax({
                url: '/archival-storage/load_state/' + get_state_url_params(),
                dataType: 'json',
                success: function (json) {
                  callback(json);
                },
                // Handle case where there is no saved state.
                error: function () {
                  callback(null);
                }
            });
        },
        'columnDefs': [
          {
            'targets': get_default_hidden_column_indices(),
            'visible': false
          },
          {
            'targets': get_unorderable_column_indices(),
            'orderable': false
          }
        ],
        'buttons': [
          {
              'extend': 'colvis',
              'text': '<i class="fa fa-cog" aria-hidden="true"></i> ' + gettext('Select columns')
          }
        ],
      'language': {
        'sEmptyTable':            pgettext('DataTable - sEmptyTable',         'No data available in table'),
        'sInfo':                  pgettext('DataTable - sInfo',               'Showing _START_ to _END_ of _TOTAL_ entries'),
        'sInfoEmpty':             pgettext('DataTable - sInfoEmpty',          'Showing 0 to 0 of 0 entries'),
        'sInfoFiltered':          pgettext('DataTable - sInfoFiltered',       '(filtered from _MAX_ total entries)'),
        'sInfoPostFix':           '',
        'sInfoThousands':         pgettext('DataTable - sInfoThousands',      ','),
        'sLengthMenu':            pgettext('DataTable - sLengthMenu',         'Show _MENU_ entries'),
        'sLoadingRecords':        pgettext('DataTable - sLoadingRecords',     'Loading...'),
        'sProcessing':            pgettext('DataTable - sProcessing',         'Processing...'),
        'sSearch':                pgettext('DataTable - sSearch',             'Search:'),
        'sZeroRecords':           pgettext('DataTable - sZeroRecords',        'No matching records found'),
        'oPaginate': {
            'sFirst':             pgettext('DataTable - sFirst',              'First'),
            'sLast':              pgettext('DataTable - sLast',               'Last'),
            'sNext':              pgettext('DataTable - sNext',               'Next'),
            'sPrevious':          pgettext('DataTable - sPrevious',           'Previous')
        },
        'oAria': {
            'sSortAscending':     pgettext('DataTable - sSortAscending',      ': activate to sort column ascending'),
            'sSortDescending':    pgettext('DataTable - sSortDescending',     ': activate to sort column descending')
        }
      },
      'bLengthChange': false,
      'bFilter': false,
      'bAutoWidth': false,
      'sPaginationType': 'full_numbers',
      'bServerSide': true,
      'sAjaxSource': '/archival-storage/search?' + search.toUrlParams(),
      'aoColumns': cols,
      'fnServerData': function(sSource, aoData, fnCallback) {
        aoData.push({ 'name': 'file_mode', 'value': showFiles });
        $.getJSON(sSource, aoData, function(json) {
          fnCallback(json);
        });
      },
    });
  }

  var dtable = get_datatable(false);

  function refresh_search_results() {

    // If we have a datatable, destroy its layout.
    dtable.fnDestroy();

    // JQuery makes sure that the HTML element itself is emptied. The
    // datatable library will raise an error if the number of columns it
    // expects to find differs. This can happen, if like we're doing, when
    // changing the layout of the tables we want to display.
    $('#archival-storage-entries').empty();

    // Show files is a page state. We collect that state information early for
    // use in each of the functions that then need it.
    var showFiles = $('#id_show_files').prop('checked');

    // Return the correct datatable based on whether the user has selected
    // to see the AIPs only, or file list.
    dtable = get_datatable(showFiles);

    // Refresh visibliity of the "Create an AIC" button to reflect new DataTable.
    set_create_aic_visibility(showFiles);

    // Refresh the visibility of the Download CSV button.
    set_download_csv_visibility(showFiles);
  }

  function set_create_aic_visibility(showFiles) {
    if (showFiles) {
      $("#create-aic-btn").hide();
    } else {
      $("#create-aic-btn").show();
    }
  }

  $('#id_show_files').change(function() {
    refresh_search_results();
  });

  $('#search_submit').click(function() {
    refresh_search_results();
  });

  // Prevent user from refreshing page by submitting the form when hitting 'enter'.
  $('#search_form_container').on('keypress', '.aip-search-query-input', function (e) {
    if (e.which == 13) {  // Return key
      // Remove focus from query input field to update its value.
      e.target.blur();
      refresh_search_results();
      return false;
    }
  });

  $("#create-aic-btn").click(function() {
    var aip_uuids = []
    // Get object containing UUIDs from the DataTable.
    var table_uuids = $('#id_show_files').prop('checked')
      ? []
      : $('#archival-storage-entries').DataTable().column(1).data();
    // Add each UUID in the returned object to our clean aip_uuids array.
    for (i = 0; i < table_uuids.length; i++) {
      aip_uuids.push(table_uuids[i]);
    }
    // Redirect window URL to Django create_aic view, including the AIP UUIDs
    // as a comma-separated string in the URL parameters.
    var uuids_string = aip_uuids.join(",");
    window.location = "/archival-storage/search/create_aic/?uuids=" + uuids_string;
  });

  // Vars and functions to Enable the download of the Archival Storage table
  // as a CSV from Elasticsearch.
  const csvMimeType = "text/csv";
  const downloadCSVButton = "download-csv-btn"
  const csvFileName = "archival-storage-report.csv"

  function set_download_csv_visibility(showFiles) {
    btn = $("#download-csv-btn");
    if (showFiles) {
      btn.hide();
    } else {
      btn.show();
    }
  }

  // Return the contents of the Elasticsearch index as a CSV file.
  document.getElementById(downloadCSVButton).onclick = function() { exportFile(csvMimeType, csvFileName) };

  function exportFile(mimeType, reportFileName) {
    // Params to help us to route the query appropriately and
    // extensibly.
    //
    // Param mimeType: The format of the content requested.
    // Param reportFileName: The default download filename.
    //
    // NB. If we extend this For files add the parameter to the
    // dictionary:
    //
    //      "file_mode": showFiles,
    //
    var params = {
      "requestFile": true,
      "mimeType": mimeType,
      "fileName": reportFileName,
      "returnAll": true,
    };
    query = $.param(params);
    window.open('/archival-storage/search/?' + query);
  }

});
