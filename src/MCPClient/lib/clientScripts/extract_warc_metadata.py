#!/usr/bin/env python2

from __future__ import print_function

import django
import re
import sys

from custom_handlers import get_script_logger

django.setup()
logger = get_script_logger("archivematica.mcp.client.extract_warc_metadata")



def read_warc_software_agent(warc_file, header):
    content_length = int(header.get('Content-Length', 0))

    if not content_length:
        print('Invalid content-length received: {}'.format(header.get('Content-Length')), file=sys.stderr)
        sys.exit(1)

    content = warc_file.read(content_length)
    r = re.search(r'software:\s+(.*?)$', content, re.I | re.M)
    if r is not None:
        return r.group(1)

    return None


def read_first_warcinfo_header(warc_file):
    # Get start of WARC header for the record
    ln = warc_file.readline()

    r = re.match('WARC/\d\.\d\r\n', ln)
    if not r:
        print('Bad header line encountered: {}'.format(ln), file=sys.stderr)
        sys.exit(1)

    header = {}

    while 1:
        ln = warc_file.readline()

        if not ln:
            print('Unexpected EOF when reading WARC header', file=sys.stderr)
            sys.exit(1)
        elif ln == '\r\n':  # Blank newline indicates end of header
            break

        r = re.match(r'(.*?):\s+(.*?)$', ln)
        if r is None:
            continue

        header[r.group(1)] = r.group(2).strip()

    if header.get('WARC-Type') != 'warcinfo':
        print('Encountered unexpected record type: {}'.format(header.get('WARC-Type')), file=sys.stderr)
        print('Record of type "warcinfo" expected.')
        sys.exit(1)

    return header


def main():
    file_location = sys.argv[1]
    file_uuid = sys.argv[2]

    if not file_location.lower().endswith('.warc'):
        print('Skipping non-WARC file.')
        return 0

    print('Extracting WARC metadata...')
    with open(file_location, 'rb') as f:
        header = read_first_warcinfo_header(f)
        software_agent = read_warc_software_agent(f, header)

        print('Got software agent:', software_agent)

        # a = models.Agent.objects.create(name='test', agenttype='software');

if __name__ == '__main__':
    sys.exit(main())
