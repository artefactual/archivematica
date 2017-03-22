import os

import django_auth_ldap.backend


class CustomLdapConfig(django_auth_ldap.backend.LDAPBackend):
    """Customize LDAP config."""

    def __init__(self):
        super(CustomLdapConfig, self).__init__()
        self.replacement = os.environ.get('AUTH_LDAP_USERNAME_SUFFIX', '')

    def ldap_to_django_username(self, username):
        # Replaces user creation in get_ldap_users
        return username.replace(self.replacement, '')

    def django_to_ldap_username(self, username):
        # Replaces user creation in get_ldap_users
        return username + self.replacement
