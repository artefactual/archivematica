#!/usr/bin/env python2

import archivematicaXMLNamesSpace as ns
import os
import sys
from lxml import etree

VERSION_MAP = {
    # Only change exit code if AIP format changes. If unknown, default to latest
    # version. Currently, all AIPs are the same format so no special cases
    # required.
    # Example:
    # 'Archivematica-1.2': 100,
}


def get_version_from_mets(mets):
    for agent in mets.iter(ns.metsBNS+"agentIdentifier"):
        if agent.findtext(ns.metsBNS+"agentIdentifierType") != "preservation system":
            continue
        return agent.findtext(ns.metsBNS+"agentIdentifierValue")
    return None

if __name__ == '__main__':
    sip_uuid = sys.argv[1]
    unit_path = sys.argv[2]

    mets_path = os.path.join(unit_path, "data", "METS.%s.xml" % (sip_uuid))
    if not os.path.isfile(mets_path):
        print >>sys.stderr, "Mets file not found: ", mets_path
        sys.exit(0)

    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(mets_path, parser)
    
    version = get_version_from_mets(root)
    print 'Version found in METSt:', version
    
    sys.exit(VERSION_MAP.get(version, 0))
