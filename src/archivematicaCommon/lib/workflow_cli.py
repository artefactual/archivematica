#!/usr/bin/env python2

from __future__ import print_function, unicode_literals

import os
import sys

import workflow


def usage(commands):
    script_name = os.path.basename(__file__)
    sys.exit('{} [{}]'.format(script_name, '|'.join(commands)))


if __name__ == '__main__':
    commands = ['WorkflowGet']

    if len(sys.argv) == 1:
        usage(commands)

    cmd = sys.argv[1]
    client = workflow.get_client()

    if cmd not in commands:
        usage(commands)

    if cmd == 'WorkflowGet':
        try:
            id_ = sys.argv[2]
        except IndexError:
            sys.exit('Missing parameters (id)')
        try:
            resp = client.get_workflow(id_)
            print('Watched directories: {} items'.format(len(resp.watchedDirectories)))
            print('Chains: {} items'.format(len(resp.chains)))
            print('Links: {} items'.format(len(resp.links)))
            for item in resp.links.items():
                print(item)
        except workflow.ClientError as e:
            print('Error:', e)
