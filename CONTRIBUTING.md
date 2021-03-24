# Contributing

Thank you for considering a contribution to Archivematica!
This document outlines the change submission process for Archivematica, along
with our standards for new code contributions. Following these guidelines helps
us assess your changes faster and makes it easier for us to merge your
submission!

There are many ways to contribute: writing tutorials or blog posts about your
experience, improving the [documentation], submitting bug reports, answering 
questions on the [mailing list], or writing code which can be incorporated into 
Archivematica itself.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Submitting bugs](#submitting-bugs)
- [Submitting enhancement ideas](#submitting-enhancements)
- [Submitting code changes](#submitting-code-changes)
  - [Getting started](#getting-started)
  - [When to submit code for review?](#when-to-submit-code-for-review)
  - [Opening the pull request](#opening-the-pull-request)
  - [Discussion](#discussion)
  - [Cleaning up the commit history](#cleaning-up-the-commit-history)
  - [Stalled pull requests](#stalled-pull-requests)
- [Contributor's Agreement](#contributors-agreement)
  - [Why do I have to sign a Contributor's Agreement?](#why-do-i-have-to-sign-a-contributors-agreement)
  - [How do I send in an agreement?](#how-do-i-send-in-an-agreement)
- [Contribution standards](#contribution-standards)
  - [Style](#style)
    - [Some extra notes](#some-extra-notes)
    - [Exceptions](#exceptions)
    - [Working with legacy code](#working-with-legacy-code)
  - [Documentation](#documentation)
  - [Tests](#tests)
  - [Commit History](#commit-history)
    - [Commits should be specific and atomic](#commits-should-be-specific-and-atomic)
    - [Every commit should work](#every-commit-should-work)
    - [Commit summaries should be concise](#commit-summaries-should-be-concise)
    - [Commit messages should be as detailed as they need to be (and no more)](#commit-messages-should-be-as-detailed-as-they-need-to-be-and-no-more)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Submitting bugs

If you find a security vulnerability, do NOT open an issue. Email
info@artefactual.com instead.

Issues can be filed using GitHub Issues in the [Archivematica Issues repo]. 
It is recommended to file issues there rather than in any of the 
Archivematica-related code repositories. Artefactual staff also use GitHub 
issues for any work they do on the Archivematica project.

You can also post in our [user] mailing list. A post to the mailing list is 
always welcome, especially if you're unsure if it's a bug or a local problem!

Useful questions to answer if you're having problems include:

* What version of Archivematica and the Storage Service are you using?
* How was Archivematica installed? Package install, Ansible, etc?
* Was this a fresh install or an upgrade?
* What did you do to cause this bug to happen?
* What did you expect to happen?
* What did you see instead?
* Can you reproduce this reliably?
* If a specific Job is failing, what output did it produce? This is available
  by clicking on the gear icon.

## Submitting enhancement ideas

Similar to submitting bugs, you are welcome to submit ideas for enhancements or
new features in the [Archivematica Issues repo]. This is  also where Artefactual 
staff record upcoming enhancements when they have been sponsored for inclusion
either by Artefactual Systems or by a client.

Please feel free also to use the [Issues repo wiki] as a space for gathering and 
collaborating on ideas. If you are not already a member of the 
Archivematica repo (required for editing the wiki), file an issue there with
the title "Request membership."

## Submitting code changes

Every new feature and bugfix to a project is expected to go through code
review before inclusion. This applies both to developers at Artefactual and to
outside contributors.

Here's an outline of the contribution process:

1. File an issue in the
   [Archivematica Issues repo].
2. Fork the Artefactual project on GitHub, and commit your changes to a branch
   in your fork.
3. Open a pull request.
4. Back and forth discussion with developers on the branch.
5. Make any changes suggested by reviewers.
6. Repeat 3 and 4 as necessary.
7. Clean up commit history, if necessary.
8. Sign a Contributor's Agreement, if you haven't already.
9. Your branch will be merged!

### Permalinks

Issues can be enhanced by using GitHub's permalink features for [files] and
[code snippets].
Permalinks allow users to look back over old issues and pull requests and see
what the code looked like at a certain point in time. This can be useful where
lines may now have been added or removed but the topic of the conversation may
still be relevant or of interest to the reader.

### Getting started

So you have something to contribute to an Artefactual project. Great!

To install Archivematica, see our [development installation] instructions.

Artefactual uses [GitHub]'s pull request feature for code review. Every change 
being submitted to an Artefactual project should be
submitted as a pull request to the appropriate repository. A branch being
submitted for code review should contain commits covering a related section of
code. Try not to bundle unrelated changes together in one branch; it makes
review harder.

If you're not familiar with forking repositories and creating branches in
GitHub, consult their [guide].

### When to submit code for review?

Your code doesn't have to be ready yet to submit for code review! You should
submit a branch for code review as soon as you want to get feedback on it.
Sometimes, that means submitting a feature-complete branch, but sometimes that
means submitting an early WIP in order to get feedback on direction. Don't be
shy about submitting early.

### Opening the pull request

GitHub has an [excellent] guide on using the pull request feature.

### Discussion

Discussion on pull requests is usually a back and forth process. Don't feel
like you have to make every change the reviewer suggests; the pull request is
a great place to have in-depth conversation on the issue.

Do make use of GitHub's line comment feature!

![Line comment]

By viewing the "Files changed", you can leave a comment on any line of the
diff. This is a great way to scope discussion to a particular part of a diff.
Any discussion you have in a specific part of the diff will also be
automatically hidden once a change is pushed that addresses it, which helps
keep the pull request page clear and readable.

Anyone can participate in code review discussions. Feel free to jump in if you
have something to contribute on another pull request, even if you're not the
one who opened it.

For more details about code review in particular, look at our
[code review guidelines].

### Cleaning up the commit history

Once code review is finished or nearly finished, and no further development is
planned on the branch, the branch's commit history should be cleaned up.
You can alter the commit history of a branch using git's powerful
[interactive rebase feature].

### Stalled pull requests

Pull requests that have been inactive for 60 days will be closed and properly
tagged using the "stalled" label. At that point, we prefer to continue the
discussion under the original GitHub issue that should be linked from the pull
request.

## Contributor's Agreement

In order for the Archivematica development team to accept any patches or code
commits, contributors must first sign this [Contributor's Agreement].
The Archivematica contributor's agreement is based almost verbatim on the
[Apache Foundation]'s individual [contributor license].

If you have any questions or concerns about the Contributor's Agreement,
please email us at agreement@artefactual.com to discuss them.

### Why do I have to sign a Contributor's Agreement?

One of the key challenges for open source software is to support a collaborative
development environment while protecting the rights of contributors and users 
over the long-term.
Unifying Archivematica copyrights through contributor agreements is the best way
to protect the availability and sustainability of Archivematica over the 
long-term as free and open-source software.
In all cases, contributors who sign the Contributor's Agreement retain full 
rights to use their original contributions for any other purpose outside of 
Archivematica, while enabling Artefactual Systems, any successor organization 
which may eventually take over responsibility for Archivematica, and the wider 
Archivematica community to benefit from their collaboration and contributions 
in this open source project.

[Artefactual Systems] has made the decision and has a proven track record of 
making our intellectual property available to the community at large.
By standardizing contributions on these agreements the Archivematica 
intellectual property position does not become too complicated.
This ensures our resources are devoted to making our project the best they can 
be, rather than fighting legal battles over contributions.

### How do I send in an agreement?

Please read and sign the [Contributor's Agreement] and email it to 
agreement@artefactual.com.

Alternatively, you may send a printed, signed agreement to:

    Artefactual Systems Inc.
    201 - 301 Sixth Street
    New Westminster BC  V3L 3A7
    Canada

## Contribution standards

### Style

Archivematica uses the Python [PEP8] community style guidelines. Newly-written 
code should conform to PEP-8 style. PEP8 is a daunting document, but there are 
very good linters available that you can run to check style in your code.

* The [Black] tool formats the code automatically. The output is deterministic 
  for any given input. Editor integration is possible.

* The [flake8] tool checks for style problems as well as errors and complexity. 
  It can be used at the command line or as a plugin in your preferred text 
  editor/IDE. The Archivematica [continuous integration system] will currently 
  check code for compliance against flake8.

We have integrated these tools with our CI, i.e. pull requests will fail to
build when the tools above report errors.

Additionally [Pylint] is used by developers internally at Artefactual to 
highlight other potential areas of improvement during code-review.

#### Some extra notes

A few additional stylistic preferences might not get flagged by linters:

* Don't use variable or parameter names that shadow builtin functions and
  types. For example, don't name a variable "file". (Unfortunately, Python uses
  many useful names for its builtin types and functions.)
* Sort imports alphabetically within their grouping to reduce duplicate
  imports.

#### Exceptions

Archivematica ignores the PEP8 rule concerning line length; lines longer than
80 characters are acceptable.

**NB.** This is error "501", for the purposes of silencing it in flake8 or
other linting tools.

#### Working with legacy code

Older portions of the Archivematica codebase don't always conform to PEP8
rules; the codebase is slowly transitioning to PEP8 style. Don't worry about
rewriting existing code to conform to the guidelines when adding new code;
however, if possible, it's great if your new code does conform.

When working in sections of code that don't conform to PEP8, it's okay to relax
a few PEP8 rules in order to match existing code. In particular:

* When modifying an existing function which uses camelCase variables or
  parameters, it's okay to make your new variables/parameters camelCase to
  match.
* When adding new functions to a module or class that uses camelCase naming,
  it's okay to make your new function and its parameters camelCase to match.
  Try to use snake_case internally, however.

You should try to write Python 2 / Python 3 compatible code where possible.
Using `from __future__ import print_function, division, absolute_import` will
help with this. Some libraries run in Python 2 and Python 3 already; this
behaviour should be maintained.

### Documentation

New classes and functions should generally be documented using
[docstrings]; these help in providing clarity, and can also be used to generate 
API documentation later. Generally any function which isn't obvious 
(any function longer than a line or two) should have a docstring. 
When in doubt: document! Python's [PEP 257] document provides a useful
guideline for docstring style. Generally, prefer using 
[Sphinx-compatible docstrings]. More [examples] and [attributes to use] can
be found on the Sphinx website.

### Tests

New code should also have unit tests. Tests are written in [unittest] style 
and run with [py.test]. For tests requiring the Django ORM, we use the 
Django-provided[TestCase], which extends `unittest.TestCase`.

Tests are found in the `tests` directory, a sibling of the directory containing
the code. `test_foo.py` contains tests for `foo.py`. For clarity, group tests
for the same function and similar tests into the same class within that file.
This will also allow you to share setup and teardown code.

If you are testing code that makes HTTP requests, using [VCR.py] is highly 
recommended. It should already be a development dependency.

### Commit History

A clean commit history makes it easier to see what changes are related, and why
there were made. It makes reviewing code easier, and spelunking in the codebase
to find why a change was made more rewarding. The following few criteria help
outline what makes for a clean commit history:

#### Commits should be specific and atomic

Any single commit should cover a specific change. That change might span
multiple files, but it shouldn't introduce multiple distinct functional changes
unless it's impossible to separate those changes from each other. It's okay
(and normal!) for a branch that makes a lot of changes to consist of many small
commits, each of which makes individual small changes. This makes it easier to
revert individual commits from a branch, and also makes it easier to isolate
the commit that caused a particular bug with git-blame.

In development, it's common to introduce a change with a commit and then
introduce multiple other commits with small fixes for that change. When getting
ready for merging, those commits should all be squashed together.

#### Every commit should work

No individual commit should put the software in a broken state. It's fine for
code to go unused (because the feature it's been introduced for isn't there
yet), but no new functional issues should be introduced by a given commit.
This ensures that reverting any individual commit from the branch is safe, and
that git-bisect stays reliable for tracking down bugs.

### Commit messages

The Archivematica project follows Chris Beams' guidelines on
[How to Write a Git Commit Message], and specifically the
[seven rules of a great Git commit message]:

1. Separate subject from body with a blank line
2. Limit the subject line to 50 characters
3. Capitalize the subject line
4. Do not end the subject line with a period
5. Use the imperative mood in the subject line
6. Wrap the body at 72 characters
7. Use the body to explain what and why vs. how

#### Commit summaries should be concise

The commit summary (the first line of a commit message) should be short and
clear. Usually, the first line of the commit message should be no more than 50
characters. Since the summary is just a *summary* of the change, it should be
readable at a glance when looking through git history.

A good commit summary makes it clear a) what *part* of the code is changing,
and b) what the change is. For example:

Clear commit summary:

> Replace 404 messages with a user-friendly one

Unclear commit summaries:

> Fixed some normalization bugs

> Bugfixes

The unclear messages make it hard to tell at a glance what changed, and that
makes browsing the commit history harder.

A commit message should use the [imperative mood] which should always be able to
complete the following sentence:

    If applied, this commit will <your subject line here>

#### Commit messages should be as detailed as they need to be (and no more)

The commit message is the rest of the commit past the first line.
If a commit makes a small and obvious change, it's fine to not even have a
commit message past the summary.

The commit message is your place to clarify the justification for a change.
While there's no need to rehash anything that code comments already say, if
there's more detail that helps a reader understand *why* a change was made, be
as verbose as you need to! Remember: future-you (or another developer) will
read this when going through the commit history to understand why a change was
made. Make their life easier.

Each line of a commit message should be no more than 72 characters in width.
The following is an outline of a commit message combined with an ideal commit
summary:

```
Capitalized, short (50 chars or less) summary

More detailed explanatory text, if necessary.  Wrap it to about 80
characters or so.  In some contexts, the first line is treated as the
subject of an email and the rest of the text as the body.  The blank
line separating the summary from the body is critical (unless you omit
the body entirely); tools like rebase can get confused if you run the
two together.

Further content comes after a blank line.
```
[documentation]: https://github.com/artefactual/archivematica-docs/
[mailing list]: https://groups.google.com/forum/#!forum/archivematica
[Archivematica Issues repo]: https://github.com/archivematica/Issues
[user]: https://groups.google.com/forum/#!forum/archivematica
[Archivematica Issues repo]: https://github.com/archivematica/Issues
[Issues repo wiki]: https://github.com/archivematica/Issues/wiki 
[files]: https://help.github.com/articles/getting-permanent-links-to-files/
[code snippets]: https://help.github.com/articles/creating-a-permanent-link-to-a-code-snippet/
[development installation]: https://wiki.archivematica.org/Getting_started#Installation
[GitHub]: https://github.com/
[guide]: https://help.github.com/articles/fork-a-repo
[excellent]: https://help.github.com/articles/using-pull-requests
[Line comment]: http://i.imgur.com/FsWppGN.png
[code review guidelines]: code_review.md
[interactive rebase feature]: http://www.git-scm.com/book/en/Git-Tools-Rewriting-History
[Contributor's Agreement]: https://wiki.archivematica.org/images/e/e6/Archivematica-CLA-firstname-lastname-YYYY.pdf
[Apache Foundation]: http://apache.org
[contributor license]: http://www.apache.org/licenses/icla.txt
[Artefactual Systems]: http://artefactual.com
[PEP8]: https://www.python.org/dev/peps/pep-0008/
[Black]: https://github.com/ambv/black
[flake8]: https://pypi.python.org/pypi/flake8
[continuous integration system]: https://travis-ci.org/artefactual/archivematica
[Pylint]: https://www.pylint.org/
[docstrings]: https://en.wikipedia.org/wiki/Docstring#Python
[PEP 257]: https://www.python.org/dev/peps/pep-0257/
[Sphinx-compatible docstrings]: http://pythonhosted.org/an_example_pypi_project/sphinx.html#function-definitions
[examples]: http://sphinx-doc.org/domains.html#info-field-lists
[attributes to use]: http://sphinx-doc.org/domains.html#the-python-domain
[unittest]: https://docs.python.org/2/library/unittest.html
[py.test]: http://pytest.org
[TestCase]: https://docs.djangoproject.com/en/1.8/topics/testing/tools/#django.test.TestCase
[VCR.py]: https://github.com/kevin1024/vcrpy
[How to Write a Git Commit Message]: https://chris.beams.io/posts/git-commit/
[seven rules of a great Git commit message]: https://chris.beams.io/posts/git-commit/#seven-rules
[imperative mood]: https://chris.beams.io/posts/git-commit/#imperative
