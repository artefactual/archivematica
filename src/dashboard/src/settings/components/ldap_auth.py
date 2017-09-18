import os

import ldap
from django_auth_ldap.config import LDAPSearch, ActiveDirectoryGroupType


# LDAP config
# See: https://pythonhosted.org/django-auth-ldap/index.html

# Environment variables this is configured to read:
# From django_auth_ldap:
# * AUTH_LDAP_SERVER_URI
# * AUTH_LDAP_BIND_DN
# * AUTH_LDAP_BIND_PASSWORD
# * AUTH_LDAP_USER_SEARCH
# * AUTH_LDAP_USER_DN_TEMPLATE
# * AUTH_LDAP_GROUP_SEARCH_BASE_DN
# * AUTH_LDAP_GROUP_SEARCH_FILTERSTR
# * AUTH_LDAP_REQUIRE_GROUP
# Custom:
# * AUTH_LDAP_USERNAME_SUFFIX:
#    Remove this suffix from LDAP username to make Django username
# * AUTH_LDAP_GROUP_IS_ACTIVE
#    Set Django's is_active based on membership in this group
# * AUTH_LDAP_GROUP_IS_STAFF
#    Set Django's is_staff based on membership in this group

# Server Config
AUTH_LDAP_SERVER_URI = os.environ.get('AUTH_LDAP_SERVER_URI', '')
AUTH_LDAP_BIND_DN = os.environ.get('AUTH_LDAP_BIND_DN', '')
AUTH_LDAP_BIND_PASSWORD = os.environ.get('AUTH_LDAP_BIND_PASSWORD', '')


# User search/bind
# Use one of AUTH_LDAP_USER_SEARCH or AUTH_LDAP_USER_DN_TEMPLATE
AUTH_LDAP_USER_SEARCH = os.environ.get('AUTH_LDAP_USER_SEARCH', None)
AUTH_LDAP_USER_DN_TEMPLATE = os.environ.get('AUTH_LDAP_USER_DN_TEMPLATE', None)
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    'email': 'mail',
}
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": os.environ.get('AUTH_LDAP_GROUP_IS_ACTIVE', ''),
    "is_staff": os.environ.get('AUTH_LDAP_GROUP_IS_STAFF', ''),
}
AUTH_LDAP_START_TLS = True  # Recommended


# Group config
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    base_dn=os.environ.get('AUTH_LDAP_GROUP_SEARCH_BASE_DN', ''),
    scope=ldap.SCOPE_SUBTREE,
    filterstr=os.environ.get('AUTH_LDAP_GROUP_SEARCH_FILTERSTR', '')
)
# For choices see:
# https://pythonhosted.org/django-auth-ldap/groups.html#types-of-groups
AUTH_LDAP_GROUP_TYPE = ActiveDirectoryGroupType()

AUTH_LDAP_REQUIRE_GROUP = os.environ.get('AUTH_LDAP_REQUIRE_GROUP', None)

# Options
AUTH_LDAP_GLOBAL_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: False,
    ldap.OPT_REFERRALS: False,
}

# All LDAP usernames have this suffix - it is removed when creating Django users
AUTH_LDAP_USERNAME_SUFFIX = os.environ.get('AUTH_LDAP_USERNAME_SUFFIX', '')
