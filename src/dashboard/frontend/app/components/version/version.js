'use strict';

angular.module('appraisalTab.version', [
  'appraisalTab.version.interpolate-filter',
  'appraisalTab.version.version-directive'
])

.value('version', '0.1');
