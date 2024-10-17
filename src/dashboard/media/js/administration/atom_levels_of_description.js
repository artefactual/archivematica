/*
 *
 * Fetch levels of description
 *
 */

function fetchAtomLevelsOfDescription(url) {
  $.ajax({
    url: url,
    type: 'GET',
    async: false,
    cache: false,
    success: function(results) {
      window.location.reload();
    },
    error: function() {
      alert(gettext('Error retrieving levels of description from AtoM'));
    }
  });
}

/*
 *
 * Manage levels of description
 *
 */

function submitAtomLevelOperation(operation, id) {
  $('#level_operation').val(operation);
  $('#level_id').val(id);
  $('#level_form').submit();
}

function promoteLevel(id) {
  submitAtomLevelOperation('promote', id);
}

function demoteLevel(id) {
  submitAtomLevelOperation('demote', id);
}

function deleteLevel(id) {
  if (confirm(gettext('Are you sure you want to delete this level of description?'))) {
    submitAtomLevelOperation('delete', id);
  }
}
