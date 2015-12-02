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


paths = (
    '/usr/lib/archivematica/archivematicaCommon',
    '/usr/share/archivematica/dashboard',
)
for item in paths:
    if item not in sys.path:
        sys.path.append(item)


os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

application = get_wsgi_application()

# See http://blog.dscpl.com.au/2008/12/using-modwsgi-when-developing-django.html
from django.conf import settings
if settings.DEBUG:
    import monitor
    monitor.start(interval=1.0)
