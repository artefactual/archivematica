#!/usr/bin/env python2

"""
Execute the .call(jobs) function of a clientScripts module from multiple
processes.

Takes a list of jobs to be executed and split them across a specified number of
subprocesses.  Once the subprocesses complete, gather up the results and return
them to the MCP Client.

This is invoked when a clientScripts module provides a `concurrent_instances`
function (indicating that it supports being run as a subprocess).
"""


import six.moves.cPickle
import importlib
import logging
import multiprocessing
import os
import sys
import tempfile
import traceback

import django

django.setup()
from databaseFunctions import auto_close_db
from executeOrRunSubProcess import launchSubProcess

logger = logging.getLogger("archivematica.mcp.client")

# Using this instead of __file__ to ensure we don't get fork_runner.pyc!
THIS_SCRIPT = "fork_runner.py"


def call(module_name, jobs, task_count=multiprocessing.cpu_count()):
    """
    Split `jobs` into `task_count` groups and fork a subprocess to run
    `module_name`.call() for each of them.
    """
    jobs_by_uuid = {}
    for job in jobs:
        jobs_by_uuid[job.UUID] = job

    pool = multiprocessing.Pool(processes=task_count)

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


def _split_jobs(jobs, n):
    "Split `jobs` into n approximately equally-sized pieces"
    chunk_size = len(jobs) / n
    result = []

    while jobs:
        # Last chunk might be a little bigger
        if len(result) == (n - 1):
            result.append(jobs)
            jobs = []
        else:
            result.append(jobs[0:chunk_size])

        jobs = jobs[chunk_size:]

    return result


@auto_close_db
def _run_jobs(module_name, jobs):
    (fd, output_file) = tempfile.mkstemp()

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
            six.moves.cPickle.dumps(environment, protocol=0),
            printing=False,
            capture_output=True,
        )

        with os.fdopen(fd) as f:
            result = six.moves.cPickle.load(f)

            if isinstance(result, dict) and result["uncaught_exception"]:
                e = result["uncaught_exception"]
                # Something went wrong with our client script.  This shouldn't
                # happen under normal operation, but might happen during
                # development.
                logging.error(
                    ("Failure while executing '%s':\n" % (module_name)) + e["traceback"]
                )
                raise Exception(e["type"] + ": " + e["message"])
            else:
                return result

    finally:
        os.unlink(output_file)


# Executed in our subprocess (see note in _run_jobs above).
if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise Exception(
            "Must be called with a module name (and a list of pickled jobs on stdin)"
        )

    module_to_run = sys.argv[1]
    environment = six.moves.cPickle.load(sys.stdin)

    sys.path = environment["sys.path"]
    jobs = environment["jobs"]
    output_file = environment["output_file"]

    with open(output_file, "w") as f:
        try:
            module = importlib.import_module(module_to_run)
            module.call(jobs)
            six.moves.cPickle.dump(jobs, f)
        except Exception as e:
            six.moves.cPickle.dump(
                {
                    "uncaught_exception": {
                        "message": e.message,
                        "type": type(e).__name__,
                        "traceback": traceback.format_exc(),
                    }
                },
                f,
            )
