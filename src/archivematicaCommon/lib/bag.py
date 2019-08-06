# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import multiprocessing
import sys

from bagit import Bag, BagError


def is_bag(path, printfn=print):
    """Determine whether the directory contains a BagIt package.

    The constructor of ``Bag`` is fast enough but we may prefer to optimize
    later.
    """
    try:
        Bag(path)
    except BagError as err:
        printfn("Error opening BagIt package:", err, file=sys.stderr)
        return False
    return True


def is_valid(path, completeness_only=False, printfn=print):
    """Return whether a BagIt package is valid given its ``path``."""
    try:
        bag = Bag(path)
        bag.validate(
            processes=multiprocessing.cpu_count(), completeness_only=completeness_only
        )
    except BagError as err:
        printfn("Error validating BagIt package:", err, file=sys.stderr)
        return False
    return True
