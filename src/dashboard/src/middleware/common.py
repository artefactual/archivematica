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
