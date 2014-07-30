#!/usr/bin/env python2
from __future__ import print_function
import datetime
from lxml import etree
import os
import sys

import archivematicaXMLNamesSpace as ns
import archivematicaCreateMETS2 as createmets2
import archivematicaCreateMETSRights as createmetsrights
import archivematicaCreateMETSMetadataCSV as createmetscsv

# dashboard
from main import models


def update_header(root, now):
    """
    Update metsHdr to have LASTMODDATE.
    """
    metshdr = root.find('mets:metsHdr', namespaces=ns.NSMAP)
    metshdr.set('LASTMODDATE', now)
    return root


def update_dublincore(root, sip_uuid, now):
    """
    Add new dmdSec for updated Dublin Core info relating to entire SIP.

    Case: No DC in DB: Do nothing
    Case: DC in DB is untouched (METADATA_STATUS_REINGEST): Do nothing
    Case: New DC in DB with METADATA_STATUS_ORIGINAL: Add new DC
    Case: DC in DB with METADATA_STATUS_UPDATED: mark old, create updated
    """

    # Check for DC in DB with METADATA_STATUS_UPDATED
    updated = models.DublinCore.objects.filter(
        metadataappliestoidentifier=sip_uuid,
        metadataappliestotype_id=createmets2.SIPMetadataAppliesToType,
        status=models.METADATA_STATUS_UPDATED
    ).exists()

    # If no updated DC, check for a newly added DC
    if not updated:
        new = models.DublinCore.objects.filter(
            metadataappliestoidentifier=sip_uuid,
            metadataappliestotype_id=createmets2.SIPMetadataAppliesToType,
            status=models.METADATA_STATUS_ORIGINAL
        ).exists()
        if new:
            updated = False
        else:
            # No new or updated DC found - return early
            print('No updated or new DC metadata found')
            return root

    print('DC form metadata was updated:', updated)

    # Get structMap element related to SIP DC info
    objects_div = root.find('mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]', namespaces=ns.NSMAP)
    ids = objects_div.get('DMDID', '')
    print('Existing dmdIds for DC metadata:', ids)

    # Create element
    dc_elem = createmets2.getDublinCore(createmets2.SIPMetadataAppliesToType, sip_uuid)
    count_dmdsecs = int(root.xpath('count(mets:dmdSec)', namespaces=ns.NSMAP))
    dmdid = "dmdSec_%d" % (count_dmdsecs + 1)  # DMDID should be larger than any existing one
    dmd_sec = etree.Element(ns.metsBNS + "dmdSec", ID=dmdid, CREATED=now)
    print('Adding new DC in dmdSec with ID', dmdid)
    if updated:
        dmd_sec.set('STATUS', 'updated')
        # Update old DC
        # Get dmdSecs associated with the SIP
        search_ids = ' or '.join(['@ID="%s"' % x for x in ids.split()])
        dmdsecs = root.xpath('mets:dmdSec[%s]' % search_ids, namespaces=ns.NSMAP)
        # Set status=original if none
        for d in dmdsecs:
            # If no status (not updated), set to original
            status = d.get('STATUS')
            if not status:
                print(d.get('ID'), 'status set to original')
                d.set('STATUS', 'original')

    mdWrap = etree.SubElement(dmd_sec, ns.metsBNS + "mdWrap", MDTYPE="DC")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
    xmlData.append(dc_elem)

    # Append to document
    try:
        add_after = root.findall('mets:dmdSec', namespaces=ns.NSMAP)[-1]
    except IndexError:
        add_after = root.find('mets:metsHdr', namespaces=ns.NSMAP)
    add_after.addnext(dmd_sec)

    # Update structMap
    ids = ids + ' ' + dmdid if ids else dmdid
    objects_div.set('DMDID', ids)

    return root


def update_rights(root, sip_uuid, now):
    """
    Add rightsMDs for updated PREMIS Rights.
    """
    rights_counter = int(root.xpath('count(mets:amdSec/mets:rightsMD)', namespaces=ns.NSMAP))  # HACK

    # Get amdSecs to add rights to. Only add to first amdSec for original files
    file_elems = root.findall('mets:fileSec/mets:fileGrp[@USE="original"]/mets:file', namespaces=ns.NSMAP)
    ids = [x.get('ADMID', '').split()[0] for x in file_elems]
    search_ids = ' or '.join(['@ID="%s"' % x for x in ids])
    amdsecs = root.xpath('mets:amdSec[%s]' % search_ids, namespaces=ns.NSMAP)

    # Check for newly added rights
    rights_list = models.RightsStatement.objects.filter(
        metadataappliestoidentifier=sip_uuid,
        metadataappliestotype_id=createmets2.SIPMetadataAppliesToType,
        status=models.METADATA_STATUS_ORIGINAL
    )
    if not rights_list:
        print('No new rights added')
    else:
        rights_counter = add_rights_elements(rights_list, amdsecs, now, rights_counter)

    # Check for updated rights
    rights_list = models.RightsStatement.objects.filter(
        metadataappliestoidentifier=sip_uuid,
        metadataappliestotype_id=createmets2.SIPMetadataAppliesToType,
        status=models.METADATA_STATUS_UPDATED
    )
    if not rights_list:
        print('No updated rights found')
    else:
        add_rights_elements(rights_list, amdsecs, now, rights_counter, updated=True)

    return root


def add_rights_elements(rights_list, amdsecs, now, rights_counter, updated=False):
    """
    Create and add rightsMDs for everything in rights_list to amdsecs.
    """
    # Add to files' amdSecs
    for amdsec in amdsecs:
        # Get element to add rightsMDs after
        try:
            # Add after other rightsMDs
            add_after = amdsec.findall('mets:rightsMD', namespaces=ns.NSMAP)[-1]
        except IndexError:
            # If no rightsMDs, then techMD is aways there and previous subsection
            add_after = amdsec.findall('mets:techMD', namespaces=ns.NSMAP)[-1]
        for rights in rights_list:
            # Generate ID based on number of other rightsMDs
            rights_counter += 1
            rightsid = 'rightsMD_%s' % rights_counter
            print('Adding rightsMD', rightsid, 'to amdSec with ID', amdsec.get('ID'))

            # Get file UUID for this file
            file_uuid = amdsec.findtext('mets:techMD/mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]//premis:objectIdentifierValue', namespaces=ns.NSMAP)
            print(rightsid, 'is for file', file_uuid)

            # Create element
            rightsMD = etree.Element(ns.metsBNS + "rightsMD", ID=rightsid, CREATED=now)
            mdWrap = etree.SubElement(rightsMD, ns.metsBNS + 'mdWrap', MDTYPE='PREMIS:RIGHTS')
            xmlData = etree.SubElement(mdWrap, ns.metsBNS + 'xmlData')
            rights_statement = createmetsrights.createRightsStatement(rights, file_uuid)
            xmlData.append(rights_statement)

            if updated:
                rightsMD.set('STATUS', 'current')
                # Find superseded rightsMD and mark as such
                # rightsBasis is semantically unique (though not currently
                # enforced in code). Find rightsMDs with the same rights basis
                # and mark superseded
                superseded = amdsec.xpath('mets:rightsMD[not(@STATUS) or @STATUS="current"]//premis:rightsBasis[text()="' + rights.rightsbasis + '"]/ancestor::mets:rightsMD', namespaces=ns.NSMAP)
                for elem in superseded:
                    print('Marking', elem.get('ID'), 'as superseded')
                    elem.set('STATUS', 'superseded')

            add_after.addnext(rightsMD)
            add_after = rightsMD

    return rights_counter


def add_events(root, sip_uuid):
    """
    Add reingest events for all existing files.
    """
    # Get all reingestion events for files in this SIP
    reingest_events = models.Event.objects.filter(file_uuid__sip__uuid=sip_uuid, event_type='reingestion')
    digiprov_counter = int(root.xpath('count(mets:amdSec/mets:digiprovMD)', namespaces=ns.NSMAP))  # HACK
    # Get Agent
    try:
        agent = models.Agent.objects.get(identifiertype="preservation system", name="Archivematica", agenttype="software")
    except models.Agent.DoesNotExist:
        agent = None
    except models.Agent.MultipleObjectsReturned:
        agent = None
        print('WARNING multiple agents found for Archivematica')

    for event in reingest_events:
        # Use fileSec to get amdSec (use first amdSec)
        print('Adding reingestion event to', event.file_uuid_id)
        f = event.file_uuid
        rel_path = f.currentlocation.replace('%SIPDirectory%', '', 1).replace('%transferDirectory%', '', 1)
        file_elem = root.xpath('mets:fileSec/mets:fileGrp/mets:file/mets:FLocat[@xlink:href="' + rel_path + '"]/ancestor::mets:file', namespaces=ns.NSMAP)[0]
        amdid = file_elem.get('ADMID').split()[0]
        print(event.file_uuid_id, 'has amdSec with ADMID', amdid)
        amdsec = root.find('mets:amdSec[@ID="' + amdid + '"]', namespaces=ns.NSMAP)

        # Add event after digiprovMD
        digiprov_counter += 1
        digiprovid = 'digiprovMD_%s' % digiprov_counter
        digiprovMD = etree.Element(ns.metsBNS + "digiprovMD", ID=digiprovid)

        createmets2.createEvent(digiprovMD, event)

        # Add digiprovMD after other event digiprovMDs
        amdsec.xpath('mets:digiprovMD/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]/parent::mets:digiprovMD', namespaces=ns.NSMAP)[-1].addnext(digiprovMD)

        # Add agent if it's not already in this amdSec
        if agent and not amdsec.xpath('.//mets:mdWrap[@MDTYPE="PREMIS:AGENT"]//premis:agentIdentifierValue[text()="' + agent.identifiervalue + '"]', namespaces=ns.NSMAP):
            print('Adding Agent for', agent.identifiervalue)
            digiprov_counter += 1
            digiprovid = 'digiprovMD_%s' % digiprov_counter
            digiprovMD = etree.Element(ns.metsBNS + "digiprovMD", ID=digiprovid, )
            mdWrap = etree.SubElement(digiprovMD, ns.metsBNS + "mdWrap", MDTYPE='PREMIS:AGENT')
            xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
            xmlData.append(createmets2.createAgent(
                agent.identifiertype, agent.identifiervalue,
                agent.name, agent.agenttype))
            # Add digiprovMD after other agent digiprovMDs
            amdsec.xpath('mets:digiprovMD/mets:mdWrap[@MDTYPE="PREMIS:AGENT"]/parent::mets:digiprovMD', namespaces=ns.NSMAP)[-1].addnext(digiprovMD)

    return root


def add_new_files(root, sip_uuid, sip_dir, now):
    """
    Add new metadata files to structMap, fileSec.  Add new amdSecs??? What events?  Parse files to add metadata to METS.
    """
    return root


def update_mets(sip_dir, sip_uuid):
    old_mets_path = os.path.join(
        sip_dir,
        'objects',
        'submissionDocumentation',
        'METS.' + sip_uuid + '.xml')
    print('Looking for old METS at path', old_mets_path)
    # Discard whitespace now so when printing later formats correctly
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(old_mets_path, parser=parser)
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat('T')

    update_header(root, now)
    update_dublincore(root, sip_uuid, now)
    update_rights(root, sip_uuid, now)
    add_events(root, sip_uuid)
    add_new_files(root, sip_uuid, sip_dir, now)

    # Delete original METS

    return root

if __name__ == '__main__':
    tree = update_mets(*sys.argv[1:])
    tree.write('mets.xml', pretty_print=True)
