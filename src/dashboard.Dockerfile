FROM node:10-alpine as webpack-bundle
COPY dashboard/frontend/transfer-browser/ /src/transfer-browser/
COPY dashboard/frontend/appraisal-tab/ /src/appraisal-tab/
RUN apk add --no-cache git && chown -R node:node /src
USER node
RUN cd /src/transfer-browser \
	&& npm install \
	&& cd /src/appraisal-tab \
	&& npm install

FROM python:2.7-jessie

ENV DEBIAN_FRONTEND noninteractive
ENV DJANGO_SETTINGS_MODULE settings.production
ENV PYTHONPATH /src/dashboard/src/:/src/archivematicaCommon/lib/
ENV PYTHONUNBUFFERED 1
ENV AM_GUNICORN_BIND 0.0.0.0:8000
ENV AM_GUNICORN_CHDIR /src/dashboard/src
ENV FORWARDED_ALLOW_IPS *

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

COPY --from=webpack-bundle /src/media/js/build/transfer_browser.js /src/dashboard/src/media/js/build/
COPY --from=webpack-bundle /src/media/js/build/appraisal_tab.js /src/dashboard/src/media/js/build/

COPY archivematicaCommon/ /src/archivematicaCommon/
COPY dashboard/ /src/dashboard/
COPY dashboard/install/dashboard.gunicorn-config.py /etc/archivematica/dashboard.gunicorn-config.py

USER archivematica

RUN env \
	DJANGO_SETTINGS_MODULE=settings.local \
		/src/dashboard/src/manage.py collectstatic --noinput --clear

EXPOSE 8000

ENTRYPOINT /usr/local/bin/gunicorn --config=/etc/archivematica/dashboard.gunicorn-config.py wsgi:application
