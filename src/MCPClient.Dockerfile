FROM ubuntu:14.04

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /src/MCPClient/lib/:/src/archivematicaCommon/lib/:/src/dashboard/src/
ENV ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_ARCHIVEMATICACLIENTMODULES /src/MCPClient/lib/archivematicaClientModules
ENV ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLIENTASSETSDIRECTORY /src/MCPClient/lib/assets/
ENV ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLIENTSCRIPTSDIRECTORY /src/MCPClient/lib/clientScripts/

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		apt-transport-https \
		curl \
		git \
		python-software-properties \
		software-properties-common \
	&& rm -rf /var/lib/apt/lists/*

# OS dependencies
RUN set -ex \
	&& curl -s https://packages.archivematica.org/GPG-KEY-archivematica | apt-key add - \
	&& add-apt-repository "deb [arch=amd64] http://packages.archivematica.org/1.6.x/ubuntu-externals trusty main" \
	&& add-apt-repository "deb http://archive.ubuntu.com/ubuntu/ trusty multiverse" \
	&& add-apt-repository "deb http://archive.ubuntu.com/ubuntu/ trusty-security universe" \
	&& add-apt-repository "deb http://archive.ubuntu.com/ubuntu/ trusty-updates multiverse" \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		atool \
		bagit \
		bulk-extractor \
		ffmpeg \
		libavcodec-extra-56 \
		fits \
		imagemagick \
		inkscape \
		jhove \
		libimage-exiftool-perl \
		libxml2-utils \
		md5deep \
		mediainfo \
		nailgun-client \
		openjdk-7-jre-headless \
		p7zip-full \
		pbzip2 \
		readpst \
		rsync \
		siegfried \
		sleuthkit \
		tesseract-ocr \
		tree \
		ufraw \
		unrar-free \
		uuid \
	&& rm -rf /var/lib/apt/lists/*

# Build dependencies
RUN set -ex \
	&& curl -s https://bootstrap.pypa.io/get-pip.py | python \
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
	&& rm -rf /var/lib/apt/lists/*

COPY archivematicaCommon/requirements/ /src/archivematicaCommon/requirements/
COPY dashboard/src/requirements/ /src/dashboard/src/requirements/
COPY MCPClient/requirements/ /src/MCPClient/requirements/
RUN pip install -r /src/archivematicaCommon/requirements/production.txt -r /src/archivematicaCommon/requirements/dev.txt
RUN pip install -r /src/dashboard/src/requirements/production.txt -r /src/dashboard/src/requirements/dev.txt
RUN pip install -r /src/MCPClient/requirements/production.txt -r /src/MCPClient/requirements/dev.txt

COPY archivematicaCommon/ /src/archivematicaCommon/
COPY dashboard/ /src/dashboard/
COPY MCPClient/ /src/MCPClient/

RUN set -ex \
	&& groupadd --gid 333 --system archivematica \
	&& useradd --uid 333 --gid 333 --system archivematica

USER archivematica

ENTRYPOINT /src/MCPClient/lib/archivematicaClient.py
