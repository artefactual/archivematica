# -*- coding: utf-8 -*-

"""
Shared executor, to spread work across multiple threads.
"""
from __future__ import absolute_import, unicode_literals

import multiprocessing

import concurrent.futures


executor = concurrent.futures.ThreadPoolExecutor(
    # Lots of workers, since we're mostly IO bound
    max_workers=multiprocessing.cpu_count()
    * 3
)
