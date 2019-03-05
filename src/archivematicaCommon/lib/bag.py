from __future__ import print_function

import multiprocessing
import sys

from bagit import Bag, BagError


def is_valid(path, completeness_only=False, printfn=print):
    """Return whether a BagIt package is valid given its ``path``."""
    try:
        bag = Bag(path)
        bag.validate(
            processes=multiprocessing.count(), completeness_only=completeness_only
        )
    except BagError as err:
        printfn("Error validating BagIt package:", err, file=sys.stderr)
        return False
    return True
