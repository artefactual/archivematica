#
# Base
#

ARG TARGET=mcp-server

FROM ubuntu:18.04 AS base

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

ARG REQUIREMENTS=/archivematica/requirements-dev.txt

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		apt-transport-https \
		curl \
		git \
		gettext \
		gpg-agent \
		locales \
		locales-all \
		software-properties-common \
		libldap2-dev \
		libsasl2-dev \
	&& rm -rf /var/lib/apt/lists/*

# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# OS dependencies
RUN set -ex \
	&& curl -s https://packages.archivematica.org/GPG-KEY-archivematica | apt-key add - \
	&& add-apt-repository --no-update --yes "deb [arch=amd64] http://packages.archivematica.org/1.11.x/ubuntu-externals bionic main" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ bionic multiverse" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ bionic-security universe" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ bionic-updates multiverse" \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		atool \
		bulk-extractor \
		clamav \
		ffmpeg \
		ghostscript \
		coreutils \
		libavcodec-extra \
		fits \
		imagemagick \
		inkscape \
		jhove \
		libimage-exiftool-perl \
		libevent-dev \
		libjansson4 \
		mediainfo \
		mediaconch \
		nailgun \
		openjdk-8-jre-headless \
		p7zip-full \
		pbzip2 \
		pst-utils \
		rsync \
		siegfried \
		sleuthkit \
		tesseract-ocr \
		tree \
		ufraw \
		unar \
		unrar-free \
		uuid \
	&& rm -rf /var/lib/apt/lists/*

# Download ClamAV virus signatures
RUN freshclam --quiet

# Build dependencies
RUN set -ex \
	&& curl -s https://bootstrap.pypa.io/get-pip.py | python \
	&& curl -sL https://deb.nodesource.com/setup_12.x | bash -E - \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		build-essential \
		python-dev \
		libmysqlclient-dev \
		libffi-dev \
		libyaml-dev \
		libssl-dev \
		libxml2-dev \
		libxslt-dev \
		nodejs \
	&& rm -rf /var/lib/apt/lists/*

# Create Archivematica user
RUN set -ex \
	&& groupadd --gid 333 --system archivematica \
	&& useradd --uid 333 --gid 333 --create-home --system archivematica

# Install requirements
COPY ./requirements.txt /archivematica/requirements.txt
COPY ./requirements-dev.txt /archivematica/requirements-dev.txt
RUN pip install -r ${REQUIREMENTS}


#
# Sources
#

FROM scratch AS sources

COPY . /archivematica


#
# Dashboard
#

FROM base AS archivematica-dashboard

ENV DJANGO_SETTINGS_MODULE settings.production
ENV PYTHONPATH /archivematica/src/dashboard/src/:/archivematica/src/archivematicaCommon/lib/
ENV AM_GUNICORN_BIND 0.0.0.0:8000
ENV AM_GUNICORN_CHDIR /archivematica/src/dashboard/src
ENV FORWARDED_ALLOW_IPS *

COPY --from=sources /archivematica /archivematica

RUN set -ex \
	&& internalDirs=' \
		/archivematica/src/dashboard/src/static \
		/archivematica/src/dashboard/src/media \
	' \
	&& mkdir -p $internalDirs \
	&& chown -R archivematica:archivematica $internalDirs \
	&& rm -rf /var/lib/apt/lists/* \
	&& chown -R archivematica:archivematica /archivematica/src/dashboard/frontend

COPY ./src/dashboard/install/dashboard.gunicorn-config.py /etc/archivematica/dashboard.gunicorn-config.py

USER archivematica

RUN cd /archivematica/src/dashboard/frontend && npm install

RUN env DJANGO_SETTINGS_MODULE=settings.local /archivematica/src/dashboard/src/manage.py collectstatic --noinput --clear

ENTRYPOINT ["/usr/local/bin/gunicorn", "--config=/etc/archivematica/dashboard.gunicorn-config.py", "wsgi:application"]


#
# MCPServer
#

FROM base as archivematica-mcp-server

ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /archivematica/src/MCPServer/lib/:/archivematica/src/archivematicaCommon/lib/:/archivematica/src/dashboard/src/

COPY --from=sources /archivematica /archivematica

RUN set -ex \
	&& mkdir -p /var/archivematica/sharedDirectory \
	&& chown -R archivematica:archivematica /var/archivematica

USER archivematica

ENTRYPOINT ["/archivematica/src/MCPServer/lib/archivematicaMCP.py"]


#
# MCPClient
#

FROM base as archivematica-mcp-client

ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /archivematica/src/MCPClient/lib/:/archivematica/src/archivematicaCommon/lib/:/archivematica/src/dashboard/src/
ENV ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_ARCHIVEMATICACLIENTMODULES /archivematica/src/MCPClient/lib/archivematicaClientModules
ENV ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLIENTASSETSDIRECTORY /archivematica/src/MCPClient/lib/assets/
ENV ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLIENTSCRIPTSDIRECTORY /archivematica/src/MCPClient/lib/clientScripts/

COPY --from=sources /archivematica /archivematica
COPY --from=sources /archivematica/src/archivematicaCommon/lib/externals/fido/ /usr/lib/archivematica/archivematicaCommon/externals/fido/
COPY --from=sources /archivematica/src/archivematicaCommon/lib/externals/fiwalk_plugins/ /usr/lib/archivematica/archivematicaCommon/externals/fiwalk_plugins/

USER archivematica

ENTRYPOINT ["/archivematica/src/MCPClient/lib/archivematicaClient.py"]


#
# Target
#

FROM archivematica-${TARGET}
