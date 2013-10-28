#!/usr/bin/python2
import os
import subprocess
import sys


def main(target, output):
    args = [
        'bulk_extractor', target, '-o', output,
        '-M', '250', '-q', '-1'
    ]
    try:
        os.makedirs(output)
        subprocess.call(args)
        return 0
    except Exception as e:
        return e

if __name__ == '__main__':
    target = sys.argv[1]
    sipdir = sys.argv[2]
    file_uuid = sys.argv[3]
    output = os.path.join(sipdir, 'logs', 'bulk-' + file_uuid)
    sys.exit(main(target, output))
