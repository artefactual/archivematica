import angular from 'angular';
import _ from 'lodash';

// The default hash function may confuse two arrays of objects
// of the same length as the same set of records.
var hash_fn = records => {
  return JSON.stringify(records);
};

angular.module('aggregationFilters', []).

filter('format_data', function() {
  var format_data_fn = records => {
    var format_data = {};
    for (var i in records) {
      var record = records[i];

      // Don't count transfers or directories
      if (record.type !== 'file') {
        continue;
      }

      // Set 'Unidentified' format and/or group for those
      // files where they're missing. This also sets the 
      // values in the records at the SelectedFiles service,
      // allowing them to be filtered in the file list panel.
      if (!record.format) {
        record.format = 'Unidentified';
      }
      if (!record.group) {
        record.group = 'Unidentified';
      }

      if (!format_data[record.format]) {
        format_data[record.format] = {count: 0, size: 0};
      }

      format_data[record.format].count++;
      format_data[record.format].puid = record.puid || '';
      format_data[record.format].format = record.format;
      format_data[record.format].group = record.group;
      format_data[record.format].size += parseFloat(record.size) || 0;
    }

    var out_data = [];
    for (var key in format_data) {
      out_data.push({format: key, data: format_data[key]});
    }

    return _.sortBy(out_data, format => format.format);
  };

  return _.memoize(format_data_fn, hash_fn);
}).

filter('format_graph', () => {
  var format_graph_fn = records => {
    var data = {
      series: ['Format'],
      data: [],
    };
    angular.forEach(records, (format_data, _) => {
      var readable_name = format_data.format;
      if (format_data.data.puid) {
       readable_name += ' (' + format_data.data.puid + ')';
      }
      data.data.push({
        format: format_data.format,
        x: readable_name,
        y: [format_data.data.count],
        tooltip: readable_name,
      });
    });
    return data;
  };

  return _.memoize(format_graph_fn, hash_fn);
}).

filter('size_graph', function($filter) {
  var size_graph_fn = records => {
    var data = {
      series: ['Format'],
      data: [],
    };
    angular.forEach(records, (format_data, _) => {
      var readable_name = format_data.format;
      if (format_data.data.puid) {
       readable_name += ' (' + format_data.data.puid + ')';
      }
      data.data.push({
        format: format_data.format,
        x: readable_name,
        y: [format_data.data.size],
        tooltip: readable_name + ', ' + $filter('number')(format_data.data.size) + ' MB',
      });
    });
    return data;
  };

  return _.memoize(size_graph_fn, hash_fn);
}).

filter('find_transfers', function() {
  var transfer_fn = records => records.filter(el => el.type === 'transfer');

  return _.memoize(transfer_fn, hash_fn);
}).

filter('find_files', function() {
  var file_fn = records => records.filter(el => el.type === 'file' && el.bulk_extractor_reports);

  return _.memoize(file_fn, hash_fn);
}).

filter('tag_count', function() {
  var tag_fn = records => {
    var out = {};
    for (var i in records) {
      var record = records[i];
      for (var tag_index in record.tags) {
        var tag = record.tags[tag_index];
        out[tag] ? out[tag]++ : out[tag] = 1;
      }
    }

    // Return as array so it is sortable
    return _.map(out, (count, tag) => [tag, count]);
  };

  return _.memoize(tag_fn, hash_fn);
});
