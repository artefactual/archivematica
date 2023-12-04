# [Archivematica]

By [Artefactual]

[![GitHub CI]][Test workflow]
[![codecov]][Archivematica Codecov]

Archivematica is a web- and standards-based, open-source application
which allows your institution to preserve long-term access to
trustworthy, authentic and reliable digital content.  Our target users
are archivists, librarians, and anyone working to preserve digital
objects.

You are free to copy, modify, and distribute Archivematica with
attribution under the terms of the AGPLv3 license.  See the [LICENSE]
file for details.

## Installation

* [Production installation]
* [Development installation]

## Other resources

* [Website][Archivematica]: User and administrator documentation
* [Wiki]: Developer facing documentation, requirements analysis and
  community resources
* [Issues]: Git repository used for tracking Archivematica issues and
  feature/enhancement ideas
* [User Google Group]: Forum/mailing list for user questions (both
  technical and end-user)
* [Paid support]: Paid support, hosting, training, consulting and
  software development contracts from Artefactual

## Contributing

Thank you for your interest in Archivematica!
For more details, see the [contributing guidelines]

## Reporting an issue

Issues related to Archivematica, the Storage Service, or any related
repository can be filed in the [Archivematica Issues repository].

### Security

If you have a security concern about Archivematica or any related
repository, please see the [SECURITY file] for information about how
to safely report vulnerabilities.

## Related projects

Archivematica consists of several projects working together, including:

* [Archivematica][Archivematica GitHub]: This repository! Main
  repository containing the user-facing dashboard, task manager
  MCPServer and clients scripts for the MCPClient
* [Storage Service]: Responsible for moving files to Archivematica for
  processing, and from Archivematica into long-term storage
* [Format Policy Registry]: Submodule shared between Archivematica and
  the Format Policy Registry (FPR) server that displays and updates
  FPR rules and commands

For more projects in the Archivematica ecosystem, see the [getting started] page.

[Archivematica]: https://www.archivematica.org/
[Artefactual]: https://www.artefactual.com/
[GitHub CI]: https://github.com/artefactual/archivematica/actions/workflows/test.yml/badge.svg
[Test workflow]: https://github.com/artefactual/archivematica/actions/workflows/test.yml
[codecov]: https://codecov.io/gh/artefactual/archivematica/branch/qa/1.x/graph/badge.svg?token=tKlfjhmrlC
[Archivematica Codecov]: https://codecov.io/gh/artefactual/archivematica
[LICENSE]: LICENSE
[Production installation]: https://www.archivematica.org/docs/latest/admin-manual/installation-setup/installation/installation/
[Development installation]: https://github.com/artefactual/archivematica/tree/qa/1.x/hack
[Wiki]: https://www.archivematica.org/wiki/Development
[Issues]: https://github.com/archivematica/Issues
[User Google Group]: https://groups.google.com/forum/#!forum/archivematica
[Paid support]: https://www.artefactual.com/services/
[contributing guidelines]: CONTRIBUTING.md
[Archivematica Issues repository]: https://github.com/archivematica/Issues/issues
[SECURITY file]: SECURITY.md
[Archivematica GitHub]: https://github.com/artefactual/archivematica
[Storage Service]: https://github.com/artefactual/archivematica-storage-service
[Format Policy Registry]: https://github.com/artefactual/archivematica/tree/qa/1.x/src/dashboard/src/fpr
[getting started]: https://wiki.archivematica.org/Getting_started#Projects
