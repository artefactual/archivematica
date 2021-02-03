# flake8: noqa

from __future__ import absolute_import

from .test import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "MCPCLIENTTEST",
        "USER": "archivematica",
        "PASSWORD": "demo",
        "HOST": "mysql",
        "PORT": "3306",
        "CONN_MAX_AGE": 600,
    }
}
