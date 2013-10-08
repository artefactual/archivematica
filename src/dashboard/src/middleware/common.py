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

from django.conf import settings
from django.http import HttpResponseServerError
from django.template.base import TemplateDoesNotExist

class AJAXSimpleExceptionResponseMiddleware:
    def process_exception(self, request, exception):
        if settings.DEBUG:
            if request.is_ajax():
                import sys, traceback
                (exc_type, exc_info, tb) = sys.exc_info()
                response = "%s\n" % exc_type.__name__
                response += "%s\n\n" % exc_info
                response += "TRACEBACK:\n"
                for tb in traceback.format_tb(tb):
                    response += "%s\n" % tb
                return HttpResponseServerError(response)

class SpecificExceptionErrorPageResponseMiddleware:
    def process_exception(self, request, exception):
        if settings.DEBUG and type(exception) == TemplateDoesNotExist:
            return HttpResponseServerError('Missing template: ' + str(exception)) 
