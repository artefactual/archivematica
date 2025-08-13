import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

django.setup()
from archivematica.search.service import setup_search_service_from_conf

application = get_wsgi_application()

# Set up search service
setup_search_service_from_conf(settings)
