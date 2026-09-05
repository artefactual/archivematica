# Archivematica development on Docker Compose

## Table of contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Audience](#audience)
- [Requirements](#requirements)
  - [Elasticsearch container](#elasticsearch-container)
- [Installation](#installation)
  - [GNU make](#gnu-make)
- [Python dependency workflows](#python-dependency-workflows)
- [Upgrading to the latest version of Archivematica](#upgrading-to-the-latest-version-of-archivematica)
- [Web UIs](#web-uis)
- [Source code auto-reloading](#source-code-auto-reloading)
- [Logs](#logs)
  - [Clearing the logs](#clearing-the-logs)
- [Scaling](#scaling)
- [Ports](#ports)
- [Tests](#tests)
  - [AMAUATs](#amauats)
- [Resetting the environment](#resetting-the-environment)
- [Cleaning up](#cleaning-up)
- [Percona tuning](#percona-tuning)
- [OIDC authentication](#oidc-authentication)
- [LDAP authentication](#ldap-authentication)
- [CAS authentication](#cas-authentication)
- [Shibboleth authentication](#shibboleth-authentication)
- [Instrumentation](#instrumentation)
  - [Running Prometheus and Grafana](#running-prometheus-and-grafana)
  - [Percona Monitoring and Management](#percona-monitoring-and-management)
- [Troubleshooting](#troubleshooting)
  - [Nginx returns 502 Bad Gateway](#nginx-returns-502-bad-gateway)
  - [Bootstrap seems to run but the Dashboard and Elasticsearch are still down](#bootstrap-seems-to-run-but-the-dashboard-and-elasticsearch-are-still-down)
  - [PMM client service doesn't start](#pmm-client-service-doesnt-start)
  - [My environment is still broken](#my-environment-is-still-broken)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Audience

This Archivematica environment is based on Docker Compose and it is
specifically **designed for developers**. Compose can be used in a production
environment but that is beyond the scope of this recipe. Please read
the [documentation][audience-compose-reference].

Artefactual developers use Docker Compose on Linux heavily so it's important
that you're familiar with it, and some choices in the configuration of this
environment break in other operative systems. This setup is actively tested on
Linux hosts running both `linux/amd64` and `linux/arm64` architectures. We rely
exclusively on container images and packages that provide support for both
architectures. However, our production-ready deployments are currently validated
only on `linux/amd64`.

[audience-compose-reference]: https://docs.docker.com/reference/cli/docker/compose/

## Requirements

[System requirements][requirements-am-docs]. The following is a sample of
memory usage when the environment is initialized in a virtual machine with
8 GB of RAM:

```shell
docker stats --all --format "table {{.Name}}\t{{.MemUsage}}"
```

```console
NAME                                 MEM USAGE / LIMIT
am-archivematica-mcp-client-1        41.3MiB / 7.763GiB
am-archivematica-dashboard-1         145.1MiB / 7.763GiB
am-archivematica-mcp-server-1        39.43MiB / 7.763GiB
am-archivematica-storage-service-1   83.96MiB / 7.763GiB
am-nginx-1                           2.715MiB / 7.763GiB
am-elasticsearch-1                   900.2MiB / 7.763GiB
am-gearmand-1                        3.395MiB / 7.763GiB
am-mysql-1                           551.9MiB / 7.763GiB
am-clamavd-1                         570MiB / 7.763GiB
```

Software dependencies: Docker Engine, Docker Compose, git and make. Please use
a version of Docker Engine greater than 23.0 which includes Buildkit as the
default builder with support for multi-stage builds and a version of Docker
Compose greater than 2.17 which supports restarts of dependent services.

It is beyond the scope of this document to explain how these dependencies are
installed in your computer.

Follow [these instructions][requirements-docker-install] to install Docker
Engine in Ubuntu. Docker also provides instructions on how to use it as a
[non-root user][requirements-docker-non-root] so you don't have to run the
following `docker compose` commands with `sudo`. Make sure to read about the
[security implications][requirements-docker-security] of this change.

[requirements-am-docs]: https://www.archivematica.org/docs/latest/getting-started/overview/system-requirements/
[requirements-docker-install]: https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
[requirements-docker-non-root]: https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user
[requirements-docker-security]: https://docs.docker.com/engine/security/#docker-daemon-attack-surface

### Elasticsearch container

For the Elasticsearch container to run properly, you may need to increase the
maximum virtual memory address space `vm.max_map_count` to at least `262144`.
This is a configuration setting on the host machine running Docker, not the
container itself.

To make this change run:

```shell
sudo sysctl -w vm.max_map_count=262144
```

To persist this setting, modify `/etc/sysctl.conf` and add:

```text
vm.max_map_count=262144
```

For more information, please consult the Elasticsearch `6.x`
[documentation][elasticsearch-docs-map-count].

[elasticsearch-docs-map-count]: https://www.elastic.co/guide/en/elasticsearch/reference/6.8/vm-max-map-count.html

## Installation

First, clone this repository this way:

```shell
git clone https://github.com/artefactual/archivematica.git --branch qa/1.x --recurse-submodules
```

This will set up the submodules defined in
<https://github.com/artefactual/archivematica/tree/qa/1.x/hack/submodules> which
are from the `qa/1.x` branch of Archivematica and the `qa/0.x` branch of
Archivematica Storage Service. These two branches are the focus of
Archivematica development and pull requests are expected to target them.

Next, run the installation (and all Docker Compose) commands from within the
`hack` directory:

```shell
cd ./archivematica/hack
```

Run the following command to create two Docker external volumes:

```shell
make create-volumes
```

These are heavily used in our containers but they are provided in the host
machine:

- `$HOME/.am/am-pipeline-data` - Archivematica's shared directory.
- `$HOME/.am/ss-location-data` - the transfer source location.

Next, build the Docker images:

```shell
make build
```

You may want to rebuild images with this command after updating the
`Dockerfile`, `pyproject.toml`, or `uv.lock`, but it's not necessary to rebuild
the images after changing Python code.

Start the services with:

```shell
docker compose up -d
```

On the first run, the Archivematica services will fail because the databases
of the Dashboard and the Storage Service have not been created. To do so, run:

```shell
make bootstrap
```

Be aware that this command drops and recreates both databases, and then runs
Django's migrations so you will lose any existing data if you run it again.

Now that the databases have been created, use the following command to restart
only the Archivematica services:

```shell
make restart-am-services
```

You should now be able to access Archivematica services through the [Web UIs](#web-uis).

### GNU make

Make commands above, and any subsequent calls to it below can be reviewed using
the following command:

```shell
make help
```

## Python dependency workflows

Install uv using the [uv installation documentation], then synchronize the
locked project and development dependencies from the repository root:

```shell
make sync
```

The root Makefile also provides `sync-runtime`, `lock`, `lock-check`, `upgrade`,
`lint`, and `check` targets. Declare runtime dependencies in
`project.dependencies` and development dependencies in
`dependency-groups.dev` in `pyproject.toml`. The committed `uv.lock` is the
sole dependency lock; requirements exports are not maintained.

The default interpreter is pinned in `.python-version`. CI overrides it to
exercise every supported Python version. The Docker build independently pins
the uv tool image and digest so tool upgrades and dependency upgrades remain
explicit.

The `hack` Makefile can update the root lock using the pinned uv container:

```shell
make lock-dependencies-am
make upgrade-dependencies-am
```

[uv installation documentation]: https://docs.astral.sh/uv/getting-started/installation/

## Upgrading to the latest version of Archivematica

To upgrade your installation to include the most recent changes in the
submodules, use the following commands:

```shell
git pull --rebase
git submodule update --init --recursive
docker compose up -d --force-recreate --build
make bootstrap
make restart-am-services
```

The submodules are not always up to date, i.e. they may not be pointing to the
latest commits of their tracking branches. They can be updated manually using
`git pull --rebase`:

```shell
cd ./submodules/archivematica-storage-service && git pull --rebase
cd ./submodules/archivematica-sampledata && git pull --rebase
cd ./submodules/archivematica-acceptance-tests && git pull --rebase
```

Once you're done, run:

```shell
docker compose up -d --force-recreate --build
make bootstrap
make restart-am-services
```

Working with submodules can be a little confusing. GitHub's
[Working with submodules][submodules-0] blog post is a good introduction.

[submodules-0]: https://blog.github.com/2016-02-01-working-with-submodules/

## Web UIs

- Archivematica Dashboard: <http://127.0.0.1:62080/>
- Archivematica Storage Service: <http://127.0.0.1:62081/>

The default credentials for the Archivematica Dashboard and the Storage Service
are username: `test`, password: `test`.

## Source code auto-reloading

Dashboard and Storage Service are served by Gunicorn. Auto‑reload is disabled by
default because Gunicorn's reload in our setup is poll‑based: it cannot use the
inotify API with our gevent configuration, so it continuously scans the
filesystem which causes unnecessary CPU load even when idle. Enable it only when
you strictly need it in your workflow.

To enable reload for either service, set flags in Compose's `.env` file in the
`hack` directory and recreate the affected services:

```env
AM_GUNICORN_RELOAD=true
SS_GUNICORN_RELOAD=true
```

Then recreate the services so the new configuration takes effect, e.g.:

```shell
docker compose up -d --force-recreate --no-deps archivematica-dashboard archivematica-storage-service
```

Other components in the stack, such as the `MCPServer`, do not support
auto-reloading and must be restarted manually, for example:

```shell
docker compose up -d --force-recreate --no-deps archivematica-mcp-server
```

If you've added new dependencies or modified the `Dockerfile`, also include the
`--build` flag to ensure the container uses the latest image:

```shell
docker compose up -d --force-recreate --build --no-deps archivematica-mcp-server
```

## Logs

In recent versions of Archivematica we've changed the logging configuration so
the log events are sent to the standard streams. This is a common practice
because it makes much easier to aggregate the logs generated by all the
replicas that we may be deploying of our services across the cluster.

Docker Compose aggregates the logs for us so you can see everything from one
place. Some examples:

- `docker compose logs --follow`
- `docker compose logs --follow archivematica-storage-service`
- `docker compose logs --follow nginx archivematica-dashboard`

### Clearing the logs

Docker keeps the logs in files using the [JSON File logging driver][logs-0].
If you want to clear them, we provide a simple script that can do it for us
quickly but it needs root privileges, e.g.:

```shell
sudo make flush-logs
```

[logs-0]: https://docs.docker.com/config/containers/logging/json-file/

## Scaling

With Docker Compose we can run as many containers as we want for a service,
e.g. by default we only provision a single replica of the
`archivematica-mcp-client` service but nothing stops you from running more:

```shell
docker compose up -d --scale archivematica-mcp-client=3
```

We still have one service but three containers. Let's verify that the workers
are connected to Gearman:

```shell
echo workers | socat - tcp:127.0.0.1:62004,shut-none | grep "_v0.0" | awk '{print $2}' - | sort -u
```

```console
172.19.0.15
172.19.0.16
172.19.0.17
```

## Ports

| Service                                 | Container port | Host port   |
| --------------------------------------- | -------------- | ----------- |
| mysql                                   | `tcp/3306`     | `tcp/62001` |
| elasticsearch                           | `tcp/9200`     | `tcp/62002` |
| gearman                                 | `tcp/4730`     | `tcp/62004` |
| clamavd                                 | `tcp/3310`     | `tcp/62006` |
| nginx » archivematica-dashboard         | `tcp/80`       | `tcp/62080` |
| nginx » archivematica-storage-service   | `tcp/8000`     | `tcp/62081` |

## Tests

The `Makefile` includes many useful targets for testing. List them all with:

```shell
make help | grep test-
```

The following targets use [`tox`](https://tox.readthedocs.io),
[`tox-uv`](https://github.com/tox-dev/tox-uv), and
[`pytest`](https://docs.pytest.org) to run the tests using MySQL:

```text
test-all                   Run all tests.
test-archivematica-common  Run Archivematica Common tests.
test-dashboard             Run Dashboard tests.
test-mcp-client            Run MCPClient tests.
test-mcp-server            Run MCPServer tests.
test-storage-service       Run Storage Service tests.
```

`tox` keeps the existing test orchestration and separate environments for each
target. `tox-uv` synchronizes those environments from the committed `uv.lock`
before calling `pytest`. The configurations live in `pyproject.toml`, and you
can set the [`TOXARGS`][tox-cli] and [`PYTEST_ADDOPTS`][pytest-cli] environment
variables to pass command-line options to each.

[tox-cli]: https://tox.readthedocs.io/en/latest/config.html#cli
[pytest-cli]: https://docs.pytest.org/en/stable/example/simple.html#how-to-change-command-line-options-defaults

For example you can run all the tests in `tox` [parallel
mode](https://tox.wiki/en/latest/user_guide.html#parallel-mode)
and make it extra verbose like this:

```shell
env TOXARGS='-vv --parallel' make test-all
```

The MySQL databases created by `pytest` are kept and reused after
each run, but you could [force it to recreate them][pytest-recreate-db] like
this:

```shell
env PYTEST_ADDOPTS='--create-db' make test-dashboard
```

[pytest-recreate-db]: https://pytest-django.readthedocs.io/en/latest/database.html#example-work-flow-with-reuse-db-and-create-db

Or you could run only a specific test module using its relative path
in the `PYTHONPATH` of the `tox` environment like this:

```shell
env PYTEST_ADDOPTS=tests/test_reingest_mets.py make test-mcp-client
```

### AMAUATs

The sources of the [Archivematica Automated User Acceptance Tests
(AMAUATs)](https://github.com/artefactual-labs/archivematica-acceptance-tests)
are available inside Docker using volumes so you can edit
them and the changes will apply immediately. They can be executed with the
`test-at-behave` Makefile target.

For example, once your Archivematica services start and you can reach the [Web
UIs](#web-uis) you can execute the [`black-box`][amauats-black-box] tag of the
AMAUATs in Firefox like this:

```shell
make test-at-behave TAGS=black-box BROWSER=Firefox
```

[amauats-black-box]: https://github.com/artefactual-labs/archivematica-acceptance-tests/tree/qa/1.x/features/black_box

## Resetting the environment

In many cases, as a tester or a developer, you want to restart all the
containers at once and make sure the latest version of the images are built.
But also, you don't want to lose your data like the search index or the
database. If this is case, run the following command:

```shell
docker compose up -d --force-recreate --build
```

Additionally you may want to delete all the data including the stuff in the
external volumes:

```shell
make flush
```

Both snippets can be combined or used separately.

You may need to update the codebase, and for that you can run this command:

```shell
git submodule update --init --recursive
```

## Cleaning up

The most effective way is:

```shell
docker compose down --volumes
```

It doesn't delete the external volumes described in the
[Installation](#installation) section of this document. You have to delete the
volumes manually with:

```shell
docker volume rm am-pipeline-data
docker volume rm ss-location-data
```

Optionally you may also want to delete the directories:

```shell
rm -rf $HOME/.am/am-pipeline-data $HOME/.am/ss-location-data
```

## Percona tuning

To use different settings on the MySQL container, please edit the
`etc/mysql/tunning.conf` file and rebuild the container with:

```shell
docker compose up -d --force-recreate mysql
```

## OIDC authentication

Use the `docker-compose.oidc.yml` overlay to start Keycloak and enable
the Dashboard's and Storage Service's OIDC authentication settings:

```shell
docker compose -f docker-compose.yml -f docker-compose.oidc.yml up -d
```

This overlay is intended for local testing and demonstrations only. It starts
Keycloak with sample realms, default credentials, and static secrets and
should not be treated as a production-ready deployment. The configuration for
the Keycloak realm can be found in the `hack/etc/keycloak/realm.json` file.

To access the Keycloak interface visit <http://127.0.0.1:8080> using these
administrative credentials:

- Username: `admin`
- Password: `admin`

To access the Dashboard or Storage Service through Keycloak use the "Log in
with OpenID Connect" links in their login pages and use these credentials:

Regular user:

- Username: `demo@example.com`
- Password: `test`

Administrative user:

- Username: `admin@example.com`
- Password: `test`

The Dashboard, the Storage Service and the browser all reach Keycloak as
`keycloak.localhost:8080`. The hostname must resolve to the local host in the
browser, which is the standard behaviour for `*.localhost` names in modern
browsers and Linux distributions, and the overlay also sets it as a Docker
network alias so the containers can use the same URLs. If `keycloak.localhost`
does not resolve on your host, add the following entry to `/etc/hosts`:

```text
127.0.0.1 keycloak.localhost
```

## LDAP authentication

Use the `docker-compose.ldap.yml` overlay to start a [VegardIT OpenLDAP]
server and enable LDAP authentication in the Dashboard and Storage Service.
The base development environment must be installed and bootstrapped first as
described in the [Installation](#installation) section:

```shell
docker compose -f docker-compose.yml -f docker-compose.ldap.yml up -d --build
```

The OpenLDAP image is pinned by digest so the development and integration-test
directories use the same server build. Its initial directory entries are
loaded from `hack/etc/ldap/init_org_entries.ldif`, but only while the directory
is being initialized. The image stores its configuration and database in
anonymous volumes that Compose reattaches when a container is recreated, and
the initialization marker they carry makes the entrypoint skip the LDIF. Pass
`--renew-anon-volumes` to discard that state after editing the LDIF or the LDAP
environment settings:

```shell
docker compose -f docker-compose.yml -f docker-compose.ldap.yml up -d \
  --force-recreate --renew-anon-volumes \
  openldap archivematica-dashboard archivematica-storage-service
```

Without `--renew-anon-volumes` the server keeps its previous directory and the
edit is silently ignored.

This overlay uses unencrypted LDAP and shared test passwords, and is intended
for local testing and demonstrations only. The LDAP server is available to
host tools at `ldap://127.0.0.1:62083`; its directory uses the base DN
`dc=archivematica,dc=org`. For example:

```shell
ldapsearch -x -H ldap://127.0.0.1:62083 \
  -D uid=ldapadmin,dc=archivematica,dc=org -w test \
  -b dc=archivematica,dc=org '(objectClass=*)'
```

All application users share the password `test`:

| Username   | LDAP groups                                          | Dashboard access | Storage Service role |
| ---------- | ---------------------------------------------------- | ---------------- | -------------------- |
| `demo`     | `enabled`                                            | Regular user     | Reader               |
| `reviewer` | `enabled`, `reviewers`                               | Regular user     | Reviewer             |
| `manager`  | `enabled`, `managers`, `reviewers`                   | Regular user     | Manager              |
| `admin`    | `enabled`, `administrators`, `managers`, `reviewers` | Superuser        | Administrator        |
| `disabled` | `enabled`, `disabled`                                | Denied           | Denied               |
| `outsider` | none                                                 | Denied           | Denied               |

Each user also has a `<username>_ldap` uid because the integration test suite
in `tests/integration/` shares this directory and enables
`AUTH_LDAP_USERNAME_SUFFIX`. Use the bare usernames with this overlay, which
leaves the suffix unset.

The multi-role memberships make precedence visible: Administrator wins over
Manager and Reviewer, and Manager wins over Reviewer. The `enabled` group is
required for authentication and `disabled` takes precedence over it.
LDAP attributes populate each local user's first name, last name, and email on
every login. The Dashboard maps the `administrators` group to its staff and
superuser flags; its other authenticated users have the same regular-user
access.

The Storage Service maps LDAP groups to its permission roles:

- **Reader** can view and list records.
- **Reviewer** adds approval or rejection of package deletion requests.
- **Manager** can perform storage and configuration operations, but cannot
  manage users.
- **Administrator** has unrestricted access, including user management.

LDAP authentication is added ahead of the local Django authentication backend,
so the local accounts created during bootstrap can still log in. Enabling LDAP
also disables user editing across both applications, for local accounts as well
as LDAP ones: the Dashboard profile page drops the name, email, and password
fields, keeping only the API key and email preferences, and the Storage Service
hides its user creation and editing actions.

Visiting the Dashboard at <http://127.0.0.1:62080> or the Storage Service at
<http://127.0.0.1:62081> shows the normal login page; enter one of the LDAP
usernames above to exercise the integration.

[VegardIT OpenLDAP]: https://github.com/vegardit/docker-openldap

## CAS authentication

Use the `docker-compose.cas.yml` overlay to start an [Apereo CAS] server and
enable the Dashboard's and Storage Service's CAS authentication settings. The
base development environment must be installed and bootstrapped first as
described in the [Installation](#installation) section:

```shell
docker compose -f docker-compose.yml -f docker-compose.cas.yml up -d --build
```

The first build of the `cas` image takes several minutes: it downloads the
[Apereo CAS WAR overlay] template pinned to the `CAS_OVERLAY_COMMIT` build
argument (a commit of the overlay template's `7.3` branch that builds the CAS
`7.3.8` stable release) and compiles it with the JSON service registry and
JSON user store modules.
Subsequent builds are cached. The CAS server configuration is mounted from
`hack/etc/cas/` at runtime, so editing the properties, the registered services
in `hack/etc/cas/services/` or the users in `hack/etc/cas/config/users.json`
only requires restarting the `cas` service.

CAS support in Archivematica uses `django-cas-ng`, whose migrations are only
applied when CAS is enabled. If the environment was bootstrapped without the
CAS overlay, apply the migrations once before logging in:

```shell
docker compose -f docker-compose.yml -f docker-compose.cas.yml run --rm --no-deps \
  --entrypoint /src/src/archivematica/dashboard/manage.py \
  archivematica-dashboard migrate --noinput

docker compose -f docker-compose.yml -f docker-compose.cas.yml run --rm --no-deps \
  --entrypoint /src/src/archivematica/storage_service/manage.py \
  archivematica-storage-service migrate --noinput
```

This overlay is intended for local testing and demonstrations only. The CAS
login interface is available at <http://cas.localhost:62082/cas/login> and the
following users are predefined:

All users share the password `test` and are members of the CAS groups
released through the `memberOf` attribute:

| Username   | CAS groups                | Dashboard role | Storage Service role |
| ---------- | ------------------------- | -------------- | -------------------- |
| `demo`     | `users`                   | Regular user   | Reader               |
| `admin`    | `administrators`, `users` | Superuser      | Administrator        |
| `manager`  | `managers`, `users`       | Regular user   | Manager              |
| `reviewer` | `reviewers`, `users`      | Regular user   | Reviewer             |

The overlay maps the CAS groups to roles through the
`AUTH_CAS_CHECK_ADMIN_ATTRIBUTES` and `AUTH_CAS_*_ATTRIBUTE` settings. The
Dashboard only supports mapping to its superuser flag; the Storage Service
also supports the manager and reviewer roles and falls back to the reader
role when no group matches.

The `cas.localhost` hostname must resolve to the local host in the browser,
which is the standard behaviour for `*.localhost` names in modern browsers and
Linux distributions. The overlay also sets it as a Docker network alias so the
Dashboard and Storage Service containers can use the same CAS URL for ticket
validation. If `cas.localhost` does not resolve on your host, add the
following entry to `/etc/hosts`:

```text
127.0.0.1 cas.localhost
```

Visiting the Dashboard at <http://127.0.0.1:62080> redirects to the CAS login
page. After authenticating, open the Storage Service at
<http://127.0.0.1:62081> in the same browser session to verify CAS single
sign-on.

[Apereo CAS]: https://apereo.github.io/cas/
[Apereo CAS WAR overlay]: https://apereo.github.io/cas/7.3.x/installation/WAR-Overlay-Installation.html

## Shibboleth authentication

Use the `docker-compose.shibboleth.yml` overlay to put a [Shibboleth Service
Provider] in front of the Dashboard and the Storage Service, with a Keycloak
realm as the SAML identity provider, and enable the Shibboleth authentication
settings of both applications. The base development environment must be
installed and bootstrapped first as described in the
[Installation](#installation) section:

```shell
docker compose -f docker-compose.yml -f docker-compose.shibboleth.yml up -d --build
```

This overlay differs from the other single sign-on overlays in how the
applications are reached. The Dashboard and the Storage Service do not speak
SAML themselves: they trust the `eppn`, `givenName`, `sn`, `mail` and
`entitlement` request headers set by a service provider in front of them. The
overlay builds a small Apache httpd image with `mod_shib` (the Shibboleth
Service Provider packaged by Debian) from `hack/etc/shibboleth/` and replaces
the nginx configuration so that <http://127.0.0.1:62080> and
<http://127.0.0.1:62081> are proxied through it. Requests between the
Archivematica services keep using the container names and never go through
the service provider. Requests to the `/api/` paths of both applications do
not require a Shibboleth session, so API clients keep working with their API
keys, and neither do the Dashboard's static files and logged-out page, which
the browser loads once the session is gone. Requests that carry the attribute
headers themselves are rejected by the service provider (`Attempt to spoof
header` in its log).

The service provider configuration is mounted from `hack/etc/shibboleth/` at
runtime, so editing it only requires recreating the `shibboleth-sp` service.
The identity provider is a `shibboleth` realm that Keycloak imports from
`hack/etc/keycloak/shibboleth-realm.json` when its container is created, so
after editing the realm recreate both:

```shell
docker compose -f docker-compose.yml -f docker-compose.shibboleth.yml up -d \
  --force-recreate keycloak shibboleth-sp
```

This overlay is intended for local testing and demonstrations only: it uses
unencrypted HTTP, shared test passwords, unsigned authentication requests and
identity provider metadata fetched over plain HTTP. Visiting the Dashboard at
<http://127.0.0.1:62080> or the Storage Service at <http://127.0.0.1:62081>
redirects to the Keycloak login page. The following users are predefined, all
with the password `test`:

| Username   | Entitlements                                                          | Dashboard role | Storage Service role |
| ---------- | --------------------------------------------------------------------- | -------------- | -------------------- |
| `demo`     | `preservation-user`                                                   | Regular user   | Reader               |
| `reviewer` | `preservation-reviewer`                                               | Regular user   | Reviewer             |
| `manager`  | `preservation-manager`, `preservation-reviewer`                       | Regular user   | Manager              |
| `admin`    | `preservation-admin`, `preservation-manager`, `preservation-reviewer` | Superuser      | Administrator        |

The applications identify users by the `eppn` (eduPersonPrincipalName)
attribute, which the realm releases as the user's email address, so the local
accounts are named `demo@example.com`, `admin@example.com` and so on; their
first name, last name and email are taken from the `givenName`, `sn` and `mail`
attributes on every login. The entitlements are Keycloak groups whose
`entitlement` attribute is released as the multi-valued eduPersonEntitlement
attribute. Both applications require it: the Dashboard maps
`preservation-admin` to its superuser flag, and the Storage Service maps
`preservation-admin`, `preservation-manager` and `preservation-reviewer` to its
administrator, manager and reviewer roles, falling back to the reader role. The
overlapping memberships make the precedence visible: administrator wins over
manager, which wins over reviewer. The attribute and entitlement names are part
of each application's settings rather than environment variables, so the
overlay only enables the backends. Enabling Shibboleth disables user editing in
both applications.

Logging out ends the session in the service provider only. The Keycloak
session survives, so the next visit logs the same user in again without asking
for a password; to switch users, sign out of Keycloak at
<http://keycloak.localhost:8080/realms/shibboleth/protocol/openid-connect/logout>
or use a private browsing window. The Dashboard returns to its logged-out page
after the service provider logout.

The service provider and the browser reach Keycloak as
`keycloak.localhost:8080`, the hostname the [OIDC overlay](#oidc-authentication)
uses too, so the same `/etc/hosts` note applies if it does not resolve on your
host. Keycloak is told this hostname (`KC_HOSTNAME`) because the identity
provider metadata embeds it, and the service provider fetches that metadata
through the `keycloak` container name because libcurl, which `shibd` uses,
resolves `*.localhost` names to the loopback address on its own.

To inspect a session, open <http://127.0.0.1:62080/Shibboleth.sso/Session> (or
the same path on port 62081) after logging in: it lists the attributes the
service provider received. The service provider status page is limited to the
container, and its log carries both `shibd` and Apache:

```shell
docker compose -f docker-compose.yml -f docker-compose.shibboleth.yml \
  exec shibboleth-sp curl -s http://127.0.0.1/Shibboleth.sso/Status

docker compose -f docker-compose.yml -f docker-compose.shibboleth.yml \
  logs shibboleth-sp
```

The Keycloak administration console at <http://keycloak.localhost:8080>
(username `admin`, password `admin`) shows the `shibboleth` realm, its two SAML
clients and the `archivematica-attributes` client scope that releases the
attributes.

[Shibboleth Service Provider]: https://shibboleth.atlassian.net/wiki/spaces/SP3/overview

## Instrumentation

### Running Prometheus and Grafana

[Prometheus][instrumentation-0] and [Grafana][instrumentation-1] can be used
to monitor Archivematica processes.

To run them, reference the `docker-compose.instrumentation.yml` file:

```shell
docker compose -f docker-compose.yml -f docker-compose.instrumentation.yml up -d
```

Prometheus will start on [127.0.0.1:9090][instrumentation-2]; Grafana on
[127.0.0.1:3000][instrumentation-3].

[instrumentation-0]: https://prometheus.io/
[instrumentation-1]: https://grafana.com/
[instrumentation-2]: http://127.0.0.1:9090
[instrumentation-3]: http://127.0.0.1:3000

### Percona Monitoring and Management

Extending the default environment, you can deploy an instance of
[Percona Monitoring and Management][instrumentation-4] configured by default to
collect metrics and query analytics data from the `mysql` service. To set up the
PMM server and client services alongside all the others you'll need to indicate
two Docker Compose files:

```shell
docker compose -f docker-compose.yml -f docker-compose.pmm.yml up -d
```

To access the PMM server interface, visit <http://127.0.0.1:62007>:

- Username: ``admin``
- Password: ``admin``

[instrumentation-4]: https://www.percona.com/doc/percona-monitoring-and-management

## Troubleshooting

### Nginx returns 502 Bad Gateway

We're using Nginx as a proxy. Likely the underlying issue is that
either the Dashboard or the Storage Service died. Run `docker compose
ps` to confirm the state of their services like this:

```shell
docker compose ps --all archivematica-dashboard archivematica-storage-service
```

```console
NAME                                 IMAGE                              COMMAND                  SERVICE                         CREATED             STATUS                      PORTS
am-archivematica-dashboard-1         am-archivematica-dashboard         "/usr/local/bin/guni…"   archivematica-dashboard         11 minutes ago      Up 27 seconds               8000/tcp
am-archivematica-storage-service-1   am-archivematica-storage-service   "/usr/local/bin/guni…"   archivematica-storage-service   11 minutes ago      Exited (3) 28 seconds ago
```

You want to see what's in the logs of the `archivematica-storage-service`
service, e.g.:

```shell
docker compose logs --no-log-prefix --tail 5 archivematica-storage-service
```

```console
  File "<frozen importlib._bootstrap>", line 953, in _find_and_load_unlocked
ModuleNotFoundError: No module named 'storage_service.wsgi'
[2023-06-02 03:53:00 +0000] [9] [INFO] Worker exiting (pid: 9)
[2023-06-02 03:53:00 +0000] [1] [INFO] Shutting down: Master
[2023-06-02 03:53:00 +0000] [1] [INFO] Reason: Worker failed to boot.
```

Now we know why -  I had deleted the `wsgi` module. The worker crashed and
Gunicorn gave up. This could happen for example when we're rebasing a branch
and git is not atomically moving things around. But it's fixed now and you want
to give it another shot so we run `docker compose up -d` to ensure that all the
services are up again. Next run `docker compose ps` to verify that it's all up.

### Bootstrap seems to run but the Dashboard and Elasticsearch are still down

If after running the bootstrap processes and `docker compose ps` still shows
that the dashboard and elasticsearch are still down then check the
elasticsearch logs using:

```shell
docker compose logs --no-log-prefix --tail 8 elasticsearch
```

You may see entries as follows:

```console
[2023-06-02T03:50:27,970][INFO ][o.e.b.BootstrapChecks    ] [am-node] bound or publishing to a non-loopback address, enforcing bootstrap checks
ERROR: [1] bootstrap checks failed
[1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]
[2023-06-02T03:50:28,006][INFO ][o.e.n.Node               ] [am-node] stopping ...
[2023-06-02T03:50:28,077][INFO ][o.e.n.Node               ] [am-node] stopped
[2023-06-02T03:50:28,077][INFO ][o.e.n.Node               ] [am-node] closing ...
[2023-06-02T03:50:28,088][INFO ][o.e.n.Node               ] [am-node] closed
[2023-06-02T03:50:28,090][INFO ][o.e.x.m.j.p.NativeController] [am-node] Native controller process has stopped - no new native processes can be started
```

This indicates that you may need to increase the virtual memory available to
Elasticsearch, as discussed in the section [Elasticsearch container][es-0]
above.

[es-0]: #elasticsearch-container

### PMM client service doesn't start

In some cases the `pmm_client` service fails to start reporting the following
error:

```console
[main] app already is running, exiting
```

You'll need to fully recreate the container to make it work:

```shell
docker compose -f docker-compose.yml -f docker-compose.pmm.yml rm pmm_client
docker compose -f docker-compose.yml -f docker-compose.pmm.yml up -d
```

### My environment is still broken

You've read this far but you haven't yet figured out why your development
environment is not working? Here are some tips:

- Does your system meet the [requirements](#requirements)? Some services like
  Elasticsearch or ClamAV need a lot of memory!
- Make sure that you've checked out the
  [latest](https://github.com/artefactual/archivematica/commits/qa/1.x)
  commit of this repository.
- Make sure that your repositories under `/hack/submodules`
  (submodules) are up to date. If you are working off your own
  branches, make sure they are not outdated.  Rebase often!
- Look for open/closed [issues][am-issues] that may relate to your
  problem!
- [Get support](https://www.archivematica.org/community/).

[am-issues]: https://github.com/archivematica/issues/issues
