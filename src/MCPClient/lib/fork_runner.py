#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Execute the .call(jobs) function of a clientScripts module from multiple
processes.

Takes a list of jobs to be executed and split them across a specified number of
subprocesses.  Once the subprocesses complete, gather up the results and return
them to the MCP Client.

This is invoked when a clientScripts module provides a `concurrent_instances`
function (indicating that it supports being run as a subprocess).
"""

from importlib import import_module
import logging
from math import floor
from multiprocessing import cpu_count, Pool
import os
import sys
from tempfile import mkstemp
from traceback import format_exc

from django.utils import six
from django.utils.six.moves import cPickle

from databaseFunctions import auto_close_db
from executeOrRunSubProcess import launchSubProcess

logger = logging.getLogger("archivematica.mcp.client")

# Using this instead of __file__ to ensure we don't get fork_runner.pyc!
THIS_SCRIPT = "fork_runner.py"


def call(module_name, jobs, task_count=cpu_count()):
    """Split `jobs` into `task_count` groups and fork a subprocess to run
    `module_name`.call() for each of them.
    """
    jobs_by_uuid = {}
    for job in jobs:
        jobs_by_uuid[job.UUID] = job
    pool = Pool(processes=task_count)
    try:
        results = []
        for job_subset in _split_jobs(jobs, task_count):
            results.append(pool.apply_async(_run_jobs, (module_name, job_subset)))

        finished_jobs = []
        for result in results:
            finished_jobs += result.get()

        for finished_job in finished_jobs:
            job = jobs_by_uuid[finished_job.UUID]
            job.load_from(finished_job)
    finally:
        pool.terminate()


def _split_jobs(jobs, n_split):
    """Split `jobs` into n approximately equally-sized pieces"""
    chunk_size = int(floor(len(jobs) / n_split))
    result = []
    while jobs:
        # Last chunk might be a little bigger
        if len(result) == (n_split - 1):
            result.append(jobs)
            jobs = []
        else:
            result.append(jobs[0:chunk_size])
        jobs = jobs[chunk_size:]
    return result


@auto_close_db
def _run_jobs(module_name, jobs):
    """Launch the fork_runner script within itself for Jobs given in the
    supplied args.
    """
    (file_descriptor, output_file) = mkstemp()
    try:
        environment = {"jobs": jobs, "sys.path": sys.path, "output_file": output_file}
        # A bit of trickiness: Re-execute ourselves (fork_runner.py) in a
        # subprocess as a standalone script.  This ensures that we're running in
        # a clean environment (avoiding issues with things like forking while
        # holding a connection to the database)
        #
        # We communicate with our subprocess by supplying our `environment` map
        # on stdin.  It gives results back to us by writing them to a temporary
        # file.
        (status, stdout, stderr) = launchSubProcess(
            [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), THIS_SCRIPT),
                module_name,
            ],
            cPickle.dumps(environment, protocol=0),
            printing=False,
            capture_output=True,
        )
        with os.fdopen(file_descriptor, "rb") as file_:
            result = cPickle.load(file_)
            if isinstance(result, dict) and result.get("uncaught_exception"):
                err = result.get("uncaught_exception", {})
                logging.error(
                    "Failure while executing '%s':\n%s",
                    module_name,
                    err.get("traceback", "Cannot retrieve key: 'traceback'"),
                )
                raise Exception(
                    "{}: {}".format(
                        err.get("type", "Cannot retrieve key: 'type'"),
                        err.get("message", "Cannot retrieve key: 'message'"),
                    )
                )
            else:
                return result
    finally:
        os.unlink(output_file)


def main(args):
    """Primary entry-point for this script."""
    module_to_run = args[1]
    logger.info("Running module: %s", module_to_run)
    if six.PY2:
        # PY2 read stdin as-is, file-like object.
        environment = cPickle.load(sys.stdin)
    if six.PY3:
        # PY3 need to return buffer from _io.TextIOWrapper to read as bytes.
        environment = cPickle.load(sys.stdin.buffer)
    sys.path = environment.get("sys.path")
    jobs_ = environment.get("jobs")
    output_file = environment.get("output_file")
    with open(output_file, "wb") as out_f:
        try:
            module = import_module(module_to_run)
            module.call(jobs_)
            cPickle.dump(jobs_, out_f, protocol=0)
        except Exception as err:
            cPickle.dump(
                {
                    "uncaught_exception": {
                        "message": err.message,
                        "type": type(err).__name__,
                        "traceback": format_exc(),
                    }
                },
                out_f,
                protocol=0,
            )


# Executed in our subprocess (see note in _run_jobs above).
if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise Exception(
            "Must be called with a module name (and a list of pickled jobs on stdin)"
        )
    main(sys.argv)
