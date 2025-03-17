'use strict';

import '../../app/filters/aggregation.filter.js';
import '../../app/services/transfer.service.js';

describe('AggregationFilters', function() {
  var format_data;
  var find_files;
  var find_transfers;
  var tag_count;

  var fmt_91_records = [{
    'id': '054a0f2c-79bb-4051-b82b-4b0f14564811',
    'title': 'lion.svg',
    'format': 'Scalable Vector Graphics 1.0',
    'group': 'Image (Vector)',
    'type': 'file',
    'puid': 'fmt/91',
    'size': 5,
    'bulk_extractor_reports': ['logs.zip'],
    'tags': [],
  }, {
    'id': '7f70d25c-be05-4950-a384-dac159926960',
    'title': 'rose_quartz.svg',
    'format': 'Scalable Vector Graphics 1.0',
    'group': 'Image (Vector)',
    'type': 'file',
    'puid': 'fmt/91',
    'size': 2,
    'bulk_extractor_reports': ['logs.zip'],
    'tags': ['test'],
  }];
  var fmt_11_records = [{
    'id': '4e941898-3914-4add-b1f6-476580862069',
    'title': 'pearl.png',
    'format': 'PNG 1.0',
    'group': 'Image (Raster)',
    'type': 'file',
    'puid': 'fmt/11',
    'size': 13,
    'bulk_extractor_reports': ['logs.zip'],
    'tags': ['test', 'test2'],
  }];
  var no_fmt_record = [{
    'id': 'dc08bcee-c4b9-490e-a98e-a884c4a9973c',
    'title': 'pptC1.tmp',
    'format': 'Generic AIFF',
    'group': 'Audio',
    'extension': '.aif',
    'size': 34,
    'bulk_extractor_reports': [],
    'type': 'file',
    'puid': '',
    'tags': [],
  }];
  var record_with_no_logs = [{
    'id': 'b2a14653-5fd8-458c-b4ae-ccaab4b46b0c',
    'title': 'lapis_lazuli.tiff',
    'format': 'TIFF for Image Technology (TIFF/IT)',
    'group': 'Image (Raster)',
    'type': 'file',
    'puid': 'fmt/153',
    'size': 89,
  }];
  var transfers = [{
    'id': 'fb91bf38-3836-4312-a928-699c564865da',
    'title': 'garnet',
    'type': 'transfer',
    'original_order': '/fixtures/transferdata/fb91bf38-3836-4312-a928-699c564865da/directory_tree.txt',
  }];

  beforeEach(function() {
    angular.mock.module('aggregationFilters');
    angular.mock.module('transferService');

    inject(function($injector) {
      format_data = $injector.get('$filter')('format_data');
      find_files = $injector.get('$filter')('find_files');
      find_transfers = $injector.get('$filter')('find_transfers');
      tag_count = $injector.get('$filter')('tag_count');
    });
  });

  it('should aggregate data about multiple files with the same format', function() {
    var aggregate_data = format_data(fmt_91_records);
    expect(aggregate_data.length).toEqual(1);
    expect(aggregate_data[0].format).toEqual('Scalable Vector Graphics 1.0');
    expect(aggregate_data[0].data.format).toEqual('Scalable Vector Graphics 1.0');
    expect(aggregate_data[0].data.size).toEqual(7);
    expect(aggregate_data[0].data.count).toEqual(2);
    expect(aggregate_data[0].data.group).toEqual('Image (Vector)');
  });

  it('should produce one entry for each format in the source records', function() {
    var records = fmt_91_records.concat(fmt_11_records);
    var aggregate_data = format_data(records);
    expect(aggregate_data.length).toEqual(2);
    expect(aggregate_data[0].format).toEqual('PNG 1.0');
    expect(aggregate_data[0].data.puid).toEqual('fmt/11');
    expect(aggregate_data[0].data.format).toEqual('PNG 1.0');
    expect(aggregate_data[0].data.count).toEqual(1);
    expect(aggregate_data[0].data.group).toEqual('Image (Raster)');
    expect(aggregate_data[1].format).toEqual('Scalable Vector Graphics 1.0');
    expect(aggregate_data[1].data.puid).toEqual('fmt/91');
    expect(aggregate_data[1].data.format).toEqual('Scalable Vector Graphics 1.0');
    expect(aggregate_data[1].data.count).toEqual(2);
    expect(aggregate_data[1].data.group).toEqual('Image (Vector)');
  });

  it('should aggregate data about files with no PUID', function() {
    var aggregate_data = format_data(no_fmt_record);
    expect(aggregate_data.length).toEqual(1);
    expect(aggregate_data[0].format).toEqual('Generic AIFF');
    expect(aggregate_data[0].data.puid).toEqual('');
    expect(aggregate_data[0].data.format).toEqual('Generic AIFF');
    expect(aggregate_data[0].data.size).toEqual(34);
    expect(aggregate_data[0].data.count).toEqual(1);
    expect(aggregate_data[0].data.group).toEqual('Audio');
  });

  it('should filter lists of files to contain only files', function() {
    var records = fmt_91_records.concat(fmt_11_records, transfers);
    var filtered_records = find_files(records);
    expect(filtered_records.length).toEqual(3);
    expect(filtered_records[0].title).toEqual('lion.svg');
  });

  it('should omit files with no bulk_extractor logs', function() {
    var records = fmt_91_records.concat(record_with_no_logs);
    expect(records.length).toEqual(3);
    var filtered_records = find_files(records);
    expect(filtered_records.length).toEqual(2);
    expect(filtered_records[0].title).toEqual('lion.svg');
  });

  it('should filter lists of files to contain only transfers', function() {
    var records = fmt_91_records.concat(fmt_11_records, transfers);
    var filtered_records = find_transfers(records);
    expect(filtered_records.length).toEqual(1);
    expect(filtered_records[0].title).toEqual('garnet');
  });

  it('should be able to aggregate tag acounts', function() {
    var records = fmt_91_records.concat(fmt_11_records);
    var tags = tag_count(records);
    expect(tags[0][0]).toEqual('test');
    expect(tags[0][1]).toEqual(2);
    expect(tags[1][0]).toEqual('test2');
    expect(tags[1][1]).toEqual(1);
  });
});
