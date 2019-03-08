# Archivematica dashboard frontend components

Getting started
---------------

This application uses npm to manage its dependencies; dependencies used in the browser are bundled together using [webpack](https://webpack.github.io).
When first installing or updating the application, run `npm install` in the terminal to install all dependencies and build a copy of the bundled app.

Running a server
----------------

This application currently can't be run standalone; it can only be run as a part of an Archivematica installation, since it depends on some external JavaScript and some backend APIs.

Application architecture
------------------------

### Structure

This application is structured according to the guidelines in the [community Angular style-guide](https://github.com/johnpapa/angular-styleguide#application-structure).

### Separation of concerns

Each individual feature of the application should be developed as a separate scope with its own controller.
Scopes should never be nested in partials.
Each controller should contain as little logic as possible; controllers are primarily used to assign scope variables and call methods on other objects.
The majority of the application's logic is intended to be held in directives, filters, and services.

### Sharing data

Since each controller scope is separate, data can't be directly shared between controllers.
Instead, data sharing occurs using Angular *service* objects.
Each service object is a singleton object which can have both instance methods and properties; bindable attributes of a service should be assigned to properties, while methods should only be used for getters whose values do not need to be watched for changes.

This example, based on the transfer tree/report pane workflow, explains how it works.

One controller, the `TreeController`, contains a transfer tree UI that allows the user to select elements.
Selected elements are then filtered and displayed within the scope of another controller, ReportController.
Since the two controllers are completely separate scopes, we need an intermediary to share data between the two of them; to do that, we create a `SelectedFiles` service which has a method to add and remove entries, and a bindable property called `selected` which simply lists all selected files.

First, in the TreeController, we inject the SelectedFiles service, and add or remove objects from it every time we've detected a change to the user's selection.

```js
angular.module('treeController', []).controller('TreeController', function(Tree, SelectedFiles) {
  Tree.onClick(function(element) {
    if (element.isSelected) {
      SelectedFiles.add(element);
    } else {
      SelectedFiles.remove(element.id);
    }
  });
});
```

Then, in ReportController, we assign the service object to a scope variable.
We assign the service object itself and not its property so that the digest loop can detect changes to the property.

```js
angular.module('reportController', []).controller('ReportController', function($scope, SelectedFiles) {
  $scope.records = SelectedFiles;
});
```

Finally, in the template, we can now iterate over the contents of the `records` scope variable and have those be updated with every change made to `SelectedFiles.selected`:

```html
<div ng-controller='ReportController'>
  <div ng-repeat='record in records.selected'>{{ record }}</div>
</div>
```

Testing
-------

Unit tests are written using the [Jasmine](https://jasmine.github.io/2.3/introduction.html) test framework.
This section will give a high-level overview of this application's tests, but is not meant to replace the Jasmine documentation.

Unit tests can be found in the "tests/unit" directory in the root of the application.
Each distinct feature being tested should be given its own "spec" file; for example, the spec for the "facet" feature is named "facetSpec.js".

### Running tests

Tests can be run inside the root directory of the application by running `npm test`.
By default, tests are run in Chrome; Chrome must be installed to run the tests.

### Structure

Each test file is treated as a *specification* (or spec) of an aspect of the application's functionality; each test is mean to be readable as a specification for how the application should behave.
Each spec is comprised of a `describe` block, which describes an individual feature; that `describe` block then contains `it` blocks, which are used to define individual aspects of that feature.
For example, a simple test file could look like this:

```js
describe('MyFeature', function() {
  it('should be able to do this specific thing', function() {
    # test logic goes here
  });
});
```

At the top of each `describe` block, there should be one or more `beforeEach` statements to set up the environment for each test.
At a minimum, it's necessary to load the appropriate module being tested, for example:

```js
beforeEach(module('myFeatureModule'));
```

### Mocking REST calls

Some tests call code which performs asynchronous REST calls; these require extra handling in order to ensure the data is fetched and the test conditions execute before the test function completes.
These REST calls can be mocked using Angular's `_$httpBackend_` feature, which allows specific REST requests to be mocked and responses to be returned at a predictable point of time.

REST calls are mocked in a `beforeEach` function within the `describe` block.
Here's a simple example:

```js
beforeEach(angular.mock.inject(function(_$httpBackend_) {
  _$httpBackend_.when('GET', '/some/url').respond(['some', 'response']);
}));
```

`angular.mock.inject` is used to provide access to the `_$httpBackend_` service.
The `when` method defines a route to intercept, and the `respond` method is used to specify the object to be returned when that route is accessed using the specified HTTP verb.

After mocking the route in a `beforeEach` function, each test that calls one of the mocked routes needs to flush the pending requests to ensure that the tests receive a response before the test method ends.
For example:

```js
it('should be able to fetch a specific file', inject(function(_$httpBackend_, File) {
  File.get('25bb5793-aee9-4303-af99-7bb4ec256bc0').then(function(file) {
    expect(file.id).toEqual('25bb5793-aee9-4303-af99-7bb4ec256bc0');
  });
  _$httpBackend_.flush();
}));
```

Because the result from calling `File.get` is a *promise*, it's only executed when a response is received from the server - so it probably won't actually be executed before the test completes.
Calling `_$httpBackend_.flush()` ensures that the mocked response is immediately returned, and the promise returned by `File.get` immediately resolves.


Using Babel
-----------

All of the source code in this project is processed through [Babel](https://babeljs.io), which allows code to be written using ES2015, the latest version of the JS standard which isn't yet fully supported by web browsers.
When a bundle is written, Babel transpiles the code into browser-compatible JavaScript.

Here's a quick overview of new ES2015 features and how they're used in this project; a more complete guide to new features can be found [in the Babel documentation](https://babeljs.io/docs/learn-es2015/).

### Arrow functions

ES6 includes a second function syntax, the arrow function.
It looks like this:

```js
arg => {
  // function body
}
```

Or:

```js
(arg1, arg2) => {
  // function body
}
```

This form has two main advantages:

#### Callback arguments

Arrow functions can only be used as anonymous function expressions, and look cleaner when passed as a literal argument to a function.
Compare:

```js
[1, 2].forEach(function(element) {
  console.log(element);
})

[1, 2].forEach(element => {
  console.log(element);
})
```

With one-line arrow functions, it's also possible to omit the braces; in this case there's implicit return and the value of the statement is always returned.
This is useful to write concise `map` statements, for example:

```js
[1, 2, 3].map(n => `Value is: ${n}`) //=> [ 'Value is: 1', 'Value is: 2', 'Value is: 3' ]
```

#### `this` scope

Arrow functions inherit `this` from the calling scope.

Traditional JS functions have their own scope for `this`; in strict mode `this` is undefined for unbound functions, and in non-strict mode it refers to the global object.
This makes using function expressions as callbacks in an OO context really confusing, and is why this has been a common idiom:

```js
var self = this;
Transfer.get().then(function(response) {
  self.data = response;
});
```

Arrow functions don't define their own `this`; they inherit it from the parent scope. Here's an example from the new transfer browser:

```js
this.source_location_browser.list().then(locations => {
  locations.forEach(location => {
    this.source_locations[location.uuid] = location;
  });
  // preselect the first location, and browse its contents
  this.source_location = locations[0].uuid;
  this.browse(this.source_location);
}, error => {
  this.source_locations = previous_locations;
});
```

In order to avoid confusion, use the following rule:

* Functions which are bound to a name via the `function name()` syntax remain as traditional functions.
* Functions which are assigned to variables or which are passed as literals to function calls are written as arrow functions, even if `this` is not used.

### `let` variable definition

JavaScript's `var` statement isn't block-scoped; instead it's scoped to the enclosing function, regardless of location.
This means that it's possible (by accident) to override an existing variable in a way you might not expect to work:

```js
var i = 255;
for (var i in [1, 2, 3]) {
  // ...
}
i // => is now 3
```

For backwards compatibility, `var`'s scoping remains the same, but a new variable definition statement has been added: `let`.
`let` is block-scoped:

```js
var i = 255;
for (let i in [1, 2, 3]) {
  // ...
}
i // => is still 255
```

For consistency, define all variables as `let` unless the scoping of `var` is needed.

### Template strings

Before ES2015, JavaScript didn't have string interpolation or format strings.
As a result, including values in strings tends to look pretty verbose:

```js
var message = 'Oh no! Something terrible happened with file "' + file.title + '"!';
```

ES2015 adds a new string type, the [template string](https://babeljs.io/docs/learn-es2015/#template-strings); this string type uses backticks instead of quotes, and supports string interpolation using the bash-like `${}` syntax:

```js
let message = `Oh no! Something terrible happened with file "${file.title}"`;
```

Prefer using template strings over catting multiple strings together, unless the latter is shorter or easier to read.

### Classes

ES6 provides support for classes with constructors, alongside existing prototype-based objects.
It turns out to be quite easy to define Angular services and controllers as objects, and this makes some stuff quite a bit cleaner.
For example, instance methods on controller objects can be easily referenced from templates, which obviates the need to assign functions to properties.

Here's a good guide that covers over how this works: http://angular-tips.com/blog/2015/06/using-angular-1-dot-x-with-es6-and-webpack/

### Modules

ES6 provides support for real modules with their own separate namespaces.
They're somewhat similar to Python modules, except that values are exported explicitly rather than every defined name being automatically importable.
For example, instead of the `angular` name being globally available, we need to obtain a reference to it by importing it:

```js
import angular from 'angular';
```

This has a few implications:

* Write every file as a module, and export appropriate values if there's something to export. This behaves a bit strangely in the context of Angular modules (since Angular has its own module system which defines modules via side effects of `angular.module` calls), but works very well for things like helper functions and classes.
* Within modules, it's not necessary to worry about polluting the global object: variables are no longer being magically attached to `window`. This means IIFEs are unnecessary.
* Make sure that all dependencies get imported in the places they're used, instead of relying on global `<script>` tags in the HTML page.

Prefer using the ES2015 `import` syntax over the `require` function when writing code.


Translations
------------

This process has not been wired with Webpack yet.

You need to install `angular-gettext-cli`. It is not an application dependency,
it is a build dependency.

    npm install -g angular-gettext-cli

Extract messages:

    # Attention, this is going to include the dist file - please remove before you run this command!
    angular-gettext-cli --files "./app/**/*.+(js|html)" --dest "./app/locale/extract.pot" --marker-name "i18n"

Merge extracted messages with existing language files:

    cd app/locale
    msgmerge -qUN translations.es.po extract.pot

Compile messages:

    angular-gettext-cli --compile --files "app/locale/*.po" --dest "app/locale/translations.json" --format "json" --module "dashboard"

The contents of `app/locale` should be tracked in git.
