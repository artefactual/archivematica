'use strict';

import 'angular';
import 'angular-mocks/angular-mocks';

var context = require.context('./unit', true, /Spec\.js$/); //make sure you have your directory and regex test set correctly!
context.keys().forEach(context);
