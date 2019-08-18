FROM artefactual/archivematica-mcp-client-base:20190227.01.9a3872e0

# Via: https://github.com/matthewfeickert/Docker-Python3-Ubuntu/.
#
# Python versions:
#
# Python 3.5.7: March 18, 2019.
# Python 3.6.9: July 02, 2019.
# Python 3.7.4: July 08, 2019.
#
ARG PYTHON_MAJOR_VERSION=3.5
ARG PYTHON_VERSION_TAG=3.5.7
ARG PYTHON_3=true

COPY docker_helper_scripts/install_python.sh /home/archivematica/install_python.sh
RUN /home/archivematica/install_python.sh \
		${PYTHON_3} \
		${PYTHON_MAJOR_VERSION} \
		${PYTHON_VERSION_TAG} && \
	rm -r /home/archivematica/install_python.sh

ENV DJANGO_SETTINGS_MODULE settings.common
ENV PYTHONPATH /src/MCPClient/lib/:/src/archivematicaCommon/lib/:/src/dashboard/src/
ENV ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_ARCHIVEMATICACLIENTMODULES /src/MCPClient/lib/archivematicaClientModules
ENV ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLIENTASSETSDIRECTORY /src/MCPClient/lib/assets/
ENV ARCHIVEMATICA_MCPCLIENT_MCPCLIENT_CLIENTSCRIPTSDIRECTORY /src/MCPClient/lib/clientScripts/

COPY archivematicaCommon/requirements/ /src/archivematicaCommon/requirements/
COPY dashboard/src/requirements/ /src/dashboard/src/requirements/
COPY MCPClient/requirements/ /src/MCPClient/requirements/
RUN pip install -U pip
RUN pip install -r /src/archivematicaCommon/requirements/production.txt -r /src/archivematicaCommon/requirements/dev.txt
RUN pip install -r /src/dashboard/src/requirements/production.txt -r /src/dashboard/src/requirements/dev.txt
RUN pip install -r /src/MCPClient/requirements/production.txt -r /src/MCPClient/requirements/dev.txt

COPY archivematicaCommon/ /src/archivematicaCommon/
COPY dashboard/ /src/dashboard/
COPY MCPClient/ /src/MCPClient/

# Some scripts in archivematica-fpr-admin executed by MCPClient rely on certain
# files being available in this image (e.g. see https://git.io/vA1wF).
COPY archivematicaCommon/lib/externals/fido/ /usr/lib/archivematica/archivematicaCommon/externals/fido/
COPY archivematicaCommon/lib/externals/fiwalk_plugins/ /usr/lib/archivematica/archivematicaCommon/externals/fiwalk_plugins/

USER archivematica

ENTRYPOINT ["/src/MCPClient/lib/archivematicaClient.py"]
