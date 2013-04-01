$(document).ready(function() {

  var toggleableBooleanElementNames = [
    'backup_transfer',
    'quarantine_transfer',
    'normalize_transfer',
    'store_aip'
  ];

  function disableApplicableBooleanSelects() {
    for(var index in toggleableBooleanElementNames) {
      var elementName = toggleableBooleanElementNames[index]
        , relatedBooleanSelectName
        , disabled;

      $('[name="' + elementName + '"]').each(function() {
        disabled = ($(this).attr('checked') != 'checked');
        relatedBooleanSelectName = elementName + '_toggle';
        $('[name="' + relatedBooleanSelectName + '"]').each(function() {
          if (disabled) {
            $(this).attr('disabled', 'true');
          } else {
            $(this).removeAttr('disabled');
          }
        });
      });
    }
  }

  // disable applicable boolean selects on initial page load
  disableApplicableBooleanSelects();

  var toggleableSelectElementNames = [
    'create_sip_enabled',
    'select_format_id_tool_enabled',
    'normalize_enabled',
    'compression_algo_enabled',
    'compression_level_enabled',
    'store_aip_location_enabled'
  ];

  function disableApplicableSelects() {
    for(var index in toggleableSelectElementNames) {
      var elementName = toggleableSelectElementNames[index]
        , relatedSelectName
        , disabled;

     $('[name="' + elementName + '"]').each(function() {
       disabled = ($(this).attr('checked') != 'checked');
       relatedSelectName = elementName.replace('_enabled', '');
       $('[name="' + relatedSelectName + '"]').each(function() {
         if (disabled) {
           $(this).attr('disabled', 'true');
         } else {
           $(this).removeAttr('disabled');
         }
       });
     });
    }
  }

  // disable applicable selects on initial page load
  disableApplicableSelects();

  // update disabling when checkboxes are toggled
  $('[type="checkbox"]').change(function() {
    disableApplicableBooleanSelects();
    disableApplicableSelects();
  });
});
