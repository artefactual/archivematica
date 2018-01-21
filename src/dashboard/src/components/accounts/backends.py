import re

from django.conf import settings
from django.dispatch import receiver

from django_auth_ldap.backend import LDAPBackend, populate_user
from shibboleth.backends import ShibbolethRemoteUserBackend

from components.helpers import generate_api_key


class CustomShibbolethRemoteUserBackend(ShibbolethRemoteUserBackend):
    def configure_user(self, user):
        generate_api_key(user)
        return user


class CustomLDAPBackend(LDAPBackend):
    """Customize LDAP config."""

    def __init__(self):
        super(CustomLDAPBackend, self).__init__()
        self._username_suffix = settings.AUTH_LDAP_USERNAME_SUFFIX

    def ldap_to_django_username(self, username):
        # Replaces user creation in get_ldap_users
        return re.sub(self._username_suffix + '$', '', username)

    def django_to_ldap_username(self, username):
        # Replaces user creation in get_ldap_users
        return username + self._username_suffix


@receiver(populate_user)
def ldap_populate_user(sender, user, ldap_user, **kwargs):
    generate_api_key(user)
