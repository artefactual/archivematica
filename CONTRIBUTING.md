## Style

Archivematica uses the Python [PEP8](https://www.python.org/dev/peps/pep-0008/) community style guidelines.
Newly-written code should conform to PEP-8 style.
PEP8 is a daunting document, but there are very good linters available that you can run to check style in your code.
The Archivematica development uses [Sublime Text](sublimetext.com/) with the [SublimeLinter-flake8](https://github.com/SublimeLinter/SublimeLinter-flake8) plugin, which automatically scans your code and displays any style notes inline.
Similar plugins are available for other editors, or the [flake8](https://pypi.python.org/pypi/flake8) tool can be used at the command line.

### Some extra notes

A few additional stylistic preferences might not get flagged by linters:

* Don't use variable or parameter names that shadow builtin functions and types.
  For example, don't name a variable "file".
  (Unfortunately, Python uses many useful names for its builtin types and functions.)
* Most of the time, prefer importing specific names from modules instead of importing the entire module.
  This makes it easier to tell at the top of a file what is being used from its dependencies.
  For example:

```python
# Good

from main.models import File

f = File.objects.get(uuid="something")

# Bad

import main.models

f = models.File.objects.get(uuid="something")
```

### Exceptions

Archivematica ignores the PEP8 rule concerning line length; lines longer than 80 characters are acceptable.
This is error "501", for the purposes of silencing it in flake8 or other linting tools.

### Working with legacy code

Older portions of the Archivematica codebase don't always conform to PEP8 rules; the codebase is slowly transitioning to PEP8 style.
Don't worry about rewriting existing code to conform to the guidelines when adding new code; however, if possible, it's great if your new code does conform.

When working in sections of code that don't conform to PEP8, it's okay to relax a few PEP8 rules in order to match existing code.
In particular:

* When modifying an existing function which uses camelCase variables or parameters, it's okay to make your new variables/parameters camelCase to match.
* When adding new functions to a module or class that uses camelCase naming, it's okay to make your new function and its parameters camelCase to match.
  Try to use snake_case internally, however.

## Documentation

New classes and functions should generally be documented using [docstrings](https://en.wikipedia.org/wiki/Docstring#Python); these help in providing clarity, and can also be used to generate API documentation later.
Generally any function which isn't obvious (any function longer than a line or two) should have a docstring.
When in doubt: document!
Generally, prefer using [Sphinx-style docstrings](http://pythonhosted.org/an_example_pypi_project/sphinx.html#function-definitions).
