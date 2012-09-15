function repeatingDocumentationIdentifierRecordsSchema(dataType) {
  var schema = {};

  schema[dataType + 'documentationidentifiertype'] = {
    'label': 'Type',
    'type': 'input'
  };

  schema[dataType + 'documentationidentifiervalue'] = {
    'label': 'Value',
    'type': 'input'
  };

  schema[dataType + 'documentationidentifierrole'] = {
    'label': 'Role',
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
  setUpRepeatingField('copyrightnotes_', parentId, 'Copyright Note', schema, '/formdata/copyrightnote/' + parentId + '/', true);
}

function setUpRepeatingCopyrightDocumentationIdentifierRecords(parentId) {
  var schema = repeatingDocumentationIdentifierRecordsSchema('copyright');
  setUpRepeatingField('copyrightdocidfields_', parentId, 'Copyright Documentation Identifier', schema, '/formdata/copyrightdocumentationidentifier/' + parentId + '/', true);
}

function setUpRepeatingStatuteDocumentationIdentifierRecords(parentId) {
  var schema = repeatingDocumentationIdentifierRecordsSchema('statute');
  setUpRepeatingField('statutedocidfields_', parentId, 'Statute Documentation Identifier', schema, '/formdata/statutedocumentationidentifier/' + parentId + '/', true);
}

function setUpRepeatingStatuteNotesRecords(parentId) {
  var schema = repeatingNotesRecordsSchema('statute');
  setUpRepeatingField('statutenotes_', parentId, 'Statute Note', schema, '/formdata/statutenote/' + parentId + '/', true);
}

function setUpRepeatingLicenseDocumentationIdentifierRecords(parentId) {
  var schema = repeatingDocumentationIdentifierRecordsSchema('license');
  setUpRepeatingField('licensedocidfields_', parentId, 'License Documentation Identifier', schema, '/formdata/licensedocumentationidentifier/' + parentId + '/', true);
}

function setUpRepeatingOtherRightsDocumentationIdentifierRecords(parentId) {
  var schema = repeatingDocumentationIdentifierRecordsSchema('otherrights');
  setUpRepeatingField('otherrightsdocidfields_', parentId, 'Other Rights Documentation Identifier', schema, '/formdata/otherrightsdocumentationidentifier/' + parentId + '/', true);
}

function setUpRepeatingOtherRightsNotesRecords(parentId) {
  var schema = {
    'otherrightsnote': {},
  };
  setUpRepeatingField('otherrightsnotes_', parentId, 'Other Rights Note', schema, '/formdata/otherrightsnote/' + parentId + '/', true);
}

function setUpRepeatingLicenseNotesRecords(parentId) {
  var schema = {
    'licensenote': {},
  };
  setUpRepeatingField('licensenotes_', parentId, 'License Note', schema, '/formdata/licensenote/' + parentId + '/', true);
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
  setUpRepeatingField('rightsrestrictions_', parentId, 'Restriction', schema, '/formdata/rightsrestriction/' + parentId + '/', true);
}

function setUpRepeatingRightsGrantedNotesRecords(parentId) {
  var schema = {
    'rightsgrantednote': {},
  };
  setUpRepeatingField('rightsfields_', parentId, 'Rights Granted Note', schema, '/formdata/rightsnote/' + parentId + '/', true);
}

// repeating child field to a formset bound to existing data
function setUpRepeatingField(idPrefix, parentId, description, schema, url, noCreation) {
  var rights = new RepeatingDataView({
    el: $('#' + idPrefix + parentId),
    description: description,
    parentId: parentId,
    schema: schema,
    url: url,
    noCreation: noCreation
  });
  rights.render();

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
      instructions = "You'll be able to create a "
        + instructionDescription
        + " record once the above section is completed.";

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
    $('#other_rights_notes_label').text('Note');
  }

  // relabel certain form fields to be specific to selected basis
  $('#other_documentation_identifier_label').text(basis + ' documentation identifier:');

  if (basis == 'Donor') {
    basis = 'Donor agreement';
    $('#other_rights_notes_label').text(basis + ' note');
  } else {
    if (basis == 'Policy') {
      $('#other_rights_notes_label').text(basis + ' note');
    } else {
      $('#other_rights_notes_label').text('Note');
    }
  }

  // relabel certain form fields to be specific to selected basis
  $("label[for='id_rightsstatementotherrightsinformation_set-0-otherrightsapplicablestartdate']")
    .text(basis + ' start date');
  $("label[for='id_rightsstatementotherrightsinformation_set-0-otherrightsapplicableenddate']")
    .text(basis + ' end date');
}

// hide the last fieldset, to reduce visual clutter, and add a button to reveal it
function appendRevealButton($list, dataType) {

  if ($list.length > 1) {
    // hide last statute form
    $list.last().hide();

    // make toggle button
    var $toggleButton = $('<h3 class="btn" style="float:right">Create new ' + dataType + '?</h3>');

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
  $.extend($.inputmask.defaults.definitions, {
    'y': {
      'validator': '[012]\\d\\d\\d',
      'cardinality': 4,
      'prevalidator': [
        { 'validator': '[012]', 'cardinality': 1 }
      ]
    }
  });

  $('input[type="text"][name*="date"]').inputmask('y/m/d');

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
