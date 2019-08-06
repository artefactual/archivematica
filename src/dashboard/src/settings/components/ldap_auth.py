# -*- coding: utf-8 -*-
from __future__ import absolute_import

from os import environ

from django.core.exceptions import ImproperlyConfigured

try:
    import ldap
    from django_auth_ldap import config as ldap_config
except ImportError:
    raise ImproperlyConfigured(
        "python-ldap and django-auth-ldap must be installed to use LDAP authentication."
    )


# All LDAP usernames have this suffix - it is removed when creating Django users
AUTH_LDAP_USERNAME_SUFFIX = environ.get("AUTH_LDAP_USERNAME_SUFFIX", "")

AUTH_LDAP_SERVER_URI = environ.get("AUTH_LDAP_SERVER_URI", "ldap://localhost")
AUTH_LDAP_BIND_DN = environ.get("AUTH_LDAP_BIND_DN", "")
AUTH_LDAP_BIND_PASSWORD = environ.get("AUTH_LDAP_BIND_PASSWORD", "")

if "AUTH_LDAP_USER_SEARCH_BASE_DN" in environ:
    AUTH_LDAP_USER_SEARCH = ldap_config.LDAPSearch(
        environ.get("AUTH_LDAP_USER_SEARCH_BASE_DN"),
        ldap.SCOPE_SUBTREE,
        environ.get("AUTH_LDAP_USER_SEARCH_BASE_FILTERSTR", "(uid=%(user)s)"),
    )
AUTH_LDAP_USER_DN_TEMPLATE = environ.get("AUTH_LDAP_USER_DN_TEMPLATE", None)
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

AUTH_LDAP_USER_FLAGS_BY_GROUP = {}
if "AUTH_LDAP_GROUP_IS_ACTIVE" in environ:
    AUTH_LDAP_USER_FLAGS_BY_GROUP["is_active"] = environ.get(
        "AUTH_LDAP_GROUP_IS_ACTIVE"
    )
if "AUTH_LDAP_GROUP_IS_STAFF" in environ:
    AUTH_LDAP_USER_FLAGS_BY_GROUP["is_staff"] = environ.get("AUTH_LDAP_GROUP_IS_STAFF")
if "AUTH_LDAP_GROUP_IS_SUPERUSER" in environ:
    AUTH_LDAP_USER_FLAGS_BY_GROUP["is_superuser"] = environ.get(
        "AUTH_LDAP_GROUP_IS_SUPERUSER"
    )

if "AUTH_LDAP_GROUP_SEARCH_BASE_DN" in environ:
    AUTH_LDAP_GROUP_SEARCH = ldap_config.LDAPSearch(
        base_dn=environ.get("AUTH_LDAP_GROUP_SEARCH_BASE_DN", ""),
        scope=ldap.SCOPE_SUBTREE,
        filterstr=environ.get("AUTH_LDAP_GROUP_SEARCH_FILTERSTR", ""),
    )

# https://pythonhosted.org/django-auth-ldap/groups.html#types-of-groups
AUTH_LDAP_GROUP_TYPE = ldap_config.ActiveDirectoryGroupType()

AUTH_LDAP_REQUIRE_GROUP = environ.get("AUTH_LDAP_REQUIRE_GROUP", None)
AUTH_LDAP_DENY_GROUP = environ.get("AUTH_LDAP_DENY_GROUP", None)

AUTH_LDAP_FIND_GROUP_PERMS = environ.get(
    "AUTH_LDAP_FIND_GROUP_PERMS", "FALSE"
).upper() in ("TRUE", "YES", "ON", "1")
AUTH_LDAP_CACHE_GROUPS = environ.get("AUTH_LDAP_CACHE_GROUPS", "FALSE").upper() in (
    "TRUE",
    "YES",
    "ON",
    "1",
)
try:
    AUTH_LDAP_GROUP_CACHE_TIMEOUT = int(
        environ.get("AUTH_LDAP_GROUP_CACHE_TIMEOUT", "3600")
    )
except ValueError:
    AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600

AUTH_LDAP_START_TLS = environ.get("AUTH_LDAP_START_TLS", "TRUE").upper() in (
    "TRUE",
    "YES",
    "ON",
    "1",
)

AUTH_LDAP_GLOBAL_OPTIONS = {}
if environ.get("AUTH_LDAP_PROTOCOL_VERSION", None) == "3":
    AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_PROTOCOL_VERSION] = ldap.VERSION3
if environ.get("AUTH_LDAP_TLS_CACERTFILE", None):
    AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_CACERTFILE] = environ.get(
        "AUTH_LDAP_TLS_CACERTFILE"
    )
if environ.get("AUTH_LDAP_TLS_CERTFILE", None):
    AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_CERTFILE] = environ.get(
        "AUTH_LDAP_TLS_CERTFILE"
    )
if environ.get("AUTH_LDAP_TLS_KEYFILE", None):
    AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_KEYFILE] = environ.get(
        "AUTH_LDAP_TLS_KEYFILE"
    )
if environ.get("AUTH_LDAP_TLS_REQUIRE_CERT", None):
    require_cert = environ.get("AUTH_LDAP_TLS_REQUIRE_CERT").lower()
    if require_cert == "never":
        AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_REQUIRE_CERT] = ldap.OPT_X_TLS_NEVER
    elif require_cert == "allow":
        AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_REQUIRE_CERT] = ldap.OPT_X_TLS_ALLOW
    elif require_cert == "try":
        AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_REQUIRE_CERT] = ldap.OPT_X_TLS_TRY
    elif require_cert == "demand":
        AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_REQUIRE_CERT] = ldap.OPT_X_TLS_DEMAND
    elif require_cert == "hard":
        AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_REQUIRE_CERT] = ldap.OPT_X_TLS_HARD
    else:
        raise ImproperlyConfigured(
            (
                "Unexpected value for AUTH_LDAP_TLS_REQUIRE_CERT: {}. "
                "Supported values: 'never', 'allow', try', 'hard', or 'demand'."
            ).format(require_cert)
        )

# Non-configurable sane defaults
AUTH_LDAP_ALWAYS_UPDATE_USER = True
