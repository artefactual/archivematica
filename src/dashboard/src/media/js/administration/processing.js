$(document).ready(function() {

  var toggleableElementNames = [
    'backup_transfer',
    'quarantine_transfer',
    'normalize_transfer',
    'store_aip'
  ];

  function disableApplicableRadioButtons() {
    for(var index in toggleableElementNames) {
      var elementName = toggleableElementNames[index]
        , relatedRadioButtonName
        , disabled;

      $('[name="' + elementName + '"]').each(function() {
        disabled = ($(this).attr('checked') != 'checked');
        relatedRadioButtonName = elementName + '_toggle';
        $('[name="' + relatedRadioButtonName + '"]').each(function() {
          if (disabled) {
            $(this).attr('disabled', 'true');
          } else {
            $(this).removeAttr('disabled');
          }
        });
      });
    }
  }

  // disable applicable radion buttons on initial page load
  disableApplicableRadioButtons();

  // update disabling when checkboxes are toggled
  $('[type="checkbox"]').change(function() {
    disableApplicableRadioButtons();
  });
});
