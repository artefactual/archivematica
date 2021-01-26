# Dashboard Configuration

## Table of contents

- [Dashboard Configuration](#dashboard-configuration)
  - [Table of contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Environment variables](#environment-variables)
  - [Configuration files](#configuration-files)
  - [Parameter list](#parameter-list)
    - [Application variables](#application-variables)
    - [Gunicorn variables](#gunicorn-variables)
    - [LDAP variables](#ldap-variables)
    - [CAS variables](#cas-variables)
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

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_TIME_ZONE`**:
    - **Description:** application time zone. See [TIME_ZONE](https://docs.djangoproject.com/en/1.8/ref/settings/#time-zone) for more details.
    - **Config file example:** `Dashboard.time_zone`
    - **Type:** `string`
    - **Default:** `"UTC"`

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
    - **Description:** controls what Elasticsearch indexes are enabled:
        - When set to `aips`, the Backlog tab, Appraisal tab, and the SIP Arrange pane in the Ingest tab will not be displayed.
        - When set to `transfers`, the Archival storage tab will not be displayed.
        - When set to `false`, all the mentioned parts in the previous cases will not be displayed.
        - When set to `aips,transfers` (the order does not matter) or `true`, all the mentioned parts will be displayed.
    The status of Elasticsearch indexing is indicated in the Archivematica GUI under Administration > General.
    - **Config file example:** `Dashboard.search_enabled`
    - **Type:** `boolean` or `string`
    - **Default:** `true`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_GEARMAN_SERVER`**:
    - **Description:** address of the Gearman server.
    - **Config file example:** `Dashboard.gearman_server`
    - **Type:** `string`
    - **Default:** `127.0.0.1:4730`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_PASSWORD_MINIMUM_LENGTH`**:
    - **Description:** sets minimum length for user passwords.
    - **Config file example:** `Dashboard.password_minimum_length`
    - **Type:** `integer`
    - **Default:** `8`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_PASSWORD_DISABLE_COMMON_VALIDATION`**:
    - **Description:** disables password validation that prevents users from using passwords that occur in a [list of common passwords](https://github.com/django/django/blob/stable/1.11.x/django/contrib/auth/common-passwords.txt.gz).
    - **Config file example:** `Dashboard.password_disable_common_validation`
    - **Type:** `boolean`
    - **Default:** `false`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_PASSWORD_DISABLE_USER_ATTRIBUTE_SIMILARITY_VALIDATION`**:
    - **Description:** disables password validation that prevents users from using passwords that are too similar to their username and other user attributes.
    - **Config file example:** `Dashboard.password_disable_user_attribute_similarity_validation`
    - **Type:** `boolean`
    - **Default:** `false`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_PASSWORD_DISABLE_COMPLEXITY_VALIDATION`**:
    - **Description:** disables password validation that checks that passwords contain at least three of: lower-case characters, upper-case characters, numbers, special characters.
    - **Config file example:** `Dashboard.password_disable_complexity_validation`
    - **Type:** `boolean`
    - **Default:** `false`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_SHIBBOLETH_AUTHENTICATION`**:
    - **Description:** enables the Shibboleth authentication system.
    - **Config file example:** `Dashboard.shibboleth_authentication`
    - **Type:** `boolean`
    - **Default:** `false`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_CAS_AUTHENTICATION`**:
    - **Description:** enables the CAS authentication system.
    - **Config file example:** `Dashboard.cas_authentication`
    - **Type:** `boolean`
    - **Default:** `false`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_LDAP_AUTHENTICATION`**:
    - **Description:** enables the LDAP authentication system.
    - **Config file example:** `Dashboard.ldap_authentication`
    - **Type:** `boolean`
    - **Default:** `false`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_OIDC_AUTHENTICATION`**:
    - **Description:** enables the OIDC authentication system.
    - **Config file example:** `Dashboard.oidc_authentication`
    - **Type:** `boolean`
    - **Default:** `false`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_STORAGE_SERVICE_CLIENT_TIMEOUT`**:
    - **Description:** configures the Storage Service client to stop waiting for a response after a given number of seconds.
    - **Config file example:** `Dashboard.storage_service_client_timeout`
    - **Type:** `float`
    - **Default:** `86400`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_STORAGE_SERVICE_CLIENT_QUICK_TIMEOUT`**:
    - **Description:** configures the Storage Service client to stop waiting for a response after a given number of seconds when the client uses asynchronous API endpoints.
    - **Config file example:** `Dashboard.storage_service_client_quick_timeout`
    - **Type:** `float`
    - **Default:** `5`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_AGENTARCHIVES_CLIENT_TIMEOUT`**:
    - **Description:** configures the agentarchives client to stop waiting for a response after a given number of seconds.
    - **Config file example:** `Dashboard.agentarchives_client_timeout`
    - **Type:** `float`
    - **Default:** `300`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_POLLING_INTERVAL`**:
    - **Description:** describes the interval (in seconds) at which the
    dashboard client will request an update from the server, e.g. to refresh
    the microservice jobs display.
    - **Config file example:** `Dashboard.polling_interval`
    - **Type:** `integer`
    - **Default:** `10`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_PROMETHEUS_ENABLED`**:
    - **Description:** Determines if Prometheus metrics should be collected.
    - **Config file example:** `Dashboard.prometheus_enabled`
    - **Type:** `boolean`
    - **Default:** `False`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_AUDIT_LOG_MIDDLEWARE`**:
    - **Description:** enables X-Username header with authenticated HTTP responses.
    - **Config file example:** `Dashboard.audit_log_middleware`
    - **Type:** `boolean`
    - **Default:** `False`

- **`ARCHIVEMATICA_DASHBOARD_DASHBOARD_SITE_URL`**:
    - **Description:** the public address of this service.
    - **Config file example:** `Dashboard.site_url`
    - **Type:** `string`
    - **Default:** `None`

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

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_BACKEND`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.backend`
    - **Type:** `string`
    - **Default:** `django.core.mail.backends.console.EmailBackend`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_HOST`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.host`
    - **Type:** `string`
    - **Default:** `smtp.gmail.com`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_HOST_USER`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.host_user`
    - **Type:** `string`
    - **Default:** `your_email@example.com`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_HOST_PASSWORD`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.host_password`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_PORT`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.port`
    - **Type:** `integer`
    - **Default:** `587`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_SSL_CERTFILE`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.ssl_certfile`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_SSL_KEYFILE`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.ssl_keyfile`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_USE_SSL`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.use_ssl`
    - **Type:** `boolean`
    - **Default:** `False`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_USE_TLS`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.use_tls`
    - **Type:** `boolean`
    - **Default:** `True`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_FILE_PATH`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.file_path`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_DEFAULT_FROM_EMAIL`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.default_from_email`
    - **Type:** `string`
    - **Default:** `webmaster@example.com`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_SUBJECT_PREFIX`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.subject_prefix`
    - **Type:** `string`
    - **Default:** `[Archivematica]`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_TIMEOUT`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.timeout`
    - **Type:** `integer`
    - **Default:** `300`

- ** `ARCHIVEMATICA_DASHBOARD_EMAIL_SERVER_EMAIL`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details. When the value is `None`, Archivematica uses the value in `EMAIL_HOST_USER`.
    - **Config file example:** `email.server_email`
    - **Type:** `string`
    - **Default:** `None`


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
    - **Description:** Number of gunicorn worker processes to run.  Note that since Archivematica
    installations typically run many processes on the same system, a lower number of workers than
    Gunicorn recommends should be used. See [WORKERS](http://docs.gunicorn.org/en/stable/settings.html#workers) and [How Many Workers?](https://docs.gunicorn.org/en/stable/design.html#how-many-workers) for more details.
    - **Type:** `integer`
    - **Default:** `3`

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

### LDAP variables

These variables specify the behaviour of LDAP authentication. Only applicable if `ARCHIVEMATICA_DASHBOARD_DASHBOARD_LDAP_AUTHENTICATION` is set.

- **`AUTH_LDAP_USERNAME_SUFFIX`**:
    - **Description:** A suffix that is _stripped_ from LDAP usernames when
      generating Dashboard usernames (e.g., if set to `_ldap`, LDAP user
      `demo_ldap` will be saved as `demo`).
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_SERVER_URI`**:
    - **Description:** Address of the LDAP server to authenticate against.
    - **Type:** `string`
    - **Default:** `ldap://localhost`

- **`AUTH_LDAP_BIND_DN`**:
    - **Description:** LDAP "bind DN"; the object to authenticate against the LDAP server with, in order
    to lookup users, e.g. "cn=admin,dc=example,dc=com".  Empty string for anonymous.
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_BIND_PASSWORD`**:
    - **Description:** Password for the LDAP bind DN.
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_USER_SEARCH_BASE_DN`**:
    - **Description:** Base LDAP DN for user search, e.g. "ou=users,dc=example,dc=com".
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_USER_SEARCH_BASE_FILTERSTR`**:
    - **Description:** Filter for identifying LDAP user objects, e.g. "(uid=%(user)s)". The `%(user)s`
    portion of the string will be replaced by the username. This variable is only used if
    `AUTH_LDAP_USER_SEARCH_BASE_DN` is not empty.
    - **Type:** `string`
    - **Default:** `(uid=%(user)s)`

- **`AUTH_LDAP_USER_DN_TEMPLATE`**:
    - **Description:** Template for LDAP user search, e.g. "uid=%(user)s,ou=users,dc=example,dc=com".
    Not applicable if `AUTH_LDAP_USER_SEARCH_BASE_DN` is set.
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_GROUP_IS_ACTIVE`**:
    - **Description:** Template for LDAP group used to set the Django user `is_active` flag, e.g.
    "cn=active,ou=django,ou=groups,dc=example,dc=com".
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_GROUP_IS_STAFF`**:
    - **Description:** Template for LDAP group used to set the Django user `is_staff` flag, e.g.
    "cn=staff,ou=django,ou=groups,dc=example,dc=com".
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_GROUP_IS_SUPERUSER`**:
    - **Description:** Template for LDAP group used to set the Django user `is_superuser` flag, e.g.
    "cn=admins,ou=django,ou=groups,dc=example,dc=com".
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_GROUP_SEARCH_BASE_DN`**:
    - **Description:** Base LDAP DN for group search, e.g. "ou=django,ou=groups,dc=example,dc=com".
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_GROUP_SEARCH_FILTERSTR`**:
    - **Description:** Filter for identifying LDAP group objects, e.g. "(objectClass=groupOfNames)".
    This variable is only used if `AUTH_LDAP_GROUP_SEARCH_BASE_DN` is not empty.
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_REQUIRE_GROUP`**:
    - **Description:** Filter for a group that LDAP users must belong to in order to authenticate, e.g.
    "cn=enabled,ou=django,ou=groups,dc=example,dc=com"
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_DENY_GROUP`**:
    - **Description:** Filter for a group that LDAP users must _not_ belong to in order to authenticate,
    e.g. "cn=disabled,ou=django,ou=groups,dc=example,dc=com"
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_FIND_GROUP_PERMS`**:
    - **Description:** If we should use LDAP group membership to calculate group permissions.
    - **Type:** `boolean`
    - **Default:** `false`

- **`AUTH_LDAP_CACHE_GROUPS`**:
    - **Description:** If we should cache groups to minimize LDAP traffic.
    - **Type:** `boolean`
    - **Default:** `false`

- **`AUTH_LDAP_GROUP_CACHE_TIMEOUT`**:
    - **Description:** How long we should cache LDAP groups for (in seconds). Only applies if
    `AUTH_LDAP_CACHE_GROUPS` is true.
    - **Type:** `integer`
    - **Default:** `3600`

- **`AUTH_LDAP_START_TLS`**:
    - **Description:** Determines if we update to a secure LDAP connection using StartTLS after connecting.
    - **Type:** `boolean`
    - **Default:** `true`

- **`AUTH_LDAP_PROTOCOL_VERSION`**:
    - **Description:** If set, forces LDAP protocol version 3.
    - **Type:** `integer`
    - **Default:** ``

- **`AUTH_LDAP_TLS_CACERTFILE`**:
    - **Description:** Path to a custom LDAP certificate authority file.
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_TLS_CERTFILE`**:
    - **Description:** Path to a custom LDAP certificate file.
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_TLS_KEYFILE`**:
    - **Description:** Path to a custom LDAP key file (matching the cert given in `AUTH_LDAP_TLS_CERTFILE`).
    - **Type:** `string`
    - **Default:** ``

- **`AUTH_LDAP_TLS_REQUIRE_CERT`**:
    - **Description:** How strict to be regarding TLS cerfiticate verification. Allowed values are "never",
    "allow", "try", "demand", or "hard". Corresponds to the TLSVerifyClient OpenLDAP setting.
    - **Type:** `string`
    - **Default:** ``

### CAS variables

These variables specify the behaviour of CAS authentication. Only applicable if `ARCHIVEMATICA_DASHBOARD_DASHBOARD_CAS_AUTHENTICATION` is set.

- **`AUTH_CAS_SERVER_URL`**:
    - **Description:** Address of the CAS server to authenticate against. Defaults to CAS demo server.
    - **Type:** `string`
    - **Default:** `https://django-cas-ng-demo-server.herokuapp.com/cas/`

- **`AUTH_CAS_PROTOCOL_VERSION`**:
    - **Description:** Version of CAS protocol to use. Allowed values are "1", "2", "3", or "CAS_2_SAML_1_0".
    - **Type:** `string`
    - **Default:** `3`

- **`AUTH_CAS_CHECK_ADMIN_ATTRIBUTES`**:
    - **Description:** Determines if we check user attributes returned by CAS server to determine if user is an administrator.
    - **Type:** `boolean`
    - **Default:** `false`

- **`AUTH_CAS_ADMIN_ATTRIBUTE`**:
    - **Description:** Name of attribute to check for administrator status, if `AUTH_CAS_CHECK_ADMIN_ATTRIBUTES` is True.
    - **Type:** `string`
    - **Default:** `None`

- **`AUTH_CAS_ADMIN_ATTRIBUTE_VALUE`**:
    - **Description:** Value in `AUTH_CAS_ADMIN_ATTRIBUTE` that indicates user is an administrator, if `AUTH_CAS_CHECK_ADMIN_ATTRIBUTES` is True.
    - **Type:** `string`
    - **Default:** `None`

- **`AUTH_CAS_AUTOCONFIGURE_EMAIL`**:
    - **Description:** Determines if we auto-configure an email address for new users by following the rule username@domain.
    - **Type:** `boolean`
    - **Default:** `false`

- **`AUTH_CAS_EMAIL_DOMAIN`**:
    - **Description:** Domain to use for auto-configured email addresses, if `AUTH_CAS_AUTOCONFIGURE_EMAIL` is True.
    - **Type:** `string`
    - **Default:** `None`

### OIDC variables

**OIDC support is experimental, please share your feedback!**

These variables specify the behaviour of OpenID Connect (OIDC) authentication. Only applicable if `ARCHIVEMATICA_DASHBOARD_DASHBOARD_OIDC_AUTHENTICATION` is set.

- **`OIDC_RP_CLIENT_ID`**:
    - **Description:** OIDC client ID
    - **Type:** `string`
    - **Default:** ``

- **`OIDC_RP_CLIENT_SECRET`**:
    - **Description:** OIDC client secret
    - **Type:** `string`
    - **Default:** ``

- **`AZURE_TENANT_ID`**:
    - **Description:** Azure Active Directory Tenant ID - if this is provided, the endpoint URLs will be automatically generated from this.
    - **Type:** `string`
    - **Default:** ``

- **`OIDC_OP_AUTHORIZATION_ENDPOINT`**:
    - **Description:** URL of OIDC provider authorization endpoint
    - **Type:** `string`
    - **Default:** ``

- **`OIDC_OP_TOKEN_ENDPOINT`**:
    - **Description:** URL of OIDC provider token endpoint
    - **Type:** `string`
    - **Default:** ``

- **`OIDC_OP_USER_ENDPOINT`**:
    - **Description:** URL of OIDC provider userinfo endpoint
    - **Type:** `string`
    - **Default:** ``

- **`OIDC_OP_JWKS_ENDPOINT`**:
    - **Description:** URL of OIDC provider JWKS endpoint
    - **Type:** `string`
    - **Default:** ``

- **`OIDC_RP_SIGN_ALGO`**:
    - **Description:** Algorithm used by the ID provider to sign ID tokens
    - **Type:** `string`
    - **Default:** `HS256`

## Logging configuration

Archivematica 1.6.1 and earlier releases are configured by default to log to
subdirectories in /var/log/archivematica, such as
`/var/log/archivematica/dashboard/dashboard.debug.log`. Starting with
Archivematica 1.7.0, configuration defaults to using stdout and stderr
for all logs. If no changes are made to the new default configuration, logs
will be handled by whichever process is managing Archivematica's services. For
example on Ubuntu 16.04, Ubuntu 18.04 or CentOS 7, Archivematica's processes are
managed by systemd. Logs for the Dashboard can be accessed using
`sudo journalctl -u archivematica-dashboard`. When running Archivematica using
docker, `docker-compose logs` commands can be used to access the logs from
different containers.

The dashboard will look in `/etc/archivematica` for a file called
`dashboard.logging.json`, and if found, this file will override the default
behaviour described above.

The [`dashboard.logging.json`](./dashboard.logging.json) file in this directory
provides an example that implements the logging behaviour used in Archivematica
1.6.1 and earlier.
