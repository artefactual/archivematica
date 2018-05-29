"""Decorators used by the MCPServer worker found in the worker module."""

# This file is part of Archivematica.
#
# Copyright 2010-2018 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

import cPickle

from worker_error import RPCServerError, UnexpectedPayloadError


def log_exceptions(logger):
    """Worker handler decorator to log exceptions."""
    def decorator(func):
        def wrap(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as err:
                internal_err = isinstance(err, RPCServerError)
                logger.error('Exception raised by handler %s: %s',
                             func.__name__, err, exc_info=not internal_err)
                raise  # So GearmanWorker knows that it failed.
        return wrap
    return decorator


def unpickle_payload(fn):
    """Worker handler decorator to unpickle the incoming payload.

    It prepends an argument before calling the decorated function.
    """
    def wrap(*args, **kwargs):
        gearman_job = args[1]
        payload = cPickle.loads(gearman_job.data)
        if not isinstance(payload, dict):
            raise UnexpectedPayloadError('Payload is not a dictionary')
        kwargs['payload'] = payload
        return fn(*args, **kwargs)
    return wrap


def pickle_result(fn):
    """Worker handler decorator to pickle the returned value."""
    def wrap(*args, **kwargs):
        return cPickle.dumps(fn(*args, **kwargs))
    return wrap
