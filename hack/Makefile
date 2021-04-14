.DEFAULT_GOAL := help

# Ensure that Composes uses BuildKit.
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

# Paths for Docker named volumes
AM_PIPELINE_DATA ?= $(HOME)/.am/am-pipeline-data
SS_LOCATION_DATA ?= $(HOME)/.am/ss-location-data

CALLER_UID=$(shell id -u)
CALLER_GID=$(shell id -g)

SRCDIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../src)

NULL :=
SPACE := $(NULL) $(NULL)

define compose_all
	docker-compose -f docker-compose.yml -f docker-compose.acceptance-tests.yml -f docker-compose.pmm.yml $(1)
endef

define compose_amauat
	docker-compose -f docker-compose.yml -f docker-compose.acceptance-tests.yml $(1)
endef

define compose_tests
	docker-compose -f docker-compose.yml -f docker-compose.tests.yml $(1)
endef

define run_toxenvs
	$(call compose_tests, \
		run \
			-e DJANGO_SETTINGS_MODULE=settings.testmysql \
			-e PYTEST_ADDOPTS=$(subst $(SPACE),\$(SPACE),${PYTEST_ADDOPTS}) \
			--user $(CALLER_UID):$(CALLER_GID) \
			--workdir /src \
			--rm \
			--entrypoint tox \
				archivematica-tests \
					$(subst $(SPACE), -e ,$(SPACE)$(1)) \
					${TOXARGS})
endef

start-mysql: test-build
	$(call compose_tests, \
		run \
			--user $(CALLER_UID):$(CALLER_GID) \
			--rm \
			--entrypoint bash \
				archivematica-tests \
					/src/hack/wait-for-it.sh mysql:3306 --timeout=30)

define create_db
	docker-compose exec -T mysql mysql -hlocalhost -uroot -p12345 -e '\
		DROP DATABASE IF EXISTS `$(1)`; \
		CREATE DATABASE `$(1)`; \
		GRANT ALL ON `$(1)`.* TO "archivematica"@"%" IDENTIFIED BY "demo";'
endef

define drop_db
	docker-compose exec -T mysql mysql -hlocalhost -uroot -p12345 -e 'DROP DATABASE IF EXISTS `$(1)`;'
endef

create-volumes:  ## Create external data volumes.
	mkdir -p ${AM_PIPELINE_DATA}
	docker volume create \
		--opt type=none \
		--opt o=bind \
		--opt device=$(AM_PIPELINE_DATA) \
			am-pipeline-data
	mkdir -p ${SS_LOCATION_DATA}
	docker volume create \
		--opt type=none \
		--opt o=bind \
		--opt device=$(SS_LOCATION_DATA) \
			ss-location-data

build:  # Build Compose services.
	docker-compose build

bootstrap: bootstrap-storage-service bootstrap-dashboard-db bootstrap-dashboard-frontend  ## Full bootstrap.

bootstrap-storage-service:  ## Boostrap Storage Service (new database).
	docker-compose exec -T mysql mysql -hlocalhost -uroot -p12345 -e "\
		DROP DATABASE IF EXISTS SS; \
		CREATE DATABASE SS; \
		GRANT ALL ON SS.* TO 'archivematica'@'%' IDENTIFIED BY 'demo';"
	docker-compose run \
		--rm \
		--entrypoint /src/storage_service/manage.py \
			archivematica-storage-service \
				migrate --noinput
	docker-compose run \
		--rm \
		--entrypoint /src/storage_service/manage.py \
			archivematica-storage-service \
				create_user \
					--username="test" \
					--password="test" \
					--email="test@test.com" \
					--api-key="test" \
					--superuser
	# SS needs to be restarted so the local space is created.
	# See #303 (https://git.io/vNKlM) for more details.
	docker-compose restart archivematica-storage-service

makemigrations-ss:
	docker-compose run \
		--user $(CALLER_UID):$(CALLER_GID) \
		--rm \
		--entrypoint /src/storage_service/manage.py \
			archivematica-storage-service \
				makemigrations

manage-dashboard:  ## Run Django /manage.py on Dashboard, suppling <command> [options] as value to ARG, e.g., `make manage-ss ARG=shell`
	docker-compose run \
		--user $(CALLER_UID):$(CALLER_GID) \
		--rm \
		--entrypoint /src/src/dashboard/src/manage.py \
			archivematica-dashboard \
				$(ARG)

manage-ss:  ## Run Django /manage.py on Storage Service, suppling <command> [options] as value to ARG, e.g., `make manage-ss ARG='shell --help'`
	docker-compose run \
		--user $(CALLER_UID):$(CALLER_GID) \
		--rm \
		--entrypoint /src/storage_service/manage.py \
			archivematica-storage-service \
				$(ARG)

bootstrap-dashboard-db:  ## Bootstrap Dashboard (new database).
	docker-compose exec -T mysql mysql -hlocalhost -uroot -p12345 -e "\
		DROP DATABASE IF EXISTS MCP; \
		CREATE DATABASE MCP; \
		GRANT ALL ON MCP.* TO 'archivematica'@'%' IDENTIFIED BY 'demo';"
	docker-compose run \
		--rm \
		--entrypoint /src/src/dashboard/src/manage.py \
			archivematica-dashboard \
				migrate --noinput
	docker-compose run \
		--rm \
		--entrypoint /src/src/dashboard/src/manage.py \
			archivematica-dashboard \
				install \
					--username="test" \
					--password="test" \
					--email="test@test.com" \
					--org-name="test" \
					--org-id="test" \
					--api-key="test" \
					--ss-url="http://archivematica-storage-service:8000" \
					--ss-user="test" \
					--ss-api-key="test" \
					--site-url="http://archivematica-dashboard:8000"

bootstrap-dashboard-frontend:  ## Build front-end assets.
	docker-compose run \
		-e HOME=/tmp/yarn-config \
		--rm \
		--no-deps \
		--user $(CALLER_UID):$(CALLER_GID) \
		--entrypoint yarn \
			archivematica-dashboard \
				--cwd=/src/src/dashboard/frontend install --frozen-lockfile

restart-am-services:  ## Restart Archivematica services: MCPServer, MCPClient, Dashboard and Storage Service.
	docker-compose restart archivematica-mcp-server
	docker-compose restart archivematica-mcp-client
	docker-compose restart archivematica-dashboard
	docker-compose restart archivematica-storage-service

compile-requirements-am:  ## Run pip-compile for Archivematica
	docker-compose run --workdir /src \
		-e XDG_CACHE_HOME=/tmp/pip-cache \
		--rm \
		--no-deps \
		--user $(CALLER_UID):$(CALLER_GID) \
		--entrypoint bash archivematica-mcp-server \
			-c "make pip-compile"

compile-requirements-ss:  ## Run pip-compile for Storage Service
	docker-compose run --workdir /src/requirements \
		-e XDG_CACHE_HOME=/tmp/pip-cache \
		--rm \
		--no-deps \
		--user $(CALLER_UID):$(CALLER_GID) \
		--entrypoint bash archivematica-storage-service \
			-c "make pip-compile"

db:  ## Connect to the MySQL server using the CLI.
	docker-compose exec mysql mysql -hlocalhost -uroot -p12345

flush: flush-shared-dir flush-search bootstrap restart-am-services  ## Delete ALL user data.

flush-shared-dir-mcp-configs:  ## Delete processing configurations - it restarts MCPServer.
	rm -f ${AM_PIPELINE_DATA}/sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml
	rm -f ${AM_PIPELINE_DATA}/sharedMicroServiceTasksConfigs/processingMCPConfigs/automatedProcessingMCP.xml
	docker-compose restart archivematica-mcp-server

flush-shared-dir:  ## Delete contents of the shared directory data volume.
	rm -rf ${AM_PIPELINE_DATA}/*

flush-search:  ## Delete Elasticsearch indices.
	docker-compose exec archivematica-mcp-client curl -XDELETE "http://elasticsearch:9200/aips,aipfiles,transfers,transferfiles"

flush-logs:  ## Delete container logs - requires root privileges.
	@./helpers/flush-docker-logs.sh

# These include the database names used in the settings.testmysql
# modules plus the prefixed and suffixed variations used by Django and
# tox
__TEST_DBS := DASHBOARDTEST MCPCLIENTTEST MCPSERVERTEST SSTEST test_DASHBOARDTEST test_DASHBOARDTEST_archivematica-common test_DASHBOARDTEST_dashboard test_MCP test_MCPCLIENTTEST test_MCPCLIENTTEST_mcpclient test_MCPSERVERTEST test_MCPSERVERTEST_mcpserver test_SS test_SSTEST test_SSTEST_storage-service
flush-test-dbs: start-mysql
	$(foreach test_db,$(__TEST_DBS),$(call drop_db,$(test_db));)

test-build:  ## Build archivematica-tests image.
	docker build \
		-t archivematica-tests \
		-f $(CURDIR)/Dockerfile \
		--build-arg TARGET=archivematica-tests \
			../

__TOXENVS_MCPSERVER := py27-mcpserver
test-mcp-server: start-mysql  ## Run MCPServer tests.
	$(call run_toxenvs,$(__TOXENVS_MCPSERVER))

test-mcp-server-py36: start-mysql  ## Run MCPServer tests in Python 3.6.
	$(call run_toxenvs,py36-mcpserver)

__TOXENVS_MCPCLIENT = py27-mcpclient mcpclient-ensure-no-mutable-globals
test-mcp-client: start-mysql  ## Run MCPClient tests.
	$(call run_toxenvs,$(__TOXENVS_MCPCLIENT))

test-mcp-client-py36: start-mysql  ## Run MCPClient tests in Python 3.6.
	$(call run_toxenvs,py36-mcpclient)

__TOXENVS_DASHBOARD = py27-dashboard
test-dashboard: start-mysql  ## Run Dashboard tests.
	$(call run_toxenvs,$(__TOXENVS_DASHBOARD))

test-dashboard-py36: start-mysql  ## Run Dashboard tests in Python 3.6.
	$(call run_toxenvs,py36-dashboard)

__TOXENVS_STORAGE_SERVICE = py27-storage-service
test-storage-service: start-mysql  ## Run Storage Service tests.
	$(call run_toxenvs,$(__TOXENVS_STORAGE_SERVICE))

test-storage-service-py36: start-mysql  ## Run Storage Service tests in Python 3.6.
	$(call run_toxenvs,py36-storage-service)

test-storage-service-integration:  ## Run Storage Service unit and integration tests using MySQL and MinIO.
	$(CURDIR)/submodules/archivematica-storage-service/integration/run.sh

__TOXENVS_ARCHIVEMATICA_COMMON = py27-archivematica-common
test-archivematica-common: start-mysql  ## Run Archivematica Common tests.
	$(call run_toxenvs,$(__TOXENVS_ARCHIVEMATICA_COMMON))

test-archivematica-common-py36: start-mysql  ## Run Archivematica Common tests in Python 3.6.
	$(call run_toxenvs,py36-archivematica-common)

__TOXENVS_CHECKFORMIGRATIONS = checkformigrations-dashboard checkformigrations-storage-service
test-checkformigrations: start-mysql  ## Check there are no pending migrations.
	$(call create_db,DASHBOARDTEST)
	$(call create_db,SSTEST)
	$(call run_toxenvs,$(__TOXENVS_CHECKFORMIGRATIONS))

__TOXENVS_LINTING = linting
test-linting:  ## Check linting.
	$(call run_toxenvs,$(__TOXENVS_LINTING))

__TOXENVS_ALL := $(__TOXENVS_MCPSERVER) $(__TOXENVS_MCPCLIENT) $(__TOXENVS_DASHBOARD) $(__TOXENVS_STORAGE_SERVICE) $(__TOXENVS_ARCHIVEMATICA_COMMON)
test-all: start-mysql  ## Run all tests.
	$(call run_toxenvs,$(__TOXENVS_ALL))

test-at-build:  ## AMAUAT: build image.
	$(call compose_amauat, \
		build archivematica-acceptance-tests)

test-at-check: test-at-build  ## AMAUAT: test browsers.
	$(call compose_amauat, \
		run --rm --no-deps archivematica-acceptance-tests /home/archivematica/acceptance-tests/simplebrowsertest.py)

define AT_HELP

   Archivematica acceptance tests (Listing).

   The most effective way to run these tests is to run them by tag. For
   example:

      $ make test-at-behave TAGS=aip-encrypt BROWSER=Firefox
      $ make test-at-behave TAGS=black-box

   Commonly used acceptance tests in the Archivematica suite:

      * aip-encrypt        :Tests the encryption of AIPs.
      * aip-encrypt-mirror :Tests the replication of encrypted AIPs.
      * black-box          :Test Archivematica without Selenium web-driver.
      * icc                :Conformance check feature on ingest.
      * ipc                :Policy check feature on ingest.
      * picc               :Policy check feature for preservation derivatives.
      * mo-aip-reingest    :Metadata-only reingest.
      * tpc                :Policy check feature on transfer.
      * uuids-dirs         :Tests whether UUIDs are assigned to AIP sub-DIRs.

endef

export AT_HELP
test-at-help:  ## AMAUAT: list commonly used acceptance test tags.
	@echo "$$AT_HELP"

TAGS ?= mo-aip-reingest
BROWSER ?= Firefox
test-at-behave: test-at-build  ## AMAUAT: run behave, default is `make test-at-behave TAGS=mo-aip-reingest BROWSER=Firefox`.
	$(call compose_amauat, \
		run --rm -e HEADLESS=1 --no-deps archivematica-acceptance-tests /usr/local/bin/behave \
			--no-capture --no-capture-stderr --no-logcapture \
			$(subst $(SPACE), --tags=,$(SPACE)$(TAGS)) --no-skipped -v --stop \
			-D driver_name=$(BROWSER) \
			-D ssh_accessible=no \
			-D am_url=http://nginx/ \
			-D am_username=test \
			-D am_password=test \
			-D am_api_key=test \
			-D am_version=1.8 \
			-D ss_url=http://nginx:8000/ \
			-D ss_username=test \
			-D ss_password=test \
			-D ss_api_key=test \
			-D transfer_source_path=archivematica/archivematica-sampledata/TestTransfers/acceptance-tests \
			-D home=archivematica)

test-at-black-box: TAGS=black-box  ## AMAUAT: run the black-box automation tests.
test-at-black-box: test-at-behave

test-frontend:  ## Run Dashboard JS tests.
	docker build \
		-t archivematica-dashboard-testing \
		-f $(CURDIR)/Dockerfile \
		--build-arg TARGET=archivematica-dashboard-testing \
			../
	docker run \
		-e HOME=/tmp/yarn-config \
		--rm \
		--user $(CALLER_UID):$(CALLER_GID) \
		--volume "$(SRCDIR)/dashboard:/src/src/dashboard" \
		--entrypoint yarn \
			archivematica-dashboard-testing \
				--cwd=/src/src/dashboard/frontend install --frozen-lockfile
	docker run \
		--rm \
		--volume "$(SRCDIR)/dashboard/frontend:/src/src/dashboard/frontend" \
			archivematica-dashboard-testing

stop:  # Stop all containers.
	$(call compose_all, stop)

help:  ## Print this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
