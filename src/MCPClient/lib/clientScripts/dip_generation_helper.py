#!/usr/bin/env python2
from __future__ import print_function
import argparse
import sys


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse metadata for DIP helpers')
    parser.add_argument('--sipUUID', required=True, help='%SIPUUID%')
    parser.add_argument('--sipPath', required=True, help='%SIPDirectory%')
    args = parser.parse_args()

    rc = 0

    sys.exit(rc)
