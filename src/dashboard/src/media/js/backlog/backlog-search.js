$(document).ready(function()
  {
    var search = renderBacklogSearchForm(null, null, null);

    function render_file_actions_col(relative_path, type, row_data) {
      return '<a class="btn btn-default fa-download fa" target="_blank" href="' + '/filesystem/download_ss/?filepath=' +
              Base64.encode('/originals/' + relative_path) + '">' + gettext('Download') + '</a>';
    }

    function render_transfer_actions_col(uuid, type, row_data) {
      return '<a class="btn btn-default" href="/backlog/download/' + uuid + '">' + gettext('Download') + '</a>' +
             '<a href="/backlog/delete/' + uuid + '"><img title="' + gettext('Request deletion') + '" \
             class="delete-icon" src="/media/images/delete.png"></a>';
    }

    function get_datatable() {
      if ($('#id_show_files').prop('checked')) {
        var cols = [
          {sTitle: gettext('Filename'), mData: 'filename'},
          {sTitle: gettext('Transfer UUID'), mData: 'sipuuid'},
          {sTitle: gettext('Actions'), mData: 'relative_path', mRender: render_file_actions_col}
        ];
      }
      else {
        var cols = [
          {sTitle: gettext('Name'), mData: 'name'},
          {sTitle: gettext('Transfer UUID'), mData: 'uuid'},
          {sTitle: gettext('File count'), mData: 'file_count'},
          {sTitle: gettext('Ingest date'), mData: 'ingest_date'},
          {sTitle: gettext('Actions'), mData: 'uuid', mRender: render_transfer_actions_col}
        ];
      }

      return $('#backlog-entries').dataTable({
        'language': {
          'sEmptyTable':            pgettext('DataTable - sEmptyTable',         'No data available in table'),
          'sInfo':                  pgettext('DataTable - sInfo',               'Showing _START_ to _END_ of _TOTAL_ entries'),
          'sInfoEmpty':             pgettext('DataTable - sInfoEmpty',          'Showing 0 to 0 of 0 entries'),
          'sInfoFiltered':          pgettext('DataTable - sInfoFiltered',       '(filtered from _MAX_ total entries)'),
          'sInfoPostFix':           '', // pgettext('DataTable - sInfoPostFix',        ''),
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
        'sAjaxSource': '/backlog/search?' + search.toUrlParams(),
        'aoColumns': cols,
        'fnServerData': function(sSource, aoData, fnCallback) {
          aoData.push({ 'name': 'file_mode', 'value': $('#id_show_files').prop('checked') });
          $.getJSON(sSource, aoData, function(json) {
            fnCallback(json);
          });
        },
      });
    }

    var dtable = get_datatable();

    function refresh_search_results() {

      // If we have a datatable destroy its layout.
      dtable.fnDestroy();

      // JQuery makes sure that the HTML element itself is emptied. The
      // datatable library will raise an error if the number of columns it
      // expects to find differs. This can happen, if like we're doing, when
      // changing the layout of the tables we want to display.
      $('#backlog-entries').empty();

      // Return the correct datatable based on whether the user has selected
      // to see the transfer backlog only, or file list.
      dtable = get_datatable();

    }

    $('#id_show_files').change(function() {
      refresh_search_results();
    });

    $('#search_submit').click(function() {
      refresh_search_results();
    });

    // Prevent user from refreshing page by submitting the form when hitting 'enter'
    $('.aip-search-query-input').keypress(function(e) {
      if (e.which == 13) {
        return false;
      }
    });
  });
