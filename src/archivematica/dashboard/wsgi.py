import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

django.setup()
from archivematica.search import client

application = get_wsgi_application()

# Set up Elasticsearch client
client.setup_reading_from_conf(settings)
