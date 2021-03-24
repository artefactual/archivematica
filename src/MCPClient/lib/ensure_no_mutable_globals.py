#!/usr/bin/env python2

"""Ensure there are no mutable globals in the client scripts

This executable ensures that there are no mutable globals being accessed by
functions or methods used in the client scripts.

The function ``print_mutable_globals_usage`` analyzes all of the functions and
methods defined in all of the client scripts and collects all of the globals
which have mutable types that are accessed by those functions/methods. It
creates a dict from said globals to the list of modules::functions/methods that
access them. If the dict is non-empty, it is printed and an exit code of 1 is
returned. Otherwise a happy message is printed and 0 is returned.
"""

from __future__ import print_function
from dis import HAVE_ARGUMENT, opmap
import importlib
import logging
import os
import pprint
import sys
import types

import django
import prometheus_client

from archivematicaClient import get_supported_modules


# These are the global types that should not be potentially dangerous to use.
# Note, we are explicitly watching out for ``types.NoneType`` as a possible bad
# type since common practice is to use ``None`` as a default value for a global
# and then reassign globally it to something mutable.
GOOD_GLOBAL_TYPES = (
    types.ModuleType,
    types.FunctionType,
    types.TypeType,
    types.ClassType,
    django.db.models.base.ModelBase,
    logging.Logger,
    int,
    str,
    tuple,
    django.conf.LazySettings,
    django.db.DefaultConnectionProxy,
    prometheus_client.Counter,
    prometheus_client.Gauge,
    prometheus_client.Histogram,
    prometheus_client.Summary,
)


def get_globals(func, module):
    """Scan the bytecode of a function and return a set of the global
    variables it uses.

    Taken, with modification, from
    https://stackoverflow.com/questions/33160744/detect-all-global-variables-within-a-python-function/33160791#33160791
    """
    GLOBAL_OPS = opmap["LOAD_GLOBAL"], opmap["STORE_GLOBAL"]
    EXTENDED_ARG = opmap["EXTENDED_ARG"]
    func = getattr(func, "im_func", func)
    try:
        code = func.func_code
    except AttributeError:
        return []
    names = code.co_names
    op = (ord(c) for c in code.co_code)
    globs = set()
    extarg = 0
    for c in op:
        if c in GLOBAL_OPS:
            fg_attr = names[next(op) + next(op) * 256 + extarg]
            try:
                fg_val = getattr(module, fg_attr)
            except AttributeError:  # global is a Python builtin
                pass
            else:
                if not isinstance(fg_val, GOOD_GLOBAL_TYPES):
                    globs.add(fg_attr)
        elif c == EXTENDED_ARG:
            extarg = (next(op) + next(op) * 256) * 65536
            continue
        elif c >= HAVE_ARGUMENT:
            next(op)
            next(op)
        extarg = 0
    return sorted(globs)


def collect_globals(attr, val, module, module_name, global2modules_funcs_3):
    """Update dict ``global2modules_funcs_3`` by adding as keys the names of
    any mutable globals defined in ``module_name`` and adding as values of
    those keys a list of the functions (or methods), i.e., named ``attr``
    reverencing object ``val``, that access said globals.
    """
    module_func = "{}:{}".format(module_name, attr)
    for fg_attr in get_globals(val, module):
        key = "{}, {}".format(fg_attr, type(getattr(module, fg_attr)))
        global2modules_funcs_3.setdefault(key, []).append(module_func)
    return global2modules_funcs_3


def analyze_module(module_name):
    """Analyze module ``module_name`` by importing it and returning a dict that
    documents the mutable globals that are accessed by any of its functions or
    methods.
    """
    global2modules_funcs_2 = {}
    module = importlib.import_module("clientScripts." + module_name)
    for attr in dir(module):
        val = getattr(module, attr)
        if attr.startswith("__"):
            continue
        if isinstance(val, (types.TypeType, types.ClassType)):
            for class_attr in dir(val):
                global2modules_funcs_2 = collect_globals(
                    "{}.{}".format(attr, class_attr),
                    getattr(val, class_attr),
                    module,
                    module_name,
                    global2modules_funcs_2,
                )
        elif isinstance(val, types.FunctionType):
            global2modules_funcs_2 = collect_globals(
                attr, val, module, module_name, global2modules_funcs_2
            )
    return global2modules_funcs_2


def print_mutable_globals_usage(supported_modules):
    """Pretty-print mutable global usage by the client scripts named in
    ``supported_modules``. It's easiest to understand what this prints by
    looking at an example::

        {"sharedVariablesAcrossModules (<type 'instance'>)":
         ['create_mets_v2:archivematicaCreateMETSRightsDspaceMDRef',
          'create_mets_v2:call',
          'create_mets_v2:createDublincoreDMDSecFromDBData',
          'create_mets_v2:createFileSec',
          'create_mets_v2:include_custom_structmap',
          'create_mets_v2:parseMetadata',
          'extract_maildir_attachments:handle_job',
          'extract_maildir_attachments:parse'],
         ...}

    The above indicates that a mutable global named
    ``sharedVariablesAcrossModules`` is accessed by the function
    ``archivematicaCreateMETSRightsDspaceMDRef`` defined in the client script
    ``create_mets_v2.py``.
    """
    global2modules_funcs = {}
    for module_name in supported_modules.values():
        for global_, modules_funcs in analyze_module(module_name).items():
            global2modules_funcs.setdefault(global_, [])
            global2modules_funcs[global_] += modules_funcs
    worrisome = {
        k: v
        for k, v in global2modules_funcs.items()
        if k.split(",")[0] == k.split(",")[0].upper()
        and k.split(",")[1].strip() == "<type 'dict'>"
    }
    unacceptable = {k: v for k, v in global2modules_funcs.items() if k not in worrisome}
    if worrisome:
        print("\nWorrisome:")
        pprint.pprint(worrisome)
    if unacceptable:
        print("\nUnacceptable:")
        pprint.pprint(unacceptable)
        return 1
    if not worrisome:
        print("No mutable globals accessed in client scripts.")
    return 0


if __name__ == "__main__":
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "archivematicaClientModules"
    )
    sys.exit(print_mutable_globals_usage(get_supported_modules(config_path)))
