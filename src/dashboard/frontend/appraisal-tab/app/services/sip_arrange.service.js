import angular from 'angular';
import {decode_browse_response, format_entries} from 'archivematica-browse-helpers';
import Base64 from 'base64-helpers';
// lodash is used by restangular
import 'lodash';
import 'restangular';

angular.module('sipArrangeService', ['restangular']).

factory('SipArrange', ['Restangular', function(Restangular) {
  var SipArrange = Restangular.one('filesystem');

  // public

  // Creates a new SIP arrange directory.
  // * path - The full destination path within the arrange space; must begin with /arrange/
  // * title - String to display within the UI
  // * parent - Will be attached as the "parent" property in the returned object
  //
  // Returns an object formatted in the same format used by `list_contents`.
  var create_directory = function(path, title, parent) {
    // Return a formatted directory object
    var on_success = success => {
      return {
        title: title,
        has_children: true,
        children: [],
        path: path.replace(/^\/arrange\//, ''),
        parent: parent,
        display: true,
        children_fetched: false,
        type: 'arrange_entry',
        directory: true,
      };
    };

    return post_form(SipArrange, 'create_directory_within_arrange', {path: Base64.encode(path)}).then(on_success);
  };

  // Copies files listed in `source` to `destination`.
  // Paths in `source` must begin with /originals/ and paths in `destination` must begin with /arrange/
  var copy_to_arrange = function(source, destination) {
    var params = {};
    if (typeof source === 'string' && typeof destination === 'string') {
      params = {
        'filepath': Base64.encode(source),
        'destination': Base64.encode(destination),
      };
    } else {
      params = {
        'filepath': source.map(path => Base64.encode(path)),
        'destination': destination.map(path => Base64.encode(path)),
      };
    }
    return post_form(SipArrange, 'copy_to_arrange', params);
  };

  // Lists the files in a given location.
  // * path - A directory located in SIP arrange. Must begin with /arrange/
  // * parent - If specified, will be attached to the returned objects as the `parent` key
  //
  // Returns a list of objects; check archivematica-browse-helpers for the format:
  // https://github.com/artefactual-labs/archivematica-browse-helpers
  var list_contents = function(path, parent) {
    var format_root = data => {
      return data.directories.map(directory => {
        return {
          title: directory,
          has_children: true,
          children: [],
          // "path" tracks the full path to the directory, including
          // all of its parents.
          // Since these are top-level directories, their paths are the
          // same as their names.
          path: directory,
          display: true,
          properties: data.properties[directory],
          children_fetched: false,
          type: 'arrange_entry',
          directory: true,
        };
      });
    };

    let format_files = data => {
      // format_entries expects a directory that does not end in /
      let parent_path = parent.path && parent.path.slice(-1) === '/' ? parent.path.slice(0, -1) : parent.path;
      let entries = format_entries(data, parent_path, parent);
      entries.forEach(entry => entry.type = 'arrange_entry');
      return entries;
    };

    path = path || '';
    var on_success = path === '' ? format_root : format_files;
    return SipArrange.one('contents').one('arrange').get({path: Base64.encode(path)}).then(decode_browse_response).then(on_success);
  };

  // Deletes a file or directory from arrangement at the location `target`.
  // `target` must begin with /arrange/.
  var remove = function(target) {
    return post_form(SipArrange.one('delete'), 'arrange', {filepath: Base64.encode(target)});
  };

  // Starts a SIP from the directory at `target`.
  // `target` must begin with /arrange/.
  var start_sip = function(target) {
    return post_form(SipArrange, 'copy_from_arrange', {filepath: Base64.encode(target)});
  };

  // private

  // Helper function to POST content with a form-encoded body
  // instead of a JSON-encoded body.
  var post_form = function(model, path, body) {
    return model.customPOST(
      // form-encode body
      jQuery.param(body),
      path,
      {}, // URL parameters - always empty
      {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    )
  };

  return {
    create_directory: create_directory,
    copy_to_arrange: copy_to_arrange,
    list_contents: list_contents,
    remove: remove,
    start_sip: start_sip,
  };
}]);
