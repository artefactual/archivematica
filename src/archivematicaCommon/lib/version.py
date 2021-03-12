ARCHIVEMATICA_VERSION = (1, 13, 0)


def get_version():
    """Returns the version number as a string."""
    # Inspired by Django's get_version
    version = ARCHIVEMATICA_VERSION
    parts = 2 if version[2] == 0 else 3
    main = ".".join(str(x) for x in version[:parts])
    return main


def get_preservation_system_identifier():
    """Returns the system identifier including the application name."""
    return "Archivematica-%s" % get_version()


def get_full_version():
    return ".".join(str(x) for x in ARCHIVEMATICA_VERSION)
