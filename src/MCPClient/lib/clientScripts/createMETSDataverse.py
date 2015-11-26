#!/usr/bin/env python2
from __future__ import print_function
import sys

import archivematicaFunctions

import metsrw

def create_dataverse_sip_dmdsec(sip_path):
    """
    Return SIP-level Dataverse dmdSecs for inclusion in the AIP METS.

    :param str: Path to the SIP
    :return: List of dmdSec Elements
    """
    # Find incoming external METS
    metadata_mets_paths = archivematicaFunctions.find_metadata_files(sip_path, 'METS.xml', only_transfers=True)
    # If doesn't exist, return None
    if not metadata_mets_paths:
        return []
    ret = []
    for metadata_path in metadata_mets_paths:
        # Parse it
        try:
            mets = metsrw.METSDocument.fromfile(metadata_path)
        except mets.MetsError:
            print('Could not parse external METS (Dataverse)', metadata_path, file=sys.stderr)
            continue

        # Get SIP-level DDI
        for f in mets.all_files():
            # TODO get better query API
            if f.type == "Directory" and f.dmdsecs:
                # Serialize
                ret += [d.serialize() for d in f.dmdsecs]
    # Return list
    return ret

def create_dataverse_tabfile_dmdsec(sip_path, tabfile):
    """
    Returns dmdSec associated with the given tabfile, if one exists.
    """
    # Find incoming external METS
    metadata_mets_paths = archivematicaFunctions.find_metadata_files(sip_path, 'METS.xml', only_transfers=True)
    # If doesn't exist, return None
    if not metadata_mets_paths:
        return None

    for metadata_path in metadata_mets_paths:
        # Parse it
        try:
            mets = metsrw.METSDocument.fromfile(metadata_path)
        except mets.MetsError:
            print('Could not parse external METS (Dataverse)', metadata_path, file=sys.stderr)
            continue

        # Get SIP-level DDI
        for f in mets.all_files():
            if f.type == "Item" and f.path.endswith(tabfile):
                # Found the correct tabfile
                return [d.serialize() for d in f.dmdsecs]
    return []
