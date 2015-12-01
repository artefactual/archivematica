import os, sys
from django.core.wsgi import get_wsgi_application

# Ensure that the path does not get added multiple times
path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

application = get_wsgi_application()

# See http://blog.dscpl.com.au/2008/12/using-modwsgi-when-developing-django.html
from django.conf import settings
if settings.DEBUG:
    import monitor
    monitor.start(interval=1.0)
