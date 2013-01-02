$(document).ready(function() {
  var ajaxChildDataUrl = '/filesystem/children/'
    , ajaxSelectedDirectoryUrl = '/administration/storage/json/'
    , ajaxAddDirectoryUrl = '/administration/storage/json/'
    , ajaxDeleteDirectoryUrl = '/administration/storage/delete/json/'
    , picker = new DirectoryPickerView({
      el:               $('#explorer'),
      levelTemplate:    $('#template-dir-level').html(),
      entryTemplate:    $('#template-dir-entry').html(),
      ajaxChildDataUrl: ajaxChildDataUrl,
      ajaxSelectedDirectoryUrl: ajaxSelectedDirectoryUrl,
      ajaxAddDirectoryUrl: ajaxAddDirectoryUrl,
      ajaxDeleteDirectoryUrl: ajaxDeleteDirectoryUrl
  });

  picker.structure = {
    'name': 'var',
    'parent': '',
    'children': []
  };

  picker.render();
  picker.updateSelectedDirectories();
});
