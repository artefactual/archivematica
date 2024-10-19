import angular from 'angular';
import Base64 from 'base64-helpers';
import '../services/facet.service';
import '../services/tag.service';

angular.module('transferService', ['facetService', 'tagService']).

// Provides functions to manage transfer backlog data fetched from Archivematica.
// The Transfer service is able to take a set of data and track it internally,
// while also tracking reformatted copies of the data for convenience.
factory('Transfer', ['Facet', 'Tag', function(Facet, Tag) {
  var get_record = function(id) {
    var record = this.id_map[id];
    if (!record) {
      throw 'Unable to find a record of name ' + String(id) + ' in Transfer\'s ID map';
    } else {
      return record;
    }
  };

  var create_flat_map = (records, map) => {
    if (map === undefined) {
      map = {};
    }

    angular.forEach(records, record => {
      if (record.id === '') {
        // it's a log/metadata file
        // use the encoded path to identify the node
        record.id = record.relative_path;
      }
      map[record.id] = record;
      create_flat_map(record.children, map);
    });

    return map;
  };

  var populate_tag_list = (records, list) => {
    angular.forEach(records, (record, id) => {
      if (!record.tags) {
        return;
      }
      for (var i = 0; i < record.tags.length; i++) {
        var tag = record.tags[i];
        if (list.indexOf(tag) === -1) {
          list.push(tag);
        }
      }
    });
  };

  var clean_record_titles = records => {
    angular.forEach(records, record => {
      record.title = Base64.decode(record.title);
      record.relative_path = Base64.decode(record.relative_path);
    });
  };

  var remove_tag_if_necessary = (self, tag) => {
    if (self.list_tags(tag).length === 0) {
      self.tags = self.tags.filter(element => element !== tag);
    }
  };

  var remove_all = function(id) {
    var record = this.id_map[id];
    if (record) {
      record.tags = [];
    }
  };

  var expand_children = (self, nodes) => {
    angular.forEach(nodes, node => {
      if (node.type === 'transfer' || node.type === 'directory') {
        self.expanded_nodes.push(node);
        if (angular.isDefined(node.children) && node.children.length) {
          expand_children(self, node.children);
        }
      }
    });
  };

  return {
    // A nested tree of transfer backlog data, populated using the format returned
    // by the Archivematica transfer backlog API.
    // Identical to that format, except that titles are not base64-encoded.
    data: [],
    // A flat list of all file formats in this set of data.
    formats: [],
    // An object which maps file IDs to files.
    // This provides a more convenient method to retrieve files by ID without needing
    // to go through a getter function.
    // This is populated when `resolve` is called.
    id_map: {},
    // A flat list of all unique tags associated with the files in this transfer.
    // This is initially populated by `resolve`, and is updated whenever tags are
    // added or removed using the methods on this service.
    tags: [],
    // A list to keep track of the expanded nodes, used to expand/collapse nodes programmatically.
    expanded_nodes: [],
    // Provided a set of data retrieved from the transfer backlog, performs the following:
    // * populates the `data`, `formats`, `id_map` and `tags` attributes.
    // * tracks a full list of all unique tags in the set of files.
    // * base64-decodes the titles of all records in `data`.
    // * sets the `display` attributes using the `filter` method.
    resolve: function(data) {
      this.data = data.transfers;
      this.formats = data.formats;
      this.id_map = create_flat_map(data.transfers);
      populate_tag_list(this.id_map, this.tags);
      clean_record_titles(this.id_map);
      this.filter();
    },
    // Filters the full list of currently-tracked files using the Facet service,
    // tracking a `display` attribute which is set to `true` or `false` as appropriate.
    // Files will not be removed from the list if they don't pass the facets.
    filter: function() {
      angular.forEach(this.id_map, file => {
        if (file.type === 'file') {
          file.display = Facet.passes_filters(file, ['tags']);
        } else {
          file.display = true;
        }
      });
    },

    // Adds a `tag` to the file with `id`.
    // If `skip_submit` is `true`, doesn't submit the new tag to the Archivematica API.
    add_tag: function(id, tag, skip_submit) {
      var record = get_record.apply(this, [id]);
      // log/metadata files use their encoded paths as identifiers
      if (record.id === Base64.encode(record.relative_path)) {
        // it's a log/metadata file and should not be tagged
        return;
      }
      record.tags = record.tags || [];

      if (record.tags.indexOf(tag) !== -1) {
        return;
      }
      record.tags.push(tag);
      this.tag_updates[id] = record.tags;

      // Add this tag to the flat list of current tags if not already present
      if (this.tags.indexOf(tag) === -1) {
        this.tags.push(tag);
      }

      if (!skip_submit) {
        Tag.submit(id, record.tags);
      }
    },
    // Like `add_tag`, but adds the tag to all of the files in the `ids` array.
    add_list_of_tags: function(ids, tag, skip_submit) {
      angular.forEach(ids, id => {
        this.add_tag(id, tag, skip_submit);
      });
    },
    // Removes a `tag` from the file with `id`.
    // // If `skip_submit` is `true`, doesn't remove the tag in the Archivematica API.
    remove_tag: function(id, tag, skip_submit) {
      var record = get_record.apply(this, [id]);

      if (!tag) {
        var record = get_record.apply(this, [id]);
        var tags_for_id = record.tags;

        remove_all.apply(this, [id]);
        angular.forEach(tags_for_id, tag => {
          remove_tag_if_necessary(this, tag);
        });

        if (!skip_submit) {
          Tag.remove(id);
        }
        this.tag_updates[id] = record.tags;
        return;
      }

      if (record.tags === undefined) {
        $log.warn('Tried to remove tag for file with ID ' + String(id) + ' but no tags are specified for that file');
        return;
      }
      record.tags = record.tags.filter(record_tag => record_tag !== tag);
      this.tag_updates[id] = record.tags;

      // If this is the last occurrence of this tag, delete it from the tag list
      remove_tag_if_necessary(this, tag);

      if (!skip_submit) {
        Tag.submit(id, record.tags);
      }
    },
    // Returns the list of all tags for the file with `id`.
    get_tag: function(id) {
      var record = get_record.apply(this, [id]);
      return record.tags || [];
    },
    // Lists all files tagged with `tag`.
    list_tags: function(tag) {
      var results = [];
      angular.forEach(this.id_map, (record, id) => {
        var tags = record.tags || [];
        if (tags.indexOf(tag) !== -1) {
          results.push(id);
        }
      });

      return results;
    },
    // Empties the list of tracked tags.
    clear_tags: function() {
      this.tags = [];
    },
    collapse_all_nodes: function() {
      this.expanded_nodes = [];
    },
    expand_all_nodes: function() {
      expand_children(this, this.data);
    },
    // Share tag updates with the other controllers
    tag_updates: {},
  };
}]);
