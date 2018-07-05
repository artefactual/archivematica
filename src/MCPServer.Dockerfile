FROM python:2.7-jessie

ENV DEBIAN_FRONTEND noninteractive
ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /src/MCPServer/lib/:/src/archivematicaCommon/lib/:/src/dashboard/src/
ENV PYTHONUNBUFFERED 1

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		gettext \
		libmysqlclient-dev \
		libldap2-dev \
		libsasl2-dev \
		locales \
		locales-all \
	&& rm -rf /var/lib/apt/lists/*

# Set the locale
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8

COPY archivematicaCommon/requirements/ /src/archivematicaCommon/requirements/
COPY dashboard/src/requirements/ /src/dashboard/src/requirements/
COPY MCPServer/requirements/ /src/MCPServer/requirements/
RUN pip install -r /src/archivematicaCommon/requirements/production.txt -r /src/archivematicaCommon/requirements/dev.txt
RUN pip install -r /src/dashboard/src/requirements/production.txt -r /src/dashboard/src/requirements/dev.txt
RUN pip install -r /src/MCPServer/requirements/production.txt -r /src/MCPServer/requirements/dev.txt

COPY archivematicaCommon/ /src/archivematicaCommon/
COPY dashboard/ /src/dashboard/
COPY MCPServer/ /src/MCPServer/

RUN set -ex \
	&& groupadd --gid 333 --system archivematica \
	&& useradd --uid 333 --gid 333 --system archivematica

RUN set -ex \
	&& mkdir -p /var/archivematica/sharedDirectory \
	&& chown -R archivematica:archivematica /var/archivematica

USER archivematica

ENTRYPOINT /src/MCPServer/lib/archivematicaMCP.py
