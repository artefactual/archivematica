#!/usr/bin/env python2
#Author Bruce Eckel (www.BruceEckel.com)
#Source http://www.artima.com/weblogs/viewpost.jsp?thread=230001

from __future__ import print_function
import os

def detectCPUs():
    """
    Detects the number of CPUs on a system. Cribbed from pp.
    """
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        if "SC_NPROCESSORS_ONLN" in os.sysconf_names: # Linux & Unix:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else: # OSX:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read()) # Windows:
    if "NUMBER_OF_PROCESSORS" in os.environ:
        ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
    if ncpus > 0:
        return ncpus
    return 1 # Default

if __name__ == '__main__':
    print(detectCPUs())
