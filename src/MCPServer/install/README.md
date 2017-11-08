## Configuration files

This directory contains the following files:

- [`serverConfig.conf`](./serverConfig.conf) - a sample configuration file that
the user can place in `/etc/archivematica/serverConfig.conf` to tweak the
configuration of MCPServer.

- [`serverConfig.logging.json`](./serverConfig.logging.json) - read the
[logging configuration section](#logging-configuration) for more details.

## Logging configuration

Archivematica 1.6.1 and earlier releases are configured by default to log to
subdirectories in `/var/log/archivematica`, such as
`/var/log/archivematica/MCPServer/MCPServer.debug.log`. Starting with
Archivematica 1.7.0, logging configuration defaults to using stdout and stderr
for all logs. If no changes are made to the new default configuration logs
will be handled by whichever process is managing Archivematica's services. For
example on Ubuntu 16.04 or Centos 7, Archivematica's processes are managed by
systemd. Logs for the MCPServer can be accessed using
`sudo journalctl -u archivematica-mcp-server`. On Ubuntu 14.04, upstart is used
instead of systemd, so logs are usually found in `/var/log/upstart`. When
running Archivematica using docker, `docker-compose logs` commands can be used
to access the logs from different containers.

The MCPServer will look in `/etc/archivematica` for a file called
`serverConfig.logging.json`, and if found, this file will override the default
behaviour described above.

The [`serverConfig.logging.json`](./serverConfig.logging.json) file in this
directory provides an example that implements the logging behaviour used in
Archivematica 1.6.1 and earlier.
