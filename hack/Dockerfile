ARG TARGET=archivematica-mcp-server

FROM ubuntu:18.04 AS base

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		apt-transport-https \
		curl \
		gettext \
		git \
		gpg-agent \
		locales \
		software-properties-common \
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
	&& add-apt-repository --no-update --yes "deb [arch=amd64] http://packages.archivematica.org/1.12.x/ubuntu-externals bionic main" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ bionic multiverse" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ bionic-security universe" \
	&& add-apt-repository --no-update --yes "deb http://archive.ubuntu.com/ubuntu/ bionic-updates multiverse" \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		build-essential python-dev python3-dev libyaml-dev clamav \
	&& /src/hack/osdeps.py Ubuntu-18 1 | grep -v -E "nginx|postfix" | xargs apt-get install -y --no-install-recommends \
	&& rm -rf /var/lib/apt/lists/*

# Download ClamAV virus signatures
RUN freshclam --quiet

# Install pip, Node.js and Yarn
RUN set -ex \
	&& curl -s https://bootstrap.pypa.io/pip/2.7/get-pip.py | python \
	&& curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
	&& add-apt-repository --yes "deb https://dl.yarnpkg.com/debian/ stable main" \
	&& apt-get install -y --no-install-recommends \
		yarn nodejs \
	&& rm -rf /var/lib/apt/lists/*

RUN set -ex \
	&& groupadd --gid 333 --system archivematica \
	&& useradd -m --uid 333 --gid 333 --system archivematica

RUN set -ex \
	&& mkdir -p /var/archivematica/sharedDirectory \
	&& chown -R archivematica:archivematica /var/archivematica

COPY requirements-dev.txt /src/requirements-dev.txt
RUN pip2 install -r /src/requirements-dev.txt

COPY . /src

# -----------------------------------------------------------------------------

FROM base AS python3

RUN set -ex \
	&& curl -s https://bootstrap.pypa.io/get-pip.py | python3.6

COPY requirements-dev-py3.txt /src/requirements-dev-py3.txt
RUN pip3 install -r /src/requirements-dev-py3.txt

# -----------------------------------------------------------------------------

FROM base AS archivematica-mcp-client

# Some scripts in archivematica-fpr-admin executed by MCPClient rely on certain
# files being available in this image (e.g. see https://git.io/vA1wF).
COPY src/archivematicaCommon/lib/externals/fido/ /usr/lib/archivematica/archivematicaCommon/externals/fido/
COPY src/archivematicaCommon/lib/externals/fiwalk_plugins/ /usr/lib/archivematica/archivematicaCommon/externals/fiwalk_plugins/

USER archivematica

ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /src/src/MCPClient/lib/:/src/src/archivematicaCommon/lib/:/src/src/dashboard/src/
ENV ARCHIVEMATICA_MCPCLIENT_ARCHIVEMATICACLIENTMODULES /src/src/MCPClient/lib/archivematicaClientModules
ENV ARCHIVEMATICA_MCPCLIENT_CLIENTASSETSDIRECTORY /src/src/MCPClient/lib/assets/
ENV ARCHIVEMATICA_MCPCLIENT_CLIENTSCRIPTSDIRECTORY /src/src/MCPClient/lib/clientScripts/

ENTRYPOINT ["/src/src/MCPClient/lib/archivematicaClient.py"]

# -----------------------------------------------------------------------------

FROM base AS archivematica-mcp-server

USER archivematica

ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /src/src/MCPServer/lib/:/src/src/archivematicaCommon/lib/:/src/src/dashboard/src/

ENTRYPOINT ["/src/src/MCPServer/lib/archivematicaMCP.py"]

# -----------------------------------------------------------------------------

FROM base AS archivematica-dashboard

RUN set -ex \
	&& internalDirs=' \
		/src/src/dashboard/src/static \
		/src/src/dashboard/src/media \
	' \
	&& mkdir -p $internalDirs \
	&& chown -R archivematica:archivematica $internalDirs \
	&& yarn --cwd=/src/src/dashboard/frontend install --frozen-lockfile

WORKDIR /src/src/dashboard/src

USER archivematica

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

ENTRYPOINT ["/usr/local/bin/gunicorn", "--config=/src/src/dashboard/install/dashboard.gunicorn-config.py", "wsgi:application"]

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
