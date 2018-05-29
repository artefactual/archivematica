"""Detect CPU cores.

This module contains a function that helps to determine the number of CPU cores
available in the system.

Inspired by code shared by Bruce Eckel (www.BruceEckel.com) found at
http://www.artima.com/weblogs/viewpost.jsp?thread=230001.
"""

import os


def detect_cores():
    """Detect the number of CPU cores on a system."""
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        if "SC_NPROCESSORS_ONLN" in os.sysconf_names:  # Linux & Unix:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else:  # OSX:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())  # Windows:
    if "NUMBER_OF_PROCESSORS" in os.environ:
        ncpus = int(os.environ["NUMBER_OF_PROCESSORS"])
    if ncpus > 0:
        return ncpus
    return 1  # Default
