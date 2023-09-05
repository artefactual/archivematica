ARG TARGET=archivematica-mcp-server

FROM ubuntu:22.04 AS base

ARG USER_ID=1000
ARG GROUP_ID=1000
ARG PYTHON_VERSION=3.9

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		apt-transport-https \
		build-essential \
		curl \
		gettext \
		git \
		gpg-agent \
		libbz2-dev \
		libffi-dev \
		liblzma-dev \
		libncursesw5-dev \
		libreadline-dev \
		libsqlite3-dev \
		libssl-dev \
		libxml2-dev \
		libxmlsec1-dev \
		locales \
		software-properties-common \
		tk-dev \
		xz-utils \
		zlib1g-dev \
	&& rm -rf /var/lib/apt/lists/*

# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# OS dependencies
COPY hack/osdeps.py /src/hack/osdeps.py
COPY src/dashboard/osdeps /src/src/dashboard/osdeps
COPY src/MCPServer/osdeps /src/src/MCPServer/osdeps
COPY src/MCPClient/osdeps /src/src/MCPClient/osdeps
RUN set -ex \
	&& curl -s https://packages.archivematica.org/GPG-KEY-archivematica | apt-key add - \
	&& add-apt-repository --no-update --yes "deb [arch=amd64] http://packages.archivematica.org/1.15.x/ubuntu-externals jammy main" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ jammy multiverse" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ jammy-security universe" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ jammy-updates multiverse" \
	&& curl -so /tmp/repo-mediaarea_1.0-21_all.deb -L https://mediaarea.net/repo/deb/repo-mediaarea_1.0-21_all.deb \
	&& dpkg -i /tmp/repo-mediaarea_1.0-21_all.deb \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		libyaml-dev clamav \
	&& /src/hack/osdeps.py Ubuntu-22 1 | grep -v -E "nginx|postfix|python3.9-dev" | xargs apt-get install -y --no-install-recommends \
	&& rm -rf /var/lib/apt/lists/*

# Download ClamAV virus signatures
RUN freshclam --quiet

# Install pip, Node.js and Yarn
RUN set -ex \
	&& curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
	&& add-apt-repository --yes "deb https://dl.yarnpkg.com/debian/ stable main" \
	&& apt-get install -y --no-install-recommends \
		yarn nodejs \
	&& rm -rf /var/lib/apt/lists/*

ENV PYENV_ROOT="/pyenv/data"
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN set -ex \
	&& groupadd --gid ${GROUP_ID} --system archivematica \
	&& useradd --uid ${USER_ID} --gid ${GROUP_ID} --home-dir /var/archivematica --system archivematica \
	&& mkdir -p /var/archivematica/sharedDirectory \
	&& mkdir -p /pyenv \
	&& chown -R archivematica:archivematica /var/archivematica /pyenv

USER archivematica

RUN set -ex \
	&& curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash \
	&& pyenv install ${PYTHON_VERSION} \
	&& pyenv global ${PYTHON_VERSION}

COPY requirements-dev.txt /src/requirements-dev.txt

RUN set -ex \
	&& pyenv exec python${PYTHON_VERSION} -m pip install --upgrade pip setuptools \
	&& pyenv exec python${PYTHON_VERSION} -m pip install --requirement /src/requirements-dev.txt \
	&& pyenv rehash

COPY . /src

# Allow Django's compilemessages to write *.mo files to the messages subdirectories.
USER root
RUN set -ex \
	&& find /src/src/dashboard/src/locale -type d -name 'LC_MESSAGES' -exec chown archivematica:archivematica '{}' \;
USER archivematica

# -----------------------------------------------------------------------------

FROM base AS archivematica-mcp-client

ARG PYTHON_VERSION=3.9

# Some scripts in archivematica-fpr-admin executed by MCPClient rely on certain
# files being available in this image (e.g. see https://git.io/vA1wF).
COPY src/archivematicaCommon/lib/externals/fido/ /usr/lib/archivematica/archivematicaCommon/externals/fido/
COPY src/archivematicaCommon/lib/externals/fiwalk_plugins/ /usr/lib/archivematica/archivematicaCommon/externals/fiwalk_plugins/

ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /src/src/MCPClient/lib/:/src/src/MCPClient/lib/clientScripts:/src/src/archivematicaCommon/lib/:/src/src/dashboard/src/
ENV ARCHIVEMATICA_MCPCLIENT_ARCHIVEMATICACLIENTMODULES /src/src/MCPClient/lib/archivematicaClientModules
ENV ARCHIVEMATICA_MCPCLIENT_CLIENTASSETSDIRECTORY /src/src/MCPClient/lib/assets/
ENV ARCHIVEMATICA_MCPCLIENT_CLIENTSCRIPTSDIRECTORY /src/src/MCPClient/lib/clientScripts/

ENTRYPOINT pyenv exec python${PYTHON_VERSION} /src/src/MCPClient/lib/archivematicaClient.py

# -----------------------------------------------------------------------------

FROM base AS archivematica-mcp-server

ARG PYTHON_VERSION=3.9

ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /src/src/MCPServer/lib/:/src/src/archivematicaCommon/lib/:/src/src/dashboard/src/

ENTRYPOINT pyenv exec python${PYTHON_VERSION} /src/src/MCPServer/lib/archivematicaMCP.py

# -----------------------------------------------------------------------------

FROM base AS archivematica-dashboard

ARG PYTHON_VERSION=3.9

USER root

RUN set -ex \
	&& internalDirs=' \
		/src/src/dashboard/frontend \
		/src/src/dashboard/src/static \
		/src/src/dashboard/src/media \
	' \
	&& mkdir -p $internalDirs \
	&& chown -R archivematica $internalDirs

USER archivematica

RUN set -ex \
	&& yarn --cwd=/src/src/dashboard/frontend install --frozen-lockfile

WORKDIR /src/src/dashboard/src

ENV DJANGO_SETTINGS_MODULE settings.local
ENV PYTHONPATH /src/src/dashboard/src/:/src/src/archivematicaCommon/lib/
ENV AM_GUNICORN_BIND 0.0.0.0:8000
ENV AM_GUNICORN_CHDIR /src/src/dashboard/src
ENV FORWARDED_ALLOW_IPS *

RUN set -ex \
	&& ./manage.py collectstatic --noinput --clear \
	&& ./manage.py compilemessages

ENV DJANGO_SETTINGS_MODULE settings.production

EXPOSE 8000

ENTRYPOINT pyenv exec python${PYTHON_VERSION} -m gunicorn --config=/src/src/dashboard/install/dashboard.gunicorn-config.py wsgi:application

# -----------------------------------------------------------------------------

FROM archivematica-dashboard AS archivematica-dashboard-testing

USER root

ARG CHROME_VERSION="google-chrome-stable"
RUN curl -sL https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
	&& echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
	&& apt-get update -qqy \
	&& apt-get -qqy install ${CHROME_VERSION:-google-chrome-stable} \
	&& rm /etc/apt/sources.list.d/google-chrome.list \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/*

ARG FIREFOX_VERSION="latest"
RUN FIREFOX_DOWNLOAD_URL=$(if [ $FIREFOX_VERSION = "latest" ] || [ $FIREFOX_VERSION = "nightly-latest" ] || [ $FIREFOX_VERSION = "devedition-latest" ]; then echo "https://download.mozilla.org/?product=firefox-$FIREFOX_VERSION-ssl&os=linux64&lang=en-US"; else echo "https://download-installer.cdn.mozilla.net/pub/firefox/releases/$FIREFOX_VERSION/linux-x86_64/en-US/firefox-$FIREFOX_VERSION.tar.bz2"; fi) \
	&& apt-get update -qqy \
	&& apt-get -qqy --no-install-recommends install iceweasel \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
	&& curl -so /tmp/firefox.tar.bz2 -L $FIREFOX_DOWNLOAD_URL \
	&& apt-get -y purge iceweasel \
	&& rm -rf /opt/firefox \
	&& tar -C /opt -xjf /tmp/firefox.tar.bz2 \
	&& rm /tmp/firefox.tar.bz2 \
	&& mv /opt/firefox /opt/firefox-$FIREFOX_VERSION \
	&& ln -fs /opt/firefox-$FIREFOX_VERSION/firefox /usr/bin/firefox

USER archivematica

WORKDIR /src/src/dashboard/frontend

ENTRYPOINT ["yarn", "run", "test-single-run"]

# -----------------------------------------------------------------------------

FROM base AS archivematica-tests

# -----------------------------------------------------------------------------

FROM ${TARGET}
