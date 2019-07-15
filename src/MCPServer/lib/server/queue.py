from __future__ import absolute_import, unicode_literals

import threading
from Queue import Queue

import concurrent.futures


class JobQueue(object):

    _queued = Queue()
    _queued_by_uuid = {}
    _queued_by_uuid_lock = threading.RLock()

    def put(self, task_group, block=True, timeout=None):
        future = concurrent.futures.Future()
        with self._queued_by_uuid_lock:
            self._queued_by_uuid[task_group.UUID] = (future, task_group)
        self._queued.put(task_group, block=block, timeout=timeout)

        return future

    def get(self, block=True, timeout=None):
        return self._queued.get(block=block, timeout=timeout)

    def get_by_uuid(self, uuid):
        with self._queued_by_uuid_lock:
            return self._queued_by_uuid.pop(uuid)


job_queue = JobQueue()
