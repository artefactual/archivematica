FROM ubuntu:14.04

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /src/MCPClient/lib/:/src/archivematicaCommon/lib/:/src/dashboard/src/

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
		clamav-daemon \
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
		tika \
		tree \
		ufraw \
		unrar-free \
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

ADD archivematicaCommon/requirements/ /src/archivematicaCommon/requirements/
RUN pip install -r /src/archivematicaCommon/requirements/production.txt -r /src/archivematicaCommon/requirements/dev.txt
ADD archivematicaCommon/ /src/archivematicaCommon/

ADD dashboard/src/requirements/ /src/dashboard/src/requirements/
RUN pip install -r /src/dashboard/src/requirements/production.txt -r /src/dashboard/src/requirements/dev.txt
ADD dashboard/ /src/dashboard/

ADD MCPClient/requirements/ /src/MCPClient/requirements/
RUN pip install -r /src/MCPClient/requirements/production.txt -r /src/MCPClient/requirements/dev.txt
ADD MCPClient/ /src/MCPClient/

ADD archivematicaCommon/etc/dbsettings /etc/archivematica/archivematicaCommon/dbsettings
ADD MCPClient/etc/clientConfig.conf /etc/archivematica/MCPClient/clientConfig.conf

RUN set -ex \
	&& groupadd -r archivematica \
	&& useradd -r -g archivematica archivematica

USER archivematica

ENTRYPOINT /src/MCPClient/lib/archivematicaClient.py
