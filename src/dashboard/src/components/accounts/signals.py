from django.conf import settings
from django_auth_ldap.backend import populate_user

from components.helpers import generate_api_key


def ldap_populate_user(sender, user, ldap_user, **kwargs):
    if user.pk is None:
        user.save()
        generate_api_key(user)


# This code is imported from MCPClient, which has no
# LDAP_AUTHENTICATION setting :(
if getattr(settings, "LDAP_AUTHENTICATION", False):
    populate_user.connect(ldap_populate_user)
