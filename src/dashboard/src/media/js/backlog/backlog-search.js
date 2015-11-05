$(document).ready(function()
  {
    var search = renderBacklogSearchForm(null, null, null);

    function render_file_actions_col(relative_path, type, row_data) {
      return '<a class="btn fa-download fa" target="_blank" href="' + '/filesystem/download_ss/?filepath=' +
              Base64.encode('/originals/' + relative_path) + '">Download</a>';
    }

    function render_transfer_actions_col(uuid, type, row_data) {
      return '<a class="btn" href="/backlog/download/' + uuid + '">Download</a>' +
             '<a href="/backlog/delete/' + uuid + '"><img title="Request deletion" \
             class="delete-icon" src="/media/images/delete.png"></a>';
    }

    function get_datatable() {
      if ($('#id_show_files').prop('checked')) {
        var cols = [
          {sTitle: 'Filename', mData: 'filename'},
          {sTitle: 'Transfer UUID', mData: 'sipuuid'},
          {sTitle: 'Actions', mData: 'relative_path', mRender: render_file_actions_col}
        ];
      }
      else {
        var cols = [
          {sTitle: 'Name', mData: 'name'},
          {sTitle: 'Transfer UUID', mData: 'uuid'},
          {sTitle: 'File count', mData: 'file_count'},
          {sTitle: 'Ingest date', mData: 'ingest_date'},
          {sTitle: 'Actions', mData: 'uuid', mRender: render_transfer_actions_col}
        ];
      }

      return $('#backlog-entries').dataTable({
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
      $('#backlog-entries thead').empty();
      dtable.fnDestroy();
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
