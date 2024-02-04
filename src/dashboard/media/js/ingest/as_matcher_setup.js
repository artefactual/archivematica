function atkMatcherInitialize(DIPUUID, objectPaths, resourceData, matches) {
  var matcher = new ATKMatcherView({
    'el':                       $('#as_matcher'),
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
    'confirmButtonCSSId':       'match_confirm_button',
    'cancelButtonCSSId':        'match_cancel_button',
    'DIPUUID':                  DIPUUID,
    'objectPaths':              objectPaths,
    'resourceData':             resourceData,
    'initialMatches':           matches
 });

  matcher.render();
}
