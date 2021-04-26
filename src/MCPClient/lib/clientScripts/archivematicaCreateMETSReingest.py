#!/usr/bin/env python2
import copy
from lxml import etree
import os

import metsrw
import scandir

import create_mets_v2 as createmets2
import archivematicaCreateMETSRights as createmetsrights
import archivematicaCreateMETSMetadataCSV as createmetscsv
import namespaces as ns

# dashboard
from main import models

from django.utils import six


def _create_premis_object(premis_object_type):
    """Return new PREMIS element container (``lxml._Element`` instance).

    It uses the latest version of PREMIS available and the ``premis`` prefix.
    """
    allowed_types = ("file", "representation", "bitstream", "intellectualEntity")
    if premis_object_type not in allowed_types:
        raise ValueError("Object type used is not listed in objectComplexType")
    return etree.Element(
        ns.premisBNS + "object",
        {
            etree.QName(ns.xsiNS, "schemaLocation"): "%s %s"
            % (ns.premisNS, "https://www.loc.gov/standards/premis/premis.xsd"),
            "{http://www.w3.org/2001/XMLSchema-instance}type": "premis:{}".format(
                premis_object_type
            ),
            "version": "3.0",
        },
        nsmap={"premis": ns.premisNS},
    )


def _update_premis_object(premis_elem, premis_object_type):
    """Ensure that a PREMIS container uses the latest version of PREMIS.

    If PREMIS 2 is found, a new container is returned instead using PREMIS 3.
    The contents from the original element are transferred and updated.
    """
    if premis_elem.tag == ns.premisBNS + "object":
        return premis_elem
    if premis_elem.tag != ns.premisBNS_V2 + "object":
        raise ValueError("elem has an unexpected tag name")
    new_elem = _create_premis_object(premis_object_type)
    # Update namespace in descendants.
    premis_bns_v2_len = len(ns.premisBNS_V2)
    for child in premis_elem.iter():
        # `None` is for old Archivematica METS where the elements did not use
        # prefixes.
        if child.prefix not in ("premis", None):
            continue
        if not child.tag.startswith(ns.premisBNS_V2):
            continue
        child.tag = ns.premisBNS + child.tag[premis_bns_v2_len:]
    # Transfer contents.
    for child in premis_elem.iterchildren():
        new_elem.append(child)
    return new_elem


def update_object(job, mets):
    """
    Updates PREMIS:OBJECT.

    Updates techMD if any of the following have changed: checksumtype, identification, characterization, preservation derivative.
    Most recent has STATUS='current', all others have STATUS='superseded'
    """
    # Iterate through original files
    for fsentry in mets.all_files():
        # Only update original files
        if fsentry.use != "original" or fsentry.type != "Item" or not fsentry.file_uuid:
            continue

        # Copy techMD
        old_techmd = None
        for t in fsentry.amdsecs[0].subsections:
            if t.subsection == "techMD" and (not t.status or t.status == "current"):
                old_techmd = t
                break
        new_techmd_contents = _update_premis_object(
            copy.deepcopy(old_techmd.contents.document), "file"
        )
        modified = False

        # TODO do this with metsrw & PREMIS plugin
        # If checksum recalculated event exists, update checksum
        if models.Event.objects.filter(
            file_uuid_id=fsentry.file_uuid, event_type="message digest calculation"
        ).exists():
            job.pyprint("Updating checksum for", fsentry.file_uuid)
            modified = True
            f = models.File.objects.get(uuid=fsentry.file_uuid)
            fixity = new_techmd_contents.find(".//premis:fixity", namespaces=ns.NSMAP)
            fixity.find(
                "premis:messageDigestAlgorithm", namespaces=ns.NSMAP
            ).text = f.checksumtype
            fixity.find("premis:messageDigest", namespaces=ns.NSMAP).text = f.checksum

        # If FileID exists, update file ID
        if models.FileID.objects.filter(file_id=fsentry.file_uuid):
            job.pyprint("Updating format for", fsentry.file_uuid)
            modified = True
            # Delete old formats
            for f in new_techmd_contents.findall(
                "premis:objectCharacteristics/premis:format", namespaces=ns.NSMAP
            ):
                f.getparent().remove(f)
            # Insert new formats after size
            formats = createmets2.create_premis_object_formats(fsentry.file_uuid)
            size_elem = new_techmd_contents.find(
                "premis:objectCharacteristics/premis:size", namespaces=ns.NSMAP
            )
            for f in formats:
                size_elem.addnext(f)

        # If FPCommand output exists, update objectCharacteristicsExtension
        if models.FPCommandOutput.objects.filter(
            file_id=fsentry.file_uuid,
            rule__purpose__in=["characterization", "default_characterization"],
        ).exists():
            job.pyprint(
                "Updating objectCharacteristicsExtension for", fsentry.file_uuid
            )
            modified = True
            # Delete old objectCharacteristicsExtension
            for oce in new_techmd_contents.findall(
                "premis:objectCharacteristics/premis:objectCharacteristicsExtension",
                namespaces=ns.NSMAP,
            ):
                oce.getparent().remove(oce)
            new_oce = createmets2.create_premis_object_characteristics_extensions(
                fsentry.file_uuid
            )
            oc_elem = new_techmd_contents.find(
                "premis:objectCharacteristics", namespaces=ns.NSMAP
            )
            for oce in new_oce:
                oc_elem.append(oce)

        # If Derivation exists, update relationships
        if models.Derivation.objects.filter(
            source_file_id=fsentry.file_uuid, event__isnull=False
        ):
            job.pyprint("Updating relationships for", fsentry.file_uuid)
            modified = True
            # Delete old relationships
            for r in new_techmd_contents.findall(
                "premis:relationship", namespaces=ns.NSMAP
            ):
                r.getparent().remove(r)
            derivations = createmets2.create_premis_object_derivations(
                fsentry.file_uuid
            )
            for r in derivations:
                new_techmd_contents.append(r)

        if modified:
            new_techmd = fsentry.add_premis_object(new_techmd_contents)
            old_techmd.replace_with(new_techmd)

    return mets


def update_dublincore(job, mets, sip_uuid):
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
        status=models.METADATA_STATUS_REINGEST,
    ).exists()
    if untouched:
        # No new or updated DC found - return early
        job.pyprint("No updated or new DC metadata found")
        return mets

    # Get structMap element related to SIP DC info
    objects_div = mets.get_file(label="objects", type="Directory")
    job.pyprint("Existing dmdIds for DC metadata:", objects_div.dmdids)

    # Create element
    dc_elem = createmets2.getDublinCore(createmets2.SIPMetadataAppliesToType, sip_uuid)

    if dc_elem is None:
        if objects_div.dmdsecs:
            job.pyprint("DC metadata was deleted")
            # Create 'deleted' DC element
            dc_elem = etree.Element(
                ns.dctermsBNS + "dublincore",
                nsmap={"dcterms": ns.dctermsNS, "dc": ns.dcNS},
            )
            dc_elem.set(
                ns.xsiBNS + "schemaLocation",
                ns.dctermsNS
                + " http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd",
            )
        else:
            # No new or updated DC found - return early
            job.pyprint("No updated or new DC metadata found")
            return mets
    dmdsec = objects_div.add_dublin_core(dc_elem)
    job.pyprint("Adding new DC in dmdSec with ID", dmdsec.id_string)
    if len(objects_div.dmdsecs) > 1:
        objects_div.dmdsecs[-2].replace_with(dmdsec)

    return mets


def update_rights(job, mets, sip_uuid, state):
    """
    Add rightsMDs for updated PREMIS Rights.
    """
    # Get original files to add rights to
    original_files = [f for f in mets.all_files() if f.use == "original"]

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
        rightsmds = [
            s for s in fsentry.amdsecs[0].subsections if s.subsection == "rightsMD"
        ]
        for r in rightsmds:
            # Don't follow MDRef pointers (see #1083 for more details).
            if isinstance(r.contents, metsrw.metadata.MDRef):
                continue
            if r.status == "superseded":
                continue
            rightsbasis = ns.xml_find_premis(
                r.contents.document, ".//premis:rightsBasis"
            )
            if rightsbasis is None:
                continue
            basis = rightsbasis.text
            if basis == "Other":
                otherrightsbasis = ns.xml_find_premis(
                    r.contents.document, ".//premis:otherRightsBasis"
                )
                if otherrightsbasis is not None:
                    basis = otherrightsbasis.text
            db_rights = rightsmds_db[basis]
            if (
                not db_rights
            ):  # TODO this may need to be more robust for RightsStatementRightsGranted
                job.pyprint("Rights", r.id_string, "looks deleted - making superseded")
                r.status = "superseded"

    # Check for newly added rights
    rights_list = models.RightsStatement.objects.filter(
        metadataappliestoidentifier=sip_uuid,
        metadataappliestotype_id=createmets2.SIPMetadataAppliesToType,
        status=models.METADATA_STATUS_ORIGINAL,
    )
    if not rights_list:
        job.pyprint("No new rights added")
    else:
        add_rights_elements(job, rights_list, original_files, state)

    # Check for updated rights
    rights_list = models.RightsStatement.objects.filter(
        metadataappliestoidentifier=sip_uuid,
        metadataappliestotype_id=createmets2.SIPMetadataAppliesToType,
        status=models.METADATA_STATUS_UPDATED,
    )
    if not rights_list:
        job.pyprint("No updated rights found")
    else:
        add_rights_elements(job, rights_list, original_files, state, updated=True)

    return mets


def add_rights_elements(job, rights_list, files, state, updated=False):
    """
    Create and add rightsMDs for everything in rights_list to files.
    """
    # Add to files' amdSecs
    for fsentry in files:
        for rights in rights_list:
            # Create element
            new_rightsmd = fsentry.add_premis_rights(
                createmetsrights.createRightsStatement(
                    job, rights, fsentry.file_uuid, state
                )
            )
            job.pyprint(
                "Adding rightsMD",
                new_rightsmd.id_string,
                "to amdSec with ID",
                fsentry.amdsecs[0].id_string,
                "for file",
                fsentry.file_uuid,
            )

            if updated:
                # Mark as replacing another rightsMD
                # rightsBasis is semantically unique (though not currently enforced in code). Assume that this replaces a rightsMD with the same basis
                # Find the most ce
                superseded = [
                    s
                    for s in fsentry.amdsecs[0].subsections
                    if s.subsection == "rightsMD"
                ]
                superseded = sorted(
                    superseded, key=lambda x: (x.created is not None, x.created)
                )
                # NOTE sort(..., reverse=True) behaves differently with unsortable elements like '' and None
                for rightmd in superseded[::-1]:
                    job.pyprint("created", rightmd.created)
                    if ns.xml_xpath_premis(
                        rightmd.serialize(),
                        './/premis:rightsBasis[text()="' + rights.rightsbasis + '"]',
                    ):
                        rightmd.replace_with(new_rightsmd)
                        job.pyprint(
                            "rightsMD",
                            new_rightsmd.id_string,
                            "replaces rightsMD",
                            rightmd.id_string,
                        )
                        break


def _extract_event_agents(fsentry):
    """Find linked agents that have not been described yet.

    When altering PREMIS events for a filesystem entry, it is likely to end up
    with an incomplete set of PREMIS agents. This function returns the linked
    agents that have no corresponding PREMIS agents yet defined.
    """
    agents, orphans = set(), set()

    for premis_agent in fsentry.get_premis_agents():
        for identifier in premis_agent.agent_identifier:
            agents.add(
                (identifier.agent_identifier_type, identifier.agent_identifier_value)
            )

    for premis_event in fsentry.get_premis_events():
        for linking_agent in premis_event.linking_agent_identifier:
            item = (
                linking_agent.linking_agent_identifier_type,
                linking_agent.linking_agent_identifier_value,
            )
            if item in agents:
                continue
            orphans.add(item)

    return orphans


def add_events(job, mets, sip_uuid):
    """
    Add reingest events for all existing files.
    """
    fsentries = {item.file_uuid: item for item in mets.all_files()}
    visited = {}  # Not using a set because FSEntry is not hashable.
    agents = {
        (agent.identifiertype, agent.identifiervalue): agent
        for agent in models.Agent.objects.extend_queryset_with_preservation_system(
            models.Agent.objects.all()
        )
    }

    # Add PREMIS events.
    for event in models.Event.objects.filter(file_uuid__sip__uuid=sip_uuid).iterator():
        job.pyprint("Adding", event.event_type, "event to file", event.file_uuid_id)
        try:
            fsentry = fsentries[event.file_uuid_id]
        except KeyError:
            job.pyprint(
                "File with UUID",
                event.file_uuid_id,
                "not in METS file, skipping adding",
                event.event_type,
                "event.",
            )
            continue
        if fsentry.file_uuid not in visited:
            visited[fsentry.file_uuid] = fsentry
        fsentry.add_premis_event(createmets2.createEvent(event))

    # Add PREMIS agents.
    for fsentry in six.itervalues(visited):
        for identifier_type, identifier_value in _extract_event_agents(fsentry):
            try:
                agent = agents[(identifier_type, identifier_value)]
            except KeyError:
                continue
            job.pyprint("Adding Agent for", agent.identifiervalue)
            fsentry.add_premis_agent(createmets2.createAgent(agent))

    return mets


def add_new_files(job, mets, sip_uuid, sip_dir):
    """
    Add new files to structMap, fileSec.

    This supports adding new metadata or preservation files.

    If a new file is a metadata.csv, parse it to create dmdSecs.
    """
    # Find new files
    # How tell new file from old with same name? Check hash?
    # QUESTION should the metadata.csv be parsed and only updated if different
    # even if one already existed?
    new_files = []
    old_mets_rel_path = _get_old_mets_rel_path(sip_uuid)
    metadata_csv = None
    objects_dir = os.path.join(sip_dir, "objects")
    for dirpath, _, filenames in scandir.walk(objects_dir):
        for filename in filenames:
            # Find in METS
            current_loc = os.path.join(dirpath, filename).replace(
                sip_dir, "%SIPDirectory%", 1
            )
            rel_path = current_loc.replace("%SIPDirectory%", "", 1)
            job.pyprint("Looking for", rel_path, "in METS")
            fsentry = mets.get_file(path=rel_path)
            if fsentry is None:
                # If not in METS (and is not old METS), get File object and
                # store for later
                if rel_path != old_mets_rel_path:
                    job.pyprint(rel_path, "not found in METS, must be new file")
                    f = models.File.objects.get(
                        currentlocation=current_loc, sip_id=sip_uuid
                    )
                    new_files.append(f)
                    if rel_path == "objects/metadata/metadata.csv":
                        metadata_csv = f
            else:
                job.pyprint(rel_path, "found in METS, no further work needed")

    if not new_files:
        return mets

    # Set global counters so getAMDSec will work
    state = createmets2.MetsState(
        globalAmdSecCounter=metsrw.AMDSec.get_current_id_count(),
        globalTechMDCounter=metsrw.SubSection.get_current_id_count("techMD"),
        globalDigiprovMDCounter=metsrw.SubSection.get_current_id_count("digiprovMD"),
    )

    objects_fsentry = mets.get_file(label="objects", type="Directory")

    for f in new_files:
        # Create amdSecs
        job.pyprint("Adding amdSec for", f.currentlocation, "(", f.uuid, ")")
        amdsec, amdid = createmets2.getAMDSec(
            job,
            fileUUID=f.uuid,
            filePath=None,  # Only needed if use=original
            use=f.filegrpuse,
            sip_uuid=sip_uuid,
            transferUUID=None,  # Only needed if use=original
            itemdirectoryPath=None,  # Only needed if use=original
            typeOfTransfer=None,  # Only needed if use=original
            baseDirectoryPath=sip_dir,
            state=state,
        )
        job.pyprint(f.uuid, "has amdSec with ID", amdid)

        # Create parent directories if needed
        dirs = os.path.dirname(
            f.currentlocation.replace("%SIPDirectory%objects/", "", 1)
        ).split("/")
        parent_fsentry = objects_fsentry
        for dirname in (d for d in dirs if d):
            child = mets.get_file(type="Directory", label=dirname)
            if child is None:
                child = metsrw.FSEntry(path=None, type="Directory", label=dirname)
                parent_fsentry.add_child(child)
            parent_fsentry = child

        derived_from = None
        if f.original_file_set.exists():
            original_f = f.original_file_set.get().source_file
            derived_from = mets.get_file(file_uuid=original_f.uuid)
        entry = metsrw.FSEntry(
            path=f.currentlocation.replace("%SIPDirectory%", "", 1),
            use=f.filegrpuse,
            type="Item",
            file_uuid=f.uuid,
            derived_from=derived_from,
        )
        metsrw_amdsec = metsrw.AMDSec(tree=amdsec, section_id=amdid)
        entry.amdsecs.append(metsrw_amdsec)
        parent_fsentry.add_child(entry)

    # Parse metadata.csv and add dmdSecs
    if metadata_csv:
        mets = update_metadata_csv(job, mets, metadata_csv, sip_uuid, sip_dir, state)

    return mets


def delete_files(mets, sip_uuid):
    """
    Update METS for deleted files.

    Add a deletion event, update fileGrp USE to deleted, and remove FLocat.
    """
    deleted_files = models.File.objects.filter(
        sip_id=sip_uuid, event__event_type="deletion"
    ).values_list("uuid", flat=True)
    for file_uuid in deleted_files:
        df = mets.get_file(file_uuid=file_uuid)
        df.use = "deleted"
        df.path = None
        df.label = None
    return mets


def _get_directory_fsentry(mets, path):
    """Get a metsrw.FSEntry for a directory path.

    This splits a directory path into parts and starts looking for
    Directory type entries in the metsrw.METSDocument. The starting
    point is the Directory entry that represents the AIP.
    """
    parts = path.split(os.sep)
    parent = mets.get_file(type="Directory", parent=None)
    result = None
    for part in parts:
        child = mets.get_file(type="Directory", label=part, parent=parent)
        if child is None:
            return None
        result = parent = child
    return result


def _replace_original_dmdsec(dmdsecs, new_dmdsec):
    """Given a list of dmdSec elements, replace the original one.

    This implementation assumes the first dmdSec of the list is the
    original one and that all the dmdSec elements are of the same
    MDTYPE.

    A better approach could rely on the CREATED and STATUS attributes
    of each dmdSec and the older and newer attribute and the
    get_status method of the metsrw.SubSecion class. But currently the
    create_mets_v2 clientScript doesn't use metsrw to create the SIP
    METS and doesn't set these attributes.
    """
    if dmdsecs:
        dmdsecs[0].replace_with(new_dmdsec)


def update_metadata_csv(job, mets, metadata_csv, sip_uuid, sip_dir, state):
    job.pyprint("Parse new metadata.csv")
    full_path = metadata_csv.currentlocation.replace("%SIPDirectory%", sip_dir, 1)
    csvmetadata = createmetscsv.parseMetadataCSV(job, full_path)

    # FIXME This doesn't support having both DC and non-DC metadata in dmdSecs
    # If createDmdSecsFromCSVParsedMetadata returns more than 1 dmdSec, behaviour is undefined
    for f, md in csvmetadata.items():
        # Verify file is in AIP
        job.pyprint("Looking for", f, "from metadata.csv in SIP")
        # Find File with original or current locationg matching metadata.csv
        # Prepend % to match the end of %SIPDirectory% or %transferDirectory%
        file_obj = None
        try:
            file_obj = models.File.objects.get(
                sip_id=sip_uuid, originallocation__endswith="%" + f
            )
        except models.File.DoesNotExist:
            try:
                file_obj = models.File.objects.get(
                    sip_id=sip_uuid, currentlocation__endswith="%" + f
                )
            except models.File.DoesNotExist:
                pass
        if file_obj is not None:
            fsentry = mets.get_file(file_uuid=file_obj.uuid)
        else:
            fsentry = _get_directory_fsentry(mets, f)
        if fsentry is None:
            job.pyprint(f, "not found in database or METS file")
            continue

        job.pyprint(f, "found in database or METS file")
        job.pyprint(f, "was associated with", fsentry.dmdids)

        # Save existing dmdSecs
        dc_dmdsecs = []
        non_dc_dmdsecs = []
        for dmdsec in fsentry.dmdsecs:
            mdwrap = dmdsec.contents
            if mdwrap.mdtype == "DC":
                dc_dmdsecs.append(dmdsec)
            elif (
                mdwrap.mdtype == "OTHER"
                and getattr(mdwrap, "othermdtype", None) == "CUSTOM"
            ):
                non_dc_dmdsecs.append(dmdsec)

        # Create dmdSec
        new_dmdsecs = createmets2.createDmdSecsFromCSVParsedMetadata(job, md, state)
        # Add both
        for new_dmdsec in new_dmdsecs:
            # need to strip new_d to just the DC part
            new_dc = new_dmdsec.find(".//dcterms:dublincore", namespaces=ns.NSMAP)
            if new_dc is not None:
                new_metsrw_dmdsec = fsentry.add_dublin_core(new_dc)
                _replace_original_dmdsec(dc_dmdsecs, new_metsrw_dmdsec)
            else:
                new_non_dc = new_dmdsec.find(
                    './/mets:mdWrap[@MDTYPE="OTHER"][@OTHERMDTYPE="CUSTOM"]/mets:xmlData',
                    namespaces=ns.NSMAP,
                )
                if new_non_dc is not None:
                    new_metsrw_dmdsec = fsentry.add_dmdsec(
                        new_non_dc, "OTHER", othermdtype="CUSTOM"
                    )
                    _replace_original_dmdsec(non_dc_dmdsecs, new_metsrw_dmdsec)
        job.pyprint(f, "now associated with", fsentry.dmdids)

    return mets


def _get_old_mets_rel_path(sip_uuid):
    return os.path.join(
        "objects", "submissionDocumentation", "METS." + sip_uuid + ".xml"
    )


def update_mets(job, sip_dir, sip_uuid, state, keep_normative_structmap=True):

    old_mets_path = os.path.join(sip_dir, _get_old_mets_rel_path(sip_uuid))
    job.pyprint("Looking for old METS at path", old_mets_path)

    # Parse old METS
    mets = metsrw.METSDocument.fromfile(old_mets_path)

    update_object(job, mets)
    update_dublincore(job, mets, sip_uuid)
    update_rights(job, mets, sip_uuid, state)
    add_events(job, mets, sip_uuid)
    add_new_files(job, mets, sip_uuid, sip_dir)
    delete_files(mets, sip_uuid)

    serialized = mets.serialize()
    if not keep_normative_structmap:
        # Remove normative structMap
        structmaps = serialized.findall(
            'mets:structMap[@LABEL="Normative Directory Structure"]',
            namespaces=ns.NSMAP,
        )
        for structmap in structmaps:
            structmap.getparent().remove(structmap)
            job.pyprint("Removed normative structMap")
    return serialized
