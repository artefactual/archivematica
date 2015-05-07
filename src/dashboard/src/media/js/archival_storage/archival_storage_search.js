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

$(document).ready(function() {

  // create new form instance, providing a single row of default data
  var search = new advancedSearch.AdvancedSearchView({
    el: $('#search_form_container'),
//    allowAdd: false,
    rowTemplate: {
      'op': '',
      'query': '',
      'field': '',
      'fieldName': '',
      'type': 'term'
    },
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
  search.addSelect('field', {title: 'field name', onchange: 'selectField(this)'}, {
    '': 'Any',
    'FILEUUID': 'File UUID',
    'filePath': 'File path',
    'fileExtension': 'File extension',
    'AIPUUID': 'AIP UUID',
    'sipName': 'AIP name',
    'isPartOf': 'Part of AIC',
    'AICID': 'AIC Identifier',
    'transferMetadata': 'Transfer metadata',
    'transferMetadataOther': 'Transfer metadata (other)',
  });

  // "Other" field name, when selecting "transfer metadata (other)"
  search.addInput('fieldName', {title: 'other field name', 'class': 'aip-search-query-input', 'id': 'aip-search-query-other-field-name'});

  // default field name field
  search.addSelect('type', {title: 'query type'}, {
    'term': 'Keyword',
    'string': 'Phrase',
    'range': 'Date range'
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

  function aipSearchSubmit() {
    var destination = '/archival-storage/search/' + '?' + search.toUrlParams();
    if($('#id_show_files').is(':checked')) {
      destination += '&filemode=true';
    }
    if($('#id_show_aics').is(':checked')) {
      destination += '&show_aics=true';
    }
    window.location = destination;
  }

  // submit logic
  $('#search_submit').click(function() {
    aipSearchSubmit();
  });

  $('#search_form').submit(function() {
    aipSearchSubmit();
    return false;
  });

  $('.aip-search-query-input').keypress(function (e) {
    if (e.which == 13) {  // Return key
      aipSearchSubmit();
      return false;
    }
  });
});
