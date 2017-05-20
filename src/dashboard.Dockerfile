FROM python:2.7

ENV DEBIAN_FRONTEND noninteractive
ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /src/dashboard/src/:/src/archivematicaCommon/lib/
ENV PYTHONUNBUFFERED 1
ENV GUNICORN_CMD_ARGS \
	--user archivematica \
	--group archivematica \
	--bind 0.0.0.0:8000 \
	--workers 4 \
	--worker-class gevent \
	--timeout 172800 \
	--chdir /src/dashboard/src \
	--access-logfile - \
	--error-logfile - \
	--log-level info \
	--reload \
	--reload-engine poll \
	--name archivematica-dashboard

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		gettext \
		libmysqlclient-dev \
	&& rm -rf /var/lib/apt/lists/*

ADD archivematicaCommon/requirements/ /src/archivematicaCommon/requirements/
RUN pip install -r /src/archivematicaCommon/requirements/production.txt -r /src/archivematicaCommon/requirements/dev.txt
ADD archivematicaCommon/ /src/archivematicaCommon/

ADD dashboard/src/requirements/ /src/dashboard/src/requirements/
RUN pip install -r /src/dashboard/src/requirements/production.txt -r /src/dashboard/src/requirements/dev.txt
ADD dashboard/ /src/dashboard/

RUN set -ex \
	&& groupadd --gid 333 --system archivematica \
	&& useradd --uid 333 --gid 333 --system archivematica

RUN set -ex \
	&& internalDirs=' \
		/src/dashboard/src/static \
	' \
	&& mkdir -p $internalDirs \
	&& chown -R archivematica:archivematica $internalDirs

USER archivematica

RUN env \
	DJANGO_SETTINGS_MODULE=settings.local \
	ARCHIVEMATICA_DASHBOARD_DASHBOARD_DJANGO_SECRET_KEY=12345 \
	ARCHIVEMATICA_DASHBOARD_DASHBOARD_DJANGO_ALLOWED_HOSTS=127.0.0.1 \
		/src/dashboard/src/manage.py collectstatic --noinput --clear

EXPOSE 8000

ENTRYPOINT /usr/local/bin/gunicorn wsgi:application
