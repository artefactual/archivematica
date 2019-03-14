#!/usr/bin/env python2

from executeOrRunSubProcess import executeOrRun


def call(jobs):
    for job in jobs:
        with job.JobContext():
            exit_code, std_out, std_error = executeOrRun(
                "command", ["chmod"] + job.args[1:], printing=True, capture_output=True
            )

            job.write_error(std_error)
            job.write_output(std_out)
            job.set_status(exit_code)
