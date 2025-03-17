import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

django.setup()
from archivematica.archivematicaCommon import elasticSearchFunctions

application = get_wsgi_application()

# Set up Elasticsearch client
elasticSearchFunctions.setup_reading_from_conf(settings)
