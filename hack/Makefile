.DEFAULT_GOAL := help

# Paths for Docker named volumes
AM_PIPELINE_DATA ?= $(HOME)/.am/am-pipeline-data
SS_LOCATION_DATA ?= $(HOME)/.am/ss-location-data

CALLER_UID=$(shell id -u)
CALLER_GID=$(shell id -g)

SRCDIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../src)

NULL :=
SPACE := $(NULL) $(NULL)
COMMA := ,

define compose_all
	docker compose -f docker-compose.yml -f docker-compose.acceptance-tests.yml -f docker-compose.pmm.yml $(1)
endef

define compose_amauat
	docker compose -f docker-compose.yml -f docker-compose.acceptance-tests.yml $(1)
endef

define compose_tests
	docker compose -f docker-compose.yml -f docker-compose.tests.yml $(1)
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
					-e $(subst $(SPACE),$(COMMA),$(strip $(1))) \
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
	docker compose exec -T mysql mysql -hlocalhost -uroot -p12345 -e '\
		DROP DATABASE IF EXISTS `$(1)`; \
		CREATE DATABASE `$(1)`;'
	$(call grant_all_on_db,$(1))
endef

define grant_all_on_db
	docker compose exec -T mysql mysql -hlocalhost -uroot -p12345 -e '\
		GRANT ALL ON `$(1)`.* TO "archivematica"@"%";'
endef

define drop_db
	docker compose exec -T mysql mysql -hlocalhost -uroot -p12345 -e 'DROP DATABASE IF EXISTS `$(1)`;'
endef

define create_dbs
	$(foreach test_db,$(1),$(call create_db,$(test_db));)
endef

define grant_all_on_dbs
	$(foreach test_db,$(1),$(call grant_all_on_db,$(test_db));)
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
	# This workaround prevents Docker from creating this directory structure
	# inside the external SS_LOCATION_DATA volume directory assigning root as
	# the owner of some parts of it.
	mkdir -p $(SS_LOCATION_DATA)/archivematica/archivematica-sampledata

build:  # Build Compose services.
	docker compose build \
		--build-arg USER_ID=$(CALLER_UID) \
		--build-arg GROUP_ID=$(CALLER_GID)

bootstrap: bootstrap-storage-service bootstrap-dashboard-db bootstrap-dashboard-frontend  ## Full bootstrap.

bootstrap-storage-service:  ## Bootstrap Storage Service (new database).
	$(call create_db,SS)
	docker compose run \
		--rm \
		--no-deps \
		--entrypoint /src/storage_service/manage.py \
			archivematica-storage-service \
				migrate --noinput
	docker compose run \
		--rm \
		--no-deps \
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
	docker compose restart --no-deps archivematica-storage-service

makemigrations-ss:
	docker compose run \
		--user $(CALLER_UID):$(CALLER_GID) \
		--rm \
		--no-deps \
		--entrypoint /src/storage_service/manage.py \
			archivematica-storage-service \
				makemigrations

manage-dashboard:  ## Run Django /manage.py on Dashboard, suppling <command> [options] as value to ARG, e.g., `make manage-ss ARG=shell`
	docker compose run \
		--user $(CALLER_UID):$(CALLER_GID) \
		--rm \
		--no-deps \
		--entrypoint /src/src/dashboard/src/manage.py \
			archivematica-dashboard \
				$(ARG)

manage-ss:  ## Run Django /manage.py on Storage Service, suppling <command> [options] as value to ARG, e.g., `make manage-ss ARG='shell --help'`
	docker compose run \
		--user $(CALLER_UID):$(CALLER_GID) \
		--rm \
		--no-deps \
		--entrypoint /src/storage_service/manage.py \
			archivematica-storage-service \
				$(ARG)

bootstrap-dashboard-db:  ## Bootstrap Dashboard (new database).
	$(call create_db,MCP)
	docker compose run \
		--rm \
		--no-deps \
		--entrypoint /src/src/dashboard/src/manage.py \
			archivematica-dashboard \
				migrate --noinput
	docker compose run \
		--rm \
		--no-deps \
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
	docker build \
		-t archivematica-dashboard-frontend-builder \
		-f $(CURDIR)/Dockerfile \
		--build-arg TARGET=archivematica-dashboard-frontend-builder \
			../
	docker run \
		-e HOME=/tmp/npm-config \
		--rm \
		--user $(CALLER_UID):$(CALLER_GID) \
		--volume "$(SRCDIR)/dashboard:/src/src/dashboard" \
		--entrypoint npm \
			archivematica-dashboard-frontend-builder \
				install --no-package-lock

restart-am-services:  ## Restart Archivematica services: MCPServer, MCPClient, Dashboard and Storage Service.
	docker compose restart --no-deps archivematica-mcp-server
	docker compose restart --no-deps archivematica-mcp-client
	docker compose restart --no-deps archivematica-dashboard
	docker compose restart --no-deps archivematica-storage-service

compile-requirements-am:  ## Run pip-compile for Archivematica
	docker compose run --workdir /src \
		-e XDG_CACHE_HOME=/tmp/pip-cache \
		--rm \
		--no-deps \
		--user $(CALLER_UID):$(CALLER_GID) \
		--entrypoint bash archivematica-mcp-server \
			-c "make pip-compile"

upgrade-requirements-am:  ## Run pip-upgrade for Archivematica
	docker compose run --workdir /src \
		-e XDG_CACHE_HOME=/tmp/pip-cache \
		--rm \
		--no-deps \
		--user $(CALLER_UID):$(CALLER_GID) \
		--entrypoint bash archivematica-mcp-server \
			-c "make pip-upgrade"

compile-requirements-ss:  ## Run pip-compile for Storage Service
	docker compose run --workdir /src \
		-e XDG_CACHE_HOME=/tmp/pip-cache \
		--rm \
		--no-deps \
		--user $(CALLER_UID):$(CALLER_GID) \
		--entrypoint bash archivematica-storage-service \
			-c "make pip-compile"

upgrade-requirements-ss:  ## Run pip-upgrade for Storage Service
	docker compose run --workdir /src \
		-e XDG_CACHE_HOME=/tmp/pip-cache \
		--rm \
		--no-deps \
		--user $(CALLER_UID):$(CALLER_GID) \
		--entrypoint bash archivematica-storage-service \
			-c "make pip-upgrade"

define amauat_make
	docker compose \
		-f docker-compose.yml \
		-f docker-compose.acceptance-tests.yml \
		run \
			--workdir /src \
			-e XDG_CACHE_HOME=/tmp/pip-cache \
			--rm \
			--no-deps \
			--user $(CALLER_UID):$(CALLER_GID) \
			--entrypoint bash archivematica-acceptance-tests \
				-c "make $(1)"
endef

compile-requirements-amauat: test-at-build  ## Run pip-compile for AMAUATs
	$(call amauat_make,pip-compile)

upgrade-requirements-amauat: test-at-build  ## Run pip-upgrade for AMAUATs
	$(call amauat_make,pip-upgrade)

db:  ## Connect to the MySQL server using the CLI.
	docker compose exec mysql mysql -hlocalhost -uroot -p12345

flush: flush-shared-dir flush-search bootstrap restart-am-services  ## Delete ALL user data.

flush-shared-dir-mcp-configs:  ## Delete processing configurations - it restarts MCPServer.
	rm -f ${AM_PIPELINE_DATA}/sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml
	rm -f ${AM_PIPELINE_DATA}/sharedMicroServiceTasksConfigs/processingMCPConfigs/automatedProcessingMCP.xml
	docker compose restart --no-deps archivematica-mcp-server

flush-shared-dir:  ## Delete contents of the shared directory data volume.
	rm -rf ${AM_PIPELINE_DATA}/*

flush-search:  ## Delete Elasticsearch indices.
	docker compose exec archivematica-mcp-client curl -XDELETE "http://elasticsearch:9200/aips,aipfiles,transfers,transferfiles"

flush-logs:  ## Delete container logs - requires root privileges.
	@./helpers/flush-docker-logs.sh

# These include the database names used in the settings.testmysql
# modules plus the prefixed and suffixed variations used by Django and
# tox when running in parallel mode
__TEST_DBS_MCPCLIENT = MCPCLIENTTEST test_MCPCLIENTTEST test_MCPCLIENTTEST_mcp-client
__TEST_DBS_MIGRATIONS = DASHBOARDTEST SSTEST
__TEST_DBS_DASHBOARD = DASHBOARDTEST test_DASHBOARDTEST test_DASHBOARDTEST_dashboard test_DASHBOARDTEST_archivematica-common
__TEST_DBS_MCPSERVER = MCPSERVERTEST test_MCPSERVERTEST test_MCPSERVERTEST_mcp-server
__TEST_DBS_STORAGE_SERVICE = test_SSTEST test_SSTEST_storage-service
__TEST_DBS := $(__TEST_DBS_MCPCLIENT) $(__TEST_DBS_MIGRATIONS) $(__TEST_DBS_DASHBOARD) $(__TEST_DBS_MCPSERVER) $(__TEST_DBS_STORAGE_SERVICE) test_MCP test_SS
flush-test-dbs: start-mysql
	$(foreach test_db,$(__TEST_DBS),$(call drop_db,$(test_db));)

test-build:  ## Build archivematica-tests image.
	docker build \
		-t archivematica-tests \
		-f $(CURDIR)/Dockerfile \
		--build-arg TARGET=archivematica-tests \
		--build-arg UBUNTU_VERSION \
		--build-arg PYTHON_VERSION \
			../

__TOXENVS_MCPSERVER := mcp-server
test-mcp-server: start-mysql  ## Run MCPServer tests.
	$(call grant_all_on_dbs,$(__TEST_DBS_MCPSERVER))
	$(call run_toxenvs,$(__TOXENVS_MCPSERVER))

__TOXENVS_MCPCLIENT = mcp-client
test-mcp-client: start-mysql  ## Run MCPClient tests.
	$(call grant_all_on_dbs,$(__TEST_DBS_MCPCLIENT))
	$(call run_toxenvs,$(__TOXENVS_MCPCLIENT))

__TOXENVS_DASHBOARD = dashboard
test-dashboard: start-mysql  ## Run Dashboard tests.
	$(call grant_all_on_dbs,$(__TEST_DBS_DASHBOARD))
	$(call run_toxenvs,$(__TOXENVS_DASHBOARD))

__TOXENVS_STORAGE_SERVICE = storage-service
test-storage-service: start-mysql  ## Run Storage Service tests.
	$(call grant_all_on_dbs,$(__TEST_DBS_STORAGE_SERVICE))
	$(call run_toxenvs,$(__TOXENVS_STORAGE_SERVICE))

test-storage-service-integration:  ## Run Storage Service unit and integration tests using MySQL and MinIO.
	$(CURDIR)/submodules/archivematica-storage-service/tests/integration/run.sh

__TOXENVS_ARCHIVEMATICA_COMMON = archivematica-common
test-archivematica-common: start-mysql  ## Run Archivematica Common tests.
	$(call grant_all_on_dbs,$(__TEST_DBS_DASHBOARD))
	$(call run_toxenvs,$(__TOXENVS_ARCHIVEMATICA_COMMON))

__TOXENVS_MIGRATIONS = migrations-dashboard migrations-storage-service
test-migrations: start-mysql  ## Check there are no pending migrations.
	$(call create_dbs,$(__TEST_DBS_MIGRATIONS))
	$(call run_toxenvs,$(__TOXENVS_MIGRATIONS))

__TOXENVS_LINTING = linting
test-linting:  ## Check linting.
	$(call run_toxenvs,$(__TOXENVS_LINTING))

__TOXENVS_ALL := $(__TOXENVS_MCPSERVER) $(__TOXENVS_MCPCLIENT) $(__TOXENVS_DASHBOARD) $(__TOXENVS_STORAGE_SERVICE) $(__TOXENVS_ARCHIVEMATICA_COMMON)
test-all: start-mysql  ## Run all tests.
	$(call grant_all_on_dbs,$(__TEST_DBS_MCPSERVER) $(__TEST_DBS_MCPCLIENT) $(__TEST_DBS_DASHBOARD) $(__TEST_DBS_STORAGE_SERVICE) $(__TEST_DBS_ARCHIVEMATICA_COMMON))
	$(call run_toxenvs,$(__TOXENVS_ALL))

test-at-build:  ## AMAUAT: build image.
	$(call compose_amauat, \
		build --build-arg USER_ID=$(CALLER_UID) --build-arg GROUP_ID=$(CALLER_GID) archivematica-acceptance-tests)

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
      * tpc                :Policy check feature on transfer.
      * uuids-dirs         :Tests whether UUIDs are assigned to AIP sub-DIRs.

endef

export AT_HELP
test-at-help:  ## AMAUAT: list commonly used acceptance test tags.
	@echo "$$AT_HELP"

TAGS ?= black-box
BROWSER ?= Firefox
test-at-behave: test-at-build  ## AMAUAT: run behave, default is `make test-at-behave TAGS=black-box BROWSER=Firefox`.
	$(call compose_amauat, \
		run --rm -e HEADLESS=1 --no-deps archivematica-acceptance-tests behave \
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
		-e HOME=/tmp/npm-config \
		--rm \
		--user $(CALLER_UID):$(CALLER_GID) \
		--volume "$(SRCDIR)/dashboard:/src/src/dashboard" \
		--entrypoint npm \
			archivematica-dashboard-testing \
				install
	docker run \
		--rm \
		--volume "$(SRCDIR)/dashboard/frontend:/src/src/dashboard/frontend" \
			archivematica-dashboard-testing

stop:  # Stop all containers.
	$(call compose_all, stop)

help:  ## Print this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
