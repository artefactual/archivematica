ARCHIVEMATICA_VERSION = (1, 3, 0)


def get_version():
    """ Returns the version number as a string. """
    # Inspired by Django's get_version
    version = ARCHIVEMATICA_VERSION
    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])
    return main


def get_full_version():
    return '.'.join(str(x) for x in ARCHIVEMATICA_VERSION)
