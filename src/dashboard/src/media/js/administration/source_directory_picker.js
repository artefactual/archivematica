$(document).ready(function() {
  var ajaxChildDataUrl = '/filesystem/children/'
    , picker = new DirectoryPickerView({
      el:               $('#explorer'),
      levelTemplate:    $('#template-dir-level').html(),
      entryTemplate:    $('#template-dir-entry').html(),
      ajaxChildDataUrl: ajaxChildDataUrl
  });

  picker.structure = {
    'name': 'home',
    'parent': '',
    'children': []
  };

  picker.render();
  picker.updateSources();
});
