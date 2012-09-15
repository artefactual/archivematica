import os, sys
import django.core.handlers.wsgi

# Ensure that the path does not get added multiple times
path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

application = django.core.handlers.wsgi.WSGIHandler()

# See http://blog.dscpl.com.au/2008/12/using-modwsgi-when-developing-django.html
from django.conf import settings
if settings.DEBUG:
    import monitor
    monitor.start(interval=1.0)
