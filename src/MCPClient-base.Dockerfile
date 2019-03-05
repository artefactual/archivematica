FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		apt-transport-https \
		curl \
		git \
		gpg-agent \
		locales \
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
	&& add-apt-repository --no-update --yes "deb [arch=amd64] http://packages.archivematica.org/1.9.x/ubuntu-externals bionic main" \
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
		hashdeep \
		libavcodec-extra \
		fits \
		imagemagick \
		inkscape \
		jhove \
		libimage-exiftool-perl \
		libevent-dev \
		libjansson4 \
		libxml2-utils \
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
		unrar-free \
		uuid \
	&& rm -rf /var/lib/apt/lists/*

# Download ClamAV virus signatures
RUN freshclam --quiet

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

RUN set -ex \
	&& groupadd --gid 333 --system archivematica \
	&& useradd -m --uid 333 --gid 333 --system archivematica
