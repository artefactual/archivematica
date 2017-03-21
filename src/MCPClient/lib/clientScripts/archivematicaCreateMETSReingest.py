#!/usr/bin/env python2
from __future__ import print_function
import copy
from datetime import datetime
from lxml import etree
import os
import sys

import metsrw

import archivematicaCreateMETS2 as createmets2
import archivematicaCreateMETSRights as createmetsrights
import archivematicaCreateMETSMetadataCSV as createmetscsv
import namespaces as ns

# dashboard
from main import models


def update_object(mets, sip_uuid):
    """
    Updates PREMIS:OBJECT.

    Updates techMD if any of the following have changed:
        - checksumtype,
        - identification,
        - characterization,
        - preservation derivative.
    Most recent has STATUS='current', all others have STATUS='superseded'
    """

    # Iterate through original files (from mets:structMap)
    for fsentry in mets.all_files():
        # Only update original files
        if (    fsentry.use != 'original' or
                fsentry.type != 'Item' or
                not fsentry.file_uuid):
            continue

        # Copy techMD
        old_techmd = None
        for t in fsentry.amdsecs[0].subsections:
            if (    t.subsection == 'techMD' and
                    (not t.status or t.status == 'current')):
                old_techmd = t
                break
        new_techmd_contents = copy.deepcopy(old_techmd.contents.document)
        modified = False

        # TODO do this with metsrw & PREMIS plugin
        # If checksum recalculated event exists, update checksum
        if models.Event.objects.filter(file_uuid_id=fsentry.file_uuid, event_type='message digest calculation').exists():
            print('Updating checksum for', fsentry.file_uuid)
            modified = True
            f = models.File.objects.get(uuid=fsentry.file_uuid)
            fixity = new_techmd_contents.find('.//premis:fixity', namespaces=ns.NSMAP)
            fixity.find('premis:messageDigestAlgorithm', namespaces=ns.NSMAP).text = f.checksumtype
            fixity.find('premis:messageDigest', namespaces=ns.NSMAP).text = f.checksum

        # If FileID exists, update file ID
        if models.FileID.objects.filter(file_id=fsentry.file_uuid):
            print('Updating format for', fsentry.file_uuid)
            modified = True
            # Delete old formats
            for f in new_techmd_contents.findall('premis:objectCharacteristics/premis:format', namespaces=ns.NSMAP):
                f.getparent().remove(f)
            # Insert new formats after size
            formats = createmets2.create_premis_object_formats(fsentry.file_uuid)
            size_elem = new_techmd_contents.find('premis:objectCharacteristics/premis:size', namespaces=ns.NSMAP)
            for f in formats:
                size_elem.addnext(f)

        # If FPCommand output exists, update objectCharacteristicsExtension
        if models.FPCommandOutput.objects.filter(file_id=fsentry.file_uuid, rule__purpose__in=['characterization', 'default_characterization']).exists():
            print('Updating objectCharacteristicsExtension for', fsentry.file_uuid)
            modified = True
            # Delete old objectCharacteristicsExtension
            for oce in new_techmd_contents.findall('premis:objectCharacteristics/premis:objectCharacteristicsExtension', namespaces=ns.NSMAP):
                oce.getparent().remove(oce)
            new_oce = createmets2.create_premis_object_characteristics_extensions(fsentry.file_uuid)
            oc_elem = new_techmd_contents.find('premis:objectCharacteristics', namespaces=ns.NSMAP)
            for oce in new_oce:
                oc_elem.append(oce)

        # If Derivation exists, update relationships
        if models.Derivation.objects.filter(source_file_id=fsentry.file_uuid, event__isnull=False):
            print('Updating relationships for', fsentry.file_uuid)
            modified = True
            # Delete old relationships
            for r in new_techmd_contents.findall('premis:relationship', namespaces=ns.NSMAP):
                r.getparent().remove(r)
            derivations = createmets2.create_premis_object_derivations(fsentry.file_uuid)
            for r in derivations:
                new_techmd_contents.append(r)

        if modified:
            new_techmd = fsentry.add_premis_object(new_techmd_contents)
            old_techmd.replace_with(new_techmd)

    return mets

def update_dublincore(mets, sip_uuid):
    """
    Add new dmdSec for updated Dublin Core info relating to entire SIP.

    Case: No DC in DB, no DC in METS: Do nothing
    Case: No DC in DB, DC in METS: Mark as deleted.
    Case: DC in DB is untouched (METADATA_STATUS_REINGEST): Do nothing
    Case: New DC in DB with METADATA_STATUS_ORIGINAL: Add new DC
    Case: DC in DB with METADATA_STATUS_UPDATED: mark old, create updated
    """

    # Check for DC in DB with METADATA_STATUS_UPDATED or METADATA_STATUS_ORIGINAL
    untouched = models.DublinCore.objects.filter(
        metadataappliestoidentifier=sip_uuid,
        metadataappliestotype_id=createmets2.SIPMetadataAppliesToType,
        status=models.METADATA_STATUS_REINGEST).exists()
    if untouched:
        # No new or updated DC found - return early
        print('No updated or new DC metadata found')
        return mets

    # Get structMap element related to SIP DC info
    objects_div = mets.get_file(label='objects', type='Directory')
    print('Existing dmdIds for DC metadata:', objects_div.dmdids)

    # Create element
    dc_elem = createmets2.getDublinCore(createmets2.SIPMetadataAppliesToType, sip_uuid)

    if dc_elem is None:
        if objects_div.dmdsecs:
            print('DC metadata was deleted')
            # Create 'deleted' DC element
            dc_elem = etree.Element(ns.dctermsBNS + "dublincore", nsmap={"dcterms": ns.dctermsNS, 'dc': ns.dcNS})
            dc_elem.set(ns.xsiBNS + "schemaLocation", ns.dctermsNS + " http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd")
        else:
            # No new or updated DC found - return early
            print('No updated or new DC metadata found')
            return mets
    dmdsec = objects_div.add_dublin_core(dc_elem)
    print('Adding new DC in dmdSec with ID', dmdsec.id_string())
    if len(objects_div.dmdsecs) > 1:
        objects_div.dmdsecs[-2].replace_with(dmdsec)

    return mets


def update_rights(mets, sip_uuid):
    """
    Add rightsMDs for updated PREMIS Rights.
    """
    # Get original files to add rights to
    original_files = [f for f in mets.all_files() if f.use == 'original']

    # Check for deleted rights - exist in METS but not in DB
    # Cache rightsbasis in DB
    rightsmds_db = {}  # memoize
    for rightsbasis in models.RightsStatement.RIGHTS_BASIS_CHOICES:
        # ORIGINAL RightsStatements are unrelated to the old one.
        rightsmds_db[rightsbasis[0]] = models.RightsStatement.objects.filter(
            metadataappliestoidentifier=sip_uuid,
            metadataappliestotype_id=createmets2.SIPMetadataAppliesToType,
            rightsbasis=rightsbasis[0],
        ).exclude(status=models.METADATA_STATUS_ORIGINAL)

    for fsentry in original_files:
        rightsmds = [s for s in fsentry.amdsecs[0].subsections if s.subsection == 'rightsMD']
        for r in rightsmds:
            if r.status == 'superseded':
                continue
            rightsbasis = r.contents.document.findtext('.//premis:rightsBasis', namespaces=ns.NSMAP)
            if rightsbasis == 'Other':
                rightsbasis = r.contents.document.findtext('.//premis:otherRightsBasis', namespaces=ns.NSMAP)
            db_rights = rightsmds_db[rightsbasis]
            if not db_rights:  # TODO this may need to be more robust for RightsStatementRightsGranted
                print('Rights', r.id_string(), 'looks deleted - making superseded')
                r.status = 'superseded'

    # Check for newly added rights
    rights_list = models.RightsStatement.objects.filter(
        metadataappliestoidentifier=sip_uuid,
        metadataappliestotype_id=createmets2.SIPMetadataAppliesToType,
        status=models.METADATA_STATUS_ORIGINAL
    )
    if not rights_list:
        print('No new rights added')
    else:
        add_rights_elements(rights_list, original_files)

    # Check for updated rights
    rights_list = models.RightsStatement.objects.filter(
        metadataappliestoidentifier=sip_uuid,
        metadataappliestotype_id=createmets2.SIPMetadataAppliesToType,
        status=models.METADATA_STATUS_UPDATED
    )
    if not rights_list:
        print('No updated rights found')
    else:
        add_rights_elements(rights_list, original_files, updated=True)

    return mets


def add_rights_elements(rights_list, files, updated=False):
    """
    Create and add rightsMDs for everything in rights_list to files.
    """
    # Add to files' amdSecs
    for fsentry in files:
        for rights in rights_list:
            # Create element
            new_rightsmd = fsentry.add_premis_rights(createmetsrights.createRightsStatement(rights, fsentry.file_uuid))
            print('Adding rightsMD', new_rightsmd.id_string(), 'to amdSec with ID', fsentry.amdsecs[0].id_string(), 'for file', fsentry.file_uuid)

            if updated:
                # Mark as replacing another rightsMD
                # rightsBasis is semantically unique (though not currently enforced in code). Assume that this replaces a rightsMD with the same basis
                # Find the most ce
                superseded = [s for s in fsentry.amdsecs[0].subsections if s.subsection == 'rightsMD']
                superseded = sorted(superseded, key=lambda x: x.created)
                # NOTE sort(..., reverse=True) behaves differently with unsortable elements like '' and None
                for s in superseded[::-1]:
                    print('created', s.created)
                    if s.serialize().xpath('.//premis:rightsBasis[text()="' + rights.rightsbasis + '"]', namespaces=ns.NSMAP):
                        s.replace_with(new_rightsmd)
                        print('rightsMD', new_rightsmd.id_string(), 'replaces rightsMD', s.id_string())
                        break


def add_events(mets, sip_uuid):
    """
    Add reingest events for all existing files.
    """
    # Get all events for files in this SIP
    events = models.Event.objects.filter(file_uuid__sip__uuid=sip_uuid)

    # Get Agent
    try:
        agent = models.Agent.objects.get(identifiertype="preservation system", name="Archivematica", agenttype="software")
    except models.Agent.DoesNotExist:
        agent = None
    except models.Agent.MultipleObjectsReturned:
        agent = None
        print('WARNING multiple agents found for Archivematica')

    needs_agent = set()

    for event in events:
        print('Adding', event.event_type, 'event to file', event.file_uuid_id)
        fsentry = mets.get_file(file_uuid=event.file_uuid_id)
        if fsentry is None:
            fsentry = mets.get_deleted_file(file_uuid=event.file_uuid_id)
        if fsentry is None:
            print('File with UUID', event.file_uuid_id,
                  'not in METS file, skipping adding', event.event_type,
                  'event.')
            continue
        fsentry.add_premis_event(createmets2.createEvent(event))

        amdsec = fsentry.amdsecs[0]

        # Add agent if it's not already in this amdSec
        if agent and not mets.tree.xpath(
                'mets:amdSec[@AMDID="' + amdsec.id_string() +
                '"]//mets:mdWrap[@MDTYPE="PREMIS:AGENT"]'
                '//premis:agentIdentifierValue[text()="' +
                agent.identifiervalue + '"]', namespaces=ns.NSMAP):
            needs_agent.add(fsentry)

    for fsentry in needs_agent:
        print('Adding Agent for', agent.identifiervalue)
        fsentry.add_premis_agent(createmets2.createAgent(agent))

    return mets


def add_new_files(mets, sip_uuid, sip_dir):
    """
    Add new files to structMap, fileSec.

    This supports adding new metadata or preservation files.

    If a new file is a metadata.csv, parse it to create dmdSecs.
    """
    # Find new files
    # How tell new file from old with same name? Check hash?
    # QUESTION should the metadata.csv be parsed and only updated if different even if one already existed?
    new_files = []
    old_mets_rel_path = _get_old_mets_rel_path(sip_uuid)
    metadata_csv = None
    objects_dir = os.path.join(sip_dir, 'objects')
    for dirpath, _, filenames in os.walk(objects_dir):
        for filename in filenames:
            # Find in METS
            current_loc = os.path.join(dirpath, filename).replace(
                sip_dir, '%SIPDirectory%', 1)
            rel_path = current_loc.replace('%SIPDirectory%', '', 1)
            print('Looking for', rel_path, 'in METS')
            fsentry = mets.get_file(path=rel_path)
            if fsentry is None:
                # If not in METS (and is not old METS), get File object and
                # store for later
                if rel_path != old_mets_rel_path:
                    print(rel_path, 'not found in METS, must be new file')
                    f = models.File.objects.get(
                        currentlocation=current_loc, sip_id=sip_uuid)
                    new_files.append(f)
                    if rel_path == 'objects/metadata/metadata.csv':
                        metadata_csv = f
            else:
                print(rel_path, 'found in METS, no further work needed')

    if not new_files:
        return mets

    # Set global counters so getAMDSec will work
    createmets2.globalAmdSecCounter = int(mets.tree.xpath('count(mets:amdSec)', namespaces=ns.NSMAP))
    createmets2.globalTechMDCounter = int(mets.tree.xpath('count(mets:amdSec/mets:techMD)', namespaces=ns.NSMAP))
    createmets2.globalDigiprovMDCounter = int(mets.tree.xpath('count(mets:amdSec/mets:digiprovMD)', namespaces=ns.NSMAP))

    objects_fsentry = mets.get_file(label='objects', type='Directory')

    for f in new_files:
        # Create amdSecs
        print('Adding amdSec for', f.currentlocation, '(', f.uuid, ')')
        amdsec, amdid = createmets2.getAMDSec(
            fileUUID=f.uuid,
            filePath=None,  # Only needed if use=original
            use=f.filegrpuse,
            type=None,  # Not used
            sip_uuid=sip_uuid,
            transferUUID=None,  # Only needed if use=original
            itemdirectoryPath=None,  # Only needed if use=original
            typeOfTransfer=None,  # Only needed if use=original
            baseDirectoryPath=sip_dir,
        )
        print(f.uuid, 'has amdSec with ID', amdid)

        # Create parent directories if needed
        dirs = os.path.dirname(f.currentlocation.replace('%SIPDirectory%objects/', '', 1)).split('/')
        parent_fsentry = objects_fsentry
        for dirname in (d for d in dirs if d):
            child = mets.get_file(type='Directory', label=dirname)
            if child is None:
                child = metsrw.FSEntry(
                    path=None,
                    type='Directory',
                    label=dirname,
                )
                parent_fsentry.add_child(child)
            parent_fsentry = child

        derived_from = None
        if f.original_file_set.exists():
            original_f = f.original_file_set.get().source_file
            derived_from = mets.get_file(file_uuid=original_f.uuid)
        entry = metsrw.FSEntry(
            path=f.currentlocation.replace('%SIPDirectory%', '', 1),
            use=f.filegrpuse,
            type='Item',
            file_uuid=f.uuid,
            derived_from=derived_from,
        )
        metsrw_amdsec = metsrw.AMDSec(tree=amdsec, section_id=amdid)
        entry.amdsecs.append(metsrw_amdsec)
        parent_fsentry.add_child(entry)

    # Parse metadata.csv and add dmdSecs
    if metadata_csv:
        mets = update_metadata_csv(mets, metadata_csv, sip_uuid, sip_dir)

    return mets


def delete_files(mets, sip_uuid):
    """
    Update METS for deleted files.

    Add a deletion event, update fileGrp USE to deleted, and remove FLocat.
    """
    deleted_files = models.File.objects.filter(
        sip_id=sip_uuid,
        event__event_type='deletion',
    ).values_list('uuid', flat=True)
    for file_uuid in deleted_files:
        df = mets.get_file(file_uuid=file_uuid)
        df.use = 'deleted'
        df.path = None
        df.label = None
    return mets


def update_metadata_csv(mets, metadata_csv, sip_uuid, sip_dir):
    print('Parse new metadata.csv')
    full_path = metadata_csv.currentlocation.replace('%SIPDirectory%', sip_dir, 1)
    csvmetadata = createmetscsv.parseMetadataCSV(full_path)

    # FIXME This doesn't support having both DC and non-DC metadata in dmdSecs
    # If createDmdSecsFromCSVParsedMetadata returns more than 1 dmdSec, behaviour is undefined
    for f, md in csvmetadata.items():
        # Verify file is in AIP
        print('Looking for', f, 'from metadata.csv in SIP')
        # Find File with original or current locationg matching metadata.csv
        # Prepend % to match the end of %SIPDirectory% or %transferDirectory%
        try:
            file_obj = models.File.objects.get(sip_id=sip_uuid, originallocation__endswith='%' + f)
        except models.File.DoesNotExist:
            try:
                file_obj = models.File.objects.get(sip_id=sip_uuid, currentlocation__endswith='%' + f)
            except models.File.DoesNotExist:
                print(f, 'not found in database')
                continue
        print(f, 'found in database')

        fsentry = mets.get_file(file_uuid=file_obj.uuid)
        print(f, 'was associated with', fsentry.dmdids)

        # Create dmdSec
        new_dmdsecs = createmets2.createDmdSecsFromCSVParsedMetadata(md)
        # Add both
        for new_dmdsec in new_dmdsecs:
            # need to strip new_d to just the DC part
            new_dc = new_dmdsec.find('.//dcterms:dublincore', namespaces=ns.NSMAP)
            new_metsrw_dmdsec = fsentry.add_dublin_core(new_dc)
            if len(fsentry.dmdsecs) > 1:
                fsentry.dmdsecs[-2].replace_with(new_metsrw_dmdsec)

        print(f, 'now associated with', fsentry.dmdids)

    return mets


def _get_old_mets_rel_path(sip_uuid):
    return os.path.join(
        'objects',
        'submissionDocumentation',
        'METS.' + sip_uuid + '.xml')


class ModifiedMETSDocument(metsrw.METSDocument):
    """This is a monkey-patching of ``metsrw.METSDocument``. These changes, if
    approved, should be merged into metsrw itself. The main conceptual change
    is that deleted files from the fileSec of an input METS are retained in the
    output METS when ``.serialize()`` is called.
    """

    def serialize(self, fully_qualified=True):
        """Override superclass's ``serialize`` by adding deleted files to the
        set of files used to serialize the metsrw document to a METS.xml
        document.
        TODO: merge this method override into metsrw.
        """
        now = datetime.utcnow().replace(microsecond=0).isoformat('T')
        files = self.all_files()
        files = files | set(self.all_deleted_files())
        mdsecs = self._collect_mdsec_elements(files)
        root = self._document_root(fully_qualified=fully_qualified)
        root.append(self._mets_header(now=now))
        for section in mdsecs:
            root.append(section.serialize(now=now))
        root.append(self._filesec(files))
        root.append(self._structmap())
        return root

    def all_deleted_files(self):
        return self._deleted_root_elements

    def get_deleted_file(self, **kwargs):
        for entry in self.all_deleted_files():
            if all(value == getattr(entry, key) for key, value in
                   kwargs.items()):
                return entry
        return None

    def __init__(self):
        super(ModifiedMETSDocument, self).__init__()
        self._deleted_root_elements = []

    def _parse_tree(self, tree=None):
        """Extend ``_parse_tree`` by creating an instance attribute
        ``self._deleted_root_elements``, which is a list of ``FSEntry``
        instances representing the deleted files from the mets:fileSec.
        """
        super(ModifiedMETSDocument, self)._parse_tree(tree)
        # Populate ``self._deleted_root_elements`` with a set of FSEntry
        # instances, one for each deleted mets:file in
        # mets:fileSec/mets:fileGrp[@USE="deleted"]/
        tree = self.tree
        deleted_filesec_files = tree.findall(
            'mets:fileSec/mets:fileGrp[@USE="deleted"]/mets:file',
            namespaces=metsrw.utils.NAMESPACES)
        self._deleted_root_elements = self._parse_deleted_filesec_files(
            tree, deleted_filesec_files)
        # Associated derived files
        for entry in self.all_deleted_files():
            entry.derived_from = self.get_file(
                file_uuid=entry.derived_from, type='Item')
            if entry.derived_from is None:
                # Is it possible for a deleted file to be derived from another
                # deleted file?
                entry.derived_from = self.get_deleted_file(
                    file_uuid=entry.derived_from, type='Item')

    def _parse_deleted_filesec_files(self, tree, deleted_filesec_files):
        """Return a list of ``metsrw.FSEntry`` instances given a list of
        ``lxml.Element`` instances in ``deleted_filesec_files`` representing
        deleted files.
        """
        result = []
        for file_elem in deleted_filesec_files:
            path = label = file_uuid = derived_from = amdids = checksum = \
                checksumtype = None
            file_id = file_elem.get('ID')
            file_uuid = file_id.replace(metsrw.utils.FILE_ID_PREFIX, '', 1)
            group_uuid = file_elem.get('GROUPID', '').replace(
                metsrw.utils.GROUP_ID_PREFIX, '', 1)
            if group_uuid != file_uuid:
                derived_from = group_uuid  # Use group_uuid as placeholder
            amdids = file_elem.get('ADMID')
            checksum = file_elem.get('CHECKSUM')
            checksumtype = file_elem.get('CHECKSUMTYPE')
            # Create FSEntry
            fs_entry = metsrw.fsentry.FSEntry(
                path=path,
                label=label,
                use='deleted',
                type='Item',
                children=[],
                file_uuid=file_uuid,
                derived_from=derived_from,
                checksum=checksum,
                checksumtype=checksumtype)
            # Assuming that a deleted mets:file has no corresponding dmdSec
            # elements. Valid assumption?
            # Add AMDSecs
            if amdids:
                amdids = amdids.split()
                for amdid in amdids:
                    amdsec_elem = tree.find(
                        'mets:amdSec[@ID="' + amdid + '"]',
                        namespaces=metsrw.utils.NAMESPACES)
                    amdsec = metsrw.metadata.AMDSec.parse(amdsec_elem)
                    fs_entry.amdsecs.append(amdsec)
            result.append(fs_entry)
        return result


def update_mets(sip_dir, sip_uuid):
    """Updates the METS file (of the SIP with UUID ``sip_uuid``) that is stored
    on disk at <sip_dir>/objects/submissionDocumentation/METS.<sip_uuid>.xml
    """

    old_mets_path = os.path.join(sip_dir, _get_old_mets_rel_path(sip_uuid))
    print('Looking for old METS at path', old_mets_path)

    # Parse old METS
    # mets = metsrw.METSDocument.fromfile(old_mets_path)
    # TODO: merge ModifiedMETSDocument changes into metsrw library
    mets = ModifiedMETSDocument.fromfile(old_mets_path)

    update_object(mets, sip_uuid)
    update_dublincore(mets, sip_uuid)
    update_rights(mets, sip_uuid)
    add_events(mets, sip_uuid)
    add_new_files(mets, sip_uuid, sip_dir)
    delete_files(mets, sip_uuid)

    # Delete original METS

    return mets.serialize()

if __name__ == '__main__':
    tree = update_mets(*sys.argv[1:])
    tree.write('mets.xml', pretty_print=True)
