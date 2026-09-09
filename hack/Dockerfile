ARG TARGET=archivematica-mcp-server
ARG UBUNTU_VERSION=24.04
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG NODE_VERSION=24
ARG UV_VERSION=0.11.30
ARG UV_DIGEST=sha256:93b61e21202b1dab861092748e46bbd6e0e41dd84f59b9174efd2353186e1b47
ARG PYTHON_INSTALL_DIR=/python
ARG SELENIUM_DIR=/selenium
ARG MEDIAAREA_VERSION=1.0-25
ARG JHOVE_VERSION=1.34.0-1~22.04

# Pin the Docker tool image independently for reproducible builds.
FROM ghcr.io/astral-sh/uv:${UV_VERSION}@${UV_DIGEST} AS uv

# -----------------------------------------------------------------------------

FROM ubuntu:${UBUNTU_VERSION} AS base-builder

ARG PYTHON_INSTALL_DIR=/python

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
	--mount=type=cache,target=/var/lib/apt,sharing=locked \
	set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		build-essential \
		ca-certificates \
		curl \
		git \
		gnupg \
		libldap2-dev \
		libmysqlclient-dev \
		libsasl2-dev \
		libsqlite3-dev \
		locales \
		make \
		pkg-config \
		tzdata

RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

ENV PATH=${PYTHON_INSTALL_DIR}/venv/bin:$PATH

# -----------------------------------------------------------------------------

FROM base-builder AS python-builder

ARG PYTHON_VERSION
ARG PYTHON_INSTALL_DIR=/python

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python
ENV UV_PYTHON_INSTALL_DIR=${PYTHON_INSTALL_DIR}/managed
ENV UV_PYTHON_PREFERENCE=only-managed
ENV UV_PROJECT_ENVIRONMENT=${PYTHON_INSTALL_DIR}/venv

COPY --from=uv --link /uv /usr/local/bin/uv

WORKDIR /src

COPY --link .python-version pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
	set -ex \
	&& if [ -n "${PYTHON_VERSION}" ]; then \
		uv python install --no-bin "${PYTHON_VERSION}"; \
		uv sync --locked --no-install-project --python "${PYTHON_VERSION}"; \
	else \
		uv python install --no-bin; \
		uv sync --locked --no-install-project; \
	fi

# -----------------------------------------------------------------------------

FROM base-builder AS browsers-builder

ARG SELENIUM_DIR=/selenium

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
	--mount=type=cache,target=/var/lib/apt,sharing=locked \
	set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		jq

RUN set -ex \
	&& SELENIUM_CACHE=${SELENIUM_DIR}/cache \
	&& SELENIUM_BIN=${SELENIUM_DIR}/bin \
	&& mkdir -p $SELENIUM_CACHE $SELENIUM_BIN \
	&& SELENIUM_MANAGER_DOWNLOAD_URL=$(curl -sL -o /dev/null -w '%{url_effective}' https://github.com/SeleniumHQ/selenium_manager_artifacts/releases/latest | sed -e 's|/tag/\(.*\)|/download/\1/selenium-manager-linux-x86_64|g') \
	&& curl -o $SELENIUM_BIN/selenium-manager -L $SELENIUM_MANAGER_DOWNLOAD_URL \
	&& chmod +x $SELENIUM_BIN/selenium-manager \
	&& CHROME_OUTPUT=$($SELENIUM_BIN/selenium-manager --cache-path $SELENIUM_CACHE --browser chrome --output JSON) \
	&& FIREFOX_OUTPUT=$($SELENIUM_BIN/selenium-manager --cache-path $SELENIUM_CACHE --browser firefox --output JSON) \
	&& ln -s $(echo $CHROME_OUTPUT | jq -r '.result.browser_path') $SELENIUM_BIN/google-chrome \
	&& ln -s $(echo $CHROME_OUTPUT | jq -r '.result.driver_path') $SELENIUM_BIN/chromedriver \
	&& ln -s $(echo $FIREFOX_OUTPUT | jq -r '.result.browser_path') $SELENIUM_BIN/firefox \
	&& ln -s $(echo $FIREFOX_OUTPUT | jq -r '.result.driver_path') $SELENIUM_BIN/geckodriver

# -----------------------------------------------------------------------------

FROM node:${NODE_VERSION} AS archivematica-dashboard-frontend-builder

ARG USER_ID
ARG GROUP_ID

WORKDIR /src/src/archivematica/dashboard/frontend

COPY --link src/archivematica/dashboard/frontend/.npmrc /src/src/archivematica/dashboard/frontend/.npmrc
COPY --link src/archivematica/dashboard/frontend/package.json /src/src/archivematica/dashboard/frontend/package.json
COPY --link src/archivematica/dashboard/frontend/package-lock.json /src/src/archivematica/dashboard/frontend/package-lock.json

RUN --mount=type=cache,target=/root/.npm,sharing=locked \
	set -ex \
	&& npm clean-install

COPY --link src/archivematica/dashboard/frontend /src/src/archivematica/dashboard/frontend
COPY --link src/archivematica/dashboard/media/images /src/src/archivematica/dashboard/media/images

RUN npm run build \
	&& chown -R ${USER_ID}:${GROUP_ID} /src/src/archivematica/dashboard/frontend/node_modules

# -----------------------------------------------------------------------------

FROM base-builder AS base

ARG USER_ID
ARG GROUP_ID
ARG PYTHON_INSTALL_DIR=/python
ARG MEDIAAREA_VERSION
ARG JHOVE_VERSION

RUN set -ex \
	&& UBUNTU_CODENAME=$(grep -Po '(?<=^VERSION_CODENAME=).+' /etc/os-release) \
	&& UBUNTU_ARCH=$(dpkg --print-architecture)  \
	&& curl --retry 3 -fsSL https://packages.archivematica.org/1.19.x/key.asc | gpg --dearmor -o /etc/apt/keyrings/archivematica-1.19.x.gpg \
	&& echo "deb [arch=${UBUNTU_ARCH} signed-by=/etc/apt/keyrings/archivematica-1.19.x.gpg] http://packages.archivematica.org/1.19.x/ubuntu-externals ${UBUNTU_CODENAME} main" > /etc/apt/sources.list.d/archivematica-external.list \
	&& curl --retry 3 -so /tmp/repo-mediaarea.deb -L https://mediaarea.net/repo/deb/repo-mediaarea_${MEDIAAREA_VERSION}_all.deb \
	&& dpkg -i /tmp/repo-mediaarea.deb \
	&& rm /tmp/repo-mediaarea.deb

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
	--mount=type=cache,target=/var/lib/apt,sharing=locked \
	set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		atool \
		bulk-extractor \
		clamav \
		coreutils \
		ffmpeg \
		g++ \
		gcc \
		gearman \
		gettext \
		ghostscript \
		hashdeep \
		imagemagick \
		inkscape \
		jhove=${JHOVE_VERSION} \
		libffi-dev \
		libimage-exiftool-perl \
		libldap2-dev \
		libmysqlclient-dev \
		libsasl2-dev \
		libssl-dev \
		libxml2-dev \
		libxslt1-dev \
		logapp \
		md5deep \
		mediaconch \
		mediainfo \
		nfs-common \
		openjdk-8-jre-headless \
		p7zip-full \
		pbzip2 \
		pst-utils \
		python3-lxml \
		rsync \
		siegfried \
		sleuthkit \
		tesseract-ocr \
		tree \
		unar \
		unrar-free \
		uuid

# Ensure the requested UID/GID do not clash with defaults in the Ubuntu base
# image. We look up any existing user/group that already uses such identifiers
# and remove them to avoid conflicts before creating the archivematica account.
RUN set -ex \
	&& { \
		grp=$(getent group "${GROUP_ID}" | cut -d: -f1 || true); \
		if [ -n "${grp}" ]; then groupdel --force "${grp}"; fi; \
		usr=$(getent passwd "${USER_ID}" | cut -d: -f1 || true); \
		if [ -n "${usr}" ]; then userdel --remove "${usr}"; fi; \
	} \
	&& groupadd --gid ${GROUP_ID} --system archivematica \
	&& useradd --uid ${USER_ID} --gid ${GROUP_ID} --home-dir /var/archivematica --system archivematica \
	&& mkdir -p /var/archivematica/sharedDirectory \
	&& chown -R archivematica:archivematica /var/archivematica

# Download ClamAV virus signatures
RUN freshclam --quiet

USER archivematica

COPY --chown=${USER_ID}:${GROUP_ID} --from=python-builder --link ${PYTHON_INSTALL_DIR} ${PYTHON_INSTALL_DIR}
COPY --from=uv --link /uv /usr/local/bin/uv
COPY --chown=${USER_ID}:${GROUP_ID} --link . /src

ENV PYTHONPATH=/src/src

# -----------------------------------------------------------------------------

FROM base AS archivematica-mcp-client

ENV DJANGO_SETTINGS_MODULE=archivematica.MCPClient.settings.common

ENTRYPOINT ["python", "-m", "archivematica.MCPClient.archivematicaClient"]

# -----------------------------------------------------------------------------

FROM base AS archivematica-mcp-server

ENV DJANGO_SETTINGS_MODULE=archivematica.MCPServer.settings.common

ENTRYPOINT ["python", "-m", "archivematica.MCPServer.archivematicaMCP"]

# -----------------------------------------------------------------------------

FROM base AS archivematica-dashboard

ARG USER_ID
ARG GROUP_ID
ARG PYTHON_VERSION

USER root

RUN set -ex \
	&& internalDirs=' \
		/src/src/archivematica/dashboard/static \
		/src/src/archivematica/dashboard/media \
	' \
	&& mkdir -p $internalDirs \
	&& chown -R archivematica $internalDirs

USER archivematica

COPY --chown=${USER_ID}:${GROUP_ID} --from=archivematica-dashboard-frontend-builder --link /src/src/archivematica/dashboard/frontend/dist /src/src/archivematica/dashboard/frontend/dist

ENV DJANGO_SETTINGS_MODULE=archivematica.dashboard.settings.local
ENV AM_GUNICORN_BIND=0.0.0.0:8000
ENV FORWARDED_ALLOW_IPS=*

RUN set -ex \
	&& python -m archivematica.dashboard.manage collectstatic --noinput --clear \
	&& python -m archivematica.dashboard.manage compilemessages

ENV DJANGO_SETTINGS_MODULE=archivematica.dashboard.settings.production

EXPOSE 8000

ENTRYPOINT ["python", "-m", "gunicorn", "--config=/src/src/archivematica/dashboard/install/dashboard.gunicorn-config.py", "archivematica.dashboard.wsgi:application"]

# -----------------------------------------------------------------------------

FROM base AS archivematica-tests

# -----------------------------------------------------------------------------

FROM base AS archivematica-dashboard-integration-tests

USER root
ARG USER_ID
ARG GROUP_ID

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
	--mount=type=cache,target=/var/lib/apt,sharing=locked \
	set -ex \
	&& python -m playwright install-deps firefox

USER archivematica

RUN set -ex \
	&& mkdir -p /var/archivematica/.cache/ms-playwright \
	&& python -m playwright install firefox

# Copy frontend assets out of where /src is bind-mounted during tests.
COPY --chown=${USER_ID}:${GROUP_ID} --from=archivematica-dashboard-frontend-builder --link /src/src/archivematica/dashboard/frontend/dist /opt/am-dashboard-dist

# -----------------------------------------------------------------------------

FROM ${TARGET}
