FROM python:2.7

ENV DEBIAN_FRONTEND noninteractive
ENV DJANGO_SETTINGS_MODULE settings.production
ENV PYTHONPATH /src/dashboard/src/:/src/archivematicaCommon/lib/
ENV PYTHONUNBUFFERED 1
ENV AM_GUNICORN_BIND 0.0.0.0:8000
ENV AM_GUNICORN_CHDIR /src/dashboard/src
ENV FORWARDED_ALLOW_IPS *

RUN set -ex \
	&& curl -sL https://deb.nodesource.com/setup_8.x | bash - \
	&& apt-get install -y --no-install-recommends \
		gettext \
		libmysqlclient-dev \
		libldap2-dev \
		libsasl2-dev \
		nodejs \
		locales \
		locales-all \
	&& rm -rf /var/lib/apt/lists/*

# Set the locale  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8

COPY archivematicaCommon/requirements/ /src/archivematicaCommon/requirements/
COPY dashboard/src/requirements/ /src/dashboard/src/requirements/
RUN pip install -r /src/archivematicaCommon/requirements/production.txt -r /src/archivematicaCommon/requirements/dev.txt
RUN pip install -r /src/dashboard/src/requirements/production.txt -r /src/dashboard/src/requirements/dev.txt

RUN set -ex \
	&& internalDirs=' \
		/src/dashboard/src/static \
		/src/dashboard/src/media \
	' \
	&& groupadd --gid 333 --system archivematica \
	&& useradd --uid 333 --gid 333 --create-home --system archivematica \
	&& mkdir -p $internalDirs \
	&& chown -R archivematica:archivematica $internalDirs

COPY dashboard/frontend/transfer-browser/ /src/dashboard/frontend/transfer-browser/
RUN chown -R archivematica:archivematica /src/dashboard/frontend/transfer-browser \
	&& su -l archivematica -c "cd /src/dashboard/frontend/transfer-browser && npm install"

COPY dashboard/frontend/appraisal-tab/ /src/dashboard/frontend/appraisal-tab/
RUN chown -R archivematica:archivematica /src/dashboard/frontend/appraisal-tab \
	&& su -l archivematica -c "cd /src/dashboard/frontend/appraisal-tab && npm install"

COPY archivematicaCommon/ /src/archivematicaCommon/
COPY dashboard/ /src/dashboard/
COPY dashboard/install/dashboard.gunicorn-config.py /etc/archivematica/dashboard.gunicorn-config.py

ARG ARCHIVEMATICA_VERSION=UNKNOWN
ARG AGENT_CODE=UNKNOWN
RUN (echo "---"; \
	 echo "version: $ARCHIVEMATICA_VERSION"; \
	 echo "agent_code: $AGENT_CODE";) \
		> /etc/archivematica/version.yml

USER archivematica

RUN env \
	DJANGO_SETTINGS_MODULE=settings.local \
		/src/dashboard/src/manage.py collectstatic --noinput --clear

EXPOSE 8000

ENTRYPOINT /usr/local/bin/gunicorn --config=/etc/archivematica/dashboard.gunicorn-config.py wsgi:application
