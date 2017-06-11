from django.conf import settings
from django.core.wsgi import get_wsgi_application

import elasticSearchFunctions


application = get_wsgi_application()

# Set up Elasticsearch client
elasticSearchFunctions.setup(settings.ELASTICSEARCH_SERVER, settings.ELASTICSEARCH_TIMEOUT)
