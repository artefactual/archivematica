#!/usr/bin/env python2

from __future__ import print_function

import sys
import warc

import django
django.setup()
# dashboard

def main():
    file_location = sys.argv[1]
    file_uuid = sys.argv[2]

    if not file_location.lower().endswith('.warc'):
        print('Skipping non-WARC file.')
        return

    print('Extracting WARC metadata...')

if __name__ == '__main__':
    sys.exit(main())
