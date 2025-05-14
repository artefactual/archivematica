import os

from archivematica.MCPClient.settings.testmysql import *
from archivematica.MCPServer.settings.testmysql import *
from archivematica.dashboard.settings.testmysql import *

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("TEST_DB_ENGINE", "django.db.backends.mysql"),
        "NAME": os.environ.get("TEST_DB_NAME", "ARCHIVEMATICATEST"),
        "USER": os.environ.get("TEST_DB_USER", "archivematica"),
        "PASSWORD": os.environ.get("TEST_DB_PASSWORD", "demo"),
        "HOST": os.environ.get("TEST_DB_HOST", "mysql"),
        "PORT": os.environ.get("TEST_DB_PORT", "3306"),
        "CONN_MAX_AGE": 600,
        "TEST": {"NAME": f"test_{os.environ.get('TEST_DB_NAME', 'ARCHIVEMATICATEST')}"},
    }
}
