# Local/test-only Shibboleth Service Provider for Archivematica development.
#
# Apache httpd with mod_shib runs as a reverse proxy in front of the Dashboard
# (port 80) and the Storage Service (port 8000). It authenticates browsers
# against a SAML identity provider and passes the released attributes to the
# applications as request headers, which is how their Shibboleth
# authentication backends expect them.
#
# The service provider version is the one Debian packages for the base image
# release: Shibboleth SP 3.5 in trixie. Upstream publishes no Debian packages.
#
# The image is environment-agnostic: the entrypoint renders shibboleth2.xml
# from the template mounted at /etc/shibboleth-templates with the identity
# provider URL taken from SHIBBOLETH_IDP_URL, and the Apache virtual hosts are
# expected to be mounted at /etc/apache2/sites-enabled/archivematica.conf.
FROM debian:trixie-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        apache2 \
        ca-certificates \
        curl \
        gettext-base \
        libapache2-mod-shib \
    && a2enmod headers proxy proxy_http shib \
    && a2dissite 000-default \
    && rm -rf /var/lib/apt/lists/*

# Apache serves the Dashboard on 80 and the Storage Service on 8000.
RUN echo "Listen 8000" >> /etc/apache2/ports.conf

# The package leaves credential generation to the deployer; shibboleth2.xml
# references a signing and an encryption pair. The listener socket directory
# is normally created by systemd.
RUN shib-keygen -o /etc/shibboleth -n sp-signing -h shibboleth-sp -y 10 \
    && shib-keygen -o /etc/shibboleth -n sp-encrypt -h shibboleth-sp -y 10 \
    && mkdir -p /var/run/shibboleth

# Send the Apache logs to the container output.
RUN ln -sf /dev/stdout /var/log/apache2/access.log \
    && ln -sf /dev/stderr /var/log/apache2/error.log

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
