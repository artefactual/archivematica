# Dashboard Configuration

## Table of contents

- [Introduction](#introduction)
- [Environment variables](#environment-variables)
- [Configuration files](#configuration-files)
- [Parameter list](#parameter-list)
  - [Application variables](#application-variables)
  - [Gunicorn variables](#gunicorn-variables)
- [Logging configuration](#logging-configuration)

## Introduction

Archivematica components can be configured using multipe methods.  All 
components follow the same pattern:

1. **Environment variables** - setting a configuration parameter with an 
   environment variable will override all other methods.
1. **Configuration file** - if the parameter is not set by an environment 
   variable, the component will look for a setting in its default configuration file.
1. **Application defaults**  - if the parameter is not set in an environment 
   variable or the config file, the application default is used.

Logging behaviour is configured differently, and provides two methods:

1. **`logging.json` file** - if a JSON file is present in the default location,
    the contents of the JSON file will control the components logging behaviour.
1. **Application default** - if no JSON file is present, the default logging 
   behaviour is to write to standard streams (standard out and standard error).

Dashboard specific details are provided below.

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

## Configuration files

The Dashboard will look for a configuration file in one location:

- `/etc/archivematica/archivematicaCommon/dbsettings`

Traditionally, the dbsettings file was used to hold mysql login credentials, 
which are then shared with other Archivematica components like MCPClient.
Non-database parameters can be set in the dbsets,tings file, to override the
application defaults.

The dashboard is a [WSGI](https://wsgi.readthedocs.io/) application. The
default configuration uses gunicorn as an application server together with
nginx as an http server.  The dashboard is then typically run by a service
manager such as systemd, although it can be run by other systems such as 
upstart or docker instead.

This directory contains example configuration files for these services:

- [`dashboard.gunicorn-config.py`](./dashboard.gunicorn-config.py) -
  gunicorn configuration file sample. The default location for this file is
  `/etc/archivematica/dashboard.gunicorn-config.py`.

- [`dashboard.conf`](./dashboard.conf) - nginx server block sample. The default
location for this file is `/etc/nginx/sites-available/dashboard.conf`.

- [`archivematica-dashboard.service`](./archivematica-dashboard.service) -
  systemd config sample.  The default location for this file is 
  `/etc/systemd/system/archivematica-dashboard.service`.

- [`archivematica-dashboard.conf`](./archivematica-dashboard.conf) - upstart
   config sample, for use on Ubuntu 14.04 where systemd is not available. The
   default location for this file is /etc/init/archivematica-dashboard.conf.

These are fairly basic example files, that can be extended or customised to 
meet local needs.  Depending on the method used to install your Archivematica
instance, the contents of your files may differ from these examples.

## Parameter list

This is the full list of variables supported by the Dashboard.  
The first section lists application variables that can be set as environment 
variables or in the dbsettings file.
The second section lists gunicorn variable that can be set as environment
variables or in the gunicorn configuration file.

### Application variables

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

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED`**:
    - **Description:** controls whether Elasticsearch is enabled. When set to `false`, the Backlog, Appraisal, and Archival storage tabs will not be displayed; in addition, the SIP Arrange pane in the Ingest tab will not be displayed. The status of Elasticsearch indexing is indicated in the Archivematica GUI under Administration > General.
    - **Config file example:** `MCPClient.search_enabled`
    - **Type:** `boolean`
    - **Default:** `true`

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

### Gunicorn variables

- **`AM_GUNICORN_USER`**:
    - **Description:** OS user for gunicorn worker processes to run as.  See [USER](http://docs.gunicorn.org/en/stable/settings.html#user)
    - **Type:** `integer` (user id) or `string` (user name)
    - **Default:** `archivematica`

- **`AM_GUNICORN_GROUP`**:
    - **Description:** OS group for gunicorn worker processes to run as.  See [GROUP](http://docs.gunicorn.org/en/styable/settings.html#group)
    - **Type:** `integer` (group id) or `string` (group name)
    - **Default:** `archivematica`

- **`AM_GUNICORN_BIND`**:
    - **Description:** The socket for gunicorn to bind to.  See [BIND](http://docs.gunicorn.org/en/stable/settings.html#bind)
    - **Type:** `string` (host name or ip with port number)
    - **Default:** `127.0.0.1:8002`

- **`AM_GUNICORN_WORKERS`**:
    - **Description:** Number of gunicorn worker processes to run.  See [WORKERS](http://docs.gunicorn.org/en/stable/settings.html#workers)
    - **Type:** `integer` 
    - **Default:** `1`

- **`AM_GUNICORN_WORKER_CLASS`**:
    - **Description:** The type of worker processes to run.  See [WORKER-CLASS](http://docs.gunicorn.org/en/stable/settings.html#worker-class)
    - **Type:** `string`
    - **Default:** `gevent`

- **`AM_GUNICORN_TIMEOUT`**:
    - **Description:** Worker process timeout.  See [TIMEOUT](http://docs.gunicorn.org/en/stable/settings.html#timeout)
    - **Type:** `integer` (seconds)
    - **Default:** `172800`

- **`AM_GUNICORN_RELOAD`**:
    - **Description:** Restart workers when code changes.  See [RELOAD](http://docs.gunicorn.org/en/stable/settings.html#reload)
    - **Type:** `boolean`
    - **Default:** `false`

- **`AM_GUNICORN_RELOAD_ENGINE`**:
    - **Description:** Method of performing reload.  See [RELOAD-ENGINE](http://docs.gunicorn.org/en/stable/settings.html#reload-engine)
    - **Type:** `string`
    - **Default:** `auto`

- **`AM_GUNICORN_CHDIR`**:
    - **Description:** Directory to load apps from.  See [CHDIR](http://docs.gunicorn.org/en/stable/settings.html#chdir)
    - **Type:** `string`
    - **Default:** `/usr/share/archivematica/dashboard`

- **`AM_GUNICORN_ACCESSLOG`**:
    - **Description:** Location to write access log to.  See [ACCESSLOG](http://docs.gunicorn.org/en/stable/settings.html#accesslog)
    - **Type:** `string`
    - **Default:** `/dev/null`

- **`AM_GUNICORN_ERRORLOG`**:
    - **Description:** Location to write error log to.  See [ERRORLOG](http://docs.gunicorn.org/en/stable/settings.html#errorlog)
    - **Type:** `string`
    - **Default:** `-`

- **`AM_GUNICORN_LOGLEVEL`**:
    - **Description:** The granularity of Error log outputs.  See [LOGLEVEL](http://docs.gunicorn.org/en/stable/settings.html#loglevel)
    - **Type:** `string`
    - **Default:** `INFO`

- **`AM_GUNICORN_PROC_NAME`**:
    - **Description:** Name for this instance of gunicorn.  See [PROC-NAME](http://docs.gunicorn.org/en/stable/settings.html#proc-name)
    - **Type:** `string`
    - **Default:** `archivematica-dashboard`

## Logging configuration

Archivematica 1.6.1 and earlier releases are configured by default to log to
subdirectories in /var/log/archivematica, such as
`/var/log/archivematica/dashboard/dashboard.debug.log`. Starting with
Archivematica 1.7.0, configuration defaults to using stdout and stderr
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
