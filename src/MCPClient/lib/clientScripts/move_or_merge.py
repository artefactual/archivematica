#!/usr/bin/env python2

import os
import sys
import shutil


def main(src, dst):
    """
    Moves a file/directory to a new location, or moves two directories.

    If dst doesn't exist, acts like mv: src is moved to the same path as dst.
    If dst does exist and is a directory, the two directories are merged by
    moving src's contents into dst.
    """
    if os.path.exists(dst):
        for item in os.listdir(src):
            shutil.move(os.path.join(src, item), dst)
        shutil.rmtree(src)
    else:
        shutil.move(src, dst)

    return 0


def call(jobs):
    for job in jobs:
        with job.JobContext():
            src = job.args[1]
            dst = job.args[2]
            try:
                job.set_status(main(src, dst))
            except Exception as e:
                job.print_error(repr(e))
                job.set_status(1)
