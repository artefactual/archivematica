#!/bin/sh
# Render the service provider configuration and start shibd and Apache.
set -eu

: "${SHIBBOLETH_IDP_URL:?set SHIBBOLETH_IDP_URL to the identity provider public base URL, e.g. http://keycloak.localhost:8080/realms/shibboleth}"
: "${SHIBBOLETH_IDP_METADATA_URL:?set SHIBBOLETH_IDP_METADATA_URL to the identity provider metadata URL, e.g. http://keycloak:8080/realms/shibboleth/protocol/saml/descriptor}"
export SHIBBOLETH_IDP_URL SHIBBOLETH_IDP_METADATA_URL

# Only the identity provider URLs are substituted, so the template can use the
# usual $variable syntax anywhere else.
envsubst '${SHIBBOLETH_IDP_URL} ${SHIBBOLETH_IDP_METADATA_URL}' \
    < /etc/shibboleth-templates/shibboleth2.xml \
    > /etc/shibboleth/shibboleth2.xml

# Fail fast on a broken configuration.
shibd -t

# shibd loads the identity provider metadata when it starts and only retries
# after a long back-off, so wait until Keycloak serves it.
tries=0
until curl --fail --silent --show-error --max-time 5 --output /dev/null "${SHIBBOLETH_IDP_METADATA_URL}"; do
    tries=$((tries + 1))
    if [ "${tries}" -ge 60 ]; then
        echo "identity provider metadata is not available at ${SHIBBOLETH_IDP_METADATA_URL}" >&2
        exit 1
    fi
    sleep 2
done

# shibd runs in the foreground so its log reaches the container output;
# Apache is the container's main process.
shibd -f -F &
exec apache2ctl -DFOREGROUND
