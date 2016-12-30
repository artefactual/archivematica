from django.core.wsgi import get_wsgi_application

import elasticSearchFunctions


application = get_wsgi_application()

# Set up Elasticsearch client
elasticSearchFunctions.setup_reading_from_client_conf()
