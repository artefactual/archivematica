# -*- coding: utf-8 -*-

"""
Shared executor, to spread work across multiple threads.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import concurrent.futures

from django.conf import settings


executor = concurrent.futures.ThreadPoolExecutor(
    # Lower than the default, since we typically run many processes per system.
    # Defaults to the number of cores available, which is twice as many as the
    # default concurrent packages limit.
    max_workers=settings.WORKER_THREADS
)
