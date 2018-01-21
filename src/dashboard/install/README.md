# Configuration

- [Introduction](#introduction)
- [Environment variables](#environment-variables)
- [Other configuration files](#other-configuration-files)
- [Logging configuration](#logging-configuration)

## Introduction

Dashboard has multiple sources of configuration. This is the full list ordered
by precedence (with the last listed item winning prioritization):

- Application defaults
- Configuration file: `/etc/archivematica/archivematicaCommon/dbsettings`
- Environment variables (always win precedence)

## Environment variables

The value of an environment variable is a string of characters. The
configuration system coerces the value to the types supported:

- `string` (e.g. `"foobar"`)
- `int` (e.g. `"60"`)
- `float` (e.g. `"1.20"`)
- `boolean` where truth values can be represented as follows (checked in a
case-insensitive manner):
    - True (enabled):  `"1"`, `"yes"`, `"true"` or `"on"`
    - False (disabled): `"0"`, `"no"`, `"false"` or `"off"`

Certain environment strings are mandatory, i.e. they don't have defaults and
the application will refuse to start if the user does not provide one.

Please be aware that Archivematica supports different types of distributions
(Ubuntu/CentOS packages, Ansible or Docker images) and they may override some
of these settings or provide values to mandatory fields.

This is the full list of environment strings supported:

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_DJANGO_ALLOWED_HOSTS`**:
    - **Description:** a list of strings representing the host/domain names that this Django site can serve. See [`ALLOWED_HOSTS`](https://docs.djangoproject.com/en/1.8/ref/settings/#allowed-hosts) for more details.
    - **Config file example:** `Dashboard.django_allowed_hosts`
    - **Type:** `string`
    - :red_circle: **Mandatory!**

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_DJANGO_SECRET_KEY`**:
    - **Description:** a secret key used for cryptographic signing. See [SECRET_KEY](https://docs.djangoproject.com/en/1.8/ref/settings/#secret-key) for more details.
    - **Config file example:** `Dashboard.django_secret_key`
    - **Type:** `string`
    - :red_circle: **Mandatory!**

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_SHARED_DIRECTORY`**:
    - **Description:** location of the Archivematica Shared Directory.
    - **Config file example:** `Dashboard.shared_directory`
    - **Type:** `string`
    - **Default:** `"/var/archivematica/sharedDirectory/"`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_WATCH_DIRECTORY`**:
    - **Description:** location of the Archivematica Watched Directories.
    - **Config file example:** `Dashboard.watch_directory`
    - **Type:** `string`
    - **Default:** `"/var/archivematica/sharedDirectory/watchedDirectories/"`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_ELASTICSEARCH_SERVER`**:
    - **Description:** address of the Elasticsearch server.
    - **Config file example:** `Dashboard.elasticsearch_server`
    - **Type:** `string`
    - **Default:** `"127.0.0.1:9200"`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_ELASTICSEARCH_TIMEOUT`**:
    - **Description:** configures the Elasticsearch client to stop waiting for a response after a given number of seconds.
    - **Config file example:** `Dashboard.elasticsearch_timeout`
    - **Type:** `float`
    - **Default:** `10`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_GEARMAN_SERVER`**:
    - **Description:** address of the Gearman server.
    - **Config file example:** `Dashboard.gearman_server`
    - **Type:** `string`
    - **Default:** `127.0.0.1:4730`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_SHIBBOLETH_AUTHENTICATION`**:
    - **Description:** enables the Shibboleth authentication system.
    - **Config file example:** `Dashboard.shibboleth_authentication`
    - **Type:** `boolean`
    - **Default:** `false`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_LDAP_AUTHENTICATION`**:
    - **Description:** enables the LDAP authentication system.
    - **Config file example:** `Dashboard.ldap_authentication`
    - **Type:** `boolean`
    - **Default:** `false`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_STORAGE_SERVICE_CLIENT_TIMEOUT`**:
    - **Description:** configures the Storage Service client to stop waiting for a response after a given number of seconds.
    - **Config file example:** `Dashboard.storage_service_client_timeout`
    - **Type:** `float`
    - **Default:** `86400`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_AGENTARCHIVES_CLIENT_TIMEOUT`**:
    - **Description:** configures the agentarchives client to stop waiting for a response after a given number of seconds.
    - **Config file example:** `Dashboard.agentarchives_client_timeout`
    - **Type:** `float`
    - **Default:** `300`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_FPR_CLIENT_TIMEOUT`**:
    - **Description:** configures the fpr client to stop waiting for a response after a given number of seconds.
    - **Config file example:** `Dashboard.fpr_client_timeout`
    - **Type:** `float`
    - **Default:** `60`

- **`ARCHIVEMATICA_DASHBOARD_CLIENT_ENGINE`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.engine`
    - **Type:** `string`
    - **Default:** `django.db.backends.mysql`

- **`ARCHIVEMATICA_DASHBOARD_CLIENT_DATABASE`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.database`
    - **Type:** `string`
    - **Default:** `MCP`

- **`ARCHIVEMATICA_DASHBOARD_CLIENT_USER`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.user`
    - **Type:** `string`
    - **Default:** `archivematica`

- **`ARCHIVEMATICA_DASHBOARD_CLIENT_PASSWORD`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.password`
    - **Type:** `string`
    - **Default:** `demo`

- **`ARCHIVEMATICA_DASHBOARD_CLIENT_HOST`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.host`
    - **Type:** `string`
    - **Default:** `localhost`

- **`ARCHIVEMATICA_DASHBOARD_CLIENT_PORT`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.port`
    - **Type:** `string`
    - **Default:** `3306`

- **`ARCHIVEMATICA_DASHBOARD_CLIENT_CONN_MAX_AGE`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.conn_max_age`
    - **Type:** `float`
    - **Default:** `0`


## Other configuration files

This directory contains the following files:

- [`archivematica-dashboard.conf`](./archivematica-dashboard.conf) -
systemd unit file sample.

- [`dashboard.conf`](./dashboard.conf) - nginx server block sample.

- [`dashboard.gunicorn-config.py`](./dashboard.gunicorn-config.py) -
gunicorn configuration file sample.

- [`dashboard.logging.json`](./dashboard.logging.json) - read the
[logging configuration section](#logging-configuration) for more details.

## Logging configuration

Archivematica 1.6.1 and earlier releases are configured by default to log to
subdirectories in `/var/log/archivematica`, such as
`/var/log/archivematica/dashboard/dashboard.debug.log`. Starting with
Archivematica 1.7.0, logging configuration defaults to using stdout and stderr
for all logs. If no changes are made to the new default configuration, logs
will be handled by whichever process is managing Archivematica's services. For
example on Ubuntu 16.04 or Centos 7, Archivematica's processes are managed by
systemd. Logs for the Dashboard can be accessed using
`sudo journalctl -u archivematica-dashboard`. On Ubuntu 14.04, upstart is used
instead of systemd, so logs are usually found in `/var/log/upstart`. When
running Archivematica using docker, `docker-compose logs` commands can be used
to access the logs from different containers.

The dashboard will look in `/etc/archivematica` for a file called
`dashboard.logging.json`, and if found, this file will override the default
behaviour described above.

The [`dashboard.logging.json`](./dashboard.logging.json) file in this directory
provides an example that implements the logging behaviour used in Archivematica
1.6.1 and earlier.
