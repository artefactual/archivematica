# -*- coding: utf-8 -*-

from v0_create_mets.v0_create_aip_mets import create_standard_mets
from v1_create_mets.v1_create_aip_mets import create_mets as create_reduced_mets
from v1_create_mets.v1_create_tool_mets import create_tool_mets

import traceback

from custom_handlers import get_script_logger

logger = get_script_logger("archivematica.mcp.client.createMETS2")


def concurrent_instances():
    return 1


def call(jobs):

    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--sipType", action="store", dest="sip_type", default="SIP")
    parser.add_option(
        "-s",
        "--baseDirectoryPath",
        action="store",
        dest="baseDirectoryPath",
        default="",
    )
    # transferDirectory/
    parser.add_option(
        "-b",
        "--baseDirectoryPathString",
        action="store",
        dest="baseDirectoryPathString",
        default="SIPDirectory",
    )
    # transferUUID/sipUUID
    parser.add_option(
        "-f",
        "--fileGroupIdentifier",
        action="store",
        dest="fileGroupIdentifier",
        default="",
    )
    parser.add_option(
        "-t", "--fileGroupType", action="store", dest="fileGroupType", default="sipUUID"
    )
    parser.add_option("-x", "--xmlFile", action="store", dest="xmlFile", default="")
    parser.add_option(
        "-a", "--amdSec", action="store_true", dest="amdSec", default=False
    )
    parser.add_option(
        "-n",
        "--createNormativeStructmap",
        action="store_true",
        dest="createNormativeStructmap",
        default=False,
    )

    for job in jobs:
        with job.JobContext(logger=logger):
            try:
                opts, _ = parser.parse_args(job.args[1:])
                create_standard_mets(job, opts)
                create_reduced_mets(job, opts)
                create_tool_mets(job, opts)
            except Exception as err:
                job.print_error(repr(err))
                job.print_error(traceback.format_exc())
                job.set_status(1, status_code="failure")
