# MCPServer Configuration

## Table of contents

- [Introduction](#introduction)
- [Environment variables](#environment-variables)
- [Configuration file](#configuration-file)
- [Parameter list](#parameter-list)
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

MCPServer specific details are provided below.

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

## Configuration file

There is an example configuration file for MCPServer included in the source
code: (see [`the example`](./serverConfig.conf))

MCPClient will look for a configuration file in one of two locations:

- `/etc/archivematica/archivematicaCommon/dbsettings`
- `/etc/archivematica/MCPServer/serverConfig.conf`

Traditionally, the dbsettings file was used to hold mysql login credentials,
which are then shared with other Archivematica components like MCPClient.
Database credentials can be set in the serverConfig.conf file instead, or
non-database parameters could be set in the dbsettings file.

## Parameter list

This is the full list of variables supported by MCPServer:

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_TIME_ZONE`**:
    - **Description:** application time zone. See [TIME_ZONE](https://docs.djangoproject.com/en/1.8/ref/settings/#time-zone) for more details.
    - **Config file example:** `MCPServer.time_zone`
    - **Type:** `string`
    - **Default:** `"UTC"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_DJANGO_SECRET_KEY`**:
    - **Description:** a secret key used for cryptographic signing. See [SECRET_KEY](https://docs.djangoproject.com/en/1.8/ref/settings/#secret-key) for more details.
    - **Config file example:** `MCPServer.django_secret_key`
    - **Type:** `string`
    - :red_circle: **Mandatory!**

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_SHAREDDIRECTORY`**:
    - **Description:** location of the Archivematica Shared Directory.
    - **Config file example:** `MCPServer.sharedDirectory`
    - **Type:** `string`
    - **Default:** `"/var/archivematica/sharedDirectory/"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_PROCESSINGXMLFILE`**:
    - **Description:** name of the processing configuration file.
    - **Config file example:** `MCPServer.processingXMLFile`
    - **Type:** `string`
    - **Default:** `"processingMCP.xml"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_MCPARCHIVEMATICASERVER`**:
    - **Description:** address of the Gearman server.
    - **Config file example:** `MCPServer.MCPArchivematicaServer`
    - **Type:** `string`
    - **Default:** `"localhost:4730"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_WATCHDIRECTORYPATH`**:
    - **Description:** location of the Archivematica Watched Directories.
    - **Config file example:** `MCPServer.watchDirectoryPath`
    - **Type:** `string`
    - **Default:** `"/var/archivematica/sharedDirectory/watchedDirectories/"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_PROCESSINGDIRECTORY`**:
    - **Description:** loation of the processing directory.
    - **Config file example:** `MCPServer.processingDirectory`
    - **Type:** `string`
    - **Default:** `"/var/archivematica/sharedDirectory/currentlyProcessing/"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_REJECTEDDIRECTORY`**:
    - **Description:** location of the rejected directory.
    - **Config file example:** `MCPServer.rejectedDirectory`
    - **Type:** `string`
    - **Default:** `"%%sharedPath%%rejected/"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_WAITONAUTOAPPROVE`**:
    - **Description:** number of seconds that a thread will wait before attempting to approve a chain when it is pre-configured.
    - **Config file example:** `MCPServer.waitOnAutoApprove`
    - **Type:** `int`
    - **Default:** `"0"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_SEARCH_ENABLED`**:
    - **Description:** controls what Elasticsearch indexes are enabled. This can affect which options the MCP server makes available for user choices. E.g., If set to `false` or `aips`, then the MCP server will not make the "Send to backlong" option available at the "Create SIP(s)" choice point, as it will require the `transfers` indexes. Available options:
        - `true`: all indexes enabled.
        - `false`: no indexing enabled.
        - `aips`: only AIPs related indexes.
        - `transfers`: only Transfers related indexes.
        - `aips,transfers` (the order does not matter): same as `true`.
    - **Config file example:** `MCPServer.search_enabled`
    - **Type:** `boolean` or `string`
    - **Default:** `true`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_STORAGE_SERVICE_CLIENT_TIMEOUT`**:
    - **Description:** configures the Storage Service client to stop waiting for a response after a given number of seconds.
    - **Config file example:** `MCPClient.storage_service_client_timeout`
    - **Type:** `float`
    - **Default:** `86400`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_STORAGE_SERVICE_CLIENT_QUICK_TIMEOUT`**:
    - **Description:** configures the Storage Service client to stop waiting for a response after a given number of seconds. This applies only to requests that are supposed to return immediately.
    - **Config file example:** `MCPClient.storage_service_client_timeout`
    - **Type:** `float`
    - **Default:** `5`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_PROMETHEUS_BIND_ADDRESS`**:
    - **Description:** when set to a non-empty string, its value is parsed as the IP address on which to serve Prometheus metrics. If this value is not provided, but ``ARCHIVEMATICA_MCPSERVER_MCPSERVER_PROMETHEUS_BIND_PORT`` is, then 127.0.0.1 will
    be used.
    - **Config file example:** `MCPServer.prometheus_bind_addresss`
    - **Type:** `string`
    - **Default:** `""`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_PROMETHEUS_BIND_PORT`**:
    - **Description:** The port on which to serve Prometheus metrics.
    If this value is not provided, metrics will not be served.
    - **Config file example:** `MCPServer.prometheus_bind_port`
    - **Type:** `int`
    - **Default:** `""`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_WATCH_DIRECTORY_METHOD`**:
    - **Description:** how watched directory polling is done (`poll` or `inotify`). `inotify` is much more efficient, but only available
    when using a local filesystem on Linux.
    - **Config file example:** `MCPServer.watch_directory_method`
    - **Type:** `string`
    - **Default:** `"poll"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_WATCH_DIRECTORY_INTERVAL`**:
     - **Description:** time in seconds between filesystem poll intervals.
     - **Config file example:** `MCPServer.watch_directory_interval`
     - **Type:** `int`
     - **Default:** `"1"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_BATCH_SIZE`**:
    - **Description:** the amount of files that are processed by an instance of MCPClient as a group to speed up certain operations like database updates.
    - **Config file example:** `MCPServer.batch_size`
    - **Type:** `int`
    - **Default:** `"128"`

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_CONCURRENT_PACKAGES`**:
    - **Description:** the number of packages to process concurrently. Should typically correspond
    to the number of running MCPClients.
    - **Config file example:** `MCPServer.concurrent_packages`
    - **Type:** `int`
    - **Default:** 1/2 the number of CPU cores available to MCPServer, rounded up.

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_RPC_THREADS`**:
    - **Description:** the number of threads used to process RPC requests from the dashboard.
    - **Config file example:** `MCPServer.rpc_threads`
    - **Type:** `int`
    - **Default:** 4

- **`ARCHIVEMATICA_MCPSERVER_MCPSERVER_WORKER_THREADS`**:
    - **Description:** the number of threads used to handle MCPServer jobs.
    - **Config file example:** `MCPServer.worker_threads`
    - **Type:** `int`
    - **Default:** The number of CPU cores available to MCPServer, plus 1.

- **`ARCHIVEMATICA_MCPSERVER_CLIENT_ENGINE`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.engine`
    - **Type:** `string`
    - **Default:** `django.db.backends.mysql`

- **`ARCHIVEMATICA_MCPSERVER_CLIENT_DATABASE`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.database`
    - **Type:** `string`
    - **Default:** `MCP`

- **`ARCHIVEMATICA_MCPSERVER_CLIENT_USER`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.user`
    - **Type:** `string`
    - **Default:** `archivematica`

- **`ARCHIVEMATICA_MCPSERVER_CLIENT_PASSWORD`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.password`
    - **Type:** `string`
    - **Default:** `demo`

- **`ARCHIVEMATICA_MCPSERVER_CLIENT_HOST`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.host`
    - **Type:** `string`
    - **Default:** `localhost`

- **`ARCHIVEMATICA_MCPSERVER_CLIENT_PORT`**:
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.port`
    - **Type:** `string`
    - **Default:** `3306`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_BACKEND`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.backend`
    - **Type:** `string`
    - **Default:** `django.core.mail.backends.console.EmailBackend`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_HOST`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.host`
    - **Type:** `string`
    - **Default:** `smtp.gmail.com`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_HOST_USER`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.host_user`
    - **Type:** `string`
    - **Default:** `your_email@example.com`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_HOST_PASSWORD`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.host_password`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_PORT`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.port`
    - **Type:** `integer`
    - **Default:** `587`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_SSL_CERTFILE`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.ssl_certfile`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_SSL_KEYFILE`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.ssl_keyfile`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_USE_SSL`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.use_ssl`
    - **Type:** `boolean`
    - **Default:** `False`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_USE_TLS`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.use_tls`
    - **Type:** `boolean`
    - **Default:** `True`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_FILE_PATH`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.file_path`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_DEFAULT_FROM_EMAIL`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.default_from_email`
    - **Type:** `string`
    - **Default:** `webmaster@example.com`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_SUBJECT_PREFIX`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.subject_prefix`
    - **Type:** `string`
    - **Default:** `[Archivematica]`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_TIMEOUT`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.timeout`
    - **Type:** `integer`
    - **Default:** `300`

- ** `ARCHIVEMATICA_MCPSERVER_EMAIL_SERVER_EMAIL`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details. When the value is `None`, Archivematica uses the value in `EMAIL_HOST_USER`.
    - **Config file example:** `email.server_email`
    - **Type:** `string`
    - **Default:** `None`

## Logging configuration

Archivematica 1.6.1 and earlier releases are configured by default to log to
subdirectories in `/var/log/archivematica`, such as
`/var/log/archivematica/MCPServer/MCPServer.debug.log`. Starting with
Archivematica 1.7.0, logging configuration defaults to using stdout and stderr
for all logs. If no changes are made to the new default configuration, logs
will be handled by whichever process is managing Archivematica's services. For
example on Ubuntu 16.04, Ubuntu 18.04 or CentOS 7, Archivematica's processes are
managed by systemd. Logs for the MCPServer can be accessed using
`sudo journalctl -u archivematica-mcp-server`. When running Archivematica using
docker, `docker-compose logs` commands can be used to access the logs from
different containers.

The MCPServer will look in `/etc/archivematica` for a file called
`serverConfig.logging.json`, and if found, this file will override the default
behaviour described above.

The [`serverConfig.logging.json`](./serverConfig.logging.json) file in this
directory provides an example that implements the logging behaviour used in
Archivematica 1.6.1 and earlier.
