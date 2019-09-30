# -*- coding: utf-8 -*-

"""
Shared executor, to spread work across multiple threads.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import multiprocessing

import concurrent.futures


executor = concurrent.futures.ThreadPoolExecutor(
    # Lower than the default, since we typically run many processes.
    # Still quite a few workers though, since we're mostly IO bound.
    max_workers=multiprocessing.cpu_count()
    * 3
)
