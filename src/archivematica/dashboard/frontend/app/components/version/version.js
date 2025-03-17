'use strict';

angular.module('dashboard.version', [
  'dashboard.version.interpolate-filter',
  'dashboard.version.version-directive'
])

.value('version', '0.1');
