FROM python:2.7

ENV DEBIAN_FRONTEND noninteractive
ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /src/MCPServer/lib/:/src/archivematicaCommon/lib/:/src/dashboard/src/
ENV PYTHONUNBUFFERED 1

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		gettext \
		libmysqlclient-dev \
	&& rm -rf /var/lib/apt/lists/*

ADD archivematicaCommon/requirements/ /src/archivematicaCommon/requirements/
RUN pip install -r /src/archivematicaCommon/requirements/production.txt -r /src/archivematicaCommon/requirements/dev.txt
ADD archivematicaCommon/ /src/archivematicaCommon/

ADD dashboard/src/requirements/ /src/dashboard/src/requirements/
RUN pip install -r /src/dashboard/src/requirements/production.txt -r /src/dashboard/src/requirements/dev.txt
ADD dashboard/ /src/dashboard/

ADD MCPServer/requirements/ /src/MCPServer/requirements/
RUN pip install -r /src/MCPServer/requirements/production.txt -r /src/MCPServer/requirements/dev.txt
ADD MCPServer/ /src/MCPServer/

ADD archivematicaCommon/etc/dbsettings /etc/archivematica/archivematicaCommon/dbsettings
ADD MCPServer/etc/serverConfig.conf /etc/archivematica/MCPServer/serverConfig.conf

RUN set -ex \
	&& groupadd -r archivematica \
	&& useradd -r -g archivematica archivematica

RUN set -ex \
	&& mkdir -p /var/archivematica/sharedDirectory \
	&& cp -R /src/MCPServer/share/sharedDirectoryStructure/* /var/archivematica/sharedDirectory/ \
	&& chown -R archivematica:archivematica /var/archivematica

USER archivematica

ENTRYPOINT /src/MCPServer/lib/archivematicaMCP.py
