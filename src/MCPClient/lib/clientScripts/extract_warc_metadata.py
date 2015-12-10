#!/usr/bin/env python2

from __future__ import print_function

from argparse import ArgumentParser
import logging
import re
import sys

# from custom_handlers import get_script_logger


# logger = get_script_logger("archivematica.mcp.client.extract_warc_metadata")
logger = logging.getLogger(__name__)


class WarcinfoHeaderError(Exception):
    pass


def read_warc_software_agent(warc_file, header):
    content_length = int(header.get('Content-Length', 0))
    if not content_length:
        raise WarcinfoHeaderError('invalid content-length received: {}'.format(header.get('Content-Length')))

    content = warc_file.read(content_length)
    r = re.search(r'software:\s+(.*?)$', content, re.I | re.M)
    if r is not None:
        return r.group(1)

    return None


def read_first_warcinfo_header(warc_file):
    # Get start of WARC header for the record
    ln = warc_file.readline()

    r = re.match('^WARC/(?P<version>\d+\.\d+)', ln)
    try:
        r.group('version')
    except IndexError:
        raise WarcinfoHeaderError('bad header line encountered: {}'.format(ln))

    header = {}

    while 1:
        ln = warc_file.readline()

        if not ln:
            raise WarcinfoHeaderError('unexpected EOF')
        elif ln == '\r\n':  # Blank newline indicates end of header
            break

        r = re.match(r'(.*?):\s+(.*?)$', ln)
        if r is None:
            continue

        header[r.group(1)] = r.group(2).strip()

    if header.get('WARC-Type') != 'warcinfo':
        raise WarcinfoHeaderError('unexpected record type: {}, type "warcinfo" expected.'.format(header.get('WARC-Type')))

    return header


def main(file_location, file_uuid):
    if not file_location.lower().endswith('.warc'):
        logger.info('Skipping non-WARC file.')
        return 0

    logger.info('Extracting WARC metadata...')
    with open(file_location, 'rb') as f:
        try:
            header = read_first_warcinfo_header(f)
            software_agent = read_warc_software_agent(f, header)
        except WarcinfoHeaderError as e:
            logger.error('Error during extraction: %s', e)
        else:
            logger.info('Got software agent: %s', software_agent)

    return 0


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('file_location')
    parser.add_argument('file_uuid')
    parser.add_argument('--debug', action='store_true', default=False)
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())

    sys.exit(main(args.file_location, args.file_uuid))
