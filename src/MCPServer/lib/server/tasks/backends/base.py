from __future__ import absolute_import, division, print_function, unicode_literals

import abc

from django.utils import six


@six.add_metaclass(abc.ABCMeta)
class TaskBackend(object):
    """Handles out of process `Task` execution.

    Currently we only have one backend, `GearmanTaskBackend`.
    """

    @abc.abstractmethod
    def submit_task(self, job, task):
        """Submit a task as part of the job given, for offline processing."""

    @abc.abstractmethod
    def wait_for_results(self, job):
        """Generator that yields `Task` objects related to the job given,
        as they are processed by the backend.

        This method should only be called once all tasks related to the job
        have been submitted, via `submit_task`.

        Note that task objects are not necessarily returned in the order
        they were submitted.
        """
