#!/usr/bin/env python

from pathlib import Path
import argparse
import os
import sys

import django
import bag

django.setup()
from django.db import transaction

# archivematicaCommon
from executeOrRunSubProcess import executeOrRun
from fileOperations import get_extract_dir_name


# XXX: move to archivematicaCommon
def extract(job, target, destinationDirectory):
    filename, file_extension = os.path.splitext(target)

    exitC = 0

    if file_extension != ".tgz" and file_extension != ".gz":
        job.pyprint("Unzipping...")

        command = """/usr/bin/7z x -bd -o"%s" "%s" """ % (destinationDirectory, target)
        exitC, stdOut, stdErr = executeOrRun(
            "command", command, printing=False, capture_output=True
        )
        if exitC != 0:
            job.pyprint(stdOut)
            job.pyprint("Failed extraction: ", command, "\r\n", stdErr, file=sys.stderr)
    else:
        job.pyprint("Untarring...")

        parent_dir = os.path.abspath(os.path.join(destinationDirectory, os.pardir))
        file_extension = ""
        command = ("tar zxvf " + target + ' --directory="%s"') % (parent_dir)
        exitC, stdOut, stdErr = executeOrRun(
            "command", command, printing=False, capture_output=True
        )
        if exitC != 0:
            job.pyprint(stdOut)
            job.pyprint("Failed to untar: ", command, "\r\n", stdErr, file=sys.stderr)

    return exitC


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("sip_directory", type=str)

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])

                # XXX: use naming convention for now
                bag_path = Path(args.sip_directory) / "metadata" / "mdupdate.zip"

                if not bag_path.is_file():
                    continue

                try:
                    destination = Path(get_extract_dir_name(bag_path))
                except ValueError:
                    # XXX: log error
                    job.set_status(1)
                    continue

                if destination.exists():
                    # XXX: log error
                    continue

                exit_code = extract(job, str(bag_path), str(destination))

                if exit_code != 0:
                    job.set_status(exit_code)
                    continue

                if not bag.is_valid(str(destination), printfn=job.pyprint):
                    job.pyprint("Failed bagit compliance.", file=sys.stderr)
                    job.set_status(1)

                bag_path.unlink()
