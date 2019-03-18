### 1. Let's start from scratch

	$ sudo make \
		flush-shared-dir flush-search \
		bootstrap-storage-service bootstrap-dashboard-db restart-am-services

### 2. Update automated processing config to send to backlog

	$ sudo cp \
		../src/archivematica/HOW_TO_TEST.config.xml \
		~/.am/am-pipeline-data/sharedMicroServiceTasksConfigs/processingMCPConfigs/automatedProcessingMCP.xml

### 3. Start new transfer

	$ ~/Desktop/AM/start-transfer-new.sh

Wait until it's done!

### 4. Check database contents

Confirm that the files have been validated properly.

	$ docker-compose exec mysql env MYSQL_PWD=12345 mysql -hlocalhost -uroot SS -e "select * from locations_file;"

Transfer and File objects should be populated too.

	$ docker-compose exec mysql env MYSQL_PWD=12345 mysql -hlocalhost -uroot MCP -e "select * from Files;"
        $ docker-compose exec mysql env MYSQL_PWD=12345 mysql -hlocalhost -uroot MCP -e "select * from Transfers; select * from Files;"

### 5. Wipe the pipeline again!

	$ make bootstrap-dashboard-db flush-search

### 6. Rebuild backlog

	$ docker-compose exec archivematica-dashboard \
		/src/dashboard/src/manage.py rebuild_transfer_backlog --no-prompt

### 7. Test arrangement

Keep an eye on the logs, Dashboard will raise errors if it things aren't working.

	$ docker-compose logs -f archivematica-dashboard
