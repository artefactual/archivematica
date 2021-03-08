# MCPClient Configuration

## Table of contents

- [MCPClient Configuration](#mcpclient-configuration)
  - [Table of contents](#table-of-contents)
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

MCPClient specific details are provided below.

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

There is an example configuration file for MCPClient included in the source
code: (see [`the example`](./clientConfig.conf))

MCPClient will look for a configuration file in one of two locations:

- `/etc/archivematica/archivematicaCommon/dbsettings`
- `/etc/archivematica/MCPClient/clientConfig.conf`

Traditionally, the dbsettings file was used to hold mysql login credentials,
which are then shared with other Archivematica components like MCPServer.
Database credentials can be set in the clientConfig.conf file instead, or
non-database parameters could be set in the dbsettings file.

## Parameter list

This is the full list of variables supported by MCPClient:

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_TIME_ZONE`**:
    - **Description:** application time zone. See [TIME_ZONE](https://docs.djangoproject.com/en/1.8/ref/settings/#time-zone) for more details.
    - **Config file example:** `MCPClient.time_zone`
    - **Type:** `string`
    - **Default:** `"UTC"`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_DJANGO_SECRET_KEY`**:
    - **Description:** a secret key used for cryptographic signing. See [SECRET_KEY](https://docs.djangoproject.com/en/1.8/ref/settings/#secret-key) for more details.
    - **Config file example:** `MCPClient.django_secret_key`
    - **Type:** `string`
    - :red_circle: **Mandatory!**

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_SHAREDDIRECTORYMOUNTED`**:
    - **Description:** location of the Archivematica Shared Directory.
    - **Config file example:** `MCPClient.sharedDirectoryMounted`
    - **Type:** `string`
    - **Default:** `/var/archivematica/sharedDirectory/`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_PROCESSINGDIRECTORY`**:
    - **Description:** location of the Archivematica Currently Procesing Directory.
    - **Config file example:** `MCPClient.processingDirectory`
    - **Type:** `string`
    - **Default:** `/var/archivematica/sharedDirectory/currentlyProcessing/`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_REJECTEDDIRECTORY`**:
    - **Description:** location of the Archivematica Rejected Directory.
    - **Config file example:** `MCPClient.rejectedDirectory`
    - **Type:** `string`
    - **Default:** `%%sharedPath%%rejected/`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_WATCHDIRECTORYPATH`**:
    - **Description:** location of the Archivematica Watched Directories.
    - **Config file example:** `MCPClient.watchDirectoryPath`
    - **Type:** `string`
    - **Default:** `/var/archivematica/sharedDirectory/watchedDirectories/`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLIENTSCRIPTSDIRECTORY`**:
    - **Description:** location of the client scripts directory.
    - **Config file example:** `MCPClient.clientScriptsDirectory`
    - **Type:** `string`
    - **Default:** `/usr/lib/archivematica/MCPClient/clientScripts/`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLIENTASSETSDIRECTORY`**:
    - **Description:** location of the client assets directory.
    - **Config file example:** `MCPClient.clientAssetsDirectory`
    - **Type:** `string`
    - **Default:** `/usr/lib/archivematica/MCPClient/assets/`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_LOADSUPPORTEDCOMMANDSSPECIAL`**:
    - **Description:** enables loading special modules.
    - **Config file example:** `MCPClient.LoadSupportedCommandsSpecial`
    - **Type:** `boolean`
    - **Default:** `true`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_MCPARCHIVEMATICASERVER`**:
    - **Description:** address of the Gearman server.
    - **Config file example:** `MCPClient.MCPArchivematicaServer`
    - **Type:** `string`
    - **Default:** `localhost:4730`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_ARCHIVEMATICACLIENTMODULES`**:
    - **Description:** location of the client modules configuration file. This can be useful when the user wants to set up workers that can only work in a limited number of tasks, e.g. a worker exclusively dedicated to antivirus scanning or file identification.
    - **Config file example:** `MCPClient.archivematicaClientModules`
    - **Type:** `string`
    - **Default:** `/usr/lib/archivematica/MCPClient/archivematicaClientModules`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_ELASTICSEARCHSERVER`**:
    - **Description:** address of the Elasticsearch server.
    - **Config file example:** `MCPClient.elasticsearchServer`
    - **Type:** `string`
    - **Default:** `localhost:9200`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_ELASTICSEARCHTIMEOUT`**:
    - **Description:** configures the Elasticsearch client to stop waiting for a response after a given number of seconds.
    - **Config file example:** `MCPClient.elasticsearchTimeout`
    - **Type:** `float`
    - **Default:** `10`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_SEARCH_ENABLED`**:
    - **Description:** controls what Elasticsearch indexes are enabled:
        - When set to `aips` or `false`, certain client scripts will exit without interacting with the Transfers related indexes, e.g., elasticSearchIndex_v0.0 and postStoreAIPHook_v1.0.
        - When set to `transfers` or `false`, certain client scripts will exit without interacting with the AIPs related indexes, e.g., indexAIP_v0.0.
        - When set to `aips,transfers` (the order does not matter) or `true`, all interactions with the Elasticsearch indexes will be made.
    - **Config file example:** `MCPClient.search_enabled`
    - **Type:** `boolean` or `string`
    - **Default:** `true`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_INDEX_AIP_CONTINUE_ON_ERROR`**:
    - **Description:** controls whether Archivematica continues processing the package when an error occurs in `indexAIP_v0.0`.
    - **Config file example:** `MCPClient.index_aip_continue_on_error`
    - **Type:** `boolean`
    - **Default:** `false`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_REMOVABLEFILES`**:
    - **Description:** comma-separated listed of file names that will be deleted.
    - **Config file example:** `MCPClient.removableFiles`
    - **Type:** `string`
    - **Default:** `Thumbs.db, Icon, Icon\r, .DS_Store`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_TEMP_DIR`**:
    - **Description:** location of the temporary directory.
    - **Config file example:** `MCPClient.temp_dir`
    - **Type:** `string`
    - **Default:** `/var/archivematica/sharedDirectory/tmp`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_STORAGE_SERVICE_CLIENT_TIMEOUT`**:
    - **Description:** configures the Storage Service client to stop waiting for a response after a given number of seconds.
    - **Config file example:** `MCPClient.storage_service_client_timeout`
    - **Type:** `float`
    - **Default:** `86400`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_STORAGE_SERVICE_CLIENT_QUICK_TIMEOUT`**:
    - **Description:** configures the Storage Service client to stop waiting for a response after a given number of seconds when the client uses asynchronous API endpoints.
    - **Config file example:** `MCPClient.storage_service_client_quick_timeout`
    - **Type:** `float`
    - **Default:** `5`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_AGENTARCHIVES_CLIENT_TIMEOUT`**:
    - **Description:** configures the agentarchives client to stop waiting for a response after a given number of seconds.
    - **Config file example:** `MCPClient.agentarchives_client_timeout`
    - **Type:** `float`
    - **Default:** `300`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_PROMETHEUS_BIND_ADDRESS`**:
    - **Description:** when set to a non-empty string, its value is parsed as the IP address on which to serve Prometheus metrics. If this value is not provided, but ``ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_PROMETHEUS_BIND_PORT`` is, then 127.0.0.1 will
    be used.
    - **Config file example:** `MCPClient.prometheus_bind_addresss`
    - **Type:** `string`
    - **Default:** `""`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_PROMETHEUS_BIND_PORT`**:
    - **Description:** The port on which to serve Prometheus metrics.
    If this value is not provided, metrics will not be served.
    - **Config file example:** `MCPClient.prometheus_bind_port`
    - **Type:** `int`
    - **Default:** `""`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLAMAV_SERVER`**:
    - **Description:** configures the `clamdscanner` backend so it knows how to reach the clamd server via UNIX socket (if the value starts with /) or TCP socket (form `host:port`, e.g.: `myclamad:3310`).
    - **Config file example:** `MCPClient.clamav_server`
    - **Type:** `string`
    - **Default:** `/var/run/clamav/clamd.ctl`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLAMAV_PASS_BY_STREAM`**:
    - **Description:** configures the `clamdscanner` backend to stream the file's contents to clamd. This is useful when clamd does not have access to the filesystem where the file is stored. When disabled, the files are read from the filesystem by reference.
    - **Config file example:** `MCPClient.clamav_pass_by_stream`
    - **Type:** `boolean`
    - **Default:** `true`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLAMAV_CLIENT_TIMEOUT`**:
    - **Description:** configures the `clamdscanner` backend to stop waiting for a response after a given number of seconds.
    - **Config file example:** `MCPClient.clamav_client_timeout`
    - **Type:** `float`
    - **Default:** `86400`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLAMAV_CLIENT_BACKEND`**:
    - **Description:** the ClamAV backend used for anti-virus scanning. The two options that are available are: `clamscanner` (via CLI) and `clamdscanner` (over TCP or UNIX socket).
    - **Config file example:** `MCPClient.clamav_client_backend`
    - **Type:** `string`
    - **Default:** `clamdscanner`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLAMAV_CLIENT_MAX_FILE_SIZE`**:
    - **Description:** files larger than this limit will not be scanned. The unit used is megabyte (MB).
    - **Config file example:** `MCPClient.clamav_client_max_file_size`
    - **Type:** `float`
    - **Default:** `2000`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLAMAV_CLIENT_MAX_SCAN_SIZE`**:
    - **Description**: sets the maximum amount of data to be scanned for each input file. Files larger than this value will be scanned but only up to this limit. Archives and other containers are recursively extracted and scanned up to this value. The unit used is megabyte (MB).
    - **Config file example:** `MCPClient.clamav_client_max_scan_size`
    - **Type:** `float`
    - **Default:** `2000`

- **`ARCHIVEMATICA_MCPCLIENT_CLIENT_ENGINE`**
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.engine`
    - **Type:** `string`
    - **Default:** `django.db.backends.mysql`

- **`ARCHIVEMATICA_MCPCLIENT_CLIENT_DATABASE`**
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.database`
    - **Type:** `string`
    - **Default:** `MCP`

- **`ARCHIVEMATICA_MCPCLIENT_CLIENT_USER`**
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.user`
    - **Type:** `string`
    - **Default:** `archivematica`

- **`ARCHIVEMATICA_MCPCLIENT_CLIENT_PASSWORD`**
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.password`
    - **Type:** `string`
    - **Default:** `demo`

- **`ARCHIVEMATICA_MCPCLIENT_CLIENT_HOST`**
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.host`
    - **Type:** `string`
    - **Default:** `localhost`

- **`ARCHIVEMATICA_MCPCLIENT_CLIENT_PORT`**
    - **Description:** a database setting. See [DATABASES](https://docs.djangoproject.com/en/1.8/ref/settings/#databases) for more details.
    - **Config file example:** `client.port`
    - **Type:** `string`
    - **Default:** `3306`

- **`ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CAPTURE_CLIENT_SCRIPT_OUTPUT`**:
    - **Description:** controls whether or not to capture stdout from client script subprocesses.  If set to `true`, then stdout is captured; if set to `false`, then stdout is not captured. If set to `true`, then stderr is captured; if set to `false`, then stderr is captured only if the subprocess has failed, i.e., returned a non-zero exit code.
    - **Config file example:** `MCPClient.capture_client_script_output`
    - **Type:** `boolean`
    - **Default:** `true`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_BACKEND`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.backend`
    - **Type:** `string`
    - **Default:** `django.core.mail.backends.console.EmailBackend`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_HOST`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.host`
    - **Type:** `string`
    - **Default:** `smtp.gmail.com`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_HOST_USER`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.host_user`
    - **Type:** `string`
    - **Default:** `your_email@example.com`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_HOST_PASSWORD`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.host_password`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_PORT`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.port`
    - **Type:** `integer`
    - **Default:** `587`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_SSL_CERTFILE`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.ssl_certfile`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_SSL_KEYFILE`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.ssl_keyfile`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_USE_SSL`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.use_ssl`
    - **Type:** `boolean`
    - **Default:** `False`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_USE_TLS`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.use_tls`
    - **Type:** `boolean`
    - **Default:** `True`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_FILE_PATH`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.file_path`
    - **Type:** `string`
    - **Default:** `None`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_DEFAULT_FROM_EMAIL`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.default_from_email`
    - **Type:** `string`
    - **Default:** `webmaster@example.com`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_SUBJECT_PREFIX`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.subject_prefix`
    - **Type:** `string`
    - **Default:** `[Archivematica]`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_TIMEOUT`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details.
    - **Config file example:** `email.timeout`
    - **Type:** `integer`
    - **Default:** `300`

- ** `ARCHIVEMATICA_MCPCLIENT_EMAIL_SERVER_EMAIL`**:
    - **Description:** an email setting. See [Sending email](https://docs.djangoproject.com/en/1.8/topics/email/) for more details. When the value is `None`, Archivematica uses the value in `EMAIL_HOST_USER`.
    - **Config file example:** `email.server_email`
    - **Type:** `string`
    - **Default:** `None`

## Logging configuration

Archivematica 1.6.1 and earlier releases are configured by default to log to
subdirectories in `/var/log/archivematica`, such as
`/var/log/archivematica/MCPClient/MCPClient.debug.log`. Starting with
Archivematica 1.7.0, logging configuration defaults to using stdout and stderr
for all logs. If no changes are made to the new default configuration, logs
will be handled by whichever process is managing Archivematica's services. For
example on Ubuntu 16.04, Ubuntu 18.04 or CentOS 7, Archivematica's processes are
managed by systemd. Logs for the MCPClient can be accessed using
`sudo journalctl -u archivematica-mcp-client`. When running Archivematica using
docker, `docker-compose logs` commands can be used to access the logs from
different containers.

The MCPClient will look in `/etc/archivematica` for a file called
`clientConfig.logging.json`, and if found, this file will override the default
behaviour described above.

The [`clientConfig.logging.json`](./clientConfig.logging.json) file in this
directory provides an example that implements the logging behaviour used in
Archivematica 1.6.1 and earlier.
