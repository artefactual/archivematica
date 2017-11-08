## Configuration files

This directory contains the following files:

- [`archivematica-dashboard.conf`](./archivematica-dashboard.conf) - systemd unit file sample.

- [`dashboard.conf`](./dashboard.conf) - nginx server block sample. 

- [`dashboard.gunicorn-config.py`](./dashboard.gunicorn-config.py) - gunicorn configuration file sample.

- [`dashboard.logging.json`](./dashboard.logging.json) - read the
[logging configuration section](#logging-configuration) for more details.

## Logging configuration

Archivematica 1.6.1 and earlier releases are configured by default to log to
subdirectories in `/var/log/archivematica`, such as
`/var/log/archivematica/dashboard/dashboard.debug.log`. Starting with
Archivematica 1.7.0, logging configuration defaults to using stdout and stderr
for all logs. If no changes are made to the new default configuration logs
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

The [`dashboard.logging.json`](./dashboard.logging.json) file in this directory provides an example
that implements the logging behaviour used in Archivematica 1.6.1 and earlier.
