# flake8: noqa
from .test import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "DASHBOARDTEST",
        "USER": "archivematica",
        "PASSWORD": "demo",
        "HOST": "mysql",
        "PORT": "3306",
        "CONN_MAX_AGE": 600,
    }
}
