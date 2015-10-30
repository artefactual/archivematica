#!/usr/bin/env python2

from __future__ import print_function

import hashlib
import sys


def get_file_checksum(filename, algorithm='sha256'):
    """
    Perform a checksum on the specified file.

    This function reads in files incrementally to avoid memory exhaustion.
    See: http://stackoverflow.com/questions/1131220/get-md5-hash-of-a-files-without-open-it-in-python

    :param filename: The path to the file we want to check
    :param algorithm: Which algorithm to use for hashing, e.g. 'md5'
    :return: Returns a checksum string for the specified file.
    """
    h = hashlib.new(algorithm)

    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * h.block_size), b''):
            h.update(chunk)

    return h.hexdigest()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Please specify a filename.')
        sys.exit(1)

    input_file = sys.argv[1]
    for alg in ('md5', 'sha1', 'sha256', 'sha512'):
        print('{}: {}'.format(alg, get_file_checksum(input_file, alg)))

