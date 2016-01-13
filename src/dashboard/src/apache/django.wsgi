# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

import os, sys
from django.core.wsgi import get_wsgi_application
import time
import traceback
import signal
# Ensure that the path does not get added multiple times
path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

# workaround to troubleshoot mod_wsgi issues
# See http://stackoverflow.com/questions/30954398/django-populate-isnt-reentrant 

try:
    application = get_wsgi_application()
    print 'WSGI without exception'
except Exception:
    print 'handling WSGI exception'
    # Error loading applications
    if 'mod_wsgi' in sys.modules:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGINT)
        time.sleep(2.5)


# See http://blog.dscpl.com.au/2008/12/using-modwsgi-when-developing-django.html
from django.conf import settings
if settings.DEBUG:
    import monitor
    monitor.start(interval=1.0)
