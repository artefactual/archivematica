# Release notes

Release notes are prepared by Artefactual for each release of
Archivematica. Most releases also have a corresponding release of the
Storage System, and may also include corresponding releases for various
dependencies and libraries (i.e. AIPScan, Automation Tools) - be sure to
check the release notes for more information.

Features, enhancements, and bug fixes were often sponsored by members of
the Archivematica community who are dedicated to funding
Archivematica\'s ongoing development and maintenance. Code contributors
are individuals who write Archivematica code and [contribute it back to
the
project](https://github.com/artefactual/archivematica/blob/qa/1.x/CONTRIBUTING.md).
Archivematica couldn't continue to grow without sponsors and
contributors - thank you!

Questions about a release or the release notes? Ask on the
[Archivematica User Group](https://groups.google.com/g/archivematica)!

## (Current Release) Archivematica 1.17.0 and Storage Service 0.23.0

*Release date*: December 6, 2024

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.17.0_and_Storage_Service_0.23.0_release_notes).

### Environments for 1.17.0

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.17/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.17.0 and Storage Service 0.23.0 have been tested in the
following environments:

- Ubuntu 22.04 64-bit Server Edition
- Rocky Linux 9 x86_64

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the installation
instructions above.

### Changed in 1.17.0

#### Fixity reports sort failures

- Issue: <https://github.com/archivematica/Issues/issues/1681>

AIPs that fail fixity scan are displayed at the top of the list.

### Removed in 1.17.0

#### FITS

- Issue: <https://github.com/archivematica/Issues/issues/703>

[FITS](https://harvard-lts.github.io/fits/about) has been removed in
Archivematica 1.17.0 to mitigate potential vulnerabilities identified by
various security scanners.

The [Upgrading Archivematica](https://www.archivematica.org/en/docs/archivematica-1.17/admin-manual/installation-setup/upgrading/upgrading/#upgrade)
section of the documentation now includes detailed instructions for
uninstalling the FITS and nailgun packages.

### Fixed in 1.17.0

<!-- markdownlint-disable-next-line MD013 -->
#### Write-Only Replica Staging space works with transfers that include dots in their names

- Issue: <https://github.com/archivematica/Issues/issues/1697>

#### Fixity runs do not email inactive users anymore

- Issue: <https://github.com/archivematica/Issues/issues/1523>

#### AIP recovery updates

- Issue: <https://github.com/archivematica/Issues/issues/420>

AIP recovery places the recovered AIP inside the appropriate quad directory and
the documentation details the permission and directory requirements of the
process.

#### Subprocess non-UTF8 output is now escaped in MCPClient jobs

- Issue: <https://github.com/archivematica/Issues/issues/1702>

#### Tesseract OCR command can be disabled through Preservation Planning

- Issue: <https://github.com/archivematica/Issues/issues/1630>

#### The `purge_transient_processing_data` management command deletes transfer files

- Issue: <https://github.com/archivematica/Issues/issues/1714>

#### The `import_aip management command` sets the correct group ownership

- Issue: <https://github.com/archivematica/Issues/issues/1703>

#### RPM packages set the correct ownership of the static asset files

- Issue: <https://github.com/archivematica/Issues/issues/1700>

Please see the 1.17.0 milestone in GitHub for all issues addressed in this
release: <https://github.com/archivematica/Issues/milestone/26?closed=1>.

## Archivematica 1.16.0 and Storage Service 0.22.0

*Release date*: May 16, 2024

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.16.0_and_Storage_Service_0.22.0_release_notes).

### Environments for 1.16.0

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.16/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.16.0 and Storage Service 0.22.0 have been tested in the
following environments:

- Ubuntu 22.04 64-bit Server Edition
- Rocky Linux 9 x86\_64

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the
installation instructions above.

### Added in 1.16.0

#### List jobs API endpoint returns detailed output

- Issue: <https://github.com/archivematica/Issues/issues/1641>

A `detailed` parameter was added to the [List
jobs](https://www.archivematica.org/en/docs/archivematica-1.16/dev-manual/api/api-reference-archivematica/#list-jobs)
API endpoint. When the parameter is sent in the request, the endpoint
will return all the task properties returned by the
[Task](https://www.archivematica.org/en/docs/archivematica-1.16/dev-manual/api/api-reference-archivematica/#task)
endpoint.

### Changed in 1.16.0

#### PRONOM v.116

As of this Archivematica release, we are up to date to PRONOM v. 116.

[GitHub issue 1653](https://github.com/archivematica/Issues/issues/1653)

#### Python versions

- Issue: <https://github.com/archivematica/Issues/issues/1632>

Archivematica 1.16 works with all the current [Python supported
versions](https://devguide.python.org/versions/#supported-versions): 3.8
to 3.12.

#### Django 4.2

- Issue: <https://github.com/archivematica/Issues/issues/1624>

Archivematica 1.16 dropped support for Django 3.2.

### Fixed in 1.16.0

#### Update MCPClient forking model

- Issue: <https://github.com/archivematica/Issues/issues/1482>

Archivematica 1.16.0 introduces a new prefork execution model in
MCPClient based on a process pool. MCPClient workers are automatically
restarted to free resources and will reuse database connections when
possible.

The following new settings were added to the MCPClient service:

- `ARCHIVEMATICA_MCPCLIENT_WORKERS` defines the number of MCPClient
    workers. If undefined, it defaults to the number of CPUs available
    on the machine. Only client modules that define
    `concurrent_instances` will perform concurrent execution of tasks
    (e.g. identify\_file\_format).
- `ARCHIVEMATICA_MCPCLIENT_MAX_TASKS_PER_CHILD` defines the maximum
    number of tasks a worker can execute before it\'s replaced by a new
    process in order to free resources.
- `ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_PROMETHEUS_DETAILED_METRICS`
    indicates that detailed metrics should be sent to Prometheus. With
    large transfers this might affect performance of the local storage
    in Prometheus and slow down its threads in Archivematica.

See the [MCPClient
Configuration](https://github.com/artefactual/archivematica/blob/48004c5bd798ccb54196720103b462654bf9b08d/src/MCPClient/install/README.md)
page.

#### DIPs are cleaned from watched directories

- Issue: <https://github.com/archivematica/Issues/issues/1665>

#### Duracloud spaces retry chunk downloads

- Issue: <https://github.com/archivematica/Issues/issues/1607>

Thank you [Carlos Mc Gregor](https://github.com/carlosmcgregor) for
contributing this fix!

#### Partial reingest works with non-core DC properties

- Issue: <https://github.com/archivematica/Issues/issues/1620>

#### Improve paths handling in the Storage Service

- Issue: <https://github.com/archivematica/Issues/issues/1622>

Thank you [Fco. Javier Clavero](https://github.com/klavman) for starting
this work!

Please see the 1.16.0 milestone in GitHub for all issues addressed in
this release:
<https://github.com/archivematica/Issues/milestone/24?closed=1>.

## Archivematica 1.15.1 and Storage Service 0.21.1

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.15.1_and_Storage_Service_0.21.1_release_notes).

*Release date*: November 29, 2023

### Environments for 1.15.1

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.15/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.15.1 and Storage Service 0.21.1 have been tested in the
following environments:

- Ubuntu 22.04 64-bit Server Edition
- Rocky Linux 9 x86\_64

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the
installation instructions above.

### Changed for 1.15.1

#### Security upgrades

We have performed upgrades to the follow Python libraries to patch
reported security issues in earlier versions:

- agentarchives: from version 0.8.0 to 0.9.0
- amclient: from version 1.2.3 to 1.3.0
- ammcpc: from version 0.1.3 to 0.2.0
- cryptography: from version 41.0.4 to 41.0.7
- django: from version 3.2.22 to 3.2.23
- metsrw: from version 0.4.0 to 0.5.0
- urllib3: from version 1.26.17 to 2.1.0

We have also upgraded the following JavaScript front-end dependencies:

- fsevents: from version 1.1.3 to 1.2.13
- js-yaml: from version 3.7.0 to 3.13.1
- json5: from version 0.5.1 to 1.0.2
- karma: from version 0.13 to 6.0.0
- loader-utils: from version 1.0.2 to 1.4.2
- lodash: from version 4.5.1 to 4.17.12
- nodejs: from version 14.x to 20.x
- shelljs: from version 0.2.6 to 0.8.5

### Fixed for 1.15.1

#### API endpoint for listing unapproved transfers returns error

- Issue: <https://github.com/archivematica/Issues/issues/1635>

UUID identifiers were not encoded properly in the **List Unapproved
Transfers** and **List SIPS Waiting for User Input** API endpoints.

#### Transfers cannot be moved to the rejected directory

- Issue: <https://github.com/archivematica/Issues/issues/1636>

In the Archivematica 1.15.0 update, there was a backward-incompatible
change involving the configuration parsers for Django settings. This
change, part of a simplification process, has affected the handling of
the *%%sharedPath%%* variable. This variable is no longer included in
the default settings. If your custom settings rely on this variable, you
should now use *%sharedPath%* to maintain compatibility with the updated
system.

Please see the 1.15.1 milestone in GitHub for all issues addressed in
this release:
<https://github.com/archivematica/Issues/milestone/25?closed=1>.

## Archivematica 1.15.0 and Storage Service 0.21.0

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.15.0_and_Storage_Service_0.21.0_release_notes)

*Release date*: October 12, 2023

### Environments for 1.15.0

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.15/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.15.0 and Storage Service 0.21.0 have been tested in the
following environments:

- Ubuntu 22.04 64-bit Server Edition
- Rocky Linux 9 x86\_64

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the
installation instructions above.

### Changed for 1.15.0

#### Support for Ubuntu 22.04 and Rocky Linux 9

- Issue: <https://github.com/archivematica/Issues/issues/1590>

Archivematica 1.15 dropped support for Ubuntu 18.04 and CentOS 7.

#### MySQL 8.0

- Issue: <https://github.com/archivematica/Issues/issues/1618>

Archivematica 1.15 dropped support for MySQL 5.x.

#### Python 3.9

- Issue: <https://github.com/archivematica/Issues/issues/1612>

Archivematica 1.15 dropped support for Python 3.6.

#### Django 3.2

- Issue: <https://github.com/archivematica/Issues/issues/1279>

Archivematica 1.15 dropped support for Django 1.11.

### Fixed for 1.15.0

#### METS schema validation when loc.gov URLs are unreachable

- Issue: <https://github.com/archivematica/Issues/issues/1266>

Archivematica uses a local [XML
catalog](https://en.wikipedia.org/wiki/XML_catalog) to avoid contacting
the loc.gov URLs.

#### Storage Service LDAP configuration

- Issue: <https://github.com/archivematica/Issues/issues/1629>

Please see the 1.15.0 milestone in GitHub for all issues addressed in
this release:
<https://github.com/archivematica/Issues/milestone/22?closed=1>.

## Archivematica 1.14.1 and Storage Service 0.20.1

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.14.1_and_Storage_Service_0.20.1_release_notes).

*Release date*: July 19, 2023

### Environments for 1.14.1

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.14/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.14.1 and Storage Service 0.20.1 have been tested in the
following environments:

- Ubuntu 18.04 64-bit Server Edition
- CentOS 7 64-bit

Support for Ubuntu 22.04 and Rocky Linux 9 will be coming in the 1.15
release.

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the
installation instructions above.

### Fixed for 1.14.1

Please see the 1.14.1 milestone in GitHub for all issues addressed in
this release:
<https://github.com/archivematica/Issues/milestone/23?closed=1>.

## Archivematica 1.14.0 and Storage Service 0.20.0

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.14.0_and_Storage_Service_0.20.0_release_notes)

*Release date*: June 15, 2023

### Environments for 1.14.0

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.14/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.14.0 and Storage Service 0.20.0 have been tested in the
following environments:

- Ubuntu 18.04 64-bit Server Edition
- CentOS 7 64-bit

Support for Ubuntu 22.04 and Rocky Linux 9 will be coming in the 1.15
release.

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the
installation instructions above.

### Added for 1.14.0

#### Metadata import, reingest and validation in XML

This is a new set of features that allows users to include metadata
files in XML and have them parsed into the AIP METS file. Optionally,
the metadata files can also be validated against an external or local
schema. It also has improved the handling of updating or deleting
metadata on reingest.

[GitHub issue 1531](https://github.com/archivematica/Issues/issues/1531)

[GitHub issue 1537](https://github.com/archivematica/Issues/issues/1537)

[Documentation](https://archivematica.org/en/docs/archivematica-1.14/user-manual/transfer/import-metadata/#metadata-xml-validation)

This feature was sponsored by the Saxon State and University Library
Dresden. Thank you!

#### Rclone spaces in the Storage Service

The [Rclone](https://rclone.org/) space allows for use of over 40 cloud
providers with Archivematica as Transfer Source, AIP Store, DIP Store,
and Replicator locations.

[Github issue 1567](https://github.com/archivematica/Issues/issues/1567)

[Documentation](https://archivematica.org/en/docs/storage-service-0.20/administrators/#rclone)

### Changed for 1.14.0

#### PRONOM v.109

As of this Archivematica release, we are up to date to PRONOM v. 109.

[GitHub issue 1592](https://github.com/archivematica/Issues/issues/1592)

#### Other changes

- Python 2.7 removed [GitHub issue
    1506](https://github.com/archivematica/Issues/issues/1506)
- Ability to override LDAP Attributes [Github issue
    1565](https://github.com/archivematica/Issues/issues/1565)
    **Contributed by Tom Misilo- thank you!**

### Fixed for 1.14.0

Please see the 1.14 milestone in GitHub for all issues addressed in this
release:
<https://github.com/archivematica/Issues/milestone/20?closed=1>.

## Storage Service 0.19 release notes

[Original release
notes](https://wiki.archivematica.org/Storage_Service_0.19_Release_Notes)

- *Release date*: 25 Feb 2022

This release adds a new feature to the Storage Service

### Environments for Storage Service 0.19

Please see the [installation
instructions](https://www.archivematica.org/en/docs/latest/admin-manual/installation-setup/installation/installation/#installation).

Storage Service 0.19.0 has been tested in the following environments:

- Ubuntu 18.04 64-bit Server Edition
- CentOS 7 64-bit

Please note that we\'ve dropped support for Ubuntu Linux 16.04 since it
reached the end of its five-year LTS window on April 30th 2021. We\'re
planning to add support for Ubuntu 20.04 in the near future.

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the
installation instructions above.

### Upgrading for Storage Service 0.19

- With the new permission module (see [pull request
    \#625](https://github.com/artefactual/archivematica-storage-service/pull/625)
    for more), existing users defined in the application database will
    automatically become administrators when the Django migrations are
    executed. If your Storage Service is configured with an external
    authentication backend, you can use
    [SS\_AUTH\_DEFAULT\_USER\_ROLE](https://github.com/artefactual/archivematica-storage-service/tree/stable/0.19.x/install)
    to establish a new default user role for authenticated users or
    tweak the [authentication backend
    settings](https://github.com/artefactual/archivematica-storage-service/blob/stable/0.19.x/storage_service/storage_service/settings/base.py)
    to map the user roles according to your needs.

### Added for Storage Service 0.19

#### User roles

- Issue: <https://github.com/archivematica/Issues/issues/1486>

The Storage Service now includes four different user roles:
administrators, managers, reviewers and readers. Previously, users were
either administrators or not administrators, the only difference being
that administrators can create, edit, and delete other users. All
existing users will automatically become administrators on upgrade. You
may wish to review your users and adjust their permissions as needed.

Supported authentication backends like LDAP, Shibboleth or CAS include
new configuration attributes to promote authenticated users.

See
[Users](https://www.archivematica.org/en/docs/storage-service-0.19/administrators/#users)
in the Storage Service documentation for more information.

### Fixed for Storage Service 0.19

- Storage Service 0.18.x doesn\'t follow symlinks:
    <https://github.com/archivematica/Issues/issues/1515>

## Archivematica 1.13.2

[Original release
notes](notes:https://wiki.archivematica.org/Archivematica_1.13.2).

*Release date*: 13 Dec 2021

This release fixes a critical security issue found in the Archivematica
dashboard that allows unauthorized users to access some parts of the
Administration tab.

This issue was discovered as a result of a security audit by Scholars
Portal. It was not discovered as a result of a breach. Scholars Portal
reported the issue to Artefactual privately via email. Once we became
aware of the issue, we began to develop the fix. Artefactual has also
implemented security reporting process documentation across
Archivematica-related GitHub repositories and changed issue templates to
reflect a more secure process. You can review Archivematica's security
reporting process here:
<https://github.com/artefactual/archivematica/security/policy>.

### Upgrading for 1.13.2

The fix can be easily installed since this issue only affects the
dashboard.

CentOS users relying on Archivematica packages should run:

    sudo yum -y update archivematica-dashboard
    sudo systemctl restart archivematica-dashboard

Automated installations using Ansible should deploy from the stable
branch: stable/1.13.x.

Alternately, a fix can be applied to the web server. The following
configuration snippet shows an updated Nginx server block with the
additional rule added.

    server {
       listen 80;
       client_max_body_size 256M;
       server_name _;
       location / {
           set $upstream_endpoint http://archivematica-dashboard:8000;
           proxy_set_header Host $http_host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_redirect off;
           proxy_buffering off;
           proxy_read_timeout 172800s;
           proxy_pass $upstream_endpoint;
       }

       # Directive to block access to admin pages in
       # Archivematica v1.11.0 or older.
       location ~ ^/administration/accounts/login/.+$ {
           return 404;
       }
    }

After the fix has been applied, please be sure to update passwords and
API keys:

- Change the password and API key for the Storage Service user:
    -- In the Storage Service, change the password for the Storage
      Service user that the Archivematica dashboard uses. This will
      also regenerate the API key for the Storage Service user.
    -- In the Archivematica dashboard, under Administration \> General,
      update the Storage Service user password and the API key to
      reflect the new password/key.
- Change the password for AtoM/Binder DIP upload.
- Review the PREMIS agent information to ensure that it is correct.

## Archivematica 1.13.1 and Storage Service 0.18.1

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.13.1_and_Storage_Service_0.18.1_release_notes).

*Release date*: October 19, 2021

### Environments for 1.13.1

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.13/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.13.1 and Storage Service 0.18.1 have been tested in the
following environments:

- Ubuntu 18.04 64-bit Server Edition
- CentOS 7 64-bit

Please note that we\'ve dropped support for Ubuntu Linux 16.04 since it
reached the end of its five-year LTS window on April 30th 2021. We\'re
planning to add support for Ubuntu 20.04 in the short term.

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the
installation instructions above.

### Fixed for 1.13.1

Please see the 1.13.1 milestone in GitHub for all issues addressed in
this release:
<https://github.com/archivematica/Issues/milestone/19?closed=1>.

## Archivematica 1.13.0 and Storage Service 0.18.0

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.13.0_and_Storage_Service_0.18.0_release_notes).

*Release date*: July 12, 2021

### Environments for 1.13.0

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.13/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.13.0 and Storage Service 0.18.0 have been tested in the
following environments:

- Ubuntu 18.04 64-bit Server Edition
- CentOS 7 64-bit

Please note that we\'ve dropped support for Ubuntu Linux 16.04 since it
reached the end of its five-year LTS window on April 30th 2021. We\'re
planning to add support for Ubuntu 20.04 in the short term.

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the
installation instructions above.

### Added for 1.13.0

#### Disableable virus scanning

- Issue: <https://github.com/archivematica/Issues/issues/869>

Virus scanning can now be disabled from the processing configuration.

This change was **contributed** by Bodleian Library. Thank you!

#### Purge management command

- Issue: <https://github.com/archivematica/Issues/issues/1239>

A new [management
command](https://www.archivematica.org/en/docs/archivematica-1.13/admin-manual/maintenance/maintenance/#management-commands)
has been added to provide a mechanism to remove old processing data from
the system filling up the application database and search indices.

#### Strong password validation

- Issue: <https://github.com/archivematica/Issues/issues/1332>

Archivematica and the Storage Service can now require strong passwords
for user accounts. Prompts are given when creating a new user if the
password doesn\'t meet the requirements.

This feature was **sponsored** by the City of Winnipeg Archives. Thank
you!

#### Audit logging capability

- Issue: <https://github.com/archivematica/Issues/issues/1341>

This addition allows audit logs to be written to third party
applications- Artefactual Systems\' implementation of this is in a new
application called
[Auditmatica](https://github.com/artefactual-labs/auditmatica). The
change in Archivematica and the Storage Service is only to facilitate
the capture of audit logging information in other applications.

This addition was **sponsored** by the City of Winnipeg Archives. Thank
you!

#### Customized workflow file

- Issue: <https://github.com/archivematica/Issues/issues/1441>

This feature allows the user to indicate the location/existence of a
customized workflow document, in json. This would allow institutions to
add to the Archivematica workflow (e.g. custom micro-services) in a way
that is easier to maintain through upgrades. Developer documentation is
pending.

### Changed for 1.13.0

#### Python 3 for 1.13.0

- Issues:
    <https://github.com/archivematica/Issues/issues?q=is%3Aopen+is%3Aissue+milestone%3A1.13.0+label%3A%22%3Asnake%3A%C2%B3+Python+3%22>

All Archivematica components are now running on Python 3.6.

#### Archivematica Storage Service now uses MySQL by default

- Issue: <https://github.com/archivematica/Issues/issues/952>

MySQL is now the default database in Archivematica Storage Service.
SQLite is still supported but we encourage users to migrate. We have
documented the process: [Migrating data from SQLite to
MySQL](https://www.archivematica.org/en/docs/storage-service-0.18/migration-sqlite-mysql/#migration-sqlite-mysql).

#### Allow replicated AIPs to be packaged in a different format

- Issue: <https://github.com/archivematica/Issues/issues/1440>

By using an offline replica storage space it is now possible to
replicate AIPs in a different packaging format than the original AIP
(helpful in use cases such as offline tape storage, etc).

This change was **sponsored** by Norwegian Health Archives. Thank you!

#### Tasks will open in one tab only

- Issue: <https://github.com/archivematica/Issues/issues/85>

Now instead of opening multiple tabs every time a user clicks on a task
gear, they will all open in one new tab.

This change was **contributed** by Bodleian Library. Thank you!

#### Dev tools deprecated / Hiding active packages

Issue: <https://github.com/archivematica/Issues/issues/68>

Issue: <https://github.com/archivematica/Issues/issues/1446>

Due to maintainability issues, we have removed the devtools repo. The
most commonly used dev tool was used for resolving hidden transfers,
which should no longer be relevant since resolving [Issue
1446](https://github.com/archivematica/Issues/issues/1446)- active
transfers or SIPs can no longer be hidden. However as a precaution, we
have made that command available within Archivematica
(<https://github.com/artefactual/archivematica/blob/qa/1.x/src/dashboard/src/main/management/commands/resolve_pending_jobs.py>).

#### DIP storage locations now allowed in S3 spaces

- Issue: <https://github.com/archivematica/Issues/issues/1442>

This is a **contribution** by Fashion Institute of Technology NYC. Thank
you!

#### Other changes for 1.13.0

- Archivematica now records granular time stamps for original files,
    Issue 1427: <https://github.com/archivematica/Issues/issues/1427>
- Archival storage csv file sortable by size column, Issue 1450:
    <https://github.com/archivematica/Issues/issues/1450>
- Deleting AIPs does not delete associated directories from AIP store,
    Issue 359: <https://github.com/archivematica/Issues/issues/359>
- Cannot add a processing configuration if the name has diacritics,
    Issue 1104: <https://github.com/archivematica/Issues/issues/1104>
- Cannot create a replicator location in Duracloud space, Issue 1350:
    <https://github.com/archivematica/Issues/issues/1350>
- Fixity status tab sorts alphabetically, now sorts by date, Issue
    1196: <https://github.com/archivematica/Issues/issues/1196>
- Failure report not generated when email not configured, Issue 1033:
    <https://github.com/archivematica/Issues/issues/1033>
- Replicator does not replicate AIPs on re-ingest or delete replicated
    AIPs, Issue 985:
    <https://github.com/archivematica/Issues/issues/985>

### Fixed for 1.13.0

Please see the 1.13 milestone in GitHub for all issues addressed in this
release: <https://github.com/archivematica/Issues/milestone/17>.

## Archivematica 1.12.2

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.12.2).

*Release date*: 13 Dic 2021

This release fixes a critical security issue found in the Archivematica
dashboard that allows unauthorized users to access some parts of the
Administration tab.

This issue was discovered as a result of a security audit by Scholars
Portal. It was not discovered as a result of a breach. Scholars Portal
reported the issue to Artefactual privately via email. Once we became
aware of the issue, we began to develop the fix. Artefactual has also
implemented security reporting process documentation across
Archivematica-related GitHub repositories and changed issue templates to
reflect a more secure process. You can review Archivematica's security
reporting process here:
<https://github.com/artefactual/archivematica/security/policy>.

### Upgrading

The fix can be easily installed since this issue only affects the
dashboard.

CentOS users relying on Archivematica packages should run:

    sudo yum -y update archivematica-dashboard
    sudo systemctl restart archivematica-dashboard

Automated installations using Ansible should deploy from the stable
branch: stable/1.12.x.

Alternately, a fix can be applied to the web server. The following
configuration snippet shows an updated Nginx server block with the
additional rule added.

    server {
       listen 80;
       client_max_body_size 256M;
       server_name _;
       location / {
           set $upstream_endpoint http://archivematica-dashboard:8000;
           proxy_set_header Host $http_host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_redirect off;
           proxy_buffering off;
           proxy_read_timeout 172800s;
           proxy_pass $upstream_endpoint;
       }

       # Directive to block access to admin pages in
       # Archivematica v1.11.0 or older.
       location ~ ^/administration/accounts/login/.+$ {
           return 404;
       }
    }

After the fix has been applied, please be sure to update passwords and
API keys:

- Change the password and API key for the Storage Service user:
    -- In the Storage Service, change the password for the Storage
       Service user that the Archivematica dashboard uses. This will
       also regenerate the API key for the Storage Service user.
    -- In the Archivematica dashboard, under Administration \> General,
       update the Storage Service user password and the API key to
       reflect the new password/key.
- Change the password for AtoM/Binder DIP upload.
- Review the PREMIS agent information to ensure that it is correct.

## Archivematica 1.12.1 and Storage Service 0.17.1

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.12.1_and_Storage_Service_0.17.1_release_notes).

*Release date*: January 7, 2021

This minor release primarily addresses a defect related to Duracloud AIP
storage integration as well as some installation/upgrade issues
experienced after the 1.12.0 release.

### Supported environments for 1.12.1

Installation instructions:
<https://www.archivematica.org/en/docs/archivematica-1.12/admin-manual/installation-setup/installation/installation/#installation>

Upgrade instructions:
<https://www.archivematica.org/en/docs/archivematica-1.12/admin-manual/installation-setup/upgrading/upgrading/#upgrade>

Guidance on how to update mapping and reindex Elasticsearch indices:
<https://wiki.archivematica.org/Update_mapping_and_reindex_Elasticsearch_indices>

### Fixed for 1.12.1

List bugfixes with a link to the Github issue.

- AIPs larger than 1 GB cannot be stored in Duracloud:
    <https://github.com/archivematica/Issues/issues/1314>
- Upgrade from 1.11.2 to 1.12.0 fails:
    <https://github.com/archivematica/Issues/issues/1312>
- Awesome-font error in rpm packages:
    <https://github.com/archivematica/Issues/issues/1300>
- Clicking on metadata icon in transfer tab causes internal server
    error: <https://github.com/archivematica/Issues/issues/1324>
- Transfer name doesn\'t always show up (**Sponsored** by Picturae
    -thank you!): <https://github.com/archivematica/Issues/issues/1250>
- Interval setting for updated UI being ignored (**Sponsored** by
    Picturae- thank you!):
    <https://github.com/archivematica/Issues/issues/1017>

## Archivematica 1.12.0 and Storage Service 0.17.0

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.12.0_and_Storage_Service_0.17.0_release_notes).

*Release date*: October 7, 2020

### Environments for 1.12.0

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.12/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.12.0 and Storage Service 0.17.0 have been tested in the
following environments:

- Ubuntu 18.04 64-bit Server Edition
- CentOS 7 64-bit

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the
installation instructions above.

### Upgrading note for 1.12.0

If you are upgrading from Archivematica 1.10.x or earlier, please be
sure to clean up the completed transfers watched directory before
upgrading. Instructions can be found on the
[Upgrading](https://www.archivematica.org/en/docs/archivematica-1.12/admin-manual/installation-setup/upgrading/upgrading/#upgrade)
page in the documentation.

### Added for 1.12.0

#### Processing configuration selector

This feature allows the user to choose a processing configuration at the
time of transfer by way of a drop down in the \"Start transfer\" button.

- Issue: <https://github.com/archivematica/Issues/issues/1166>
- Documentation:
    <https://www.archivematica.org/en/docs/archivematica-1.12/user-manual/transfer/transfer.rst>

This feature has been sponsored by Simon Fraser University Archives.
Thank you!

#### Column selectors for the Backlog and Archival Storage tab

Users can now choose the columns displayed while browsing the Backlog
and Archival Storage tabs so they can see the information most relevant
to them.

- Issue (Archival Storage):
    <https://github.com/archivematica/Issues/issues/1168>
- Documentation (Archival Storage):
    <https://www.archivematica.org/en/docs/archivematica-1.12/user-manual/archival-storage/archival-storage/#archival-storage>
- Issue (Backlog):
    <https://github.com/archivematica/Issues/issues/1167>
- Documentation (Backlog):
    <https://www.archivematica.org/en/docs/archivematica-1.12/user-manual/backlog/backlog/#backlog>

These features have been sponsored by Simon Fraser University Archives.
Thank you!

#### AIP location column on Archival Storage tab

- Issue: <https://github.com/archivematica/Issues/issues/1214>
- Documentation:
    <https://www.archivematica.org/en/docs/archivematica-1.12/user-manual/archival-storage/archival-storage/#archival-storage>

This feature has been sponsored by Picturae. Thank you!

#### Downloadable CSV from Archival Storage search

Users can now download a CSV containing all entries in Archival Storage,
containing these columns: AIP name, Size, UUID, Number of files, Date
stored, Status, Encrypted, and Storage Location

- Issue: <https://github.com/archivematica/Issues/issues/1213>
- Documentation:
    <https://www.archivematica.org/en/docs/archivematica-1.12/user-manual/archival-storage/archival-storage/#archival-storage>

This feature has been sponsored by Picturae. Thank you!

#### Central Authentication Service (CAS) for Archivematica and Storage Service

- Issue: <https://github.com/archivematica/Issues/issues/1211>
- Documentation:
    <https://www.archivematica.org/en/docs/archivematica-1.12/admin-manual/security/security/#cas-setup>

This feature has been sponsored by Simon Fraser University Archives.
Thank you!

#### OpenID Connect (OIDC) support for Archivematica and Storage Service

**Experimental! Please share your feedback.**

- Issue: <https://github.com/archivematica/Issues/issues/1053>
- Instructions:
    <https://www.archivematica.org/en/docs/archivematica-1.12/admin-manual/security/security/#oidc-setup>

OIDC support is a community contribution by Wellcome Collection. Thank
you!

### Changed for 1.12.0

#### Django 1.12 support

- Issue: <https://github.com/artefactual/archivematica/issues/1016>

Archivematica has been upgraded to Django 1.12 LTS. Our next target is
Django 2.2 LTS!

There are a couple of things to be aware of during the Archivematica
upgrade in this respect:

- For a seamless experience for your users make sure that all active
    user sessions are deleted. We explain how here: [Maintenance \>
    Clear user
    sessions](https://www.archivematica.org/en/docs/archivematica-1.12/admin-manual/maintenance/maintenance/#clear-user-sessions).
- Django\'s User model now comes with a character limit of 150
    characters. In Archivematica v1.11.x or older we had that limit set
    to 250 characters via a third-party app that we have now deleted.
    During the database migration (i.e. when running manage.py migrate),
    users may be required to fix the problem manually. See the
    [migration module
    documentation](https://github.com/artefactual/archivematica/blob/f87d2f39acce9a59bf49f72fd7e57f9eced2dbe5/src/dashboard/src/main/migrations/0078_username_check.py#L1-L20)
    for more details. We expect this to be highly unlikely to happen
    since the exception is only triggered when the 150 character limit
    in the username field is exceeded.

#### Replace whitelist with allowlist

- Issue: <https://github.com/archivematica/Issues/issues/1226>

We have changed \"whitelist\" to \"allowlist\" in an effort to use more
inclusive language throughout Archivematica\'s code.

### Fixed for 1.12.0

- Status doesn\'t revert to \"Stored\" after deletion requests are
    rejected: <https://github.com/archivematica/Issues/issues/1273>
- Cannot create a SIP from a Bag transfer in Appraisal tab:
    <https://github.com/archivematica/Issues/issues/1267>
- Transfer/AIP status not in sync when package is deleted within SS:
    <https://github.com/archivematica/Issues/issues/1189>
- Cannot rebuild backlog or AIP indices when location is encrypted:
    <https://github.com/archivematica/Issues/issues/734>
- Disk usage pages are not reporting accurate numbers:
    <https://github.com/archivematica/Issues/issues/1281>

And more! Please see the 1.12 milestone in Github for all issues
addressed in this release:
<https://github.com/archivematica/Issues/milestone/12>

## Archivematica 1.11.2 and Storage Service 0.16.1

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.11.2_and_Storage_Service_0.16.1_release_notes).

*Release date*: June 12, 2020

This release introduces two bug fixes and one minor security fix. For
installation instructions, please see the [Installation
documentation](https://www.archivematica.org/en/docs/archivematica-1.11/admin-manual/installation-setup/installation/installation/#installation).

### Note: Ugprading for 1.11.2

If you are upgrading from Archivematica 1.10.x or earlier, please be
sure to clean up the completed transfers watched directory before
upgrading. Instructions can be found on the
[Upgrading](https://www.archivematica.org/en/docs/archivematica-1.11/admin-manual/installation-setup/upgrading/upgrading/#upgrade)
page in the documentation.

### Fixed for 1.11.2

List bugfixes with a link to the Github issue.

- Compressed AIPs break replication: [Issue
    1149](https://github.com/archivematica/Issues/issues/1149)
- Responsive top menu on dashboard blocks view of content: [Issue
    1034](https://github.com/archivematica/Issues/issues/1034)
- AM Dashboard does not implement Cross Site Request Forgery
    protection: [Issue
    1235](https://github.com/archivematica/Issues/issues/1235)

## Archivematica 1.11.1

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.11.1).

*Release date*: 20 May 2020

This release fixes a critical security issue found in the Archivematica
dashboard that allows unauthorized users to access some parts of the
Administration tab.

This issue was discovered as a result of a security audit by Scholars
Portal. It was not discovered as a result of a breach. Scholars Portal
reported the issue to Artefactual privately via email. Once we became
aware of the issue, we began to develop the fix. Artefactual has also
implemented security reporting process documentation across
Archivematica-related GitHub repositories and changed issue templates to
reflect a more secure process. You can review Archivematica's security
reporting process here:
<https://github.com/artefactual/archivematica/security/policy>.

### Upgrading for 1.11.1

The fix can be easily installed since this issue only affects the
dashboard.

CentOS users relying on Archivematica packages should run:

    sudo yum -y update archivematica-dashboard
    sudo systemctl restart archivematica-dashboard

Automated installations using Ansible should deploy from our stable
branches: stable/1.9.x, stable/1.10.x or stable/1.11.x.

Alternately, a fix can be applied to the web server. The following
configuration snippet shows an updated Nginx server block with the
additional rule added.

    server {
       listen 80;
       client_max_body_size 256M;
       server_name _;
       location / {
           set $upstream_endpoint http://archivematica-dashboard:8000;
           proxy_set_header Host $http_host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_redirect off;
           proxy_buffering off;
           proxy_read_timeout 172800s;
           proxy_pass $upstream_endpoint;
       }

       # Directive to block access to admin pages in
       # Archivematica v1.11.0 or older.
       location ~ ^/administration/accounts/login/.+$ {
           return 404;
       }
    }

After the fix has been applied, please be sure to update passwords and
API keys:

- Change the password and API key for the Storage Service user:
    -- In the Storage Service, change the password for the Storage
       Service user that the Archivematica dashboard uses. This will
       also regenerate the API key for the Storage Service user.
    -- In the Archivematica dashboard, under Administration \> General,
       update the Storage Service user password and the API key to
       reflect the new password/key.
- Change the password for AtoM/Binder DIP upload.
- Review the PREMIS agent information to ensure that it is correct.

### Note for 1.11.1

If you are upgrading from Archivematica 1.10.x or earlier, please be
sure to clean up the completed transfers watched directory before
upgrading. Instructions can be found on the
[Upgrading](https://www.archivematica.org/en/docs/archivematica-1.11/admin-manual/installation-setup/upgrading/upgrading/#upgrade)
page in the documentation.

### Fixed for 1.11.1

- [1.11.1
    milestone](https://github.com/archivematica/Issues/milestone/14)

## Archivematica 1.11 and Storage Service 0.16

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.11_and_Storage_Service_0.16_release_notes).

*Release date*: April 1, 2020

### Environments for 1.11

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.11/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.11 and Storage Service 0.16 have been tested in the
following environments:

- Ubuntu 16.04 64-bit Server Edition
- Ubuntu 18.04 64-bit Server Edition
- CentOS 7 64-bit

For development purposes, most of our developers prefer to use Docker
containers. These and all above environments are linked from the
installation instructions above.

### Note for 1.11

If you are upgrading from Archivematica 1.10.x or earlier, please be
sure to clean up the completed transfers watched directory before
upgrading. Instructions can be found on the
[Upgrading](https://www.archivematica.org/en/docs/archivematica-1.11/admin-manual/installation-setup/upgrading/upgrading/#upgrade)
page in the documentation.

### Added for 1.11

#### PREMIS Event import

This feature allows the import of PREMIS events which took place prior
to processing in Archivematica. The PREMIS events are written in an xml
format (see [sample
data](https://github.com/artefactual/archivematica-sampledata/blob/master/SampleTransfers/PremisImporter/metadata/premis.xml))
and placed in the metadata folder of a transfer. The PREMIS events are
then written to the AIP METS file.

This work was sponsored by Piql and the Norwegian Health Archives. Thank
you!

- [Documentation](https://www.archivematica.org/en/docs/archivematica-1.11/user-manual/transfer/import-metadata/#premis-xml)
- Issue: <https://github.com/archivematica/Issues/issues/710>

#### S3 as a transfer source

This allows an Amazon S3 space to be used as a transfer source location.
This feature is a community PR from Wellcome Collection. Thank you!

- [Documentation](https://www.archivematica.org/en/docs/storage-service-0.16/administrators/#s3-amazon)
- Issue: <https://github.com/archivematica/Issues/issues/975>

#### Easier access to AIP METS

This feature add a \"View METS\" button in the user interface when
viewing an AIP in Archival Storage. The METS file is then downloaded to
your desktop for your viewing pleasure.

- Documentation: pending
- Issue: <https://github.com/archivematica/Issues/issues/644>

#### Zipped transfers

This is a new transfer type that enables a zipped (non-bagged) package
to be a transfer. Similar to the zipped bag transfer, the name of the
package is used as the transfer name. This is a community contribution
by Wellcome Collection. Thank you!

- [Documentation](https://www.archivematica.org/en/docs/archivematica-1.11/user-manual/transfer/transfer/#transfer-types)
- Issue: <https://github.com/archivematica/Issues/issues/682>

#### Add package name as configurable value to call backs

When using AIP, AIC, and DIP store callbacks, the package\_name is now a
configurable value. This is a community contribution from Concordia
University Libraries, who developed this to facilitate an EPrints to
Archivematica workflow. Thank you!

- Documentation: pending
- Issue: <https://github.com/archivematica/Issues/issues/978>

### Changed for 1.11

#### Performance and monitoring improvements

This is a collection of issues fixed that improve performance for
processing at scale, and also enable performance monitoring through
external applications such as Prometheus and Grafana.

These updates have been sponsored by Piql and the Norwegian Health
Archives. Thank you!

- [Documentation](https://www.archivematica.org/en/docs/archivematica-1.11/admin-manual/installation-setup/customization/instrumentation/)
- Issues:
    -- Commonly used database tables don\'t have indexes:
       <https://github.com/archivematica/Issues/issues/907>
    -- MCPServer should reuse database connections:
       <https://github.com/archivematica/Issues/issues/913>
    -- Archivematica does not output metrics to analyze its
       performance:
       <https://github.com/archivematica/Issues/issues/906>
    -- MCPService must process all transfer packages sent to it at
       once: <https://github.com/archivematica/Issues/issues/911>
    -- Some jobs run even when disabled:
       <https://github.com/archivematica/Issues/issues/866>
    -- \"Check transfer directory for objects\" executed multiple
       times: <https://github.com/archivematica/Issues/issues/782>
    -- index\_aip crashes elasticsearch for large transfers:
       <https://github.com/artefactual/archivematica/issues/1199>

#### Improvements for full disks

Managing workflows when various spaces on the disk fill up is a
recognized pain point for Archivematica users. This project makes three
overall changes to storage space reporting in Archivematica and the
Storage Service in an effort to mitigate these issues:

- Change the processing storage usage page to clarify storage
    paths/locations and improve usability
- Improve the transfer source location and AIP storage location pages
    to clarify storage paths/locations and improve usability
- Change Storage Service functionality to support the above changes.
- Documentation: pending
- [Issues](https://github.com/archivematica/Issues/issues?q=label%3A%22RED+TEAM%3A+disk+full+project%22+is%3Aclosed)

#### Changes to default normalization for videos/images

Archivematica\'s default FPR normalization rules were creating in some
cases very large video files for arguably no sound preservation reason.
After discussion and community consultation, we have removed default
video normalization rules. Users can still \"opt in\" to the rules but
they are not enabled by default in **new or upgraded** installations.
Any custom changes you have made to your own FPR will still be
maintained after upgrade. We also removed default rules for preservation
for PNG, JPG, GIF and DNG still images. For full details and affected
formats, see [this
comment](https://github.com/archivematica/Issues/issues/912#issuecomment-565197594)
in the issue ticket.

- Issue: <https://github.com/archivematica/Issues/issues/912>

#### Allow users to choose whether to receive fail report emails

Users can now be configured to either receive fail report emails or not
(previously all users received the emails). This is a community
contribution from Hillel Arnold at Rockefeller Archive Center- thank
you!

- [Documentation](https://www.archivematica.org/en/docs/archivematica-1.11/user-manual/administer/dashboard-admin/#dashboard-users)
- Issue: <https://github.com/archivematica/Issues/issues/709>

#### Change name of sanitize names micro-service

Following reading a paper by [Elvia
Arroyo-Ramirez](https://medium.com/on-archivy/invisible-defaults-and-perceived-limitations-processing-the-juan-gelman-files-4187fdd36759)
we decided to change the name of this micro-service and align it more
with the Library of Congress events vocabulary. The micro-service now
displays as \"Change transfer filenames\" and \"Change SIP filenames\"
in the Transfer and Ingest tabs respectively.

- Issue: <https://github.com/archivematica/Issues/issues/230>

#### Drop-down menu orders

In short, the order of options in drop down menus were all over the
place and it was driving us nuts so we finally tried to put them in more
logical orders.

- Issue: <https://github.com/artefactual/archivematica/issues/891>

### Removed for 1.11

#### Quarantine

As [discussed on the community
forum](https://groups.google.com/d/msg/archivematica/rGMsO8htF38/Pl-eLimwAgAJ)
the quarantine micro-service has been removed from Archivematica in this
release.

- Issue: <https://github.com/artefactual/archivematica/issues/598>
- ADR:
    <https://github.com/archivematica/archivematica-architectural-decisions/blob/master/0008-remove-quarantine.md>

#### \"Add next\" disk image transfer button

This button seemed redundant to the workflow so it\'s been removed.

- Issue: <https://github.com/archivematica/Issues/issues/290>

### Fixed for 1.11

- Non-Dublin Core columns cause metadata re-ingest to fail
    (**Sponsored** by Piql/NHA- thank you!):
    <https://github.com/archivematica/Issues/issues/1139>
- RuntimeError which was causing sporadic workflow issues (**Community
    contribution** by Jorik van Kemanade- thank you!):
    <https://github.com/archivematica/Issues/issues/1108>
- Reindexing large transfer backlog error (**Community contribution**
    by Matt LaChance- thank you!):
    <https://github.com/archivematica/Issues/issues/962>
- Parallel bzip2 compression failing in am19rpm:
    <https://github.com/archivematica/Issues/issues/606>
- Fixity API endpoint and Fixity tool tail to check replicated AIPs
    (**Sponsored** by Piql/NHA- thank you!):
    <https://github.com/archivematica/Issues/issues/1054>
- Decision points break with 10 choices or more (**Sponsored** by
    Picturae- thank you!):
    <https://github.com/archivematica/Issues/issues/850>
- S3 us-east-1 fails when chosen as region in the Storage Service
    (**Community contribution** by Joseph Anderson, Fashion Institution
    of Technology- thank you!):
    <https://github.com/archivematica/Issues/issues/922>
- \"Remove bagged files\" reports failure when thumbnails aren\'t
    created: <https://github.com/archivematica/Issues/issues/651>
- Directories are greyed out while they still contain files available
    for arrangement (**Sponsored** by Simon Fraser University Archives
    -thank you!): <https://github.com/archivematica/Issues/issues/822>
- Dublin Core dmdSec not created if filename has diacritics:
    <https://github.com/archivematica/Issues/issues/1073>
- Cannot add metadata files through the UI (**Sponsored** by
    Piql/NHA-thank you!):
    <https://github.com/archivematica/Issues/issues/1090>
- GPG/TRANSFORMKEY being lost when reingesting an encrypted AIP:
    <https://github.com/archivematica/Issues/issues/803>
- Pointer file uses a mix of PREMIS2 and PREMIS3:
    <https://github.com/archivematica/Issues/issues/820>
- Failure to match in ArchivesSpace DIP Upload shows as success
    (**Sponsored** by Rockefeller Archive Center- thank you!):
    <https://github.com/archivematica/Issues/issues/258>
- Allow S3 credentials to be blank (**Community contribution** by
    Wellcome Collection- thank you!):
    <https://github.com/archivematica/Issues/issues/712>
- Version of METS in mets-reader-writer is an older version:
    <https://github.com/archivematica/Issues/issues/637>
- S3 bucket name can\'t be configured:
    <https://github.com/archivematica/Issues/issues/558>
- Pointer files for reingested AIP has two compression events:
    <https://github.com/archivematica/Issues/issues/1062>
- Bags with metadata fail to ingest when additional metadata is added
    by automation tools (**Sponsored** by the Museum of Modern Art-
    thank you!): <https://github.com/archivematica/Issues/issues/1022>
- Transfer browser breaks if transfer source contains read protected
    directories: <https://github.com/archivematica/Issues/issues/1019>
- AIP status in dashboard does not update after AIP is deleted:
    <https://github.com/archivematica/Issues/issues/1014>
- SIPs started from ArchivesSpace pane fail when a parent object does
    not have a title (**Community contribution** by Dallas Pillen- thank
    you!): <https://github.com/archivematica/Issues/issues/799>
- Cannot create user with accented characters/diacritics:
    <https://github.com/archivematica/Issues/issues/261>
- AIP METS and pointer METS files reference outdated METS schema:
    <https://github.com/archivematica/Issues/issues/949>
- Cannot start a transfer if transfer name has diacritics:
    <https://github.com/archivematica/Issues/issues/1051>
- Non-default processing configuration is not copied over for zipped
    transfers (**Community contribution** by Wellcome Collection- thank
    you!): <https://github.com/archivematica/Issues/issues/771>
- Directory level AIP metadata is not indexed:
    <https://github.com/archivematica/Issues/issues/888>
- Descriptive metadata added via GUI is not indexed for searching:
    <https://github.com/archivematica/Issues/issues/547>
- External PIDs are not searchable in Archival storage (**Sponsored**
    by Piql/NHA- thank you!):
    <https://github.com/archivematica/Issues/issues/1006>
- Identifiers.json import fails if \'Bind PIDs\' config option is not
    set to \'yes\' (**Sponsored** by Piql/NHA- thank you!):
    <https://github.com/archivematica/Issues/issues/963>
- Ldap auth fails on dashboard (**Sponsored** by Piql/NHA- thank
    you!): <https://github.com/archivematica/Issues/issues/841>
- Cannot create storage service location via amclient (**Sponsored**
    by International Institute of Social History- thank you!):
    <https://github.com/archivematica/Issues/issues/905>
- It is difficult to combine status for different package types
    (**Community contribution** by Rockefeller Archive Center- thank
    you!): <https://github.com/archivematica/Issues/issues/972>
- Format identification errors are not being output from the FPR
    command (**Community contribution** by Wellcome Collection- thank
    you!): <https://github.com/archivematica/Issues/issues/882>
- Time zone setting not configurable (**Sponsored** by Piql/NHA- thank
    you!): <https://github.com/archivematica/Issues/issues/1143>
- Cannot store AIP with large files (**Community contribution** by
    Jorik van Kemenade- thank you!):
    <https://github.com/archivematica/Issues/issues/981>

And more! See <https://github.com/archivematica/Issues/milestone/11> for
full list of issues addresses in the 1.11 release.

#### Upgraded tools and dependencies

- Update to PRONOM v.96
    <https://github.com/archivematica/Issues/issues/791>

#### Known issues

Please note that due to [Issue
1149](https://github.com/archivematica/Issues/issues/1149) the package
replication functionality in the Storage Service does not work in this
release. We anticipate fixing in the near future in a point release.

#### End of life dependencies

Python 2 has reached end of life. The Archivematica delivery team and a
number of community contributors have been working on upgrading this
dependency. This release merges all Python 3 code that was ready in
advance of the release, while still supporting Python 2. Components
which have been upgraded and/or tested using Python 3 include:

- Dashboard: <https://github.com/archivematica/Issues/issues/810>
- Storage Service:
    <https://github.com/archivematica/Issues/issues/806> **Note**:
    Artefactual is not able to test some storage integrations, including
    Sword2, LOCKSS-o-matic and DSpace. If you can test these storage
    integrations and find any issues, please consider [filing an
    issue](https://github.com/archivematica/Issues/issues).
- amclient: <https://github.com/archivematica/Issues/issues/817>
- Automation tools:
    <https://github.com/archivematica/Issues/issues/815>
- Fixity: <https://github.com/archivematica/Issues/issues/814>
- am/compose: <https://github.com/archivematica/Issues/issues/804>
- Fido: <https://github.com/archivematica/Issues/issues/847>

We will continue to work toward full Python 3 use in upcoming releases.

## Archivematica 1.10.2

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.10.2).

*Release date*: 20 May 2020

This release fixes a critical security issue found in the Archivematica
dashboard that allows unauthorized users to access some parts of the
Administration tab.

This issue was discovered as a result of a security audit by Scholars
Portal. It was not discovered as a result of a breach. Scholars Portal
reported the issue to Artefactual privately via email. Once we became
aware of the issue, we began to develop the fix. Artefactual has also
implemented security reporting process documentation across
Archivematica-related GitHub repositories and changed issue templates to
reflect a more secure process. You can review Archivematica's security
reporting process here:
<https://github.com/artefactual/archivematica/security/policy>.

### Upgrading for 1.10.2

The fix can be easily installed since this issue only affects the
dashboard.

CentOS users relying on Archivematica packages should run:

    sudo yum -y update archivematica-dashboard
    sudo systemctl restart archivematica-dashboard

Automated installations using Ansible should deploy from our stable
branches: stable/1.9.x, stable/1.10.x or stable/1.11.x.

Alternately, a fix can be applied to the web server. The following
configuration snippet shows an updated Nginx server block with the
additional rule added.

    server {
       listen 80;
       client_max_body_size 256M;
       server_name _;
       location / {
           set $upstream_endpoint http://archivematica-dashboard:8000;
           proxy_set_header Host $http_host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_redirect off;
           proxy_buffering off;
           proxy_read_timeout 172800s;
           proxy_pass $upstream_endpoint;
       }

       # Directive to block access to admin pages in
       # Archivematica v1.11.0 or older.
       location ~ ^/administration/accounts/login/.+$ {
           return 404;
       }
    }

After the fix has been applied, please be sure to update passwords and
API keys:

- Change the password and API key for the Storage Service user:
    -- In the Storage Service, change the password for the Storage
       Service user that the Archivematica dashboard uses. This will
       also regenerate the API key for the Storage Service user.
    -- In the Archivematica dashboard, under Administration \> General,
       update the Storage Service user password and the API key to
       reflect the new password/key.
- Change the password for AtoM/Binder DIP upload.
- Review the PREMIS agent information to ensure that it is correct.

### Fixed for 1.10.2

- [1.11.1
    milestone](https://github.com/archivematica/Issues/milestone/14)

## Archivematica 1.10.1 and Storage Service 0.15.1 release notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.10.1_release_notes).

\'\'\'Release date: Oct 22 2019 \'\'\'

### Fixed for 1.10.1

- Job output isn\'t captured when task errors : [Issue
    873](https://github.com/archivematica/Issues/issues/873)
- EventIdentifier isn\'t written for Event: Name cleanup: [Issue
    890](https://github.com/archivematica/Issues/issues/890)
- Partial (and full) reingest removes mets:sourceMD from METS file:
    [Issue 914](https://github.com/archivematica/Issues/issues/914)
- Refine storage service user configuration: [Issue
    948](https://github.com/archivematica/Issues/issues/948)

## Archivematica 1.10 and Storage Service 0.15

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.10_and_Storage_Service_0.15_release_notes).

**Release date** September 5, 2019

### Supported environments for 1.10

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.10/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.10 and Storage Service 0.15 are supported for production
use in the following environments:

- Ubuntu 16.04 64-bit Server Edition
- Ubuntu 18.04 64-bit Server Edition
- CentOS 7 64-bit

For development purposes, most of our developers prefer to use Docker
containers. These and all above supported environments are linked from
the installation instructions above.

### Added for 1.10

#### Information Packaging (Backlog) Workflow Enhancements

Simon Fraser University has sponsored a development project to improve
the ability to store Transfers for a long period of time. The goal is to
improve the metadata quality of Transfers to reduce the risk of storing
them for a long period of time in a backlog. As a result of this
project:

- Transfers placed in backlog are now packaged as bags
- The Transfer METS file now records all preservation actions that
    took place during Transfer.
- The Appraisal Tab now handles packages with more than 1,000 files.
- A backlog can be populated from a new pipeline from transfers
    created by another pipeline.
- Documentation:
    <https://www.archivematica.org/en/docs/archivematica-1.10/user-manual/appraisal/appraisal/#appraisal>
- Issues (linked from epic):
    <https://github.com/archivematica/Issues/issues/391>

#### \"Vintage\" AIP handling

AIPS created in Archivematica prior to version 1.0 can't currently be
re-ingested in more recent versions (due to namespace collisions with
the use of PREMIS 2.1).

This change will make it possible to reingest these older AIPS into
Archivematica. This work is sponsored by the City of Vancouver Archives.

- Issue: <https://github.com/archivematica/Issues/issues/24>

#### LDAP support for Storage Service

The Archivematica Storage Service now supports LDAP integration. This
was sponsored by Piql for the Norwegian Health Archives.

- Issue: <https://github.com/archivematica/Issues/issues/680>

#### External PID declaration

This feature, sponsored by the International Institute of Social
History, allows users to include identifiers minted outside of
Archivematica in their transfer and written to the premis:object
metadata in the AIP METS file. This is done via an identifiers.json file
included in the transfer.

- Issue: <https://github.com/archivematica/Issues/issues/133>
- Documentation:
    <https://www.archivematica.org/en/docs/archivematica-1.10/user-manual/transfer/transfer/#transfer-pids>

#### Avalon Integration

Archivematica 1.10 has added the ability to integrate with [Avalon Media
System](https://www.avalonmediasystem.org/) through the automation
tools. This was sponsored by Northwestern University and Indiana
University through IMLS funding. The feature allows users to prepare and
store a DIP appropriate for upload the Avalon, and then have the
automation tools send it to Avalon for ingest into that system.

- Issue: <https://github.com/archivematica/Issues/issues/643>
- Documentation:
    <https://www.archivematica.org/en/docs/archivematica-1.10/admin-manual/installation-setup/integrations/integrations/#avalon-media-system-integration>

#### Include AIP UUID in bag-info.txt

This change adds the UUID of the AIP to the External-Identifier field of
the bag-info.txt file. This change is a **community contribution** by
Helen Sherwood-Taylor (Wellcome Collection)- thank you!

- Issue: <https://github.com/archivematica/Issues/issues/492>
- Documentation:
    <https://www.archivematica.org/en/docs/archivematica-1.10/user-manual/archival-storage/aip-structure/#bagit-doc>

#### Allow designation of ArchivesSpace repository using DSpace REST location

This feature allows designation of more than one ArchivesSpace
repository by enabling it via the DSpace REST location rather than
through the configuration in the Storage Service. This was a **community
contribution** by Hrafn Malmquist (University of Edinburgh)- thank you!

- Issue: <https://github.com/archivematica/Issues/issues/435>
- Documentation:
    <https://www.archivematica.org/en/docs/storage-service-0.15/administrators/#dspace-via-rest-api>

### Changed for 1.10

#### AIP METS in PREMIS 3

As a result of the vintage AIP work described above, we have upgraded
the AIP METS file to use PREMIS 3 exclusively. In previous versions it
had a mix of versions 2 and 3.

- Issue: <https://github.com/archivematica/Issues/issues/370>

#### API endpoint for manifest validation (beta)

As part of the Avalon integration described above, we added an endpoint
that can be called to validate a manifest. While this is currently only
implemented for the Avalon manifest, it could for example be extended in
the future for metadata.csv validation and similar.

- Issue: <https://github.com/archivematica/Issues/issues/618>
- Documentation:
    <https://wiki.archivematica.org/Archivematica_API#Validate>

#### Extended service callbacks

This change allows the creation of callbacks for AIP, AIC, and DIP
storage events. This was done in service to integration with SCOPE, a
DIP access platform in use by the Canadian Centre for Architecture, but
is widely applicable to other use cases.

- Issue: <https://github.com/archivematica/Issues/issues/147>

#### Storage Service packages tab tidy-up

This change was the result of a reported bug for the Storage Service
packages tab timing out- we addressed that issue but also tidied up the
tab to make it more generally usable. See the issue for discussion of
changes.

- Issue: <https://github.com/archivematica/Issues/issues/676>
- Documentation:
    <https://www.archivematica.org/en/docs/storage-service-0.15/administrators/#packages-tab>

#### Code formatting to be handled by black

The developer team has decided to use a code formatting tool (black) to
make formatting more consistent. Pull requests to Archivematica are now
checked with a linter to ensure consistency with black.

- Issue: <https://github.com/archivematica/Issues/issues/393>

#### Additions and improvements to the AMAUATs

The AMAUATs are the Archivematica Automated User Acceptance Tests.
Thanks to **sponsorship by Wellcome Collection** we have greatly
expanded the number of automated tests that run and made most of them
\"black box\" tests that run via the API- this means they are more
robust than tests that rely on the user interface, which can break
anytime the user interface changes in some way. In addition to these
improvements, to aid in the release process we have made the AMAUATs
have versions that go along with the Archivematica version being
released. Please see the AMAUAT repo for more information:
<https://github.com/artefactual-labs/archivematica-acceptance-tests>

### Fixed for 1.10

- A number of fixes related to custom structMap import have been
    **sponsored** in this release by International Institute of Social
    History. Thank you!
    -- Custom structMaps do not support nested directories:
       <https://github.com/archivematica/Issues/issues/283>
    -- Purpose of Verify structMap in ingest is unclear:
       <https://github.com/archivematica/Issues/issues/286>
    -- Custom structMaps labelled as structMap\_2:
       <https://github.com/archivematica/Issues/issues/633>
    -- We also added documentation for custom structMap import:
       <https://www.archivematica.org/en/docs/archivematica-1.10/user-manual/transfer/import-metadata/#import-metadata>
- Verify transfer checksums succeeding without verifying the
    checksums:
    <https://github.com/artefactual/archivematica/issues/1061>
- Parallel bzip2 algorithm isn\'t written to the pointer file when
    used: <https://github.com/archivematica/Issues/issues/714>
- metsrw cannot process unicode characters:
    <https://github.com/archivematica/Issues/issues/295>
- Deleted AIPs are not removed from S3:
    <https://github.com/archivematica/Issues/issues/696>
- Cannot store AIP in S3 us-west-2-region:
    <https://github.com/archivematica/Issues/issues/639>
- S3 bucket does not use the Region set in S3 space:
    <https://github.com/archivematica/Issues/issues/638>
- File list pane always removes last tag of a file (**Sponsored** by
    Simon Fraser University- thank you!):
    <https://github.com/archivematica/Issues/issues/472>
- Storage Service import\_aip leaves uncompressed AIP data in /tmp:
    <https://github.com/archivematica/Issues/issues/706>
- AgentArchives does not log out of ArchivesSpace (**Community
    contribution** by Hrafn Malmquist (University of Edinburgh)- thank
    you!): <https://github.com/artefactual-labs/agentarchives/issues/47>
- Storage Service sort by size does not increment correctly:
    <https://github.com/archivematica/Issues/issues/678>
- verify\_checksum PREMIS events have no agent information:
    <https://github.com/archivematica/Issues/issues/774>
- Versions shown for FPR tools are outdated:
    <https://github.com/archivematica/Issues/issues/191>
- Jhove failure event has result \"well-formed and valid\":
    <https://github.com/archivematica/Issues/issues/164>
- Create METS script loops after exception (**Community contribution**
    by Helen Sherwood-Taylor (Wellcome Collection)- thank you!):
    <https://github.com/archivematica/Issues/issues/620>
- Archivematica should pin exact package versions in requirements.txt
    for predictable deployments (**Community contribution** by Helen
    Sherwood-Taylor (Wellcome Collection)- thank you!):
    <https://github.com/archivematica/Issues/issues/634>
- Delete links are not consistent in the Packages tab of the Storage
    Service: <https://github.com/archivematica/Issues/issues/711>
- MCP server doesn\'t report when the Gearman server is unavailable
    (**Community contribution** by Alex Chan (Wellcome Collection)-
    thank you!): <https://github.com/archivematica/Issues/issues/553>
- Archivematica uses both bagit-python and bagit-java:
    <https://github.com/archivematica/Issues/issues/246>
- DSpace REST location does not fall back to default values
    (**Community contribution** by Hrafn Malmquist (University of
    Edinburgh)- thank you!):
    <https://github.com/archivematica/Issues/issues/458>
- Validate function of bind\_pids occurs too early in the microservice
    script: <https://github.com/archivematica/Issues/issues/776>
- Storage Service object-counting disabling option fails:
    <https://github.com/archivematica/Issues/issues/657>
- chunkids in manifest file do not match id in DuraCloud:
    <https://github.com/archivematica/Issues/issues/574>
- Archivematica attempts to delete files from transfer source:
    <https://github.com/archivematica/Issues/issues/646>
- Double replications being creation from first replication, not
    original (**Sponsored** by Piql for the Norwegian Health Archive
    -thank you!):
    <https://github.com/artefactual/archivematica-storage-service/issues/270>
- AtoM DIP upload link in Access tab is wrong:
    <https://github.com/archivematica/Issues/issues/411>
- Metadata-only DIP fails without format version:
    <https://github.com/archivematica/Issues/issues/857>

And more! For a complete list of fixes and changes please see:
<https://github.com/archivematica/Issues/milestone/6>

### Upgraded tools and dependencies for 1.10

- Ghostscript upgraded to 9.2.x across all platforms:
    <https://github.com/archivematica/Issues/issues/714>
- JHOVE upgraded to 1.20:
    <https://github.com/archivematica/Issues/issues/521>

### Deprecated for 1.10

[Issue 174](https://github.com/archivematica/Issues/issues/174) As of
Archivematica 1.10, Archivist\'s Toolkit integration has been removed.
Please see [this
announcement](https://groups.google.com/d/msg/archivematica/-LSHh3jGiQk/FlXJ-xnHCQAJ)
for more details.

## Archivematica 1.9.3

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.9.3).

*Release date*: 20 May 2020

This release fixes a critical security issue found in the Archivematica
dashboard that allows unauthorized users to access some parts of the
Administration tab.

This issue was discovered as a result of a security audit by Scholars
Portal. It was not discovered as a result of a breach. Scholars Portal
reported the issue to Artefactual privately via email. Once we became
aware of the issue, we began to develop the fix. Artefactual has also
implemented security reporting process documentation across
Archivematica-related GitHub repositories and changed issue templates to
reflect a more secure process. You can review Archivematica's security
reporting process here:
<https://github.com/artefactual/archivematica/security/policy>.

### Upgrading for 1.9.3

The fix can be easily installed since this issue only affects the
dashboard.

CentOS users relying on Archivematica packages should run:

    sudo yum -y update archivematica-dashboard
    sudo systemctl restart archivematica-dashboard

Automated installations using Ansible should deploy from our stable
branches: stable/1.9.x, stable/1.10.x or stable/1.11.x.

Alternately, a fix can be applied to the web server. The following
configuration snippet shows an updated Nginx server block with the
additional rule added.

    server {
       listen 80;
       client_max_body_size 256M;
       server_name _;
       location / {
           set $upstream_endpoint http://archivematica-dashboard:8000;
           proxy_set_header Host $http_host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_redirect off;
           proxy_buffering off;
           proxy_read_timeout 172800s;
           proxy_pass $upstream_endpoint;
       }

       # Directive to block access to admin pages in
       # Archivematica v1.11.0 or older.
       location ~ ^/administration/accounts/login/.+$ {
           return 404;
       }
    }

After the fix has been applied, please be sure to update passwords and
API keys:

- Change the password and API key for the Storage Service user:
    -- In the Storage Service, change the password for the Storage
       Service user that the Archivematica dashboard uses. This will
       also regenerate the API key for the Storage Service user.
    -- In the Archivematica dashboard, under Administration \> General,
       update the Storage Service user password and the API key to
       reflect the new password/key.
- Change the password for AtoM/Binder DIP upload.
- Review the PREMIS agent information to ensure that it is correct.

### Fixed for 1.9.3

- [1.11.1
    milestone](https://github.com/archivematica/Issues/milestone/14)

## Archivematica 1.9.2 release notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.9.2_release_notes).

\'\'\'Release date: Friday June 28, 2019 \'\'\'

For more information about Archivematica 1.9.x, please see the release
notes for [Archivematica
1.9.0](Archivematica_1.9_and_Storage_Service_0.14_release_notes).

### Upgrading for 1.9.2

If you are upgrading from 1.9.0 to 1.9.2, please ensure that you run the
following command:

    curl -XPUT 'http://localhost:9200/aips,aipfiles,transfers,transferfiles/_settings' \
      -H "Content-Type: application/json" \
      -d '{"index.mapping.total_fields.limit": 10000, "index.mapping.depth.limit": 1000 }'

This is not required for upgrading from 1.8.x to 1.9.2.

For more information on upgrading, see [Upgrading
Archivematica](https://www.archivematica.org/en/docs/archivematica-1.9/admin-manual/installation-setup/upgrading/upgrading/#upgrade)
in the documentation.

### Fixed for 1.9.2

- Index AIP errors due to asynchronous processing: [Issue
    425](https://github.com/archivematica/Issues/issues/425)
- Error trying to connect to MCP server: [Issue
    624](https://github.com/archivematica/Issues/issues/624)

## Archivematica 1.9.1 and Storage Service 0.14.1 release notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.9.1_and_Storage_Service_0.14.1_release_notes).

*Release date*: April 11, 2019

For more information about Archivematica 1.9.x, please see the release
notes for [Archivematica
1.9.0](Archivematica_1.9_and_Storage_Service_0.14_release_notes).

### Upgrading for 1.9.1

If you are upgrading from 1.9.0 to 1.9.1, please ensure that you run the
following command:

    curl -XPUT 'http://localhost:9200/aips,aipfiles,transfers,transferfiles/_settings' \
    -H "Content-Type: application/json" \
    -d '{"index.mapping.total_fields.limit": 10000, "index.mapping.depth.limit": 1000 }'

This is not required for upgrading from 1.8.x to 1.9.1.

For more information on upgrading, see [Upgrading
Archivematica](https://www.archivematica.org/en/docs/archivematica-1.9/admin-manual/installation-setup/upgrading/upgrading/#upgrade)
in the documentation.

### Fixed for 1.9.1

- Error in rebuilding elasticsearch AIP index: [Issue
    595](https://github.com/archivematica/Issues/issues/595)
- AIP index error: *Limit of total fields \[1000\] in index \[aips\]
    has been exceeded*: [Issue
    608](https://github.com/archivematica/Issues/issues/608)
- Cannot approve DSpace file-only transfers: [Issue
    468](https://github.com/archivematica/Issues/issues/468)
- Can\'t build Docker files: [Issue
    617](https://github.com/archivematica/Issues/issues/617)
- Pointer files are not being saved when Storage Service is on a
    different VM: [Issue
    599](https://github.com/archivematica/Issues/issues/599)
- indexAIP task fails when using S3 aipstore: [Issue
    559](https://github.com/archivematica/Issues/issues/559).
    -- **Note**: this issue was also found to occur when the Storage
       Service and dashboard were deployed on different VMs. The fix
       addresses both situations.
- Reingest failing on 1.9.1: [Issue
    594](https://github.com/archivematica/Issues/issues/594)

## Archivematica 1.9 and Storage Service 0.14 release notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.9_and_Storage_Service_0.14_release_notes).

Release date: **March 6, 2019**

### Supported environments for 1.9

Please see the [installation
instructions](https://www.archivematica.org/en/docs/archivematica-1.9/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.9 and Storage Service 0.14 are supported for production
use in the following environments:

- Ubuntu 16.04 64-bit Server Edition
- Ubuntu 18.04 64-bit Server Edition
- CentOS 7 64-bit

For development purposes, most of our developers prefer to use Docker
containers. These and all above supported environments are linked from
the installation instructions above.

### Added for 1.9

#### AIP Migration

This feature creates a new endpoint for the storage service API. It will
allow a client to make a request to the API to move an AIP from one
storage location to another storage location (of the same type). The
storage service is aware of the move so there is no need to re-index
(compared to moving AIPs manually).

The primary issue for this change is archivematica/Issues: [Issue
\#71](https://github.com/archivematica/Issues/issues/71)

This work was sponsored by the Museum of Modern Art. Thank you!

#### Stored DIP deletion

This enhancement adds a new option to delete a DIP to the storage
service user interface.

This change is described by artefactual/archivematica-storage-service:
[Issue
\#319](https://github.com/artefactual/archivematica-storage-service/issues/319)

For documentation, see
[Packages](https://www.archivematica.org/en/docs/storage-service-0.14/administrators/#packages-tab)
in the Storage Service docs.

This work was sponsored by Simon Fraser University Archives. Thank you!

### Changed for 1.9

#### Increased internationalization

Archivematica 1.7 included user interface translation support (see [PR
506](https://github.com/artefactual/archivematica/pull/506)). This work
covered a majority of the user interface but did not include the text
describing jobs executed as part of the microservices. Those text
descriptions are held in the application database making it difficult to
maintain multiple translations.

This change moves these text descriptions out of the database and into
JSON files. This makes it much easier to add new translations and
maintain them over time.

Please note that while we transition to a new platform for translation
we are currently not accepting any newly translated strings for
Archivematica. For more info please see the [notification on the
Archivematica Google
Group](https://groups.google.com/d/msg/archivematica/6qMM1KJbWp8/LuPO_VqyEAAJ).

This enhancement is described by artefactual/archivematica [Issue
1101](https://github.com/artefactual/archivematica/issues/1101).

This work was sponsored in part by the Canadian Council of Archives.
Thank you!

#### Backend FPR changes

The Django app for the FPR was difficult to maintain so it has been
moved to the dashboard.

Issues: [Issue
\#181](https://github.com/archivematica/Issues/issues/181) and [Issue
\#213](https://github.com/archivematica/Issues/issues/213)

#### File identification changes

To address an issue with [file
identification](https://github.com/archivematica/Issues/issues/485) we
have implemented a change in how file identification tools are chosen in
this release. Users now enable their chosen command (Fido, Siegfried or
file extension) in Preservation Planning, and the processing
configuration decision in the dashboard is now a simple Yes/No on
whether or not to identify the files. This brings file identification
more in line with other FPR rules and processing configuration
decisions.

Instructions on how to change the identification command in the FPR are
available in the
[Identification](https://www.archivematica.org/en/docs/archivematica-1.9/user-manual/preservation/preservation-planning/#identification)
section of the Preservation Planning documentation.

Please note - if you have the file identification decision point set in
your processing configuration, you need to reset it to \"Yes\" or \"No\"
as it will default to \"None\" after upgrade.

### Fixed for 1.9

- Dataverse- Can\'t answer \'yes\' to \'Delete Packages After
    Extraction\': [Issue
    269](https://github.com/archivematica/Issues/issues/269)
- Dataverse- Multiple authors not captured in Dataverse METS: [Issue
    278](https://github.com/archivematica/Issues/issues/278)
- Logged-in user not being captured as PREMIS agent [Issue
    529](https://github.com/archivematica/Issues/issues/529)
- html lang attribute always reads \'en\' (English): [Issue
    297](https://github.com/archivematica/Issues/issues/297)
- Dashboard API returns 500 error when unit status cannot be
    determined: [Issue
    216](https://github.com/archivematica/Issues/issues/216)
- Errors in start\_transfer API request do not return useful JSON
    responses [Issue
    354](https://github.com/archivematica/Issues/issues/354) -community
    contribution by Hillel Arnold- thank you!
- Pressing \"Return\" keyboard button in Archival Storage search sends
    previously used term as search input [Issue
    271](https://github.com/archivematica/Issues/issues/271)
- AIP store fails if PREMIS agent name has accented characters [Issue
    260](https://github.com/archivematica/Issues/issues/260)
- pip problems when deploying SS with ansible [Issue
    455](https://github.com/archivematica/Issues/issues/455)
- Dashboard can\'t connect to MCPServer after a period of inactivity
    [Issue 464](https://github.com/archivematica/Issues/issues/464)
- Manually normalized preservation derivatives cannot be validated
    [Issue 331](https://github.com/archivematica/Issues/issues/331)
- AIC number added via form in Transfer tab does not get saved [Issue
    311](https://github.com/archivematica/Issues/issues/311)
- Restructure DIP for CONTENTdm fails [Issue
    333](https://github.com/archivematica/Issues/issues/333)
- AIP storage locations not correctly shown in \"Job: Store AIP
    location\" [Issue
    456](https://github.com/archivematica/Issues/issues/456)
- Dashboard status API can return status \'PROCESSING\' for completed
    SIPs [Issue 262](https://github.com/archivematica/Issues/issues/262)
- Cannot connect to ArchivesSpace with non-standard connection details
    [Issue 409](https://github.com/archivematica/Issues/issues/409)

And more! Please see [the 1.9 milestone in
Github](https://github.com/archivematica/Issues/milestone/4?closed=1)
for a complete list of fixes in this release.

#### Upgraded tools and dependencies for 1.9

- Elasticsearch has been upgraded from version 1.x to version 6.x.
    This should improve performance and ease security concerns with the
    previous version of Elasticsearch. If you are upgrading
    Archivematica from a previous version, please be sure to follow the
    [upgrade
    instructions](https://www.archivematica.org/en/docs/archivematica-1.9/admin-manual/installation-setup/upgrading/upgrading/#upgrade)
    in the documentation.

## Archivematica 1.8.1 release notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.8.1_release_notes).

*Release date*: January 10th 2019

This point release addresses a couple of bugs in the 1.8 release. Note
that these fixes are only relevant under one of two circumstances: if
you have upgraded from 1.7.x or earlier to 1.8, or if your installation
uses RPMs.

### Supported environments for 1.8.1

There are no changes to supported environments in this release.

Please continue to follow the installation instructions
[here](https://www.archivematica.org/en/docs/archivematica-1.8/admin-manual/installation-setup/installation/installation/#installation).

### Fixed for 1.8.1

- Transfers can\'t be started in AM18 RPM upgrades:
    <https://github.com/archivematica/Issues/issues/360>
- PREMIS version number isn\'t updated on upgrades from 1.7.x to
    1.8.x: <https://github.com/archivematica/Issues/issues/353>

## Archivematica 1.8 and Storage Service 0.13

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.8_and_Storage_Service_0.13_release_notes).

*Release date*: Nov 20th 2018

### Supported environments for 1.8

Please see installation instructions [link
here](https://www.archivematica.org/en/docs/archivematica-1.8/admin-manual/installation-setup/installation/installation/#installation).

Archivematica 1.8 and Storage Service 0.13 are supported for production
use in the following environments:

- Ubuntu 16.04 64-bit Server Edition
- Ubuntu 18.04 64-bit Server Edition
- CentOS 7 64-bit

For development purposes, most of our developers prefer to use Docker
containers. These and all above supported environments are linked from
the installation instructions above.

### Added for 1.8

#### Dataverse integration

Archivematica can now be configured to use a
[Dataverse](https://dataverse.org/) research data repository as a
transfer source location. Dataverse transfer source locations can be
configured to display all available datasets or a subset of them.
Datasets are retrieved directly using the Dataverse API and processed
using a new "Dataverse" transfer type. New Dataverse specific processing
includes:

- fixity checking using checksums generated by dataverse
- retrieval of derivative and metadata files associated with tabular
    data files
- creation of a Dataverse METS file describing the dataset as
    retrieved from Dataverse
- Dataverse metadata included in the AIP METS

Some advanced or more complex use cases are not fully supported, such as
handling of datasets with restricted files, versioning of datasets and
reingest of datasets. For a full list of known issues and enhancement
ideas, refer to the [Archivematica issues repository using Dataverse
label](https://github.com/archivematica/Issues/labels/OCUL%3A%20AM-Dataverse)
and the [Archivematica-Dataverse Integration Project
Wiki](https://wiki.archivematica.org/Dataverse).

This work was sponsored by [Scholars
Portal](https://scholarsportal.info/), a service of the Ontario Council
of University Libraries (OCUL). Thank you!

- Issue: See [waffle
    board](https://waffle.io/artefactual/archivematica?label=OCUL:%20AM-Dataverse)
    for all issues with the Dataverse label.
- Documentation: [Dataverse
    Integration](https://www.archivematica.org/en/docs/archivematica-1.8/user-manual/transfer/dataverse/)

#### Public URL

Archivematica now has a concept of a public URL in the general
configuration. Archivematica usually registers itself with the Storage
Service, but if you have deployed Archivematica in an environment where
the URL or IP address changes frequently (i.e. in some Docker
environments) this can cause issues. In these types of environments,
users can now declare a stable public URL that Archivematica can use to
register with the Storage Service.

This work was sponsored by Jisc. Thank you!

- Issue:
    [1140](https://github.com/artefactual/archivematica/issues/1140)
- Documentation: [General
    configuration](https://www.archivematica.org/docs/archivematica-1.8/admin-manual/installation-setup/customization/dashboard-config/#admin-dashboard-general)

#### Package storage in DSpace via its REST API

Since Archivematica 1.6 it\'s been possible to store AIPs in DSpace, but
they have been stored via SWORD. Some users have the need/desire to
store packages in DSpace via the REST API. This is now possible in
Storage Service 0.13.

This work was undertaken by Hrafn Malmquist at University of Edinburgh,
with assistance from developers at Artefactual Systems. Thank you!

- Issue:
    [391](https://github.com/artefactual/archivematica-storage-service/issues/391)
- Documentation: [DSpace via SWORD2 or REST
    API](https://www.archivematica.org/en/docs/storage-service-0.13/administrators/#dspace-via-sword2-api-or-dspace-via-rest-api)

### Changed for 1.8

Enhancements or major fixes.

#### Automatic approval of transfers

It is no longer necessary to approve transfers started in the user
interface. By default, a checkbox is ticked for the transfer to
automatically be approved- users may uncheck the box and approve their
transfers manually if desired.

This enhancement was sponsored by Jisc. Thank you!

- Issue:
    [1139](https://github.com/artefactual/archivematica/issues/1139)
- Documentation: [Process a
    transfer](https://www.archivematica.org/en/docs/archivematica-1.8/user-manual/transfer/transfer/#process-transfer)

#### Streamline checksum verification

This enhancement de-duplicates checksum verification in Archivematica,
which helps to improve the performance of Archivematica in processing
large transfers (many files and/or large files). This enhancement
includes three changes:

- Remove the \"Verify checksums generated on ingest\" micro-service
- Enhance the \"Verify AIP\" micro-service to bulk query the database
    for transfer-generated checksums and then verify that they match
    what is documented in the bag-generated manifest-.txt.
- Have \"Verify AIP\" create an AIP-level \"fixity check\"
    PREMIS:EVENT that it can pass to the Storage Service, which will
    document this verification in the pointer file.

This should not impact regular workflows, but it is worth noting that
there is no AIP-level fixity check PREMIS event for uncompressed AIPs,
which don\'t have pointer files. For uncompressed AIPs, there are still
object-level fixity events in place. Note that there is an issue in the
Archivematica Issues repository regarding this note - [Problem:
uncompressed AIPs need pointer files
\#32](https://github.com/artefactual/archivematica-storage-service/issues/324)

This work was sponsored by Columbia University Library. Thank you!

- Issue:
    [918](https://github.com/artefactual/archivematica/issues/918)

#### Indexing can be enabled/disabled for Transfers and/or Archival Storage

Previously, the ElasticSearch index feature could be disabled globally
as a scalability measure since indexing consumes a lot of resources.
However, this also disabled Backlog and Appraisal features (which also
uses indexing) and which some users still wanted to access. As of
release 1.8, Archivematica can be deployed to run with indexing enabled
just for Transfers (Backlog and Appraisal enabled), just for Archival
Storage (Backlog and Appraisal disabled), for both indexes, or for none.

- Issue:
    [1172](https://github.com/artefactual/archivematica/issues/1172)
- Documentation: [Installation \>
    Elasticsearch](https://www.archivematica.org/docs/archivematica-1.8/admin-manual/installation-setup/installation/installation/#elasticsearch)

#### Configure email settings

This change improves the ways that the email client in Archivematica can
be configured, including allowing an administrator to set the sender
email address for emails sent by Archivematica (i.e. normalization
reports, failure reports) to comply with local IT requirements.

This work was sponsored by Jisc. Thank you!

- Issue:
    [1128](https://github.com/artefactual/archivematica/issues/1128)
- Documentation: [Email notification
    configuration](https://www.archivematica.org/docs/archivematica-1.8/admin-manual/installation-setup/customization/customization/#email-notification-configuration)

#### Download processing configuration and reset to default

Previous versions of Archivematica introduced the ability to add custom
processing configurations, but users had to retrieve the custom
configuration file via the command line to use it. There is now a
download button on Administration \> Processing configuration so that
you can download the processing config from the user interface.

You can also reset a processing configuration to the installation
pre-set by clicking on the new reset button on Administration \>
Processing configuration.

The documentation for using a custom processing configuration has also
been updated.

This work was sponsored by Jisc. Thank you!

- Issue:
    [1138](https://github.com/artefactual/archivematica/issues/1138),
    [800](https://github.com/artefactual/archivematica/issues/800)
- Documentation: [Processing configuration (user
    manual)](https://www.archivematica.org/en/docs/archivematica-1.8/user-manual/administer/dashboard-admin/#processing-configuration),
    [Processing configuration (administrator
    manual)](https://www.archivematica.org/en/docs/archivematica-1.8/admin-manual/installation-setup/customization/dashboard-config/#processing-configuration),
    [Using a custom processing configuration
    file](https://www.archivematica.org/en/docs/archivematica-1.8/admin-manual/installation-setup/customization/dashboard-config/#using-a-custom-processing-configuration-file)

#### MCP batching for scalability & performance

This feature refactors how tasks are scheduled, executed & managed
within Archivematica, by grouping tasks into batches. It introduces
processing efficiencies that significantly decrease the processing power
and time required to complete Transfer and Ingest. It includes new
configuration options to further optimize processing efficiency for
particular types of Transfers (e.g. few large files vs. many small
files) and for different deployment patterns (e.g. installing components
across multiple machines).

This work was sponsored by Jisc. Thank you!

- Issue:
    [938](https://github.com/artefactual/archivematica/issues/938)
- Documentation: [Scaling
    Archivematica](https://www.archivematica.org/en/docs/archivematica-1.8/admin-manual/installation-setup/customization/scaling-archivematica/)

#### Binder integration improvements

Archivematica has had an integration with
[Binder](https://binder.readthedocs.io/en/latest/user-manual/overview/intro.html)
for several years. Binder is an open-source web application for managing
time-based media and born-digital artworks. Binder depends on
integration with both Archivematica and TMS (The Museum System).

Since Binder is built off of [AtoM](https://www.accesstomemory.org/),
much of the integration configuration was repurposed from the AtoM
integration. Archivematica 1.8 makes it explicit, for example, that the
job \"DIP Upload to AtoM\" is actually \"DIP Upload to AtoM/Binder\". In
the Administration tab, the configuration section for AtoM has also been
renamed to include Binder.

Enhancing the Binder integration itself, Archivematica\'s transfer tab
now includes an \"Access system ID\" box. This allows users to
pre-populate an access system ID for AtoM or Binder, so that DIPs can be
automatically uploaded without having to stop at the Upload DIP
microservice. Users can still use the Upload DIP popup if desired.

Finally, we\'ve added documentation on using Binder with Archivematica.

This work was sponsored by Tate. Thank you!

- Documentation: [Binder
    integration](https://www.archivematica.org/en/docs/archivematica-1.8/admin-manual/installation-setup/integrations/integrations/#binder-integration),
    [Using Binder with
    Archivematica](https://www.archivematica.org/en/docs/archivematica-1.8/admin-manual/installation-setup/integrations/binder-setup/#binder-setup),
    [Upload a DIP to
    Binder](https://www.archivematica.org/en/docs/archivematica-1.8/user-manual/access/access/#upload-a-dip-to-binder)
- Issues: [23](https://github.com/archivematica/Issues/issues/23)

#### Translations

First added in 1.7, translations in Archivematica are growing! In this
release, we\'ve pulled in translations for Archivematica.org, the
documentation, the FPR, the Storage Service, and the Archivematica
interface. The biggest part that is still missing is the
Archivematica\'s workflow engine - that is, all of the microservice and
job names in the interface. We are planning to include workflow
translations in 1.9.

Thanks to our wonderful community of translators on
[Transifex](https://www.transifex.com/artefactual/archivematica/dashboard/),
Archivematica resources can now be translated from English into French,
Spanish, Japanese, Portuguese, Brazilian Portuguese, and Swedish. Note
that the completeness of each language for each resource depends on
volunteer contributions in Transifex.

This work was originally sponsored by the Canadian Council on Archives
through a DHCP (Documentary Heritage Community Programs) grant. Thank
you!

- Issue: [231](https://github.com/archivematica/Issues/issues/231)
- Documentation:
    [Languages](https://www.archivematica.org/en/docs/archivematica-1.8/user-manual/administer/dashboard-admin/#language-choice),
    [Translating
    Archivematica](https://www.archivematica.org/en/docs/archivematica-1.8/user-manual/translations/translations/#translations)

#### File format identification updates

Archivematica 1.8 is now up to date with PRONOM v.94! For more
information on new data added to PRONOM, check the [PRONOM release
notes](http://www.nationalarchives.gov.uk/aboutapps/pronom/release-notes.xml).

This work was sponsored by the Denver Art Museum. Thank you!

#### Thumbnail normalization changes

It is now easier to configure whether or not, and how, thumbnails are
created. In the processing configuration, users can choose between yes,
normalize for thumbnails, no, do not normalize for thumbnails, or yes,
do so but only if there is a default rule in place. For users who do not
need thumbnails this could make their processing faster.

This work was sponsored by Columbia University Library. Thank you!

- Issue:
    [1022](https://github.com/artefactual/archivematica/issues/1022)
- Documentation: [Processing Configuration
    Fields](https://www.archivematica.org/en/docs/archivematica-1.8/user-manual/administer/dashboard-admin/#processing-config-fields)

### Fixed for 1.8

- [Validate preservation derivatives
    hangs](https://github.com/archivematica/Issues/issues/44) Sponsored
    by Jisc- thank you!
- [Zipped bag transfers cannot be approved via an API
    call](https://github.com/archivematica/Issues/issues/221)
    **Community contribution** by Hillel Arnold- thank you!
- [AIP verification fails for Zipped bag transfers containing
    .DS\_Store files in object
    directory](https://github.com/archivematica/Issues/issues/214)
    **Community contribution** by Hillel Arnold- thank you!
- [Can\'t use package API endpoint if Transfer Source is
    unknown](https://github.com/archivematica/Issues/issues/21)
    Sponsored by Jisc- thank you!
- [MySQL aborting transactions under heavy
    load](https://github.com/artefactual/archivematica/issues/1198)
    Sponsored by Jisc- thank you!
- [Cannot create spaces via
    API](https://github.com/archivematica/Issues/issues/36) Sponsored by
    Jisc- thank you!
- [Cannot create default locations via
    API](https://github.com/archivematica/Issues/issues/37) Sponsored by
    Jisc- thank you!
- [premis:originalName value of unpacked packages should not be
    normalized](https://github.com/artefactual/archivematica/issues/1094)
    Sponsored by the International Institute of Social History- thank
    you!
- [unapproved\_transfers endpoint throws a 500
    error](https://github.com/archivematica/Issues/issues/252) fixed
    with contributions by Hillel Arnold and the International Institute
    of Social History- thank you!
- [ASCII codes can\'t decode when the filename contains a
    backtick](https://github.com/archivematica/Issues/issues/16)
    Sponsored by the International Institute of Social History- thank
    you!
- [AIP re-ingest
    fails](https://github.com/archivematica/Issues/issues/42)
- [PREMIS events from previous transfers are
    re-appearing](https://github.com/archivematica/Issues/issues/43)
    Sponsored by Jisc- thank you!
- [Metadata reingest fails when dc:type is
    null](https://github.com/artefactual/archivematica/issues/1132)
- [Use 7-zip without compression (Copy)
    mode](https://github.com/archivematica/Issues/issues/46)
- [Cannot store AIP in DSpace due to file extension
    returned](https://github.com/archivematica/Issues/issues/69)
- [DSpace REST login error in
    SS](https://github.com/archivematica/Issues/issues/123)
- [Unable to edit DSpace REST Space settings in
    SS](https://github.com/archivematica/Issues/issues/124)
- [Packages cannot be stored in DSpace via its REST
    API](https://github.com/artefactual/archivematica-storage-service/issues/391)
- [Metadata added before \"Approve Transfer\"
    disappears](https://github.com/archivematica/Issues/issues/140)
- [Generate AIP METS fails for bag SIPs if bag-info.txt has multiple
    instances of the same
    label](https://github.com/archivematica/Issues/issues/173)
    **Community contribution** by Hillel Arnold- thank you!
- [Zip files with diacritic characters are failing to
    extract](https://github.com/artefactual/archivematica/issues/1104)
    Sponsored by the International Institute of Social History- thank
    you!
- [restructureBagForComplianceFileUUIDsAssigned needs to create
    intermediate directories for Zipped bag
    transfers](https://github.com/archivematica/Issues/issues/220)
    -**Community contribution** by Hillel Arnold. Thank you!
- [Ingest fails if Archivematica isn\'t connected to the
    Internet](https://github.com/artefactual/archivematica/issues/1050)
- [Can\'t store encrypted uncompressed
    AIPs](https://github.com/archivematica/Issues/issues/294)
- [Can\'t add AIC number through metadata
    form](https://github.com/archivematica/Issues/issues/308)
- [GPG key generation doesn\'t work in Ubuntu
    18.04](https://github.com/archivematica/Issues/issues/306)
- [Cannot save settings on general settings form in
    1.8](https://github.com/archivematica/Issues/issues/307)
- [Rights.csv metadata is not imported to METS
    file](https://github.com/archivematica/Issues/issues/305)
- [Cannot create more than one SIP from a
    transfer](https://github.com/archivematica/Issues/issues/270)
- [Archivematica making multiple copies of large
    transfers](https://github.com/artefactual/archivematica/issues/1207)
- [Large transfers don\'t show up in the
    dashboard](https://github.com/archivematica/Issues/issues/280)
- [Create SIP fails when directories contain
    UUIDs](https://github.com/archivematica/Issues/issues/192)
    **Community contribution** by Jason Jordan- thank you!
- [Can\'t arrange a SIP from backlog with long
    names](https://github.com/archivematica/Issues/issues/53)
- [Normalization output formatting
    error](https://github.com/archivematica/Issues/issues/151)
- [Package names are being
    modified](https://github.com/archivematica/Issues/issues/201)
- [Choosing AtoM/Binder/AT/AS config is
    unnecessary](https://github.com/archivematica/Issues/issues/55)
- [Hard to know which formats are related to which PRONOM IDs in
    FPR](https://github.com/archivematica/Issues/issues/132)

### Upgraded tools and dependencies for 1.8

- Fido has been upgraded to version 1.3.12
- Siegfried has been upgraded to version 1.7.10
- FITS has been upgraded to version 1.1.0
- gunicorn has been upgraded to version 19.9.0

### End of life dependencies for 1.8

#### Archivists\' Toolkit integration

Archivists\' Toolkit has been deprecated since 2013. The Archivists\'
Toolkit DIP upload feature has not had active development or testing
since then. There are no plans to start testing or to fix any problems
with the feature. As a result, there is a [proposal deprecate this
feature in Archivematica
1.9](https://github.com/archivematica/Issues/issues/174). Community
response is welcome via a comment on the issue in GitHub.

### Known issues for 1.8

- There is a [bug](https://github.com/archivematica/Issues/issues/333)
    preventing the CONTENTdm workflow in this release. There will be a
    patch available with a fix.

## Archivematica 1.7.2 release notes

[Original release notes](https://wiki.archivematica.org/Archivematica_1.7.2_release_notes)

**Released**: September 12, 2018.

### New in 1.7.2

[Support for Ubuntu 18.04 - Issue
119](https://github.com/archivematica/Issues/issues/119)

**Note:** Ubuntu 18.04 is considered **experimental** for this release.
We anticipate it being fully supported in version 1.8.

**Archivematica 1.7.2 will be the last release supported on Ubuntu
14.04.**

### Fixed for 1.7.2

- [Upload DIP task restarts when mcp-server is restarted - Issue
    112](https://github.com/archivematica/Issues/issues/112)
- [Upload DIP to ArchivesSpace not working - Issue
    1112](https://github.com/artefactual/archivematica/issues/1112)
- [archivespaceids.csv attempts to match derivatives to originals
    -Issue
    1034](https://github.com/artefactual/archivematica/issues/1034)
- [disabling ES search appears to break
    dspace\_handle\_to\_archivesspace and post\_store\_aip\_callback -
    Issue
    1174](https://github.com/artefactual/archivematica/issues/1174)
- [ghostscript to-PDF normalization command claims to create PDF/A 1a
    when in fact it creates PDF/A 1b - Issue
    1158](https://github.com/artefactual/archivematica/issues/1158)
- [\"Upload DIP\" task restarts when mcp-server is restarted - Issue
    112](https://github.com/archivematica/Issues/issues/112)

## Storage Service 0.12 release notes

[Original release notes](https://wiki.archivematica.org/Storage_Service_0.12_Release_Notes)

**Released** September 12, 2018.

### New in  0.12

#### Asynchronous processing

**Sponsored** by Jisc

- [Issue
    374](https://github.com/artefactual/archivematica-storage-service/issues/374)

This is a performance enhancement that decreases the possibility of
timeouts by moving packages asynchronously.

#### Support for S3 Storage

**Sponsored** by Jisc

Amazon S3 storage is now supported for AIP storage location.

- [Issue
    339](https://github.com/artefactual/archivematica-storage-service/issues/339)

### Changed for 0.12

#### Move files directly

**Sponsored** by Columbia University Library

- [Issue
    314](https://github.com/artefactual/archivematica-storage-service/issues/314)

This is an efficiency enhancement: files are now moved in one step
instead of two if both locations are local. Previously, the Storage
Service always moved files in two moves.

### Fixed for 0.12

- Cannot store compressed AIP in non-local file systems [Issue
    145](https://github.com/archivematica/Issues/issues/145)
- Implement new style of Python classes [Issue
    332](https://github.com/artefactual/archivematica-storage-service/issues/332)
- Allow lower case input in aip reingest API [Issue
    325](https://github.com/artefactual/archivematica-storage-service/issues/325)
- Pointer file creation causes unnecessary move operation [Issue
    365](https://github.com/artefactual/archivematica-storage-service/issues/365)
- Locations can\'t be created via the API [Issue
    367](https://github.com/artefactual/archivematica-storage-service/issues/367)
- SWORD API points can\'t be called in certain configurations [Issue
    312](https://github.com/artefactual/archivematica-storage-service/issues/312)

## Archivematica 1.7.1 release notes

[Original release notes](https://wiki.archivematica.org/Archivematica_1.7.1_release_notes)

### Changes for 1.7.1

This point release incorporates performance improvement development work
sponsored by Columbia University Library.

#### Changes to MCPClient and MCPServer

In order to improve Archivematica\'s performance (processing time),
MCPClient can now be configured to stop sending tool output through the
job scheduler and MCPServer can now be configured to require only the
return code from client tasks

This work was sponsored by Columbia University Library. Thank you!

- [Documentation](https://www.archivematica.org/en/docs/archivematica-1.7/admin-manual/installation-setup/customization/task-config/)
- Pull requests:
    [PR1075](https://github.com/artefactual/archivematica/pull/1075),
    [PR1077](https://github.com/artefactual/archivematica/pull/1077),
    [PR1078](https://github.com/artefactual/archivematica/pull/1078)

## Storage Servivce 0.11.1 Release Notes

[Original release notes](https://wiki.archivematica.org/Storage_Service_0.11.1_Release_Notes)

### Fixed for 1.7.1

- Bugfix:
    [PR350](https://github.com/artefactual/archivematica-storage-service/pull/350)
- Bugfix:
    [PR351](https://github.com/artefactual/archivematica-storage-service/pull/351)

## Archivematica 1.7 and Storage Service 0.11 Release Notes

[Original release notes](https://wiki.archivematica.org/Archivematica_1.7_and_Storage_Service_0.11_release_notes)

**Released** May 1, 2018.

Archivematica 1.7/Storage Service 0.11 has several new features, as well
as enhancements to existing features, bug fixes and updated tools. Below
you\'ll find a short description of each feature as well as links to the
relevant documentation and code changes. Thank you to everyone who has
sponsored the work that is included in this release - your dedication to
making Archivematica better is appreciated by the whole community!

This release also includes several bugfixes, especially related to
packaging. We\'ve also been concentrating on improving the overall
[Archivematica
documentation](https://www.archivematica.org/docs/archivematica-1.7/).

### Supported environments for 1.7

Installation instructions are available
[here](https://www.archivematica.org/en/docs/archivematica-1.7/admin-manual/installation-setup/installation/installation/#installation).

Archivematica can be installed using packages or Ansible scripts in
either CentOS/Red Hat or Ubuntu environments. It can also be installed
using Docker. At this time, installation instructions are provided for
officially tested and supported installation environments:

- [Automated install on Ubuntu (14.04 and 16.04) using
    Ansible](https://www.archivematica.org/en/docs/archivematica-1.7/admin-manual/installation-setup/installation/install-ansible/#install-ansible)
- [install of OS packages on CentOS/Red
    Hat](https://www.archivematica.org/en/docs/archivematica-1.7/admin-manual/installation-setup/installation/install-centos/#install-pkg-centosManual)

[Manual install of OS packages on Ubuntu (14.04 and
16.04)](https://www.archivematica.org/en/docs/archivematica-1.7/admin-manual/installation-setup/installation/install-ubuntu/#install-pkg-ubuntu)
is documented but not officially supported.

Installing Archivematica using
[Docker](https://www.archivematica.org/en/docs/archivematica-1.6/admin-manual/installation/installation/#docker)
is not officially supported for production deployments. However, it is
the preferred development environment for those who work on
Archivematica\'s code.

If you are upgrading from a previous version of Archivematica, please
see the [upgrading
instructions](https://www.archivematica.org/en/docs/archivematica-1.7/admin-manual/installation-setup/upgrading/upgrading/#upgrade).

### Added for 1.7

#### Internationalization/localization

Translation hooks have been added to the Archivematica user interface,
the Storage Service, the documentation, and the Archivematica website.
This work will support the translation of those resources into many
languages through Artefactual\'s current localization platform,
[Transifex](https://www.transifex.com). Note that translation hooks for
Archivematica workflow components (microservice names, job names, and
drop-down options) will be added in Archivematica 1.8.

This work was sponsored by the [Canadian Council of
Archives](http://archivescanada.ca/AboutCCA). Thank you!

NOTE: this work prepares Archivematica for localization; however,
minimal translation has been completed. The interface will default to
English at the present time, but can be changed to another language in
the Settings menu.

- Documentation and translator\'s guide:
    [Translations](https://www.archivematica.org/en/docs/archivematica-1.6/user-manual/translations/translations/#translations)
- Pull requests: [PR
    159](https://github.com/artefactual/archivematica-storage-service/pull/159),
    [Appraisal tab PR
    151](https://github.com/artefactual-labs/appraisal-tab/pull/151),
    [Transfer browser PR
    12](https://github.com/artefactual-labs/transfer_browser/pull/12),
    [PR 506](https://github.com/artefactual/archivematica/pull/506)

#### AIP encryption

This feature allows users to connect their Archivematica pipeline to
GPG-encrypted AIP Storage and Transfer Backlog spaces. AIPs and
transfers in backlog can also be encrypted. An AIP or transfer stored in
an encrypted location is encrypted at rest; when downloaded, an
encrypted AIP is decrypted for use.

This work was sponsored by the [Simon Fraser University
Archives](http://www.sfu.ca/archives.html). Thank you!

- Documentation: [AIP
    Encryption](https://www.archivematica.org/en/docs/archivematica-1.7/user-manual/archival-storage/archival-storage/#aip-encryption)
- Pull requests: [SS
    PR198](https://github.com/artefactual/archivematica-storage-service/pull/198),
    [PR616](https://github.com/artefactual/archivematica/pull/616),
    [Acceptance tests repo
    PR12](https://github.com/artefactual-labs/archivematica-acceptance-tests/pull/12),
    [Acceptance tests repo PR
    19](https://github.com/artefactual-labs/archivematica-acceptance-tests/pull/19),
    [Ansible role
    PR109](https://github.com/artefactual-labs/ansible-archivematica-src/pull/109),
    [SS PR
    241](https://github.com/artefactual/archivematica-storage-service/pull/241),
    [PR 738](https://github.com/artefactual/archivematica/pull/738),
    [Acceptance tests repo
    PR22](https://github.com/artefactual-labs/archivematica-acceptance-tests/pull/22),
    [METS Reader-Writer PR
    27](https://github.com/artefactual-labs/mets-reader-writer/pull/27)
- Feature files: [AIP encryption feature
    file](https://github.com/artefactual-labs/archivematica-acceptance-tests/blob/master/features/core/aip-encryption.feature),
    [AIP encryption mirror location feature
    file](https://github.com/artefactual-labs/archivematica-acceptance-tests/blob/821ece7db3f098c96b2f76ee1093aa0a14553470/features/core/aip-encryption-mirror.feature)

Note that there is an [open
issue](https://github.com/artefactual/archivematica-storage-service/issues/349)
with storing uncompressed AIPs encrypted.

#### Shibboleth and LDAP integration

Archivematica and the Storage Service can now be deployed to use LDAP or
Shibboleth authentication.

This work was sponsored by [Jisc](https://www.jisc.ac.uk/),
[MoMA](https://www.moma.org/research-and-learning/archives/), and the
[International Institute of Social History](https://socialhistory.org/) - a
truly international effort. Thank you!

- Documentation: [Security - User
    Security](https://www.archivematica.org/en/docs/archivematica-1.7/admin-manual/security/security/#user-security)
- Pull requests: [PR
    366](https://github.com/artefactual/archivematica/pull/366), [PR
    463](https://github.com/artefactual/archivematica/pull/463), [PR
    702](https://github.com/artefactual/archivematica/pull/702), [PR
    710](https://github.com/artefactual/archivematica/pull/710), [PR
    756](https://github.com/artefactual/archivematica/pull/756)

#### MediaConch integration

This integration allows users to use MediaConch to check the conformance
of .mkv files (originals and derivatives) against the Matroska
specification. It also checks the validity of media files against
user-provided policies.

This work was sponsored by the [PREFORMA
Project](http://www.preforma-project.eu/). Thank you!

- Documentation: [Format Policy Registry
    -Validation](https://www.archivematica.org/en/docs/fpr/#validation)
- Example workflow: [MediaConch
    workflow](https://wiki.archivematica.org/MediaConch_workflow)
- Pull requests: [PR
    557](https://github.com/artefactual/archivematica/pull/557), [Format
    Policy Registry PR
    35](https://github.com/artefactual/archivematica-fpr-admin/pull/35),
    [Acceptance tests PR
    13](https://github.com/artefactual-labs/archivematica-acceptance-tests/pull/13),
    [Ansible role PR
    114](https://github.com/artefactual-labs/ansible-archivematica-src/pull/114),
    [Sample data PR
    2](https://github.com/artefactual/archivematica-sampledata/pull/2),
    [Artefactual Labs Archivematica MediaConch policy check
    wrapper](https://github.com/artefactual-labs/ammcpc)
- Feature files: [Transfer tab MKV
    conformance](https://github.com/artefactual-labs/archivematica-acceptance-tests/blob/qa/1.x/features/core/transfer-mkv-conformance.feature),
    [Ingest tab MKV
    conformance](https://github.com/artefactual-labs/archivematica-acceptance-tests/blob/qa/1.x/features/core/ingest-mkv-conformance.feature),
    [Transfer policy
    check](https://github.com/artefactual-labs/archivematica-acceptance-tests/blob/qa/1.x/features/core/transfer-policy-check.feature),
    [Ingest policy
    check](https://github.com/artefactual-labs/archivematica-acceptance-tests/blob/qa/1.x/features/core/ingest-policy-check.feature)

#### Handle Server integration

Using this feature, Archivematica can be configured to make requests to
a Handle System HTTP API so that files, directories and entire AIPs can
be assigned persistent identifiers (PIDs) and derived persistent URLs
(PURLs) in the METS file. This work was sponsored by the [International
Institute of Social History](https://socialhistory.org/). Thank you!

- Documentation: [Handle Server
    configuration](https://www.archivematica.org/en/docs/archivematica-1.7/user-manual/administer/dashboard-admin/#handle-server)
- Pull requests: [PR
    690](https://github.com/artefactual/archivematica/pull/690),
    [Acceptance tests PR
    15](https://github.com/artefactual-labs/archivematica-acceptance-tests/pull/15)
- Feature files: [PID-binding
    feature](https://github.com/artefactual-labs/archivematica-acceptance-tests/blob/master/features/core/pid-binding.feature)

#### Assign UUIDs to directories and empty directories

Related to Handle Server Integration, above, this feature gives users
the options of assigning UUIDs to directories and/or empty directories
within the AIP METS file. This adds two new microservices: Assign UUIDs
to directories and Document Empty directories. You may assign UUIDs to
directories and document empty directories even if you do not have a
handle server configured and are not binding PIDs. This work was
sponsored by the [International Institute of Social
History](https://socialhistory.org/). Thank you!

- Documentation: [Assign UUIDs to
    directories](https://www.archivematica.org/en/docs/archivematica-1.7/user-manual/administer/dashboard-admin/#assign-uuids-to-directories),
    [Document empty
    directories](https://www.archivematica.org/en/docs/archivematica-1.7/user-manual/administer/dashboard-admin/#document-empty-directories)
- Pull requests: [PR
    690](https://github.com/artefactual/archivematica/pull/690), [PR
    767](https://github.com/artefactual/archivematica/pull/767), [PR
    833](https://github.com/artefactual/archivematica/pull/833)
- Feature Files: [UUIDs for
    directories](https://github.com/artefactual-labs/archivematica-acceptance-tests/blob/master/features/core/uuids-for-directories.feature)

#### Indexless Archivematica

This feature supports deployment of Archivematica in indexless mode,
disabling ElasticSearch. This means that users that don\'t require
Archivematica\'s indexing features can save the compute resources
required for what can be an intensive task. Note that disabling the
Elasticsearch index means you cannot make use of the Backlog, Appraisal,
or Archival Storage tabs.

This work was sponsored by the [Columbia University
Libraries](http://library.columbia.edu/). Thank you!

- Documentation: [Elastisearch
    indexing](https://www.archivematica.org/en/docs/archivematica-1.7/user-manual/administer/dashboard-admin/#elasticsearch-indexing),
- Pull requests: [PR
    901](https://github.com/artefactual/archivematica/pull/901)
- Feature files: [Indexless
    feature](https://github.com/artefactual-labs/archivematica-acceptance-tests/blob/master/features/core/indexless.feature)

#### README file

A README file in html format has been added to the AIP containing a
brief explanation of what the AIP is, how it was created and how it is
structured. See the contents of the README
[here](https://github.com/artefactual/archivematica/blob/f1e04ffe528156f83a137c6c4dbd228e6b53f5b2/src/MCPClient/lib/assets/README/README.html).
This feature was sponsored by the [Denver Art
Museum](https://denverartmuseum.org/). Thank you!

- Documentation: [AIP
    Structure](https://www.archivematica.org/en/docs/archivematica-1.7/user-manual/archival-storage/aip-structure/)
- Pull requests: [PR
    647](https://github.com/artefactual/archivematica/pull/647)

#### File modification dates

This feature adds a Store file modification job to the Characterize and
Extract metadata microservice and adds the metadata to the Elasticsearch
index. This allows users to view the last modified date of the files in
the Appraisal tab. This feature was sponsored by the [Bentley Historical
Library](http://bentley.umich.edu/) at University of Michigan. Thank
you!

- Documentation: [File
    list](https://www.archivematica.org/en/docs/archivematica-1.7/user-manual/appraisal/appraisal/#file-list-pane)
- Pull requests: [PR
    692](https://github.com/artefactual/archivematica/pull/692)

### Changed for 1.7

#### Anti-virus changes

**What has changed:**

Antivirus (AV) scanning using [ClamAV](https://www.clamav.net/) can now
be configured up to its maximum thresholds (previously Archivematica was
limited to ClamAV\'s default limits, around 25MB). It was discovered
that installing with the default limit would result in false-positive
PREMIS events indicating that files over 25 MB had been scanned. In
these instances, there is still a possibility that a malicious payload
existed, albeit a small chance because viruses are typically attached to
smaller files which are intended to be sent via email. Archivematica
will no longer record a PREMIS event where either a file cannot be
scanned due to the antivirus limits, or some other reason that might
suggest that AV scanning has not completed successfully. Please see the
[Archivematica 1.7
documentation](https://www.archivematica.org/en/docs/archivematica-1.7/user-manual/transfer/scan-for-viruses/)
on the effects of different configuration settings. Currently ClamAV has
an upward limit of 2 GB per file which in the Archivematica 1.7 release
is configured as the default.

**What does this mean?**

If you are concerned about AIPs created pre-Archivematica 1.7 containing
viruses, you can use AIP reingest to re-run antivirus. However, in the
majority of cases this will not be necessary. Factors to consider
include:

- what is the source of the material? Do you have reason to mistrust
    this source?
- what were the transfer protocols before the material was ingested by
    Archivematica? Did anitvirus scanning occur with another tool during
    that process?
- does your current storage system include periodic enterprise-wide
    virus scanning?

#### Archivematica decoupled from the FPR server

The FPR was originally created to manage preservation plans, i.e.
business rules and tool commands for format-based preservation events.
The FPR server's purpose has been to house the default rules and
commands while allowing institutions to make local alterations as
desired.

Going forward, we have made the decision to remove Archivematica's
dependency on the FPR server for the following reasons:

- The FPR rules on the FPR server are out of date. When new rules are
    added to the Preservation Planning tab in Archivematica, they
    aren\'t always being copied back to the FPR server.
- Currently, new Archivematica installations ping the FPR server,
    which records the IP address of the remote server. This data capture
    isn\'t useful and it isn't necessary.

Removing the FPR server as a dependency should not impact how
Archivematica is being used previous to 1.7.

The longer-term goal is to build a new FPR server, one that is
completely decoupled from Archivematica, which would serve up format
policy data to other applications using an open API. We would propose
that this future registry should not rely on a single vendor for
maintenance.

Pull requests: [PR
971](https://github.com/artefactual/archivematica/pull/971)

#### DIP upload and storage workflow improvements

This work clarifies the sequence of the Upload DIP and Store DIP jobs on
the Ingest tab. The processing configuration settings have also been
updated so that almost every decision point can be automated (the
exception is Upload DIP, which requires data entry).

This work was sponsored by
[MoMA](https://www.moma.org/research-and-learning/archives/), the [MIT
Libraries](https://libraries.mit.edu/), and the [University of
York](https://www.york.ac.uk/library/). Thank you!

- Pull request(s):
    [PR680](https://github.com/artefactual/archivematica/pull/680),
    [PR741](https://github.com/artefactual/archivematica/pull/741)

#### Dashboard API whitelist mechanism

Two changes have been made to the API whitelist functionality:

- The default API whitelist setting is now empty.
- If the API whitelist setting is empty the user can still
    authenticate against the API using the key. The whitelist is only
    activated when at least one IP address is listed.

#### Default processing configuration

As a result of several features in this release, the processing
configuration options have changed substantially, growing from 19
configurable decision points to 27. The new decision points include:

- Assign UUIDs to directories (related to Handle Server integration)
- Perform policy checks on originals (related to MediaConch
    integration)
- Perform policy checks on preservation derivatives (related to
    MediaConch integration)
- Perform policy checks on access derivatives (related to MediaConch
    integration)
- Bind PIDs (related to Handle Server integration)
- Document empty directories (related to Handle Server integration)
- Upload DIP (related to DIP upload and storage workflow improvements)
- Store DIP (related to DIP upload and storage workflow improvements)

We\'ve also changed the default configuration, leaving more decision
points set at \"None\", which will prompt the user to make a manual
decision as a transfer is being moved through the Archivematica
workflow. The purpose of these changes is to enable better testing - we
think it\'s important that users see as many decision points in real
time as possible while they are testing the system

We\'ve also set the compression level to 1 - fastest mode, which also
facilitates testing as it wraps up AIP and DIP storage more quickly;
however, it does mean that packages will not be as compressed as they
could be. If you have limited space on your test machine, we recommend
either deleting packages on a regular basis or changing the compression
level to a higher number so that packages are smaller.

Note that changes to the default configuration **should not** override
your local configuration during an upgrade or migration.

#### Miscellaneous changes

- Storage Service timeouts increased from 5 seconds to 120 seconds
    (<https://github.com/artefactual/archivematica/commit/c24183fd>)

### Fixed for 1.7

- Problem: editing notes in appraisal tab can delete data from
    ArchivesSpace
    -<https://github.com/artefactual/archivematica/issues/713>
- **Sponsored** by [International Institute of Social
    History](https://socialhistory.org/) - Failure during METS creation
    due to recursion limit
    -<https://github.com/artefactual/archivematica/commit/0881d587>
- Original AIP METS still in filegrp:SubmissionDocumentation in METS
    -<https://projects.artefactual.com/issues/10829>
- Closed issues for [Archivematica
    1.7](https://github.com/artefactual/archivematica/milestone/7?closed=1)
    and [Storage Service
    0.11](https://github.com/artefactual/archivematica-storage-service/milestone/10?closed=1)

### Upgraded tools and dependencies for 1.7

- PRONOM updated to version 92
- METS updated to version 1.11
- Fido updated to 1.3.7
- [METS
    reader-writer](https://github.com/artefactual-labs/mets-reader-writer)
    updated to 0.2.0
- [AgentArchives](https://github.com/artefactual-labs/agentarchives)
    updated to 0.3.0
- Siegfried updated to 1.6.7

### End of life dependencies for 1.7

Several dependencies in Archivematica have reached end of life and
resources did not allow for updates in 1.7. In future releases we will
address these dependencies:

- Django 1.8
- Elasticsearch 1.7
- Percona 5.5

To mitigate risks related with using these dependencies you might
consider:

- Installing Archivematica behind a firewall
- Using Archivematica without Elasticsearch (turn indexing off)

## Archivematica 1.6.1 release notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.6.1_release_notes).

Primarily a bugfix release - August 1st, 2017.

This is the first Archivematica release to provide packages for Ubuntu
16.04 (xenial). Support for xenial is considered beta. Ubuntu 14.04
(trusty) and CentOS 7.x are also supported.

### Tool Updates

- Support for PRONOM 90
- siegfried updated to version 1.7.3
- FIDO updated to version 1.3.6
- ffmpeg updated to version 3.3.2 (Ubuntu only)

### Archivematica 1.6.1

- **Sponsored** (Rockefeller Archive Center) Object Level Premis
    Rights Import
    -[PR575](https://github.com/artefactual/archivematica/pull/575)
    [Docs](https://www.archivematica.org/en/docs/archivematica-1.6/user-manual/transfer/import-metadata/#rights-csv)

- **Sponsored** (Canadian Centre for Architecture) Update METS to
    encode in UTF-8 instead of ASCII - [Issue
    \#11163](https://projects.artefactual.com/issues/11163)
    [PR541](https://github.com/artefactual/archivematica/pull/541)

- **Sponsored** (Canadian Centre for Architecture) Increase
    Elasticsearch timeout limit - [Issue
    \#11294](https://projects.artefactual.com/issues/11294)
    [PR556](https://github.com/artefactual/archivematica/pull/556)

- **Sponsored** (University of Saskatchewan Library) Allow
    UTF8-encoded transfer directory names - [Issue
    \#10712](https://projects.artefactual.com/issues/10712)
    [PR520](https://github.com/artefactual/archivematica/pull/520)

- **Contributed** ([Dallas Pillen](https://github.com/djpillen)) Use
    display\_title instead of title for sip\_name in Appraisal tab
    -[PR158](https://github.com/artefactual-labs/appraisal-tab/pull/158)

- **Contributed** ([Dallas Pillen](https://github.com/djpillen)) Use
    display\_string instead of title for digital object title with
    ArchivesSpace integration
    -[PR41](https://github.com/artefactual-labs/agentarchives/pull/41)

- Support for [PRONOM 89 and
    90](https://www.nationalarchives.gov.uk/aboutapps/pronom/release-notes.xml)

    \- [Issue \#10982](https://projects.artefactual.com/issues/10982)
    [PR660](https://github.com/artefactual/archivematica/pull/660)

- Fix upgrades when FPR Rules have been customised - [FPR Admin Issue
    \#46](https://github.com/artefactual/archivematica-fpr-admin/issues/46)
    [PR609](https://github.com/artefactual/archivematica/pull/609)

- ArchivesSpace: Don\'t special case first note when editing a record
    -[PR40](https://github.com/artefactual-labs/agentarchives/pull/40)

- Set filepath for zip files correctly when starting transfer
    -[\#11224](https://projects.artefactual.com/issues/11224)
    [PR626](https://github.com/artefactual/archivematica/pull/626)

- Change date format in verifyMD5.sh
    -[PR629](https://github.com/artefactual/archivematica/pull/629)

### Archivematica Storage Service 0.10.1

- **Sponsored** (University of British Columbia Library) Improvements
    to editing pipelines
    -[PR194](https://github.com/artefactual/archivematica-storage-service/pull/194)
- **Sponsored** (City of Vancouver Archives) Correctly update pointer
    files when reingesting uncompressed AIP\'s
    [PR203](https://github.com/artefactual/archivematica-storage-service/pull/203)
    [PR214](https://github.com/artefactual/archivematica-storage-service/pull/214)
- Update Bagit-python to version 1.5.4
    [PR207](https://github.com/artefactual/archivematica-storage-service/pull/207)

## Archivematica 1.6 release notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.6_release_notes).

We are dedicating the Archivematica 1.6 release to the memory of Nancy
Deromedi. Many of our users will know that a major defining feature of
this release is the new Appraisal and Arrangement tab. This idea was
conceived and sponsored by the Bentley Historical Library at the
University of Michigan, under the leadership of Nancy Deromedi. Sadly,
her life was cut short by cancer before the project was completed. From
Michael Shallcross, Bentley Historical Library:

"Nancy Deromedi was a leader in the field of digital preservation at the
University of Michigan\'s Bentley Historical Library from 1997 until her
untimely passing in 2014. Always eager to explore new ideas and
strategies, she inspired her colleagues to innovate, take risks, and
embrace emerging technologies. The success of the Bentley\'s
\"ArchivesSpace-Archivematica-DSpace Workflow Integration\" project
(funded by the Andrew W. Mellon Foundation) is very much a tribute to
her vision, generosity of spirit, and constant drive to find better and
more efficient solutions to preserve and provide access to digital
archives."

### Archivematica 1.6

#### New features/enhancements

- **Sponsored** (Bentley Historical Library University of Michigan)
    [Appraisal/Arrangement tab](Appraisal_Arrangement_tab)
    -- <https://projects.artefactual.com/issues/10555>
  \| \#10555\]
    -- New tab to facilitate analysis of transfer contents and
      arrangement of SIPs. Includes:
      --- Visualization of transfer contents (number/size of files,
       file types, extensions)
      --- Bulk Extractor report analysis (in tabular format)
      --- Tagging content as an \"aide memoire\" during processing
- **Sponsored** (Bentley Historical Library University of Michigan)
    [ArchivesSpace integration in Appraisal
    tab](ArchivesSpace_integration_in_Appraisal_tab)
    -- <https://projects.artefactual.com/issues/10556>
  \| \#10556\]
     --- This integration with ArchivesSpace will include pulling
       accession record and rights information from ArchivesSpace to
       facilitate arrangement of SIPs, as well as sending SIP metadata
       from Archivematica to ArchivesSpace to update or create digital
       objects and digital object components.
- **Sponsored** (Simon Fraser University Archives) Improvements to
    transfer backlog management
    -- <https://projects.artefactual.com/issues/10551>
    \| \#10551\]
    --- Ability to search transfers from archival storage tab
    --- Ability to download copies of transfers or selected files from
       archival storage tab
    --- Ability to perform transfer deletion requests from archival
       storage tab
- **Sponsored** (Zuse Institute Berlin) Full AIP re-ingest and AIP
    re-ingest improvements
    -- <https://projects.artefactual.com/issues/10563>
    \| \#10563\]
    --- Able to send an AIP back to the beginning of the transfer tab to
       re-run all major preservation micro-services
    --- Re-normalize for the purpose of preservation and update the AIP
       and version the METS file
    --- Improved handling of updated metadata
    --- Ability to define a different processing configuration for
       re-ingest
- **Sponsored** (Simon Fraser University Archives) DIP upload to AtoM
    improvements -
    -- <https://projects.artefactual.com/issues/9752>
    \| \#9752\]
    --- Add AtoM REST API endpoints to GET archival hierarchy and PUT
       archival description
    --- Add Archivematica REST API calls to AtoM endpoints to GET
       archival hierarchy and PUT archival description
    ---- Use the above to upload AIP metadata to AtoM descriptions,
       without creating DIP objects
- **Sponsored** (University of York/University of Hull) Support for
    multiple checksum algorithms
    -- <https://projects.artefactual.com/issues/10052>
    \| \#10052\]
- **Sponsored** (City of Vancouver Archives) Emailed normalization
    error report -
     -- <https://projects.artefactual.com/issues/10146>
    \| \#10146\]
- **Sponsored** (Simon Fraser University Archives) AIP view page that
    incorporates AIP download, reingest, deletion requests and
    metadata-upload to AtoM

#### New and upgraded tools/dependencies

- **Sponsored** (Bentley Historical Library) Bootstrap upgrade which
    has changed the transfer browser and SIP arrange interfaces

### Storage Service 0.10.0

- **Sponsored** (Simon Fraser University Archives) Fixity checking and
    reporting
    -- Modify Storage Service to record time and results of fixity
       checks
- **Sponsored** (University of York/University of Hull) Support for
    re-ingesting uncompressed AIPs
- **Sponsored** (Museum of Modern Art New York) Support for fixity
    check result \"None\"
- Add version page to the Storage Service

#### New and upgraded tools/dependencies in 1.6

- Siegfried: updated to 1.6.7
- Fido: updated to 1.3.5
- Django: updated to 1.8
- Django-tastypie to 0.13.2
- agentarchives 0.3.0
- gearman 2.0.2
- METS reader-writer 0.1.0
- mysqlclient 1.3.7 (Dashboard only)
- Python-dateutil 2.4.2
- lxml 3.5.0
- Bootstrap 3.0.0
- Bagit 1.5.2
- unidecode 0.04.19
- Django-mysqlpool 0.1-9
- PRONOM v.88

#### Bug fixes for 1.6

Please see bug fixes
[here](https://projects.artefactual.com/projects/archivematica/issues?query_id=79)

## Archivematica 1.5.1 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.5.1_Release_Notes).

Packaging and bug fix release - September 6, 2016

### Archivematica 1.5.1

- Archivematica and Storage Service packaged for CentOS \#10129
- Fixed error caused by files with diacritics \#10155
- Fixed incorrect file count caused by AIP reingest \#10022
- Fixed AtoM integration error (fetching levels of description)
    \#10126

### Storage Service 0.9.0

- **Sponsored** (MoMA) Changes to support Arkivum integration
    -- Enhanced download from Arkivum \#9840
- **Sponsored** (JISC) Automated DIP generation
    -- Relate packages to one another \#10081
- Fixed metadata-only AIP reingest error that caused AIP size to be
    recorded incorrectly \#10030
- Backend support for Dataverse, for a future release of Archivematica

## Archivematica 1.5.0

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.5_Release_Notes).

- **Sponsored** (Rockefeller Archive Center) ArchivesSpace integration
    -- Send DIP object metadata to ArchivesSpace
- **Sponsored** (Zuse Institute) AIP DC and Rights MD Re-ingest [Full
    AIP re-ingest requirements](AIP_re-ingest)
    -- **Sponsored** supports AIP versioning (METS file updates) \#1564
    -- **Sponsored** generate DIP from AIP after processing is complete
       -Issue \#1843
    -- does not support re-normalization
    -- note that this work is only part of the entire AIP re-ingest
       feature, the rest is not yet sponsored
- **Sponsored** (National Library of Wales) \#8678
    -- **Sponsored** Add levels of description to Submission
       Information Packages using AtoM REST endpoint to enforce
       controlled vocabulary
    -- **Sponsored** Generate hierarchical structMap in Archival
       Information Package METS file
    -- This development is concurrent with AtoM development including
       the following: generate hierarchical arrangement based on METS
       structMap, map levels of description in hierarchical METS
       structMap to Level of description element in AtoM information
       object, and display hierarchical arrangement in AtoM treeview
- **Sponsored** (MIT Libraries) Revision to DIP storage procedures
    -- This revision to the DIP storage feature will allow users to
       store a DIP after it (or its metadata) has been sent to the
       Access system. See [DIP storage to designated location\#Revision
       for version
       1.5](DIP_storage_to_designated_location#Revision_for_version_1.5)
- Backend - Not user-facing
    -- Update Django to 1.7

### Storage Service 0.8.0

- **Sponsored** (Zuse Institut) Changes to support AIP re-ingest
- Unicode/METS fix [Pull Request
    38](https://github.com/artefactual/archivematica-storage-service/pull/48)
- Update Django to version 1.8

## Archivematica 1.4.1 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.4.1_Release_Notes).

Bug fix release, June 24, 2015

### Archivematica 1.4.1

- Requesting AIP deletion causes 500 error (\#8533)
- Show Archivematica active template instead of Apache error page for
    500 errors (\#8600)

### Storage Service 0.7.1

- Permissions error copying to start of transfer (\#8540)
- Cannot browse CIFS transfer source (\#8514)

## Archivematica 1.4 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.4_Release_Notes).

### Archivematica 1.4

Released May 27, 2015

This release improves and facilitates integration with a number of
access/deposit systems, including CONTENTdm, Islandora and DSpace, as
well as bug fixes and other small usability improvements.

#### New features in 1.4

- **Sponsored** (University of Saskatchewan Library) Fedora/Islandora
    Integration
- **Sponsored** (GE Aviation) Bag ingest improvements (\#8309, PR191)
- **Sponsored** (University of British Columbia Library) DSpace Ingest
    improvements (\#6273, \#5889, PR154)
- **Sponsored** (University of British Columbia) CONTENTdm dip upload
    enhancements (\#8039, PR148)
- Transfer/SIP Creation feedback (\#7853, PR171)
- SIP Arrange enhancements (improved transfer METS) (\#7714, PR145)
- Review/Download DIP objects (See CONTENTdm DIP upload enhancements,
    \#8039)
- Processing location cleanup via dashboard (\#7921, PR199)
- Improved logging (backend only, no user-facing functionality)
    (\#6647, PR34, PR201)
- **Sponsored** (Columbia University) Extract Packages Recursively
    (\#8438, PR164)

#### Bug fixes for 1.4

- Manual normalization fixes (\#6870, PR97, PR186)
- Improvements to metadata.csv handling (\#7901, \#8007, PR210)
- Accession ID\'s now working (\#7442, PR175, PR134)
- Sanitize Transfer Names (\#7937, PR170)
- Fix Remove Transfer Components (\#7482, PR172)
- Timestamps not updating fix (\#7859, PR162)
- Remove events for sanitize directory names (\#8033, PR177)
- AIC fixes (\#8258, \#7155, PR194, PR168)
- Verify checksum fail causes SIP failure (\#8225, PR190)
- Various Archival Storage search fixes (PR213, PR215, PR216, PR217,
    PR221, PR222, PR223)
- DIP Store location preconfiguration (\#7321, PR209)

#### New and upgraded tools in 1.4

- Elasticsearch Updated to version 1.3
- FITS Updated to version 0.8.4
- FFMPEG Updated to version 2.6
- Automation tools: DSpace fixes (AT PR 2)
- **New** Support for Siegfried 1.0 for file identification (PR202)

### Storage Service 0.7

#### New features in Storage Service 0.7

- **Sponsored** (Museum of Modern Art) AIP Recovery (SS PR 47)
- **Sponsored** (University of Saskatchewan Library) Fedora/Islandora
    Integration (\#7918)

#### Bug fixes for Storage Service 0.7

- SIP Arrange results handling (\#7714)
- Default Location Handling (\#7416, SS PR40)
- Encoding bugfixes (\#7583)
- Duracloud related fixes (\#7643, \#7554, \#7549, \#7481, \#7583,)
- Misc. Testing Improvements (back-end) (SS PR47, SS PR69)

## Archivematica 1.3.2 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.3.2_Release_Notes).

### Archivematica 1.3.2

#### Security and bug fix release for 1.3.2

Released March 18, 2015

- Security fixes related to DIP upload in AtoM and CONTENTdm
- METS file fix \#8034

### Storage Service 0.6.1

#### Security and bug fix release for 0.6.1

Released March 18, 2015

- Security fixes related to installation environments where the
    Storage Service is installed on a different server than the
    Archivematica pipeline(s)
- Fixity checks for uncompressed AIPs \#7777
- Original timestamps retained when transfer started \#8024

## Archivematica 1.3.1 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_1.3.1_Release_Notes).

### Archivematica 1.3.1

Released February 5, 2015

- Bug fixes discovered during Pilot testing with hosted DuraCloud
    partners
- Spaces allowed in Archivist\'s Toolkit terms: \#7606
- Accession ID fix: \#7442
- New Archivematica documentation website launch

### Storage Service 0.6.0

Released February 5, 2015

#### New features for 0.6.0

- Improve logging \#7683
- Add exception handling, duplicate locations \#7416
- DuraCloud: Ability to fetch more than 1000 files from a space [Pull
    Request
    45](https://github.com/artefactual/archivematica-storage-service/pull/45)
- Allow storage of AIPs over 2GB [Pull Request
    53](https://github.com/artefactual/archivematica-storage-service/pull/53)
    \#7311 (requires simple configuration change that can be customized)

#### Bug fixes for 0.6.0

- DuraCloud: Encoding fixes [Pull Request
    50](https://github.com/artefactual/archivematica-storage-service/pull/50)
    [Pull Request
    51](https://github.com/artefactual/archivematica-storage-service/pull/51)
    \#7643
- Installer script fix [Pull Request
    52](https://github.com/artefactual/archivematica-storage-service/pull/52)
    \#7310
- DuraCloud: Handle hidden files in folders [Pull Request
    49](https://github.com/artefactual/archivematica-storage-service/pull/49)
- Improve unicode support [Pull Request
    44](https://github.com/artefactual/archivematica-storage-service/pull/44)
    [Pull Request
    46](https://github.com/artefactual/archivematica-storage-service/pull/46)
    \#7583
- DuraCloud: Fetch files with non-ascii characters in filenames [Pull
    Request
    54](https://github.com/artefactual/archivematica-storage-service/pull/54)
    \#7694

## Archivematica 1.3 Release Notes

[Original release notes](https://wiki.archivematica.org/Archivematica_1.3_Release_Notes)

**Released** October 24, 2014

**Important note: this is not a required upgrade from 1.2.x. Only new
users, those wanting to try out 14.04, or DuraCloud account holders need
this release.**

### New features for 1.3

- DuraCloud integration with the SS 0.5.0 release
    -- Ability to store Archival Information Packages (AIPs) in
       DuraCloud
    -- Ability to store Dissemination Information Packages (DIPs) in
       DuraCloud
    -- Ability to synchronize a local copy with a remote copy in
       DuraCloud
- [Bug fixes](http://ow.ly/DhA9T) from 1.2.2 release
- Packaged with ffmpeg 2.4 \#7243
- Ubuntu 14.04 packages available for testing purposes, but not
    verified for production use

### Storage Service 0.5.0

Released October 24, 2014

- DuraCloud integration \#7133
- Ubuntu 14.04 packages available for testing purposes, but not
    verified for production use

### New: Archivematica Dev Tools 0.0.1

Released October 24, 2014

- Archivematica 1.3.0 is packaged with Archivematica Dev Tools,
    version 0.0.1. Dev Tools had already been available through
    [GitHub](https://github.com/artefactual/archivematica-devtools) but
    are now packaged with the release.

## Archivematica 1.2.0

[Original releas
notes](https://wiki.archivematica.org/Archivematica_1.2_Release_Notes).

Released September 2014

### New features for 1.2.0

- **Sponsored** (Council of Prairie and Pacific University Libraries)
    For COPPUL hosting functionality at Bronze level, ability to process
    through to Transfer backlog only
- **Sponsored** (SFU Archives) SIP Arrangement - Create one or more
    SIPs from one or more transfers in the Ingest tab Transfer and SIP
    creation - \#1726, \#1571, \#1713, \#1035, \#6022
    -- does not support taking content out of a SIP once it\'s been
      moved to the SIP arrangement panel
- **Sponsored** (Harvard Business School Library) Directory printer
    -See requirements Directory printer for recording original order
- **Sponsored** (Harvard Business School Library) OCR - See
    requirements OCR text in DIP
- **Sponsored** (Harvard Business School Library) Store DIP - See
    requirements Store DIP
- **Sponsored** (Yale University Libraries) Forensic disk image ingest
    \#5037, \#5356, \#5900
- **Sponsored** includes identification and flagging of personal
    information in transfers, as well as other bulk extractor reporting
    functions
- Add ability to configure Characterization commands via FPR
    <https://github.com/artefactual/archivematica/pull/6>
- Add verification command micro-service (verify frame-level fixity
    and lossless compression) \#6501
- Improvements to transfer start \#6220Scalability: Add nailgun
    (improve performance of java tools like FITS)
- View pointer files from Archival Storage and Storage Service
- Improvements to file identification metadata in METS \#
- Include TIKA \#5027 and DROID in packages so FPR can be configured
    to use them as identification tools
- Include MediaInfo, Exiftool and framemd5 (maybe ffprobe) for
    characterization and metadata extraction instead of FITS \#5034
- Support Dublin Core metadata in JSON (as well as csv, which was
    already supported)
    <https://github.com/artefactual/archivematica/pull/14>
- Updated FIDO with the most recent PRONOM IDs ([Version
    77](http://www.nationalarchives.gov.uk/aboutapps/pronom/release-notes.xml))
    released July 18th, 2014

Archivematica 1.2.0 runs with a new version of the Storage Service,
0.4.0.

### New and Updated Tools for 1.2.0

new

- bulk\_extractor 1.4.4
    <http://digitalcorpora.org/downloads/bulk_extractor/>
- exiftool 9.70
    <http://www.sno.phy.queensu.ca/~phil/exiftool/index.html>
- MediaInfo 0.7.52 <http://mediaarea.net/en/MediaInfo>
- nailgun 0.9.1 <http://www.martiansoftware.com/nailgun/>
- sleuthkit 4.1.3 <http://www.sleuthkit.org/sleuthkit/download.php>
- unar 1.8.1 <http://unarchiver.c3.cx/commandline>
- Tesseract 3.02 <https://code.google.com/p/tesseract-ocr/>

updated:

- bagit 4.9.0
    <https://github.com/LibraryOfCongress/bagit-java/releases>
- ffmpeg 2.3 <https://www.ffmpeg.org/download.html#releases>
- fido 1.3.1.77 <https://github.com/openplanets/fido/tree/1.3.1-77>
- fits 0.8.2 <http://projects.iq.harvard.edu/fits/downloads>
- ImageMagick 6.6.9-7 <http://www.imagemagick.org>

### Storage Service 0.4.0

This release allows integration with LOCKSS storage, adds a fixity
checking app to the backend, and includes several developer features as
well as features required for future releases of the Archivematica
dashboard.

#### New features for 0.4.0

- Sponsored (SFU Library) LOCKSS available as an AIP storage location
    using PLN Manager \"LOCKSS-o-MATIC\" (AIP storage / API plugin)
    \#5425 PR15
- Sponsored (SFU) Ability to configure transfer backlog locations via
    the Storage Service \#6131 PR\#9
- Sponsored (Harvard Business School Library) Manage DIP storage PR11
- Sponsored (Museum of Modern Art) Fixity checking app \#6597 , 1109
    PR13
- View pointer files from Archival Storage and SS \#5716 PR5

#### Enhancements for 0.4.0

- Optimizations in moving files between Locations \#6248 PR4
- Streamlined creation of new endpoints with decorators PR14
- New dependency added unar (and lsar) used to add support for AIP\'s
    with multiple Extensions (e.g., aip.tar.gz) \#6764 PR15

#### Bugfixes for 0.4.0

- Setting Location path from the user interface \#5608 PR10
- Allow email address to be used as username \#6674 PR12
- Ability to change internal processing space \#6819
- Editing users no longer results in server error \#6717

## Storage Service 0.3.0

Released April 10th, 2014

Includes backend enhancements and API-level changes only, with no direct
user facing changes

- **Sponsored** (University of Alberta) [Dataset
    preservation](Dataset_preservation)
    -- **Sponsored** Add support for AIC\'s
       <https://github.com/artefactual/archivematica-storage-service/pull/2>
- Improved unicode support
    <https://github.com/artefactual/archivematica-storage-service/pull/3>
- v2 of internal REST API (the API used by the Dashboard) and update
    documentation
- Storage Service now supports updating - no longer necessary to
    reinstall to upgrade
    <https://github.com/artefactual/archivematica-storage-service/pull/6>

## Archivematica 1.1

[Original releas
notes](https://wiki.archivematica.org/Archivematica_1.1_Release_Notes).

Released May 2, 2014

### New features for 1.1

- **Sponsored** (University of Alberta) [Dataset
    preservation](Dataset_preservation)
    -- **Sponsored** creation and management of AICs \#5802
    -- **Sponsored** AIP pointer file \#5159
    -- **Sponsored** pointer file tracks multi-AIP relationships
    -- **Sponsored** pointer file includes compression information and
       other metadata required to find and process (e.g. open) AIP
- **Sponsored** (University of Alberta) Enhancements to [manual
    normalization workflow](UM_manual_normalization_1.0)
    -- **Sponsored** ability to add PREMIS event detail information for
       manually normalized files via the dashboard \#5216 [User Manual
       -Adding PREMIS eventDetail for manual
       normalization](UM_manual_normalization_1.1#Adding_PREMIS_eventDetail_for_manual_normalization)
- Backend/Not user-facing:
    -- Improved unicode support
       <https://github.com/artefactual/archivematica/pull/17>
    -- Better handling of preconfigured choices (processingMCP.xml)
    -- More choices in processing archive file formats (extra
       preconfigured choices)
    -- Improved handling of unit variables (passing parameters between
       micro-services)
    -- Update to FITS 0.8.0 (or newer if available)
    -- Update to ElasticSearch 0.90.13
    -- Security fix (avoid invoking subshell when running
       micro-services)
       <https://github.com/artefactual/archivematica/pull/16>
    -- File identification in mets is now from file id tool and not
       FITS <https://github.com/artefactual/archivematica/pull/15>

### Bug fixes and enhancements 1.1

- [bug fixes](http://bit.ly/1lPBqwV)

## Archivematica 1.0 Release Notes

### Archivematica 1.0

<https://wiki.archivematica.org/Archivematica_1.0_Release_Notes>

Release for public testing: September 2013

Package release: January 2014

#### New features for 1.0

- Format Policy Registry (FPR) improvements including
    -- Ability to add/change format policies in the dashboard
    -- Ability to update the local FPR from fpr.archivematica.org
    -- Upload and report performance stats to FPR
    -- For detailed information about the FPR, see [Administrator
       manual\--FPR](Administrator_manual_1.0#Format_Policy_Registry_.28FPR.29)
- Generation of \"fail\" reports in the administrative tab of the
    dashboard
- Eliminate unused interface options (e.g. DSpace transfer, CONTENTdm
    upload, ICA-AtoM upload) via the administrative tab of the dashboard
- DIP upload to Archivist Toolkit [Archivists Toolkit
    integration](Archivists_Toolkit_integration) with a metadata entry
    gui in the dashboard and actionable PREMIS rights
- AIP pointer file
- [Storage service](Administrator_manual_1.0#Storage_service) with API
- Ability to request to delete an AIP via the dashboard
- Upgraded to [FITS 0.62](https://github.com/harvard-lts/fits)
- Ability for multiple pipelines to write to a shared ElasticSearch
    index and to the same AIP store(s) (i.e. multiple dept\'s -\> one
    institution)
- Further scalability testing/prototyping and improved documentation

#### Bug fixes and enhancements for 1.0

- [bug fixes](https://projects.artefactual.com/versions/31)

## Archivematica 0.10 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_0.10-beta_Release_Notes).

Release: April 29, 2013 \| [Download](Install-0.9-beta) \|
[Screencast](https://www.youtube.com/watch?v=GWmNfuO1ofw&feature=player_embedded)
\| [Roadmap](https://archivematica.org/roadmap)\|

### New features in 0.10

- Format Policy Registry (FPR)[Format Policy Registry
    (FPR)](Format_policy_registry_requirements) including ability to
    edit format policies from the preservation planning tab
- Choose between FITS output from DROID, JHOVE, exiftool or file
    extension as the file identification basis for normalization
- Use PRONOM ID as basis for unique identifier for all source formats
    (incl. format versions);
- Manual normalization workflow
- Email handling improvements
- Advanced search screens for searching AIP contents with AIP
    retrieval (whole or part) and delivery
- Administrative setting of PREMIS agent and capture logged-in user as
    PREMIS agent
- Transfer backlog functionality including adding an accession number,
    sending indexed transfers to backlog in Archival storage, and search
    and retrieval of transfers from backlog for Ingest via dashboard
    interface
- User-friendly template to configure workflow processing settings in
    dashboard
- Emailing of \"fail\" reports
- Ability to (re)build ES index from AIP store (for pre 1.0 installs &
    in event of data corruption/loss)
- Enhancements to CONTENTdm [Metadata import](Metadata_import)
- Bulk metadata import using csv files
- Further scalability testing/prototyping and improved documentation

### Bug fixes and enhancements for 0.10

- \#585 Eliminate dialogs, open task reports in seperate tab
- \#1593 Upload original filename to ICA-AtoM instead of cleaned up
    filename
- \#1866 DIP Upload shows failed in Dashboard when no intermediate
    level selected for AtoM
- \#1867 DIP metadata not indexed in AtoM
- \#1868 Non ascii chars in transfer name cause error
- \#1871 Add unidecode as package
- \#1877 Dashboard unable to browse directory if any filename includes
    non-standard character
- \#1886 Path to SIP sometimes shows in normalization report title
- \#1890 Non-standard characters cause dashboard transfer copy to fail
- \#1943 Database error at Preservation Planning tab of dashboard
- \#1944 Template syntax error at Administration tab of dashboard -
    AtoM DIP Upload
- \#4545 Unicode/utf-8 python subprocess
- \#4679 AIP file download broken
- \#4680 AIP download broken
- \#4681 Fix AIP search metadata viewer
- \#4690 Archival Storage page dies the first time it\'s loaded if the
    aips ElasticSearch index isn\'t yet created
- \#4706 Submission documentation is not in preservation format in AIP

## Archivematica 0.9 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_0.9_Release_Notes).

Release: August 29, 2012 \| [Download](Install-0.9-beta) \|
[Screencast](https://www.youtube.com/watch?v=GWmNfuO1ofw&feature=player_embedded)
\| [Roadmap](https://archivematica.org/roadmap)\|

### New features in 0.9

- Update to ubuntu 12.04 LTS as the base operating system
- Web browser dashboard interface replacing most of the file browser
    functionality
- DIP upload to CONTENTdm
- Indexing and search of all AIP metadata using
    [ElasticSearch](http://www.elasticsearch.org/)
- Rights module update to PREMIS 2.2
- Email handling improvements and prototype ingest of maildir
- Ability to create user accounts
- Automatic restructuring of transfer for compliance
- In dashboard, grouped jobs into micro-services
- Ability to ingest Library of Congress Bagit format
- Nightly backup of MCP MySQL database
- Scalability ehnancements: see [Scalability
    testing](Scalability_testing).

### Bug fixes and enhancements in 0.9

- Issue 185 Merge multiple layers in image files into single jpeg
    access copies
- Issue 304 Transcoding with Open Office fails periodically
- Issue 575 Client can configure their timezone to offset the
    date/time in the dashboard.
- Issue 673 during reinstall archivematica-mcp-client fails
- Issue 694 The archivematica VM\'s should include a timesync
    mechanism
- Issue 980: Check tasks, microservices and dropdown menus for naming
    clarity and consistency
- Issue 722 Add Administration tab to configure workflows
- Issue 777 Browser periodically fails to refresh when running a
    micro-service
- Issue 860 Rights granted restriction is a repeatable field.
- Issue 865 Archivematica freezes if transfer directory name has
    apostrophe
- Issue 869 Omitting termOfGrant startDate in rights causes generate
    METS.xml micro-service to fail
- Issue 872 In rights list page for SIP, column on right hand side is
    confusing
- Issue 875 Inconsistent normalization failure on pdf in
    submissionDocumentation
- Issue 885 Three locations of apache.default
- Issue 886 Make overiding the default assigned threads by core count
    configurable.
- Issue 887 Make Approval steps different colour
- Issue 892 Uploaded objects should have filename as title
- Issue 894 Microservices failing to connect to the mysql database.
- Issue 897 Integrate Transcoder into MCP
- Issue 902 Remove mac icon files automatically on ingest
- Issue 903 Ensure latest version of tutorial is included in demo/Docs
- Issue 906 When access normalization fails, a copy of the original
    file should be placed in the DIP
- Issue 910 Remove hidden files during transfer
- Issue 913 Description doesn\'t match command.
- Issue 918 Choosing \"No normalization\" results in failure at
    Prepare AIP
- Issue 927 Make compression a processing decision option
- Issue 932 Make DIP upload destination a selectable or configurable
    option
- Issue 934 When micro-service fails but transfer or SIP continues
    processing, icon shows fail at the end instead of success
- Issue 935 Rejected transfers or SIPs have icon showing that
    processing was completed
- Issue 937 Order structMap contents alphabetically as default
- Issue 939 Enclose fptr elements in divs in METS structMap
- Issue 943 Mysql connection issues.
- Issue 944 Give option to restructure for compliance when failing
    compliance.
- Issue 950 Make action items larger
- Issue 955 Generate thumbnails
- Issue 958 Improve user manual instructions for error handling
- Issue 962 Ingest maildir backups and convert to mbox for access
- Issue 969 Dashboard search functionality
- Issue 972 Replace isPartOf with Relation in DC template
- Issue 976 Replace pyinotify watched directories, with something that
    compares list of files.
- Issue 977 Add user-supplied structMap to AIP METS file
- Issue 978 During DSpace transfer processing user asked to approve
    load of non-existent file\_labels.csv
- Issue 980 Check tasks, microservices and dropdown menus for naming
    clarity and consistency
- Issue 983 Replace -vpre normal in mp4 normalization command with new
    preset
- Issue 984 Access normalization fails in digitization workflow when
    filenames have periods in them
- Issue 985 Use ffmpeg.org version of ffmpeg instead of avconv
- Issue 986 Consolidate technical documentation into an
    administrator\'s manual
- Issue 991 Make sure blank value doesn\'t generate NaN in task popup
    data fields
- Issue 992 Add View METS and View AIP option at Store AIP task
- Issue 993 Add View normalization report and View normalized files
    option at Approve normalization task
- Issue 995 Swap click behavior of SIP row and magnifying glass icon
- Issue 998 Log MCP normalization output
- Issue 1001 Make user selectable replacement dic append, not replace.
- Issue 1004 Eliminate side info panels from dashboard andhome page
- Issue 1009 Include empty directories in BAG.
- Issue 1010 Resolve: two \"CREATE TABLE StandardTasksConfigs\"
- Issue 1011 Add default Archivematica structMap label to distinguish
    from user-supplied structMap
- Issue 1021 Make Archival Storage Tab load from db
- \[STRIKEOUT:Issue 1025\] Test date fields with dates before 1970
- Issue 1026 Make defaultProcessingMCP.xml configurable in the
    administration tab.
- Issue 1035 Line up micro-service names
- Issue 1036 Change Dspace transfer folder name and micro-service
- Issue 1040 When ingested file is already in an access format, the
    file is not added to the DIP
- Issue 1042 Remove default normalization to .odt for .rtf files
- Issue 1044 Remove \"None microservice\"s
- Issue 1046 Office doc normalization failing on x32 installs
- Issue 1057 DC file not added to METS
- Issue 1081 Fix numerical indicators on the dashboard so they are on
    proper tab.
- Issue 1082 Verify file id classifications of preservation or access
    formats.

## Archivematica 0.8 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_0.8_Release_Notes).

Released: February 3, 2012 ([Download](Install-0.8-alpha))

### New features in 0.8

- Complete standards-compliant PREMIS in METS implementation
- Transfer functionality:
    -- Some former ingest processes moved to transfer: eg identifier
       assignment, fixity check, checksum generation, unpacking, format
       characterization and metadata extraction
    -- Ability to create one-to-one, one-to-many, many-to-many and
       many-to-one relationships between transfers and SIPs
    -- Transfer METS file to capture original order of transfer before
       it is re-arranged into SIPs
    -- All transfer documentation, including submissionDocumentation,
       copied to all SIPs created from a transfer
- Multiple normalization options
- Configurable workflows
- Metadata templates for adding Dublin Core and PREMIS rights metadata
- DIP upload to Qubit using SWORD API
- Ability to ingest DSpace exports
- Digitization output workflows
- Enhancements to the dashboard:
    -- New theme and homepage
    -- Transfer tab
    -- Access tab linking AIPs to uploaded DIPs
    -- Administration tab

### Bug fixes and enhancements for 0.8

- Issue 249 Verify Namespaces in the mets xml document are correct
- Issue 305 Add functional tests to Archivematica wiki
- Issue 453 Create ability to opt out of micro-services
- Issue 472 Add edit template for DC metadata to dashboard
- Issue 477 Clean shutdown
- Issue 481 Change PREMIS eventType values to conform to standards
- Issue 485 Failure at \'Prepare AIP\'
- Issue 520 Multi-track audo fails to normalize correctly
- Issue 528 SIP ALERT normalization when file is not in
    preservation/access format, and has no rule to generate one
- Issue 571 Test conversion of ffv1/mkv to derivative formats
- Issue 659 Normalization report doesn\'t show directory structure
- Issue 664 RemoveTranscoderConfig.conf file from transcoder etc
- Issue 667 Extract 0 byte file test fails at Store AIP
- Issue 671 All SIP directories are being placed in Failed directory,
    even if there were no failed micro-services
- Issue 672 Include GCC and kernel source to allow building VMware
    kernel module
- Issue 674 Consider mvoing extraction to the transfer area
- Issue 683 Quarantine and unquarantine events
- Issue 684 MCP crashes if left alone
- Issue 685 Add Dublin Core to METS could be part of generate mets
- Issue 686 Sanitize name event needs work
- Issue 687 Date needs to be implemented in the replacement dic
- Issue 688 Check for whitespace in output before logging to file
- Issue 691 Remove default normalization paths for office documents
- Issue 692 Get the xml rpc not to \"SPEW\" every time something
    connects
- Issue 700 Move activeTransfers and SIPCreation up to
    watchedDirectories
- Issue 702 Bell icon missing from dashboard approval steps
- Issue 703 SIP can be ordered completed, before file UUID\'s from
    transfer have completed inclusion in the SIP
- Issue 704 Add rights entities to PREMIS files
- Issue 705 Create workflow with: No normalization
- Issue 708 Remove appraisal steps from ingest
- Issue 709 Move to the uploadedDIPs directory failed
- Issue 710 Submission documentation from transfer should end up in
    objects/submissionDocumentation in the AIP
- Issue 711 Add transfer and SIP names to dashboard
- Issue 712 Normalization report not appearing in dashboard
- Issue 713 Create workflow for ingesting output of digitization
    projects
- Issue 714 Re-organize test files
- Issue 715 Micro-services with workflow decisions not showing as
    being completed
- Issue 716 Characterize and extract metadata for submission
    documentation \*rename\* -\> Characterize and extract metadata
- Issue 718 Change Actions in Create DIP? micro-service
- Issue 719 Change Actions in Approve normalization micro-service
- Issue 721 Remove quarantine from default workflow?
- Issue 723 Do not create empty Dublin Core template
- Issue 724 Remove METSGeneration.log?
- Issue 728 Ingest exports from DSpace
- Issue 729 Controlled vocabulary for METs fileSec USE attribute
    values
- Issue 731 Move to rejected directory moves to Client lib
    %rejectedDirectory%
- Issue 732 Unquarantine isn\'t working
- Issue 733 Finalize METS structure
- Issue 734 Error in dragging files from transfer to SIP causes lost
    server connection
- Issue 735 Characterize and extract metadata for submission
    documentation micro-service appears twice with two different names
- Issue 736 Changes to dmdSec of METS file
- Issue 738 Approval steps show \"Executing command(s)\" before the
    step has been approved and after the commands have been completed
- Issue 739 Rename submission documentation.log
- Issue 743 Backup and restore
- Issue 746 METS to capture transfer structure needs qa review
- Issue 748 Remove artefacts between normalizations
- Issue 751 Set transfer type showing as failed in the dashboard
- Issue 753 Normalization report empty when normalizing to access
    copies only
- Issue 754 Update file browser right-click menu options
- Issue 755 Normalization report - office documents
- Issue 756 One-step SIP creation when one transfer = 1 SIP
- Issue 758 Create fileGrp submissionDocumentation
- Issue 760 Need to update location of database interface settings
    file
- Issue 762 Add workflow and fileGrp for service copies
- Issue 763 No mdRef to descriptive metadata in METS file for DSpace
    exports
- Issue 764 Capitalization consistency in METS file
- Issue 765 Add fileGrp text/ocr to METS file for DSpace exports
- Issue 766 Break out PREMIS entities across mets sections
- Issue 768 Dublin Core metadata being added to wrong section of METS
    file
- Issue 771 Change column headers in transfers tab
- Issue 773 Ingest tab shows wrong number of SIPs
- Issue 778 Review and update micro-services help text
- Issue 782 Unicode charactors cause Failure
- Issue 785 Bagit size limit
- Issue 786 Thumbs.db files failing to properly remove
- Issue 790 If submission documenation is only in sub directories, it
    doesn\'t detect the files
- Issue 791 Duplicated job \"Approve transfer\", same SIPUUID
- Issue 792 Clicking on delete icon in transfer/SIP tab takes user to
    panel
- Issue 793 Can\'t delete transfer or SIP
- Issue 794 Remove \"Submission Information Package\" from panel or
    create separate panel for transfers
- Issue 797 Manual SIP creation fails
- Issue 799 In PREMIS file, format information appearing in the wrong
    fields
- Issue 800 Errors in object entity of PREMIS metadata
- Issue 801 Remove \"file size calculation\" from PREMIS events
- Issue 802 EventOutcomeDetailNote for ingestion event should not be
    name of file
- Issue 803 Dspace failing compliance moves to standard transfer
- Issue 805 No link to dmdSec in fileGrp or structMap in AIP generated
    by DSpace transfer
- Issue 810 Remove unneeded divs from structMap in transfer METS file
- Issue 811 Changes to directory div in structMap of transfer METS
    file
- Issue 814 Normalization event and normalized object being assigned
    the same UUID
- Issue 815 Remove empty directories from the AIP prior to generating
    the METS file
- Issue 816 Two xmlns needed for the DC metadata:
    <http://purl.org/dc/elements/1.1/> and <http://purl.org/dc/terms/>
- Issue 817 PREMIS xmlns should be premis 2.1
- Issue 820 METS file failing validation due to invalid PREMIS
    eventDateTime
- Issue 821 In mdRef, capitalize LOCYTPE and OTHERLOCTYPE
- Issue 822 Add MDTYPE=\"OTHER\" to mdRef
- Issue 824 Unable to verify checksums that come with SIPs
- Issue 825 DC edit template won\'t accept date range
- Issue 827 METS.xml should be named METS.%sipUUID%.xml
- Issue 828 Make transfer backup a configurable option
- Issue 829 AIP compression is too slow
- Issue 830 Update license statement
- Issue 831 Add underscore to file IDs in in fileGrp and structMap if
    filename starts with a number
- Issue 832 Changes to submissionDocumentation workflow
- Issue 834 Virus check fails when filename contains accented
    characters
- Issue 835 Generate METS fails when non-ascii characters included in
    metadata
- Issue 842 AIP UUID and object UUID are required in ICA-ATOM
- Issue 849 Add rightsMD sections to METS file for DSpace exports
- Issue 851 DSpace checksum verification not reporting failures
- Issue 852 In Archival storage tab, filesizes are sorted
    alphabetically rather than numerically
- Issue 855 Add date format information to date fields in rights
    template
- Issue 856 Behaviour of rights edit form should be same as DC edit
    form
- Issue 857 Error deleting from Transfer/SIP panel
- Issue 858 Can\'t delete DC metadata or rights
- Issue 861 Rights dates fields are not edtfSimpleType
- Issue 862 ADMID in structMap should be DMDID (DSpace export)
- Issue 865 Archivematica freezes if transfer directory name has
    apostrophe
- Issue 867 Add help text to DIP upload section of Administration tab
- Issue 868 Rights entered during transfer not appearing in rights
    list for SIP
- Issue 873 Rights added during transfer do not appear in METS file if
    another right is added during SIP processing
- Issue 876 Decapitalizing strings and other string glitches
- Issue 878 Remove rights holder field from rights template
- Issue 879 DC metadata not uploaded to Qubit
- Issue 880 Add sample data to Qubit so users can test DIP upload
- Issue 883 Normalization report showing each file twice
- Issue 884 VM can\'t support ffmpeg version capable of converting
    video files to h264

## Archivematica 0.7.1 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_0.7.1_Release_Notes).

Released: June 24, 2011 ([Download](Install-0.7.1-alpha))

### New features in 0.7.1

- Enhancements to the dashboard:
    -- Archival storage tab with sortable table showing links to stored
       AIP, AIP size and total AIP storage
    -- Preservation planning tab showing preservation planning policies
       and normalization statistics
- Automatic SIP processing when SIP is dropped into receiveSIP
    directory
- Submission documentation folder that allows the user to save SIP
    documentation to the AIP
- Automatic deletion of packaged (eg zipped) files once contents have
    been extracted
- Normalization reporting
- Optional manual normalization
- Support for verifying sha1 and sha256 checksums on ingest
- Ability to ingest bags (SIPs packaged in accordance with Bagit
    specification)
- Enhanced PST file handling
- Integrity checking (verification of checksums generated on ingest)
    prior to AIP packaging
- Automatic SIP deletion from SIP backups once ingest processing is
    completed
- UUID quad storage for stored AIPs
- Improved error reporting (server and client debug log capture)
- Streamlined Archivematica shutdown and restart

### Bug fixes and enhancements for 0.7.1

- Issue 63 - During ingest run script to remove Thumbs.db files
- Issue 175 - Bagit fails to create zip file when out of disk space
- Issue 209 - Normalization - Allow spaces in file names -
    normalize.py
- Issue 215 - MCP - Handle clients disconnected while processing
- Issue 265 - Log Job approved
- Issue 276 - Adding file outputs a line to standard out.
- Issue 286 - Threading locks on client threads
- Issue 292 - ClamAV engine version out of date
- Issue 301 - Add eventDetail program=\"easyextract\";
    version=\"0.1.0\"
- Issue 331 - Set permissions on DB password file so only
    Archivematica user can read it.
- Issue 368 - Normalization failed for .wav files
- Issue 370 - Install Curator\'s Workbench on Virtual Appliance
    desktop
- Issue 371 - Install Fiwalk (and tool dependencies) on Virtual
    Appliance desktop
- Issue 379 - Access copies overwritten when original files have the
    same name
- Issue 382 - Assign File UUIDs and Checksums fails when filenames
    have accented characters
- Issue 393 - Normalization of .ac3 files failed
- Issue 400 - AC3 files failed to normalize - possible codec problem
- Issue 408 - Add externals dev repo
- Issue 410 - SIP stuck in Normalization when normalizing .mp3 files
- Issue 412 - Make date in unzipped folder extension human-readable
- Issue 438 - Update copyright statement for packaging
- Issue 443 - Include readpst in transcoder depenencies
- Issue 444 - Rename transcoder to archivematica-transcoder
- Issue 446 - Compile METS micro-service fails if video normalization
    fails
- Issue 457 - In dashboard, change flashing \"refresh\" text to
    greyed-out spinning progress wheel
- Issue 446 - Move UUID to end of filename for normalized files
- Issue 466 - Make Currently processing directory a non-hidden folder
- Issue 469 - Normalization log missing \"already in preservation
    format\" events
- Issue 471 - Archivematica freezes when processing files with
    apostrophe in filename
- Issue 476 - Use python config parser to load config files
- Issue 481 - Change PREMIS eventType values to conform to standards
- Issue 486 - Sanitized Directory names of extracted directories cause
    problems with finding the file UUID
- Issue 489 - Include date in extracted directory name
- Issue 491 - Update copyright statement in the db for transcoder
- Issue 492 - Change default verifcation command to identify 0 byte
    output files and error
- Issue 493 - Change default directory verifcation command
- Issue 494 - Create library for common archivematica functions
- Issue 498 - Include transcoder DB in creation of enviroment
- Issue 499 - Transcoder - connect to database config file
- Issue 502 - Compile METS fails when normalized PDF file is damaged
- Issue 503 - Remove generation of svg preservation copy from AI
    normalization policy
- Issue 504 - Create access copies for raw camera images
- Issue 505 - Starting 00 daemon - not working on LUCID
- Issue 506 - Change default permission on stored AIPs
- Issue 509 - Change capitalization in micro-service name
- Issue 510 - \"Remove files without PREMIS\" micro-service should not
    fail if files are successfully removed
- Issue 511 - Surround sound files don\'t normalize to mp3
- Issue 513 - WAV files being normalized
- Issue 514 - Change default permission on DIPbackups
- Issue 515 - PDF to PDFA normalization failure
- Issue 517 - Create Archivematica common package
- Issue 519 - Viruses aren\'t being detected
- Issue 520 - Multi-track audio fails to normalize correctly
- Issue 522 - Can\'t normalize PDF files
- Issue 523 - FITS error log being generated for each file in a SIP
- Issue 524 - Files with no access copy normalization path not added
    to DIP
- Issue 526 - Can\'t view normalization log after normalization fails
- Issue 527 - Updated FITS causes characterize and extract metadata
    micro-service to fail
- Issue 529 - Change dashboard tab names to match OAIS functions
- Issue 530 - Have list of micro-services open if user clicks on the
    SIP name
- Issue 531 - Need to update the fits config file on install
- Issue 532 - Inkscape failing on sample
    \'Vector.NET-Free-Vector-Art-Pack-28-Freedom-Flight.eps\' file
- Issue 533 - Audio files being converted to preservation format using
    video preservation command
- Issue 534 - Transcoder - normalize - change outputFileUUID to task
    uuid on first run
- Issue 536 - Reset default permissions on SIPbackups directory
- Issue 537 - Assign File UUIDs and checksums fails when filenames
    have quotation marks in them
- Issue 538 - Can\'t extract packages
- Issue 539 - Scan for viruses doesn\'t complete
- Issue 541 - In dashboard, use different colours for micro-services
    requiring approval and micro-services that have failed
- Issue 542 - Convert init.d scripts to upstart
- Issue 543 - Build django 1.3 for externals repo
- Issue 545 - Can\'t normalize objects
- Issue 547 - Can\'t normalize Open Office documents
- Issue 549 - Normalizing FLV files causes the MCP client/server to
    disconnect
- Issue 550 - Correct spelling in vm installer script
- Issue 551 - Add approval step after normalization to allow for
    manual normalization of files
- Issue 552 - Updated twisted python required by MCP
- Issue 555 - SIP Do All progress bar /status message
- Issue 557 - Bell icon missing from dashboard approval steps
- Issue 560 - Icon does not show failed or completed successfully when
    SIP processing is finished
- Issue 563 - PREMIS format container not present when format can\'t
    be identified by FITS
- Issue 566 - Access normalization copy fails on files without
    extension
- Issue 567 - Failure at scan for viruses. Problem related to not
    being able to find the proper UUID of a file
- Issue 569 - Transcoder extract packages fails on zipped files with
    quotation marks and asterisks in filenames
- Issue 570 - Asterisk\*.zip encounters error at transcoder extract
    packages
- Issue 577 - Failure at add dc to mets
- Issue 580 - Fail verifySIPCompliance if files exist in the top-level
    directory
- Issue 582 - Make organization load from central config file.
    -requires documentation
- Issue 589 - Used bagit options to determin an AIP has been
    successfully stored
- Issue 590 - Make Bagit\'s selectable checksum work with
    archivematica
- Issue 595 - Update local dev enviroment to use upstart daemons for
    the MCP client and server, and openofficed
- Issue 598 - Normalization failing for ffmpeg
- Issue 599 - AIP - Should contain SIP UUID and Name
- Issue 602 - Rename AIPs in index.html to SIPNAME-SIPUUID and order
    by SIPName
- Issue 604 - When restructuring bag - /metadata/bag rename
    /metadata/bagit
- Issue 605 - Changes for database groups for 0.7.1
- Issue 607 - Upload DIP micro-service fails
- Issue 608 - Document how to modify workflow to not generate a DIP
- Issue 609 - Rename normalize to preservation in transcoder database
- Issue 611 - \'Sanitize file and directory names\' is taking a long
    time
- Issue 612 - Add web service to download archival storage links
- Issue 616 - Warning message in normalization
- Issue 624 - Remove pdf as access format for docx files
- Issue 640 - Document how to add/remove extensions from
    inPreservationFormat/inAccessFormat()
- Issue 644 - Logs/fileMeta not being deleted after METS is compiled
- Issue 655 - Document how to add a user to the archivematica group

## Archivematica 0.7 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_0.7_Release_Notes).

Released: February 18, 2011 ([Download](Install-0.7-alpha))

### New features in 0.7

- A web-based [dashboard](dashboard) to track the processing of SIPs
- A fully redesigned architecture ([MCP](MCP)) for distributed
    multithreaded processing
- New normalization paths, including PST to MBOX
- A complete PREMIS metadata set for each ingested object, including
    event entities generated by Archivematica\'s micro-services

### Bug fixes for 0.7

- Issue 292 - ClamAV engine version out of date
- Issue 294 - Status when approving a job - Should be processing, not
    completed.
- Issue 295 - Add ability to remove completed/failed SIPs from
    dashboard
- Issue 296 - In dashboard, add ability to sort SIPs
- Issue 298 - Move Dashboard sources out from /var/www
- Issue 299 - Make \"Cleanup AIP post bagit\" part of the \"Bagit\"
    micro-service
- Issue 300 - In dashboard, rename \"Assign UUID\" \"Assign file UUIDs
    and checksums\"
- Issue 302 - Dashboard polling
- Issue 303 - In dashboard, sort micro-services in order of completion
- Issue 307 - In PREMIS \"receive SIP\" event, move name of received
    file to eventOutcomeDetailNote
- Issue 308 - Add Dublin Core metadata template to SIP at earlier
    stage in workflow
- Issue 309 - Add name of SIP folder to SIPS table in dashboard
- Issue 310 - When errors occur, all the tasks are highlighted even if
    some tasks were completed successfully
- Issue 311 - In file directory, change acquireSIP to receiveSIP
- Issue 312 - Create copy of DIP with all files and list of files that
    were removed from uploaded DIP
- Issue 313 - Determine standard formatting for checksum.md5 file
- Issue 314 - Log files can be edited
- Issue 315 - Add option to allow SIP to continue processing if files
    fail normalization
- Issue 316 - No fixity check event in PREMIS file
- Issue 317 - DIP is locked when it is placed in the uploadDIP
    directory
- Issue 318 - Failed SIPs go to two different folders
- Issue 319 - Re-name FITS and Bagit micro-services in dashboard
- Issue 321 - Files are empty when accessed through Browse dir
- Issue 322 - Backed up SIP folders are empty
- Issue 324 - Task table column headers missing
- Issue 325 - MCP Looking for file UUID\'s of files outside of the
    objects directory.
- Issue 326 - ClamAV scanning files slowly
- Issue 328 - Normalization fails if filename has no file extension
- Issue 330 - Create preservation plan for Microsoft Word Backup
    (.wbk) files
- Issue 335 - Can\'t upload DIP
- Issue 337 - Add test SIPS with subdirectories
- Issue 338 - Consolodate the different database scripts for the MCP.
- Issue 339 - Create FFMPEG backport to Ubuntu 10.04
- Issue 340 - Remove uploadedDIPs directory
- Issue 341 - Detox removes last character from folder name
- Issue 343 - Remove some logs from SIP before bagging
- Issue 346 - create archivematicaCreateDublinCore library package
- Issue 347 - Replace md5 with sha
- Issue 351 - remove unoconv from dependencies.
- Issue 352 - rename unoconv.sh in transcoder.
- Issue 356 - Make Checksum not recursive - Compiling SIP
- Issue 361 - Create AIP checksum is disabled.
- Issue 363 - Update FITS to 0.4.3.
- Issue 369 - Include sha256deep in dependencies
- Issue 375 - Change permissions so user can delete SIP backups,
    failed SIPs, and stored AIPs
- Issue 378 - No file details for SIPs failing normalization
- Issue 381 - Remove exclamation mark from \"Requires approval\" in
    dashboard
- Issue 384 - Help text missing from dashboard approve steps
- Issue 385 - Can\'t compile METS file for SIP containing multi-page
    Adobe Illustrator files
- Issue 386 - Add access format to format policy for Adobe Illustrator
    files
- Issue 389 - In dashboard, change Show jobs and Hide jobs to Show
    Micro-services and Hide Micro-services
- Issue 390 - In dashboard, change column header from Directory to
    Submission Information Package
- Issue 391 - In dashboard, remove strikethroughs from AIPs and DIPs
    tabs
- Issue 392 - In dashboard, change current timestamp to ingest start
    time
- Issue 397 - Use xubuntuGuiScriptsEditor, to create thunar scripts,
    as part of install.
- Issue 399 - Update Local Dev Script with new PPA for archivematica.
- Issue 401 - MCP - Database connection drops after long periods of
    innactivity.
- Issue 403 - Column headers mis-aligned in dashboard
- Issue 404 - In Micro-services list in dashboard, micro-services are
    not appearing in chronological order
- Issue 405 - Add help text to \"Normalization failed\" approval step
- Issue 406 - Remove \"SIP description\" from help text box
- Issue 407 - In PREMIS creation event, move name of normalized file
    from eventDetail to eventOutcomeDetailNote
- Issue 411 - FITS fails after upgrade to FITS 0.4.3
- Issue 413 - Tooltip boxes remain visible until user manually
    refreshes dashboard.
- Issue 415 - Incorrect date/time appearing in dashboard
- Issue 416 - Add icon to rejected SIPs
- Issue 417 - In dashboard, change Delete icon text and confirmation
    box text
- Issue 418 - Create AIP checksum fails when SIP includes a
    checksum.md5 file
- Issue 419 - Rename BLAM! script
- Issue 420 - Remove Create DC script
- Issue 421 - Job created time Dec missing decimal
- Issue 423 - Couldn\'t find any package whose name or description
    matched \"archivematica-dashboard\"
- Issue 425 - Thunar shortcuts are not created by packages.
- Issue 426 - Thunar script needs to create uca.xml if it doesn\'t
    exist.
- Issue 428 - createDublinCore.py: No such file or directory - error
- Issue 432 - Include updated sample data in packages
- Issue 433 - In packaged Archivematica, can\'t upload DIP
- Issue 435 - In packaged Archivematica, no flash/javascript support
    in browser
- Issue 437 - Update copyright statement for dashboard source files.

## Archivematica 0.6 Release Notes

[Original release
notes](https://wiki.archivematica.org/Archivematica_0.6_Release_Notes).

### Release 0.6.2-alpha

- *Release date*: December 21 2010
- Release: [0.6.2-alpha (SVN 939)
    \<http://code.google.com/p/archivematica/source/browse/tags/release-0.6.2-alpha/\>]{.title-ref}\_\_
- [Installation
    instructions](http://www.archivematica.org/wiki/index.php?title=Development_environment&oldid=2983)
- [User
    documentation](http://www.archivematica.org/wiki/index.php?title=File:ArchivematicaDocs062.pdf)

#### Changes overview in 0.6.2-alpha

- Distributed system [MCP](MCP) which manages multiple tasks as
    discrete micro-services
- Multi-node, distributed SIP processing
- Complete PREMIS implementation for files in the AIP
- Web-based dashboard to track micro-services and approve jobs
- More normalization paths, including PDF to PDF/A and support for
    vector images

### Release 0.6-alpha

*Release date*: May 2010

- Included Software: [Release 0.6-alpha](Release_0.6-alpha)
- Build instructions: [Build a virtual appliance
    0.6](Build_a_virtual_appliance_0.6)
- Download: [0.6-alpha](Download)
- SVN:
    [438](http://code.google.com/p/archivematica/source/browse/trunk/?r=438)

#### Changes overview in 0.6-alpha

- Added normalize.py
