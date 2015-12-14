import os

import django
from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
import monitor


class WSGIEnvironment(WSGIHandler):
    """
    Similar to get_wsgi_application but with environment support.
    See http://stackoverflow.com/a/21124143 for more details.
    """
    def __call__(self, environ, start_response):
        self.update_environment(environ)
        django.setup()
        if settings.DEBUG:
            self.enable_monitor()
        return super(WSGIEnvironment, self).__call__(environ, start_response)

    def update_environment(self, environ):
        """
        Copy "DJANGO_SETTING_MODULES" and the environment variables prefixed
        with "ARCHIVEMATICA_DASHBOARD" string.
        """
        os.environ['DJANGO_SETTINGS_MODULE'] = environ.get('DJANGO_SETTINGS_MODULE')
        for key, value in environ.iteritems():
            if key.startswith('ARCHIVEMATICA_DASHBOARD'):
                os.environ[key] = value

    def enable_monitor(self):
        monitor.start()


application = WSGIEnvironment()
