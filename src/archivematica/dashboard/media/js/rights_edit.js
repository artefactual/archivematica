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

function repeatingDocumentationIdentifierRecordsSchema(dataType) {
  var schema = {};

  schema[dataType + 'documentationidentifiertype'] = {
    'label': gettext('Type'),
    'type': 'input'
  };

  schema[dataType + 'documentationidentifiervalue'] = {
    'label': gettext('Value'),
    'type': 'input'
  };

  schema[dataType + 'documentationidentifierrole'] = {
    'label': gettext('Role'),
    'type': 'input'
  };

  return schema;
}

function repeatingNotesRecordsSchema(dataType) {
  var schema = {};
  schema[dataType + 'note'] = {};
  return schema;
}

function setUpRepeatingCopyrightNotesRecords(parentId) {
  var schema = repeatingNotesRecordsSchema('copyright');
  setUpRepeatingField('copyrightnotes_', parentId, gettext('Copyright Note'), schema, '/formdata/copyrightnote/' + parentId + '/', true);
}

function setUpCopyrightDocumentationIdentifierAttributes() {
    $("label:contains('Copyright documentation identifier:')").attr('title', gettext('designation used to uniquely identify documentation supporting the specified rights granted according to copyright within the repository system'));
    $('[name=copyrightdocumentationidentifiertype],[name=copyright_documentation_identifier_type]').attr('title', gettext("a designation of the domain within which the copyright documentation identifier is unique"));
    $('[name=copyrightdocumentationidentifiervalue],[name=copyright_documentation_identifier_value]').attr('title', gettext("the value of the copyrightDocumentatinIdentifier"));
    $('[name=copyrightdocumentationidentifierrole],[name=copyright_documentation_identifier_role]').attr('title', gettext("A value indicating the purpose or expected use of the documentation being identified"));
    $('[name=copyright_note],[name=copyrightnote]').attr('title', gettext("Additional information about the copyright status of the object"));
}

function setUpRepeatingCopyrightDocumentationIdentifierRecords(parentId) {
  var schema = repeatingDocumentationIdentifierRecordsSchema('copyright');
  setUpRepeatingField('copyrightdocidfields_', parentId, gettext('Copyright Documentation Identifier'), schema, '/formdata/copyrightdocumentationidentifier/' + parentId + '/', true, setUpCopyrightDocumentationIdentifierAttributes);
  setUpCopyrightDocumentationIdentifierAttributes();
}

function setUpStatuteDocumentationIdentifierAttributes() {
    $('[name=statutedocumentationidentifiertype],[name=statute_documentation_identifier_type_None]').attr('title', gettext("a designation of the domain within which the statute documenation identifier is unique"));
    $('[name=statutedocumentationidentifiervalue],[name=statute_documentation_identifier_value]').attr('title', gettext("the value of the statuteDocumentatinIdentifier"));
    $('[name=statutedocumentationidentifierrole],[name=statute_documentation_identifier_role_None]').attr('title', gettext("A value indicating the purpose or expected use of the documentation being identified"));
}

function setUpRepeatingStatuteDocumentationIdentifierRecords(parentId) {
  var schema = repeatingDocumentationIdentifierRecordsSchema('statute');
  setUpRepeatingField('statutedocidfields_', parentId, gettext('Statute Documentation Identifier'), schema, '/formdata/statutedocumentationidentifier/' + parentId + '/', true, setUpStatuteDocumentationIdentifierAttributes);
  setUpStatuteDocumentationIdentifierAttributes();
}

function setUpStatuteNoteAttributes() {
  $('[name=statutenote],[name=new_statute_note_1],[name=new_statute_note_None]').each(function(index) {
    $(this).attr('title', gettext("additional information about the statute"));
  });
}

function setUpRepeatingStatuteNotesRecords(parentId) {
  var schema = repeatingNotesRecordsSchema('statute');
  setUpRepeatingField('statutenotes_', parentId, gettext('Statute Note'), schema, '/formdata/statutenote/' + parentId + '/', true, setUpStatuteNoteAttributes);
  setUpStatuteNoteAttributes();
}

function setUpLicenseDocumentationIdentifierAttributes() {
  $("label:contains('License documentation identifier:')").attr('title', gettext('a value indicating the purpose or expected use of the documentation being identified'));
}

function setUpRepeatingLicenseDocumentationIdentifierRecords(parentId) {
  var schema = repeatingDocumentationIdentifierRecordsSchema('license');
  setUpRepeatingField('licensedocidfields_', parentId, gettext('License Documentation Identifier'), schema, '/formdata/licensedocumentationidentifier/' + parentId + '/', true, setUpLicenseDocumentationIdentifierAttributes);
  setUpLicenseDocumentationIdentifierAttributes();
}

function setUpRepeatingOtherRightsDocumentationIdentifierRecords(parentId) {
  var schema = repeatingDocumentationIdentifierRecordsSchema('otherrights');
  setUpRepeatingField('otherrightsdocidfields_', parentId, gettext('Other Rights Documentation Identifier'), schema, '/formdata/otherrightsdocumentationidentifier/' + parentId + '/', true);
}

function setUpRepeatingOtherRightsNotesRecords(parentId) {
  var schema = {
    'otherrightsnote': {},
  };
  setUpRepeatingField('otherrightsnotes_', parentId, gettext('Other Rights Note'), schema, '/formdata/otherrightsnote/' + parentId + '/', true);
}

function setUpLicenseNoteAttributes() {
  $('[name=license_note],[name=licensenote]').each(function(index) {
    $(this).attr('title', gettext("additional information about the license"));
  });
}

function setUpRepeatingLicenseNotesRecords(parentId) {
  var schema = {
    'licensenote': {},
  };
  setUpRepeatingField('licensenotes_', parentId, gettext('License Note'), schema, '/formdata/licensenote/' + parentId + '/', true, setUpLicenseNoteAttributes);
  setUpLicenseNoteAttributes();
}

function setUpRepeatingRightsGrantedRestrictionAttributes() {
  $('select').attr('title', gettext('a condition or limitation on the act'));
  $('textarea').attr('title', gettext('additional information about the rights granted'));
  $("span:contains('Open End Date')").attr('title', gettext('use "OPEN" for an open ended term of restriction. Omit endDate if the ending date is unknown or the permission statement applies to many objects with different end dates.'));
}

function setUpRepeatingRightsGrantedRestrictionRecords(parentId) {
  var schema = {
    'restriction': {
      'type': 'select',
      'options': {
        '': '',
        'Allow': 'Allow',
        'Disallow': 'Disallow',
        'Conditional': 'Conditional'
      }
    }
  };
  setUpRepeatingField('rightsrestrictions_', parentId, gettext('Restriction'), schema, '/formdata/rightsrestriction/' + parentId + '/', true, setUpRepeatingRightsGrantedRestrictionAttributes);
  setUpRepeatingRightsGrantedRestrictionAttributes();
}

function setUpRepeatingRightsGrantedNotesRecords(parentId) {
  var schema = {
    'rightsgrantednote': {},
  };
  setUpRepeatingField('rightsfields_', parentId, gettext('Rights Granted Note'), schema, '/formdata/rightsnote/' + parentId + '/', true);
}

// repeating child field to a formset bound to existing data
function setUpRepeatingField(idPrefix, parentId, description, schema, url, noCreation, cb) {
  var rights = new RepeatingDataView({
    el: $('#' + idPrefix + parentId),
    description: description,
    parentId: parentId,
    schema: schema,
    url: url,
    noCreation: noCreation
  });
  rights.render(cb);

  if (parentId == '' || parentId == 'None') {
    var instructionDescription = description.toLowerCase()
      , instructions;

    // make other rights fields instructions generic as they are used with
    // a number of types of basises
    if (instructionDescription == 'other rights documentation identifier') {
      instructionDescription = 'documentation identifier';
    }

    if (instructionDescription == 'other rights note') {
      instructionDescription = 'note';
    }

    if (noCreation == undefined || !noCreation) {
      instructions = interpolate(gettext('You\'ll be able to create a %s record once the above section is completed.'), [instructionDescription]);
      $('#' + idPrefix + parentId).append(
        '<span class="help-block">' + instructions + '</span>'
      );
    }
  }
}

// logic to hide forms to create new data if data already exists:
// if this is *not* called multiple data items can be created
function hideNewFormsWhenDataExists() {
  // hide "new" forms for any instances where data exists
  $('.repeating-ajax-data-fieldset').each(function() {
    var $fieldset = $(this);
    if ($fieldset.children('.repeating-data').children().length) {
      $fieldset.children('.repeating-ajax-data-row').hide();
    }
  });
}

// logic to show appropriate subform
function revealSelectedBasis() {
  var basis = $('#id_rightsbasis').val()
    , formsets = {
      'Copyright': 'copyright_formset',
      'Statute':   'statute_formset',
      'License':   'license_formset',
      'Policy':    'other_formset',
      'Donor':     'other_formset',
      'Other':     'other_formset'
  }

  // hide all formsets except basis
  for (var key in formsets) {
    if (key != basis && formsets[key]) {
      $('#' + formsets[key]).hide();
    }
  }

  // if basis has a formset, show it
  if (formsets[basis]) {
    $('#' + formsets[basis]).show();
  }

  // hide extra basis field for donor and policy basis
  if (basis == 'Donor' || basis == 'Policy') {
    $('#id_rightsstatementotherrightsinformation_set-0-otherrightsbasis').parent().parent().hide();
  } else {
    $('#id_rightsstatementotherrightsinformation_set-0-otherrightsbasis').parent().parent().show();
    $('#other_rights_notes_label').text(gettext('Note'));
  }

  // relabel certain form fields to be specific to selected basis
  $('#other_documentation_identifier_label').text(interpolate(gettext('%s documentation identifier'), [basis]));

  if (basis == 'Donor') {
    basis = 'Donor agreement';
    $('#other_rights_notes_label').text(interpolate(gettext('%s note'), [basis]));
  } else {
    if (basis == 'Policy') {
      $('#other_rights_notes_label').text(interpolate(gettext('%s note'), [basis]));
    } else {
      $('#other_rights_notes_label').text(gettext('Note'));
    }
  }

  // relabel certain form fields to be specific to selected basis
  $("label[for='id_rightsstatementotherrightsinformation_set-0-otherrightsapplicablestartdate']")
    .text(interpolate(gettext('%s start date'), [basis]));
  $("label[for='id_rightsstatementotherrightsinformation_set-0-otherrightsapplicableenddate']")
    .text(interpolate(gettext('%s end date'), [basis]));
}

// hide the last fieldset, to reduce visual clutter, and add a button to reveal it
function appendRevealButton($list, dataType) {

  if ($list.length > 1) {
    // hide last statute form
    $list.last().hide();

    // make toggle button
    var message = interpolate(gettext('Create new %s?'), [dataType]);
    var $toggleButton = $('<h3 class="btn btn-default" style="float:right">' + message + '</h3>');

    $toggleButton.click(function() {
      $toggleButton.fadeOut();
      $list.last().slideDown();
    });

    // append toggle button to second to last statute form
    $list.last().prev().append($toggleButton).append('<br clear="all"></br>');
  }
}

// setup
$(document).ready(function() {

  // apply input mask to date fields
  Inputmask.extendDefinitions({
    'd': { //basic day - from jquery.inputmask.date.extensions
        validator: "0[1-9]|[12][0-9]|3[01]",
        cardinality: 2,
        prevalidator: [{ validator: "[0-3]", cardinality: 1 }],
        placeholder: 'd'
    },
    'm': { //basic month - from jquery.inputmask.date.extensions
        validator: "0[1-9]|1[012]",
        cardinality: 2,
        prevalidator: [{ validator: "[01]", cardinality: 1 }],
        placeholder: 'm'
    },
    'y': { // modified year - to allow dates beyond 19xx and 20xx
      validator: '\\d\\d\\d\\d',
      cardinality: 4,
      placeholder: 'y'
    }
  });

  $('input[type="text"][name*="date"]').inputmask('y[-m[-d]]');

  // active formset changer
  $('#id_rightsbasis').change(revealSelectedBasis);
  revealSelectedBasis();

  // if a grant has already been made, hide the blank form to create one and
  // offer a button to reveal it
  appendRevealButton($('.grant-fieldset'), 'grant/restriction');

  // use JQuery for this as pure CSS selector isn't IE safe
  $(".grant-fieldset:not(:first)").css('margin-top', '4em');

  // reposition restriction field to inside a modelform
  $('.rights-grant-restrictions').each(function() {
    $($(this).parent().children().first().next().next()).after($(this));
  });

  // establish rightsholder autocomplete
  if ($('#id_rightsholder').length > 0) {
    // lookup rightsholder
    $.get('lookup/rightsholder/' + $('#id_rightsholder').val(), function(data) {
      $('#id_rightsholder').val(data);
    });

    // attach autocomplete
    $("#id_rightsholder").autocomplete({  

      // define callback to format results  
      source: function(req, add){  
 
        // pass request to server  
        $.getJSON("autocomplete/rightsholders", {'text': req.term}, function(data) {  
 
          // create array for response objects  
          var suggestions = [];  
  
          // process response  
          $.each(data, function(i, val){  
            suggestions.push(val);  
          });  

          // pass array to callback  
          add(suggestions);  
        });
      }
    });
  }
});
