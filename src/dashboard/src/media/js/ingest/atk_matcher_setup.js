function atkMatcherInitialize(DIPUUID, objectPaths, resourceData) {
  var matcher = new ATKMatcherView({
    'el':                       $('#atk_matcher'),
    'matcherLayoutTemplate':    $('#matcher-layout-template').html(),
    'objectPaneCSSId':          'object_pane',
    'objectPaneSearchCSSId':    'object_pane_search',
    'objectPanePathsCSSId':     'object_pane_paths',
    'objectPathTemplate':       $('#object-path-template').html(),
    'resourcePaneCSSId':        'resource_pane',
    'resourcePaneSearchCSSId':  'resource_pane_search',
    'resourcePaneItemsCSSId':   'resource_pane_items',
    'resourceItemTemplate':     $('#resource-item-template').html(),
    'matchPaneCSSId':           'match_pane',
    'matchPanePairsCSSId':      'match_pane_pairs',
    'matchItemTemplate':        $('#match-item-template').html(),
    'matchButtonCSSId':         'match_button',
    'saveButtonCSSId':          'match_save_button',
    'confirmButtonCSSId':       'match_confirm_button',
    'cancelButtonCSSId':        'match_cancel_button',
    'DIPUUID':                  DIPUUID,
    'objectPaths':              objectPaths,
    'resourceData':             resourceData
 });

  matcher.render();
}
