# Archivematica develoment on Docker Compose

- [Audience](#audience)
- [Requirements](#requirements)
  - [Docker and Linux](#docker-and-linux)
  - [Docker and Mac](#docker-and-mac)
  - [Elasticsearch container](#elasticsearch-container)
- [Installation](#installation)
- [Web UIs](#web-uis)
- [Upgrading to the latest version of Archivematica][intro-0]
- [Source code auto-reloading](#source-code-auto-reloading)
- [Logs](#logs)
- [Scaling](#scaling)
- [Ports](#ports)
- [Tests](#tests)
- [Cleaning up](#cleaning-up)
- [Instrumentation](#instrumentation)
  - [Running Prometheus and Grafana](#running-prometheus-and-grafana)
  - [Percona Monitoring and Management](#percona-monitoring-and-management)
- [Troubleshooting](#troubleshooting)
  - [Nginx returns 502 Bad Gateway](#nginx-returns-502-bad-gateway)
  - [MCPClient osdeps cannot be updated](#mcpclient-osdeps-cannot-be-updated)
  - [Error while mounting volume](#error-while-mounting-volume)
  - [make bootstrap fails to run](#make-bootstrap-fails-to-run)
  - [Bootstrap seems to run but the Dashboard and Elasticsearch are still down][intro-1]
  - [My environment is still broken](#my-environment-is-still-broken)
  - [PMM client service doesn't start](#pmm-client-service-doesnt-start)

[intro-0]: #upgrading-to-the-latest-version-of-archivematica
[intro-1]: #Bootstrap-seems-to-run-but-the-Dashboard-and-Elasticsearch-are-still-down

## Audience

This Archivematica environment is based on Docker Compose and it is
specifically **designed for developers**. Compose can be used in a production
environment but that is beyond the scope of this recipe.

Artefactual developers use Docker Compose heavily so it's important that you're
familiar with it. Please read the [documentation][audience-0].

[audience-0]: https://docs.docker.com/compose/reference/overview/

## Requirements

[System requirements][requirements-0]. Memory usage when the environment is
initialized (obtained using `docker stats`):

```
CONTAINER NAME                  MEM USAGE (MiB)
archivematica-mcp-server         60.6
archivematica-mcp-client         32.5
archivematica-dashboard          60.0
archivematica-storage-service    74.6
clamavd                         545.6
gearmand                          1.6
mysql                           530.4
redis                             1.8
nginx                             2.5
elasticsearch                   229.3
fits                             70.7
```

Software dependencies: Docker, Docker Compose, git and make. Please use a
recent version of Docker and Compose that support multi-stage builds and
BuildKit.

It is beyond the scope of this document to explain how these dependencies are
installed in your computer. If you're using Ubuntu 16.04 the following commands
may work:

    $ sudo apt update
    $ sudo apt install -y build-essential python-dev git
    $ sudo pip install -U docker-compose

And install Docker CE following [these instructions][requirements-1].

[requirements-0]: https://www.archivematica.org/docs/latest/getting-started/overview/system-requirements/
[requirements-1]: https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/

Install the `rng-tools` daemon if you want to set up GPG encrypted spaces. The
Storage Service container should have access to the `/dev/random` device.

### Docker and Linux

Docker will provide instructions on how to use it as a non-root user. This may
not be desirable for all.

	If you would like to use Docker as a non-root user, you should now consider
	adding your user to the "docker" group with something like:

	  sudo usermod -aG docker <user>

	Remember that you will have to log out and back in for this to take effect!

	WARNING: Adding a user to the "docker" group will grant the ability to run
			 containers which can be used to obtain root privileges on the
			 docker host.
			 Refer to https://docs.docker.com/engine/security/security/#docker-daemon-attack-surface
			 for more information.

The impact to those following this recipe is that any of the commands below
which call Docker will need to be run as a root user using 'sudo'.

### Docker and Mac

Installation of Archivematica on machines running macOS using Docker is
possible, but still in development and may require some extra steps. If you are
new to Archivematica and/or Docker, or have an older machine, it may be better
to instead use a Linux machine.

### Elasticsearch container

For the Elasticsearch container to run properly, you may need to increase the
maximum virtual memory address space `vm.max_map_count` to at least `[262144]`.
This is a configuration setting on the host machine running Docker, not the
container itself.

To make this change:

`sudo sysctl -w vm.max_map_count=262144`

To persist this setting, modify `/etc/sysctl.conf` and add:
`vm.max_map_count=262144`

For more information, please consult the Elasticsearch `6.x`
[documentation][documentation-0].

[documentation-0]: https://www.elastic.co/guide/en/elasticsearch/reference/current/vm-max-map-count.html

## Installation

If you haven't already, create a directory to store this repository using git
clone, and pull all the submodules:

    $ git clone https://github.com/artefactual/archivematica.git --branch qa/1.x --recurse-submodules

Run the installation (and all Docker Compose) commands from within the hack
directory:

    $ cd ./archivematica/hack

These are the commands you need to run when starting from scratch:

    $ make create-volumes
    $ make build
    $ docker-compose up -d
    $ make bootstrap
    $ make restart-am-services

`make create-volumes` creates two external volumes. They're heavily used in our
containers but they are provided in the host machine:

- `$HOME/.am/am-pipeline-data` - the shared directory.
- `$HOME/.am/ss-location-data` - the transfer source location.

### GNU make

Make commands above, and any subsequent calls to it below can be reviewed using
the following command from the compose directory:

    $ make help

## Upgrading to the latest version of Archivematica

The installation instructions above will install the submodules defined in
https://github.com/artefactual-labs/am/tree/master/src which are from the
`qa/1.x` branch of Archivematica and the `qa/0.x` branch of Archivematica
Storage Service.

To upgrade your installation to include the most recent changes in the
submodules, use the following commands:

    $ git pull --rebase
    $ git submodule update --init --recursive
    $ docker-compose up -d --force-recreate --build
    $ make bootstrap
    $ make restart-am-services

The submodules are not always up to date, i.e. they may not be pointing to the
latest commits of their tracking branches. They can be updated manually using
`git pull --rebase`:

    $ cd ./submodules/archivematica-storage-service && git pull --rebase
    $ cd ./submodules/archivematica-sampledata && git pull --rebase
    $ cd ./submodules/archivematica-acceptance-tests && git pull --rebase

Once you're done, run:

    $ docker-compose up -d --force-recreate --build
    $ make bootstrap
    $ make restart-am-services

Working with submodules can be a little confusing. GitHub's
[Working with submodules][submodules-0] blog post is a good introduction.

[submodules-0]: https://blog.github.com/2016-02-01-working-with-submodules/

## Web UIs

- Archivematica Dashboard: http://127.0.0.1:62080/
- Archivematica Storage Service: http://127.0.0.1:62081/

The default credentials for the Archivematica Dashboard and the Storage Service
are username: `test`, password: `test`.

## Source code auto-reloading

Dashboard and Storage Service are both served by Gunicorn. We set up Gunicorn
with the [reload](http://docs.gunicorn.org/en/stable/settings.html#reload)
setting enabled meaning that the Gunicorn workers will be restarted as soon as
code changes.

Other components in the stack like the `MCPServer` don't offer this option and
they need to be restarted manually, e.g.:

    $ docker-compose up -d --force-recreate --no-deps archivematica-mcp-server

If you've added new dependencies or changes the `Dockerfile` you should also
add the `--build` argument to the previous command in order to ensure that the
container is using the newest image, e.g.:

    $ docker-compose up -d --force-recreate --build --no-deps archivematica-mcp-server

## Logs

In recent versions of Archivematica we've changed the logging configuration so
the log events are sent to the standard streams. This is a common practice
because it makes much easier to aggregate the logs generated by all the
replicas that we may be deploying of our services across the cluster.

Docker Compose aggregates the logs for us so you can see everything from one
place. Some examples:

- `docker-compose logs -f`
- `docker-compose logs -f archivematica-storage-service`
- `docker-compose logs -f nginx archivematica-dashboard`

Docker keeps the logs in files using the [JSON File logging driver][logs-0].
If you want to clear them, we provide a simple script that can do it for us
quickly but it needs root privileges, e.g.:

    $ sudo make flush-logs

[logs-0]: https://docs.docker.com/config/containers/logging/json-file/

## Scaling

With Docker Compose we can run as many containers as we want for a service,
e.g. by default we only provision a single replica of the
`archivematica-mcp-client` service but nothing stops you from running more:

    $ docker-compose up -d --scale archivematica-mcp-client=3

We still have one service but three containers. Let's verify that the workers
are connected to Gearman:

    $ echo workers | socat - tcp:127.0.0.1:62004,shut-none | grep "_v0.0" | awk '{print $2}' - | sort -u
    172.19.0.15
    172.19.0.16
    172.19.0.17

## Ports

| Service                                 | Container port | Host port   |
| --------------------------------------- | -------------- | ----------- |
| mysql                                   | `tcp/3306`     | `tcp/62001` |
| elasticsearch                           | `tcp/9200`     | `tcp/62002` |
| redis                                   | `tcp/6379`     | `tcp/62003` |
| gearman                                 | `tcp/4730`     | `tcp/62004` |
| fits                                    | `tcp/2113`     | `tcp/62005` |
| clamavd                                 | `tcp/3310`     | `tcp/62006` |
| nginx » archivematica-dashboard         | `tcp/80`       | `tcp/62080` |
| nginx » archivematica-storage-service   | `tcp/8000`     | `tcp/62081` |

## Tests

The `Makefile` includes many useful targets for testing. List them all with:

    $ make 2>&1 | grep test-

The following targets use [`tox`](https://tox.readthedocs.io) and
[`pytest`](https://docs.pytest.org) to run the tests using MySQL
databases from Docker containers:

```
test-all                   Run all tests.
test-archivematica-common  Run Archivematica Common tests.
test-dashboard             Run Dashboard tests.
test-mcp-client            Run MCPClient tests.
test-mcp-server            Run MCPServer tests.
test-storage-service       Run Storage Service tests.
```

`tox` sets up separate virtual environments for each target and calls
`pytest` to run the tests. Their configurations live in the `tox.ini`
and `pytest.ini` files but you can set the [`TOXARGS`](tox-cli) and
[`PYTEST_ADDOPTS`](pytest-cli) environment variables to pass command
line options to each.

[tox-cli]: https://tox.readthedocs.io/en/latest/config.html#cli
[pytest-cli]: https://docs.pytest.org/en/stable/example/simple.html#how-to-change-command-line-options-defaults

For example you can run all the tests in `tox` [parallel
mode](https://tox.readthedocs.io/en/latest/example/basic.html#parallel-mode)
and make it extra verbose like this:

    $ env TOXARGS='-vv --parallel' make test-all

The MySQL test databases created by `pytest` are kept and reused after
each run, but you could [force it to recreate
them](pytest-recreate-db) like this:

    $ env PYTEST_ADDOPTS=--create-db make test-dashboard

[pytest-recreate-db]: https://pytest-django.readthedocs.io/en/latest/database.html#example-work-flow-with-reuse-db-and-create-db

Or you could run only a specific test module using its relative path
in the `PYTHONPATH` of the `tox` environment like this:

    $ env PYTEST_ADDOPTS=tests/test_reingest_mets.py make test-mcp-client

The sources of the [acceptance
tests](https://github.com/artefactual-labs/archivematica-acceptance-tests)
have been made available inside Docker using volumes so you can edit
them and the changes will apply immediately. Their `Makefile` targets
start with `test-at-`.

## Resetting the environment

In many cases, as a tester or a developer, you want to restart all the
containers at once and make sure the latest version of the images are built.
But also, you don't want to lose your data like the search index or the
database. If this is case, run the following command:

    $ docker-compose up -d --force-recreate --build

Additionally you may want to delete all the deta including the stuff in the
external volumes:

    $ make flush

Both snippets can be combined or used separately.

You may need to update the codebase, and for that you can run this command:

    $ git submodule update --init --recursive

## Cleaning up

The most effective way is:

    $ docker-compose down --volumes

It doesn't delete the external volumes described in the
[Installation](#installation) section of this document. You have to delete the
volumes manually with:

    $ docker volume rm am-pipeline-data
    $ docker volume rm ss-location-data

Optionally you may also want to delete the directories:

    $ rm -rf $HOME/.am/am-pipeline-data $HOME/.am/ss-location-data

## Percona tuning

To use different settings on the MySQL container, please edit the
`etc/mysql/tunning.conf` file and rebuild the container with:

    $ docker down
    $ docker-compose up -d

## Instrumentation

### Running Prometheus and Grafana

[Prometheus][instrumentation-0] and [Grafana][instrumentation-1] can be used
to monitor Archivematica processes.

To run them, reference the `docker-compose.instrumentation.yml` file:

    $ docker-compose -f docker-compose.yml -f docker-compose.instrumentation.yml up -d

Prometheus will start on [localhost:9090][instrumentation-2]; Grafana on
[localhost:3000][instrumentation-3].

[instrumentation-0]: https://prometheus.io/
[instrumentation-1]: https://grafana.com/
[instrumentation-2]: http://localhost:9090
[instrumentation-3]: http://localhost:3000

### Percona Monitoring and Management

Extending the default environment, you can deploy an instance of
[Percona Monitoring and Management][instrumentation-4] configured by default to
collect metrics and query analytics data from the `mysql` service. To set up the
PMM server and client services alongside all the others you'll need to indicate
two Docker Compose files:

    $ docker-compose -f docker-compose.yml -f docker-compose.pmm.yml up -d

To access the PMM server interface, visit http://localhost:62007:

* Username: ``pmm``
* Password: ``pmm``

[instrumentation-4]: https://www.percona.com/doc/percona-monitoring-and-management

## Troubleshooting

##### Nginx returns 502 Bad Gateway

We're using Nginx as a proxy. Likely the underlying issue is that
either the Dashboard or the Storage Service died. Run `docker-compose
ps` to confirm the state of their services like this:

```bash
$ docker-compose ps archivematica-dashboard archivematica-storage-service
                Name                              Command                State      Ports
-------------------------------------------------------------------------------------------
hack_archivematica-dashboard_1         /usr/local/bin/gunicorn -- ...   Up         8000/tcp
hack_archivematica-storage-service_1   /bin/sh -c /usr/local/bin/ ...   Exit 137
```

You want to see what's in the logs of the
`archivematica-storage-service` service, e.g.:

    $ docker-compose logs -f archivematica-storage-service

    ImportError: No module named storage_service.wsgi
    [2017-10-26 19:28:24 +0000] [11] [INFO] Worker exiting (pid: 11)
    [2017-10-26 19:28:24 +0000] [7] [INFO] Shutting down: Master
    [2017-10-26 19:28:24 +0000] [7] [INFO] Reason: Worker failed to boot.

Now we know why -  I had deleted the `wsgi` module. The worker crashed and
Gunicorn gave up. This could happen for example when we're rebasing a branch
and git is not atomically moving things around. But it's fixed now and you want
to give it another shot so we run `docker-compose up -d` to ensure that all the
services are up again. Next run `docker-compose ps` to verify that it's all up.

##### MCPClient osdeps cannot be updated

The MCPClient Docker image bundles a number of tools that are used by
Archivematica. They're listed in the [osdeps files][0] but the
[MCPClient.Dockerfile][1] is not making use of it yet. If you need to
introduce dependency changes in MCPClient you will need to update both.

In [#931][2] we started publishing a MCPClient base Docker image to speed up
development workflows. This means that the dependencies listed in the osdeps
files are now included in [MCPClient-base.Dockerfile][3]. Once the file is
updated you would publish the corresponding image as follows:

```
$ docker build -f MCPClient-base.Dockerfile -t artefactual/archivematica-mcp-client-base:20180219.01.52dc9959 .
$ docker push artefactual/archivematica-mcp-client-base:20180219.01.52dc9959
```

Where the tag `20180219.01.52dc9959` is a combination of the date, build number
that day and the commit that updates the Dockerfile.

As a developer you may want to build the image and test it before publishing it,
e.g.:

1. Edit `MCPClient-base.Dockerfile`.
2. Build image with new tag.
3. Update the `FROM` instruciton in `MCPClient.Dockerfile` to use it.
4. Build the image of the `archivematica-mcp-client` service.
5. Test it.
6. Publish image.

[0]: https://github.com/artefactual/archivematica/tree/qa/1.x/src/MCPClient/osdeps
[1]: https://github.com/artefactual/archivematica/blob/qa/1.x/src/MCPClient.Dockerfile
[2]: https://github.com/artefactual/archivematica/pull/931
[3]: https://github.com/artefactual/archivematica/blob/qa/1.x/src/MCPClient-base.Dockerfile

##### Error while mounting volume

Our Docker named volumes are stored under `/tmp` which means that it is
possible that they will be recycled at some point by the operative system. This
frequently happens when you restart your machine.

Under this scenario, if you try to bring up the services again you will likely
see one or more errors like the following:

    ERROR: for hack_archivematica-mcp-server_1  Cannot create container for
    service archivematica-mcp-server: error while mounting volume with options:
    type='none' device='/home/user/.am/am-pipeline-data' o='bind': no such file
    or directory

The solution is simple. You need to create the volumes again:

    $ make create-volumes

And now you're ready to continue as usual:

    $ docker-compose up -d --build

Optionally, you can define new persistent locations for the external volumes.
The defaults are defined in the `Makefile`:

    # Paths for Docker named volumes
    AM_PIPELINE_DATA ?= $(HOME)/.am/am-pipeline-data
    SS_LOCATION_DATA ?= $(HOME)/.am/ss-location-data

##### make bootstrap fails to run

In the event that `make bootstrap` fails to run while installing, the Bootstrap
components may need to be installed individually inside the application. This
error message is more likely if you are attemping to install Archivematica on a
Mac.

First, go into the Makefile and comment out everything in the
`bootstrap-dashboard-frontend` section of the script, then run `make bootstrap`
again and continue with the install process.

To install frontend Bootstrap dependencies manually:

```
yarn --cwd src/archivematica/src/dashboard/frontend install
```

`npm` should also work fine.

##### Bootstrap seems to run but the Dashboard and Elasticsearch are still down

If after running the bootstrap processes and `docker-compose ps` still shows
that the dashboard and elasticsearch are still down then check the
elasticsearch logs using:

`$ docker-compose logs -f elasticsearch`

You may see entries as follows:

```
[2019-01-25T16:36:43,535][INFO ][o.e.n.Node               ] [am-node] starting ...
[2019-01-25T16:36:43,671][INFO ][o.e.t.TransportService   ] [am-node] publish_address {172.18.0.7:9300}, bound_addresses {0.0.0.0:9300}
[2019-01-25T16:36:43,681][INFO ][o.e.b.BootstrapChecks    ] [am-node] bound or publishing to a non-loopback address, enforcing bootstrap checks
ERROR: [1] bootstrap checks failed
[1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]
[2019-01-25T16:36:43,688][INFO ][o.e.n.Node               ] [am-node] stopping ...
[2019-01-25T16:36:43,720][INFO ][o.e.n.Node               ] [am-node] stopped
[2019-01-25T16:36:43,720][INFO ][o.e.n.Node               ] [am-node] closing ...
[2019-01-25T16:36:43,730][INFO ][o.e.n.Node
```

This indicates that you may need to increase the virtual memory available to
Elasticsearch, as discussed in the section [Elasticsearch container][es-0]
above.

[es-0]: #elasticsearch-container

##### My environment is still broken

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
- [Get support](https://www.archivematica.org/community/support/).

##### PMM client service doesn't start

In some cases the `pmm_client` service fails to start reporting the following
error:

    [main] app already is running, exiting

You'll need to fully recreate the container to make it work:

    docker-compose -f docker-compose.yml -f docker-compose.pmm.yml rm pmm_client
    docker-compose -f docker-compose.yml -f docker-compose.pmm.yml up -d

[am-issues]: https://github.com/archivematica/issues/issues
