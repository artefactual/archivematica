"""Application thread pool used for local concurrency."""

from multiprocessing.pool import ThreadPool

from django.conf import settings as django_settings


class Executor(object):
    _instance = None

    @staticmethod
    def init():
        """Initialize Executor."""
        Executor._instance = Executor()

    def __init__(self):
        self.pool = ThreadPool(django_settings.LIMIT_TASK_THREADS)

    @staticmethod
    def apply(func, args=(), kwds={}):
        """Run callable and block until it returns.

        Equivalent of `func(*args, **kwds)`.
        Pool must be running.
        """
        return Executor._instance.pool.apply(func, args, kwds)

    @staticmethod
    def apply_async(func, args=(), kwds={}, callback=None):
        """Asynchronous version of `apply()` method.

        It returns an instance of `ApplyResult`.
        """
        return Executor._instance.pool.apply_async(
            func, args, kwds, callback)
