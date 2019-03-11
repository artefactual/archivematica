FROM python:2.7-jessie

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
		unar \
	&& rm -rf /var/lib/apt/lists/*

# Set the locale
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

#
# Chrome for Karma JS tests
#

ARG CHROME_VERSION="google-chrome-beta"
RUN curl -sL https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
	&& echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
	&& apt-get update -qqy \
	&& apt-get -qqy install ${CHROME_VERSION:-google-chrome-stable} \
	&& rm /etc/apt/sources.list.d/google-chrome.list \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/*

ARG CHROME_DRIVER_VERSION="latest"
RUN CD_VERSION=$(if [ ${CHROME_DRIVER_VERSION:-latest} = "latest" ]; then echo $(curl -sL https://chromedriver.storage.googleapis.com/LATEST_RELEASE); else echo $CHROME_DRIVER_VERSION; fi) \
	&& echo "Using chromedriver version: "$CD_VERSION \
	&& curl -so /tmp/chromedriver_linux64.zip -L https://chromedriver.storage.googleapis.com/$CD_VERSION/chromedriver_linux64.zip \
	&& rm -rf /opt/selenium/chromedriver \
	&& unar /tmp/chromedriver_linux64.zip -o /opt/selenium \
	&& rm /tmp/chromedriver_linux64.zip \
	&& mv /opt/selenium/chromedriver /opt/selenium/chromedriver-$CD_VERSION \
	&& chmod 755 /opt/selenium/chromedriver-$CD_VERSION \
	&& ln -fs /opt/selenium/chromedriver-$CD_VERSION /usr/bin/chromedriver

#
# Firefox for Karma JS tests
#
ARG FIREFOX_VERSION=65.0.1
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

ARG GECKODRIVER_VERSION=0.24.0
RUN GK_VERSION=$(if [ ${GECKODRIVER_VERSION:-latest} = "latest" ]; then echo $(curl -sL "https://api.github.com/repos/mozilla/geckodriver/releases/latest" | grep '"tag_name":' | sed -E 's/.*"v([0-9.]+)".*/\1/'); else echo $GECKODRIVER_VERSION; fi) \
	&& echo "Using GeckoDriver version: "$GK_VERSION \
	&& curl -so /tmp/geckodriver.tar.gz -L https://github.com/mozilla/geckodriver/releases/download/v$GK_VERSION/geckodriver-v$GK_VERSION-linux64.tar.gz \
	&& rm -rf /opt/geckodriver \
	&& tar -C /opt -zxf /tmp/geckodriver.tar.gz \
	&& rm /tmp/geckodriver.tar.gz \
	&& mv /opt/geckodriver /opt/geckodriver-$GK_VERSION \
	&& chmod 755 /opt/geckodriver-$GK_VERSION \
	&& ln -fs /opt/geckodriver-$GK_VERSION /usr/bin/geckodriver

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

COPY dashboard/frontend/ /src/dashboard/frontend/
RUN chown -R archivematica:archivematica /src/dashboard/frontend \
	&& su -l archivematica -c "cd /src/dashboard/frontend && npm install"

COPY archivematicaCommon/ /src/archivematicaCommon/
COPY dashboard/ /src/dashboard/
COPY dashboard/install/dashboard.gunicorn-config.py /etc/archivematica/dashboard.gunicorn-config.py

USER archivematica

RUN env \
	DJANGO_SETTINGS_MODULE=settings.local \
		/src/dashboard/src/manage.py collectstatic --noinput --clear

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/gunicorn", "--config=/etc/archivematica/dashboard.gunicorn-config.py", "wsgi:application"]
