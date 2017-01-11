#!/usr/bin/env python2

from __future__ import print_function, unicode_literals

import os

import sys

import mcpserver
from protos import mcpserver_pb2


def usage(commands):
    script_name = os.path.basename(__file__)
    sys.exit('{} [{}]'.format(script_name, '|'.join(commands)))


if __name__ == '__main__':
    commands = [
        'ApproveJob',
        'ApproveTransfer',
        'ChoiceList',
    ]

    if len(sys.argv) == 1:
        usage(commands)

    cmd = sys.argv[1]
    client = mcpserver.get_client()

    if cmd not in commands:
        usage(commands)

    if cmd == 'ApproveJob':
        try:
            job_uuid = sys.argv[2]
            choice_uuid = sys.argv[3]
        except IndexError:
            sys.exit('Missing parameters (job_uuid, choice_uuid)')
        approved = client.approve_job(job_uuid, choice_uuid)
        print("Has the job been approved? {}".format("Yes!" if approved else "No, :("))

    elif cmd == 'ApproveTransfer':
        try:
            sip_uuid = sys.argv[2]
        except IndexError:
            sys.exit('Missing parameter (sip_uuid)')
        approved = client.approve_transfer(sip_uuid)
        print("Has the transfer been approved? {}".format("Yes!" if approved else "No, :("))

    elif cmd == 'ChoiceList':
        resp = client.list_choices()
        jobs = resp.jobs
        if not len(jobs):
            sys.exit('There are no choices awaiting for decision at this moment.')
        print("Pending choices: [ Transfer = {} ] [ Ingest = {} ]".format(resp.transferCount, resp.ingestCount))
        for job in jobs:
            print("\nJob {} of unit with type {}".format(job.id, mcpserver_pb2.ChoiceListResponse.Job.UnitType.Name(job.unitType)))
            for item in job.choices:
                print("\tChoice: {} (value={})".format(item.description, item.value))
