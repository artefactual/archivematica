// styles
import './app.css';
import 'font-awesome/css/font-awesome.min.css';
import './vendor/angular-tree-control/css/tree-control.css';
import './vendor/angular-tree-control/css/tree-control-attribute.css';

// Angular must be available to cache the partials
import 'angular';

// partials
import 'ng-cache?prefix=[dir]!./analysis/analysis.html';
import 'ng-cache?prefix=[dir]!./archivesspace/form.html';
import 'ng-cache?prefix=[dir]!./examine_contents/examine_contents.html';
import 'ng-cache?prefix=[dir]!./examine_contents/file_info.html';
import 'ng-cache?prefix=[dir]!./front_page/content.html';
import 'ng-cache?prefix=[dir]!./preview/preview.html';
import 'ng-cache?prefix=[dir]!./report/format.html';
import 'ng-cache?prefix=[dir]!./report/tags.html';
import 'ng-cache?prefix=[dir]!./ui/minimize-bar.html';
import 'ng-cache?prefix=[dir]!./ui/minimize-panel.html';
import 'ng-cache?prefix=[dir]!./visualizations/formats_by_files.html';
import 'ng-cache?prefix=[dir]!./visualizations/formats_by_size.html';
import 'ng-cache?prefix=[dir]!./visualizations/visualizations.html';

// Finally, import the main entry point
import './app.js';
