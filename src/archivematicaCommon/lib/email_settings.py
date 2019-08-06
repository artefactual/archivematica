# -*- coding: utf-8 -*-
"""
Email settings and globals.

The main setting is `EMAIL_BACKEND`, which defines which backend to use. Valid
backends are:

    * Console: `django.core.mail.backends.console.EmailBackend`
    * Dummy: `django.core.mail.backends.dummy.EmailBackend`
    * File: `django.core.mail.backends.filebased.EmailBackend`
    * In-Memory: `django.core.mail.backends.locmem.EmailBackend`
    * SMTP: `django.core.mail.backends.smtp.EmailBackend`

By default, the Console backend will be used.
"""
from __future__ import absolute_import

CONFIG_MAPPING = {
    # [email]
    "email_backend": {"section": "email", "option": "backend", "type": "string"},
    "email_host": {"section": "email", "option": "host", "type": "string"},
    "email_host_user": {"section": "email", "option": "host_user", "type": "string"},
    "email_host_password": {
        "section": "email",
        "option": "host_password",
        "type": "string",
    },
    "email_port": {"section": "email", "option": "port", "type": "int"},
    "email_ssl_certfile": {
        "section": "email",
        "option": "ssl_certfile",
        "type": "string",
    },
    "email_ssl_keyfile": {
        "section": "email",
        "option": "ssl_keyfile",
        "type": "string",
    },
    "email_use_ssl": {"section": "email", "option": "use_ssl", "type": "boolean"},
    "email_use_tls": {"section": "email", "option": "use_tls", "type": "boolean"},
    "email_file_path": {"section": "email", "option": "file_path", "type": "string"},
    "default_from_email": {
        "section": "email",
        "option": "default_from_email",
        "type": "string",
    },
    "email_subject_prefix": {
        "section": "email",
        "option": "subject_prefix",
        "type": "string",
    },
    "email_timeout": {"section": "email", "option": "timeout", "type": "int"},
    "server_email": {"section": "email", "option": "server_email", "type": "int"},
}


def get_settings(config):
    """
    Extract a dict of Django email settings from the passed config object

    This should be invoked from a Django settings module and the result merged
    into the globals() dict.
    """
    settings = dict(
        # Which backend to use?
        EMAIL_BACKEND=config.get("email_backend"),
        # File Backend
        # See https://docs.djangoproject.com/en/dev/topics/email/#file-backend
        EMAIL_FILE_PATH=config.get("email_file_path"),
        # SMTP Backend
        # See https://docs.djangoproject.com/en/dev/topics/email/#smtp-backend
        EMAIL_HOST=config.get("email_host"),
        EMAIL_HOST_PASSWORD=config.get("email_host_password"),
        EMAIL_HOST_USER=config.get("email_host_user"),
        EMAIL_PORT=config.get("email_port"),
        EMAIL_SSL_CERTFILE=config.get("email_ssl_certfile"),
        EMAIL_SSL_KEYFILE=config.get("email_ssl_keyfile"),
        EMAIL_USE_SSL=config.get("email_use_ssl"),
        EMAIL_USE_TLS=config.get("email_use_tls"),
        # General settings, not backend-specific
        DEFAULT_FROM_EMAIL=config.get("default_from_email"),
        EMAIL_SUBJECT_PREFIX=config.get("email_subject_prefix"),
        EMAIL_TIMEOUT=config.get("email_timeout", None),
    )

    settings["SERVER_EMAIL"] = config.get("server_email", settings["EMAIL_HOST_USER"])
    return settings
