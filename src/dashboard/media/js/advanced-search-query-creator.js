(function(exports) {

  exports.AdvancedSearchView = Backbone.View.extend({

    initialize: function() {
      // Default row is a single-length array of a copy of the row template
      this.rows = [_.extend({}, this.options.rowTemplate)];
      this.rowTemplate = this.options.rowTemplate;
      this.fields = [];
      this.optionElements = {};
      this.allowAdd = (this.options.allowAdd != undefined)
        ? this.options.allowAdd
        : true;
      this.deleteHandleHtml = this.options.deleteHandleHtml || gettext('Delete');
      this.addHandleHtml    = this.options.addHandleHtml || gettext('Add');
      this.cssClassPrefix = this.options.cssClassPrefix || 'advanced_search_form';
    },

    addInput: function(name, attributes) {
      this.fields.push(name);
      this.optionElements[name] = this.createElement('input', attributes);
    },

    addSelect: function(name, attributes, options) {
      this.fields.push(name);
      this.optionElements[name] = this.createElement('select', attributes, options);
    },

    createElement: function(type, attributes, options) {
      var $el = $('<' + type + '>');

      for(var key in attributes) {
        $el.attr(key, attributes[key]);
      }

      for(var value in options) {
        $el.append(
          $('<option></option>').val(value).html(options[value])
        );
      }

      return $el;
    },

    generateBlankRow: function() {
      // New rows are created as copies of the row template
      return _.extend({}, this.rowTemplate);
    },

    addBlankRow: function() {
      this.rows.push(this.generateBlankRow());
    },

    deleteRow: function(delIndex) {
      var newRows = [];

      for(var rowIndex in this.rows) {
        if (rowIndex != delIndex) {
          newRows.push(this.rows[rowIndex]);
        }
      }

      this.rows = newRows;
    },

    toUrlParams: function() {
      var urlParams = '';

      // add each row
      for(var rowIndex in this.rows) {
        var $row = $('<div style="clear:both"></div>');

        // add each field
        for(var fieldIndex in this.fields) {
          var fieldName = this.fields[fieldIndex];
          if (
            this.fieldVisibilityCheck == undefined
            || this.fieldVisibilityCheck(rowIndex, fieldName)
          ) {
            urlParams = urlParams + ((urlParams != '') ? '&' : '');
            urlParams = urlParams + fieldName + '=' + encodeURIComponent(this.rows[rowIndex][fieldName]);
          }
        }
      }

      return urlParams;
    },

    getArrayOfUrlParams: function() {
      // return false if URL doesn't contain params
      if (window.location.href.indexOf('?') == -1) {
        return false;
      }

      var params = []
        , pairStrings = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');

      for(var index in pairStrings) {
        pairRaw = pairStrings[index].split('=');

        var pair = {},
            fieldName = pairRaw[0];

        if (this.fields.indexOf(fieldName) != -1) {
          pair[fieldName] = pairRaw[1];
          params.push(pair);
        }
      }

      return (params.length > 0) ? params : false;
    },

    firstKeyInObject: function(object) {
      for(key in object) {
        return key;
      }
    },

    blankUndefinedFieldsInRow: function(row) {
      for(var index in this.fields) {
        var fieldName = this.fields[index];
        if (row[fieldName] == undefined) {
          row[fieldName] = '';
        }
      }
    },

    urlParamsToData: function() {
      var arrayOfUrlParams = this.getArrayOfUrlParams();

      if (!arrayOfUrlParams) {
        return false;
      }

      var setParams = {}
        , rows = []
        , row
        , firstKey
        , rowIndex = 0
        , done = false
        , pair = arrayOfUrlParams.shift();

      while (pair != undefined) {
        row = {};
        for(var fieldIndex in this.fields) {
          var fieldName = this.fields[fieldIndex];
          // allow for field visibility logic
          if (
            this.fieldVisibilityCheck == undefined
            || this.fieldVisibilityCheck(rowIndex, fieldName)
          ) {
            if (pair != undefined) {
              firstKey = this.firstKeyInObject(pair);
              row[firstKey] = decodeURIComponent(pair[firstKey]);
            }

            pair = arrayOfUrlParams.shift();
          }
        }
        rows.push(row);
        rowIndex++;
      }

      return rows;
    },

    render: function() {
      var self = this;

      // if no data provided, create blank row
      if (this.rows == undefined) {
        this.rows = [];
        this.addBlankRow();
      }

      var $el = $('<div class="' + this.addCssClassPrefix('rows_container') + '"></div>');

      // add each row
      for(var rowIndex in this.rows) {
        var $row = $('<div style="clear:both"></div>')
            rowClasses = this.addCssClassPrefix('row');

        if (this.rows.length > 1) {
          rowClasses = rowClasses + ' ' + this.addCssClassPrefix('row_multiple');
        }

        $row.attr('class', rowClasses);

        // add each field 
        for(var fieldIndex in this.fields) {
          var fieldName = this.fields[fieldIndex]
            , value = this.rows[rowIndex][fieldName]
            , $fieldContainer = $('<div class="' + this.addCssClassPrefix('field_' + fieldName) + '" style="float:left"></div>');

          // allow for field visibility logic
          if (
            this.fieldVisibilityCheck == undefined
            || this.fieldVisibilityCheck(rowIndex, fieldName)
          ) {
            // clone and setup field instance
            var $field = $(this.optionElements[fieldName]).clone();
            $field.val(value);
            (function(self, rowIndex, fieldName) {
              $field.change(function() {
                self.rows[rowIndex][fieldName] = $(this).val();
              });
            })(self, rowIndex, fieldName);

            $fieldContainer.append($field);
          }

          $row.append($fieldContainer);
        }

        if (this.rows.length > 1) {
          // add button to delete row
          var $rowDelEl = $('<div style="float:left">' + self.deleteHandleHtml + '</div>');
          (function(self, rowIndex) {
            $rowDelEl.click(function() {
              self.deleteRow(rowIndex);
              self.render();
            });
          })(self, rowIndex);
          $row.append($rowDelEl);
        }

        $el.append($row);
      }

      if (this.allowAdd) {
        // add button to add blank rows
        var $addButton = $(this.addHandleHtml);
        var $addBlankEl = $('<div style="clear:both"></div>');
        $addBlankEl.append($addButton);

        $addButton.click(function() {
          self.addBlankRow();
          self.render();
        });
        $el.append($addBlankEl);
      }

      $(this.el)
        .empty()
        .append($el);

      return this;
    },

    addCssClassPrefix: function(className) {
      return this.cssClassPrefix + '_' + className;
    }
  });

})(typeof exports === 'undefined' ? this['advancedSearch'] = {} : exports);
