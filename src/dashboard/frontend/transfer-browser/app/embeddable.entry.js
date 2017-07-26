// styles
import './css/browser.css';
import 'angular-tree-control/css/tree-control.css';
import 'angular-tree-control/css/tree-control-attribute.css';

// Angular must be available to cache the partials
import 'angular';

// partials
import 'ng-cache?prefix=[dir]!./front_page/content.html';

// Finally, import the main entry point
import './app.js';
