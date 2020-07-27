# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.dispatch import receiver
from django_auth_ldap.backend import populate_user
from django_cas_ng.signals import cas_user_authenticated

from components.helpers import generate_api_key

logger = logging.getLogger("archivematica.dashboard")


def _cas_user_is_administrator(cas_attributes):
    """Determine if new user is an administrator from CAS attributes.

    :param cas_attributes: Attributes dict returned by CAS server.

    :returns: True if expected value is found, otherwise False.
    """
    ADMIN_ATTRIBUTE = settings.CAS_ADMIN_ATTRIBUTE
    ADMIN_ATTRIBUTE_VALUE = settings.CAS_ADMIN_ATTRIBUTE_VALUE
    if (ADMIN_ATTRIBUTE is None) or (ADMIN_ATTRIBUTE_VALUE is None):
        logger.error(
            "Error determining if new user is an administrator. Please "
            "be sure that CAS settings AUTH_CAS_ADMIN_ATTRIBUTE and "
            "AUTH_CAS_ADMIN_ATTRIBUTE_VALUE are properly set."
        )
        return False

    # CAS attributes are a dictionary. The value for a given key can be
    # a string or a list, so our approach for checking for the expected
    # value takes that into account.
    ATTRIBUTE_TO_CHECK = cas_attributes.get(ADMIN_ATTRIBUTE)
    if isinstance(ATTRIBUTE_TO_CHECK, list):
        if ADMIN_ATTRIBUTE_VALUE in ATTRIBUTE_TO_CHECK:
            return True
    elif isinstance(ATTRIBUTE_TO_CHECK, str):
        if ATTRIBUTE_TO_CHECK == ADMIN_ATTRIBUTE_VALUE:
            return True
    return False


@receiver(cas_user_authenticated)
def cas_user_authenticated_callback(sender, **kwargs):
    """Set user.is_superuser based on CAS attributes.

    When a user is authenticated, django_cas_ng sends the
    cas_user_authenticated signal, which includes any attributes
    returned by the CAS server during p3/serviceValidate.

    When the CAS_CHECK_ADMIN_ATTRIBUTES setting is enabled, we use this
    receiver to set user.is_superuser to True if we find the expected
    key-value combination configured with CAS_ADMIN_ATTRIBUTE and
    CAS_ADMIN_ATTRIBUTE_VALUE in the CAS attributes, and False if not.

    This check happens for both new and existing users, so that changes
    in group membership on the CAS server (e.g. a user being added or
    removed from the administrator group) are applied in Archivematica
    on the next login.
    """
    if not settings.CAS_CHECK_ADMIN_ATTRIBUTES:
        return

    username = kwargs.get("user")
    attributes = kwargs.get("attributes")

    if not attributes:
        return

    User = get_user_model()
    is_administrator = _cas_user_is_administrator(attributes)

    with transaction.atomic():
        user = User.objects.select_for_update().get(username=username)
        if user.is_superuser != is_administrator:
            user.is_superuser = is_administrator
            user.save()


def ldap_populate_user(sender, user, ldap_user, **kwargs):
    if user.pk is None:
        user.save()
        generate_api_key(user)


# This code is imported from MCPClient, which has no
# LDAP_AUTHENTICATION setting :(
if getattr(settings, "LDAP_AUTHENTICATION", False):
    populate_user.connect(ldap_populate_user)
