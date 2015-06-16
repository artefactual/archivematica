#!/usr/bin/python2

from __future__ import print_function
import datetime
from lxml import etree
import sys
import os

# dashboard
from main import models


def main():
    # HACK Most of this file is a hack to parse the METS file into the DB.
    # This should use the in-progress METS Reader/Writer

    sip_uuid = sys.argv[1]
    sip_path = sys.argv[2]

    # Set reingest type
    # TODO also support AIC-REIN
    sip = models.SIP.objects.filter(uuid=sip_uuid)
    sip.update(sip_type='AIP-REIN')

    # Stuff to delete
    # The cascading delete of the SIP on approve reingest deleted most things

    # Parse METS to extract information needed by later microservices
    mets_path = os.path.join(sip_path, 'metadata', 'submissionDocumentation', 'METS.'+sip_uuid+'.xml')
    root = etree.parse(mets_path)


if __name__ == '__main__':
    print('METS Reader')
    sys.exit(main())
