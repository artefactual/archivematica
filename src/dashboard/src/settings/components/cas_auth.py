# -*- coding: utf-8 -*-
from __future__ import absolute_import

from os import environ

from django.core.exceptions import ImproperlyConfigured

# We default to a live demo CAS server to facilitate QA and regression
# testing. The following credentials can be used to authenticate:
# Username: admin
# Password: django-cas-ng
CAS_DEMO_SERVER_URL = "https://django-cas-ng-demo-server.herokuapp.com/cas/"
CAS_SERVER_URL = environ.get("AUTH_CAS_SERVER_URL", CAS_DEMO_SERVER_URL)

ALLOWED_CAS_VERSION_VALUES = ("1", "2", "3", "CAS_2_SAML_1_0")

CAS_VERSION = environ.get("AUTH_CAS_PROTOCOL_VERSION", "3")
if CAS_VERSION not in ALLOWED_CAS_VERSION_VALUES:
    raise ImproperlyConfigured(
        (
            "Unexpected value for AUTH_CAS_PROTOCOL_VERSION: {}. "
            "Supported values: '1', '2', '3', or 'CAS_2_SAML_1_0'."
        ).format(CAS_VERSION)
    )

CAS_CHECK_ADMIN_ATTRIBUTES = environ.get("AUTH_CAS_CHECK_ADMIN_ATTRIBUTES", False)
CAS_ADMIN_ATTRIBUTE = environ.get("AUTH_CAS_ADMIN_ATTRIBUTE", None)
CAS_ADMIN_ATTRIBUTE_VALUE = environ.get("AUTH_CAS_ADMIN_ATTRIBUTE_VALUE", None)

CAS_AUTOCONFIGURE_EMAIL = environ.get("AUTH_CAS_AUTOCONFIGURE_EMAIL", False)
CAS_EMAIL_DOMAIN = environ.get("AUTH_CAS_EMAIL_DOMAIN", None)

CAS_LOGIN_MSG = None
CAS_LOGIN_URL_NAME = "login"
CAS_LOGOUT_URL_NAME = "logout"
