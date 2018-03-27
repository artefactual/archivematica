from django.conf import settings


def get_version():
    """ Returns the version number as a string. """
    return settings.ARCHIVEMATICA_VERSION
