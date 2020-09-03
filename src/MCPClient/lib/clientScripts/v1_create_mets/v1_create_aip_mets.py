# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import collections
import copy
from glob import glob
from itertools import chain
import lxml.etree as etree
import os
import pprint
import re
import sys
import traceback
from uuid import uuid4

import django
import scandir

django.setup()
# dashboard
from django.utils import timezone
from main.models import (
    # Audit specific models (not-volatile).
    Derivation,
    Directory,
    DublinCore,
    Event,
    File,
    FileID,
    SIP,
    SIPArrange,
    # Agent Models (volatile).
    Agent,
    # FPR Models (Foreign-key, low-volatility).
    FPCommandOutput,
)

from . import create_mets_reingest
from .create_mets_metadata_csv import parseMetadata
from .create_mets_rights import archivematicaGetRights
from .create_mets_rights_dspace_mdref import archivematicaCreateMETSRightsDspaceMDRef
from .create_mets_trim import getTrimDmdSec
from .create_mets_trim import getTrimFileDmdSec
from .create_mets_trim import getTrimAmdSec
from .create_mets_trim import getTrimFileAmdSec

# archivematicaCommon
from archivematicaFunctions import escape
from archivematicaFunctions import normalizeNonDcElementName
from archivematicaFunctions import strToUnicode
from archivematicaFunctions import unicodeToStr
from .create_mets_dataverse_v2 import (
    create_dataverse_sip_dmdsec,
    create_dataverse_tabfile_dmdsec,
)
from custom_handlers import get_script_logger

import namespaces as ns
from ..sanitize_names import sanitize_name

from bagit import Bag, BagError

# WELLCOME TODO: Reduced METS specific imports.
import metsrw
import uuid
from .fs_entries_tree import (
    dir_obj_to_premis,
    IE_PREMIS_META,
    FSEntriesTree,
    event_to_premis,
    agents_to_premis,
)


logger = get_script_logger("archivematica.mcp.client.createMETS2")


class GenerateIEAndRepresentationErr(Exception):
    """For exceptions trying to generate PREMIS output"""


class GeneratePremisError(Exception):
    """For exceptions trying to generate PREMIS output"""


class ErrorAccumulator(object):
    def __init__(self):
        self.error_count = 0


class MetsState(object):
    def __init__(
        self, globalAmdSecCounter=0, globalTechMDCounter=0, globalDigiprovMDCounter=0
    ):
        self.globalFileGrps = {}
        self.globalFileGrpsUses = [
            "original",
            "submissionDocumentation",
            "preservation",
            "service",
            "access",
            "license",
            "text/ocr",
            "metadata",
            "derivative",
        ]
        for use in self.globalFileGrpsUses:
            grp = etree.Element(ns.metsBNS + "fileGrp")
            grp.set("USE", use)
            self.globalFileGrps[use] = grp

        # counters
        self.amdSecs = []
        self.dmdSecs = []
        self.globalDmdSecCounter = 0
        self.globalAmdSecCounter = globalAmdSecCounter
        self.globalTechMDCounter = globalTechMDCounter
        self.globalDigiprovMDCounter = globalDigiprovMDCounter
        self.globalRightsMDCounter = 0
        self.fileNameToFileID = {}  # Used for mapping structMaps included with transfer
        self.globalStructMapCounter = 0

        self.trimStructMap = None
        self.trimStructMapObjects = None
        # GROUPID="G1" -> GROUPID="Group-%object's UUID%"
        # group of the object and it's related access, license

        self.CSV_METADATA = {}
        self.error_accumulator = ErrorAccumulator()


FSItem = collections.namedtuple("FSItem", "type path is_empty")
FakeDirMdl = collections.namedtuple("FakeDirMdl", "uuid")


def newChild(parent, tag, text=None, tailText=None, sets=None):
    # TODO convert sets to a dict, and use **dict
    sets = sets or []
    child = etree.SubElement(parent, tag)
    child.text = strToUnicode(text)
    if tailText:
        child.tail = strToUnicode(tailText)
    for set_ in sets:
        key, value = set_
        child.set(key, value)
    return child


SIPMetadataAppliesToType = "3e48343d-e2d2-4956-aaa3-b54d26eb9761"
TransferMetadataAppliesToType = "45696327-44c5-4e78-849b-e027a189bf4d"
FileMetadataAppliesToType = "7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17"


# NEW CODE AFTER HERE...................................................
# MEW CODE AFTER HERE...................................................
# NEW CODE AFTER HERE...................................................

# PREMIS events and object types.
INGESTION_EVENT_TYPE = "ingestion"
METADATA_EXTRACT_EVENT_TYPE = "metadata extraction"

PREMIS_AGENT = "PREMIS:AGENT"
PREMIS_EVENT = "PREMIS:EVENT"
PREMIS_OBJECT = "PREMIS:OBJECT"

# Values to use to help us construct XML.
ID_ATTR = "ID"
DMDID_NAME = "DMDID"

DIGIPROV_NAME = "digiprovMD"
DMDSEC_NAME = "dmdSec"
MDTYPE = "MDTYPE"

AMDSEC_NAME = "amdSec"
AMDSEC_ATTR = "{}{}".format(ns.metsBNS, AMDSEC_NAME)

DMDSEC = "dmdSec"
DMDSEC_ATTR = "{}{}".format(ns.metsBNS, DMDSEC)

MDWRAP_NAME = "mdWrap"
MDWRAP_ATTR = "{}{}".format(ns.metsBNS, MDWRAP_NAME)

TECHMD = "techMD"
TECHMD_ATTR = "{}{}".format(ns.metsBNS, TECHMD)

XMLDATA_NAME = "xmlData"
XMLDATA_ATTR = "{}{}".format(ns.metsBNS, XMLDATA_NAME)


def _generate_structural_relationship(sub_type, rel_uuid):
    """Generate a structural relationship to write out to a PREMIS
    object.
    """
    # WELLCOME TODO: ADD TO FSENTRIES CODE AND THEN ITS OWN PREMIS MODULE.
    return (
        (
            "relationship",
            ("relationship_type", "structural"),
            ("relationship_sub_type", sub_type),
            (
                "related_object_identification",
                ("related_object_identifier_type", "UUID"),
                ("related_object_identifier_value", rel_uuid),
            ),
        ),
    )


def _generate_repr_premis(dir_obj, representation_id):
    """Generate the PREMIS object required for a representation using
    METSRW.
    """

    object_identifiers = (
        (
            "object_identifier",
            ("object_identifier_type", "UUID"),
            ("object_identifier_value", representation_id),
        ),
    )

    relationship_to_ie = _generate_structural_relationship("represents", dir_obj.uuid)

    premis_data = ("object", IE_PREMIS_META) + object_identifiers + relationship_to_ie

    return metsrw.plugins.premisrw.data_to_premis(
        premis_data, premis_version=IE_PREMIS_META["version"]
    )


def create_repr_amd_sec():
    """Create an amdSec for the representation"""
    AMDSEC = "amdSec"
    AMDSEC_ATTR = "{}{}".format(ns.metsBNS, AMDSEC)
    return etree.Element(AMDSEC_ATTR)


def create_aip_representation(dir_obj, relative_dir_path, representation_id, state):
    """Create an amdSec for the representation."""

    state.globalTechMDCounter += 1
    tech_md = etree.Element(TECHMD_ATTR)
    tech_md.set(ID_ATTR, "{}_{}".format(TECHMD, state.globalTechMDCounter))

    md_wrap = etree.SubElement(tech_md, MDWRAP_ATTR)
    md_wrap.set(MDTYPE, PREMIS_OBJECT)

    xml_data = etree.SubElement(md_wrap, XMLDATA_ATTR)
    relationship_premis = _generate_repr_premis(dir_obj, representation_id)
    xml_data.append(relationship_premis)

    return tech_md


def create_aip_ie(dir_obj, relative_dir_path):
    """Create an AIP level IE and Representation"""

    dmd_sec = etree.Element(DMDSEC_ATTR)
    md_wrap = etree.SubElement(dmd_sec, MDWRAP_ATTR)
    md_wrap.set(MDTYPE, PREMIS_OBJECT)
    xml_data = etree.SubElement(md_wrap, XMLDATA_ATTR)

    intellectual_entity = dir_obj_to_premis(dir_obj, relative_dir_path)
    xml_data.append(intellectual_entity)

    return dmd_sec


def create_aggregate_ingestion_event(file_objs, state):
    """Create a aggregate ingestion event for the AIP and wrap it in
    a METS amdSec.
    """

    UUID_FILTER = "file_uuid"

    # WELLCOME TODO: Almost exactly the same pattern as EVENTS, and a
    # few others. Let's get rid of this redundancy if we have time.

    event_record = Event.objects.filter(
        file_uuid_id=file_objs.next().uuid, event_type=INGESTION_EVENT_TYPE
    ).first()

    try:
        ingestion_uuids = [event_record.file_uuid_id]
    except AttributeError:
        # Normalized objects do not have ingestion events. Nor do those
        # extracted from ZIP-like files during transfer.
        return create_aggregate_ingestion_event(file_objs, state)

    for file_obj in file_objs:
        event = Event.objects.filter(
            file_uuid_id=file_obj.uuid, event_type=INGESTION_EVENT_TYPE
        ).values(UUID_FILTER)
        try:
            ingestion_uuids.append(event[0].get(UUID_FILTER))
        except IndexError:
            # Placeholder logging error. In all likelihood this will be
            # an object in the class of having no ingestion event.
            logger.error(
                "Query set for '%s' is empty, we need to investigate why, is the ingest event not being written?",
                file_obj.uuid,
            )
            pass

    state.globalDigiprovMDCounter += 1
    digiprov_md = etree.Element(
        DIGIPROV_NAME, ID="{}_{}".format(DIGIPROV_NAME, state.globalDigiprovMDCounter)
    )
    md_wrap = etree.SubElement(digiprov_md, MDWRAP_ATTR, MDTYPE=PREMIS_EVENT)
    xml_data = etree.SubElement(md_wrap, XMLDATA_ATTR)

    xml_data.append(event_to_premis(event_record, ingestion_uuids))

    return digiprov_md


def createDigiprovMD(fileUUID, sip_uuid, state, tool_tech_mds=None):
    """
    Create digiprovMD for PREMIS Events and linking Agents.
    """
    ret = []

    # WELLCOME TODO: We need to create our events synthetically for
    # demonstration purposes until Archivematica creates them
    # authentically.
    event_ids = create_metadata_event(
        file_uuid=fileUUID, sip_uuid=sip_uuid, tool_tech_mds=tool_tech_mds
    )
    events = Event.objects.filter(file_uuid_id=fileUUID).exclude(
        event_type=INGESTION_EVENT_TYPE
    )

    for event_record in events:
        state.globalDigiprovMDCounter += 1
        digiprovMD = etree.Element(
            DIGIPROV_NAME,
            ID="{}_{}".format(DIGIPROV_NAME, state.globalDigiprovMDCounter),
        )
        ret.append(digiprovMD)
        mdWrap = etree.SubElement(digiprovMD, MDWRAP_ATTR, MDTYPE=PREMIS_EVENT)
        xmlData = etree.SubElement(mdWrap, XMLDATA_ATTR)
        xmlData.append(event_to_premis(event_record))

    # WELLCOME TODO: As we temporarily create our new events we should
    # also do good and clean them up.
    delete_metadata_event(event_ids)

    return ret


def create_metadata_event(file_uuid, sip_uuid, tool_tech_mds):
    """Create metadata event

    This is a temporary function.

    Characterization commands do not have events associated with them in
    Archivematica yet, what happens if we create them? Is that
    information usable to us in any way here?

    GitHub related: https://github.com/artefactual-labs/mets-reader-writer/issues/43

    """
    tool_xlink = "\"METS-tools.{}.xml#xpointer(id('{}').xml\"".format(
        sip_uuid, tool_tech_mds.get(file_uuid)
    )
    # WELLCOME TODO: We might want a separate extract event per tool?
    # 1. It's currently being output in a single tech_md in the tool
    #    mets.
    # 2. That logic might be the same a as the transfer METS as well and
    #    so let's check that.
    objs = create_premis_object_characteristics_extensions(file_uuid)
    events = []
    event_ids = []
    if not objs:
        return events
    for obj in objs[0]:
        event_id = str(uuid.uuid4())
        event_record = Event()
        event_record.event_id = event_id
        event_record.file_uuid = File.objects.filter(uuid=file_uuid).first()
        event_record.event_type = METADATA_EXTRACT_EVENT_TYPE
        event_record.event_outcome_detail = tool_xlink
        # WELLCOME TODO: EVENT DATATIME IS SET TO NOW AUTOMATICALLY BY
        # THE MODEL SO IT ISN"T ACTUALLY AUTHENTIC TO THE EVENT WE
        # WANT TO CREATE HERE. IT IS LIKELY WE WILL NEED TO CREATE THE
        # EVENT IN THE FPR INSTEAD.
        #
        # WELLCOME TODO: We haven't a datetime associated with an event.
        #
        # mysql> describe main_fpcommandoutput;
        # +----------+-------------+------+-----+---------+----------------+
        # | Field    | Type        | Null | Key | Default | Extra          |
        # +----------+-------------+------+-----+---------+----------------+
        # | id       | int(11)     | NO   | PRI | NULL    | auto_increment |
        # | content  | longtext    | YES  |     | NULL    |                |
        # | fileUUID | varchar(36) | NO   | MUL | NULL    |                |
        # | ruleUUID | varchar(36) | NO   | MUL | NULL    |                |
        # +----------+-------------+------+-----+---------+----------------+
        # 4 rows in set (0.00 sec)
        #
        # We might need to use the FPR to properly associate an event
        # with a metadata extract command.
        #
        # Metadata extract commands are "characterization" in the FPR.
        #
        event_record.save()
        event_record.agents = Agent.objects.all()
        events.append(event_record)
        event_ids.append(event_id)
    return event_ids


# WELLCOME TODO: WE MIGHT NOT NEED TO DELETE THESE EVENTS, BUT WE CAN
# BE GOOD CITIZENS AND DO IT ANYWAY...
def delete_metadata_event(event_ids):
    """Delete the temporary events created fro the Wellcome work."""
    for event_id in event_ids:
        Event.objects.filter(event_id=event_id).delete()


def _get_fsentry_tree(opts):
    """Return the AIP object to generate METS from."""
    base_directory_path = opts.baseDirectoryPath
    base_directory_path_string = "%%%s%%" % (opts.baseDirectoryPathString)
    aip_uuid = opts.fileGroupIdentifier

    # Wellcome TODO: this is way too finicky... also, it looks like we're
    # not using the second line.
    base_directory_path = os.path.join(base_directory_path, "")
    objects_directory_path = os.path.join(base_directory_path, "objects")
    objects_directory_path = base_directory_path
    try:
        aip = SIP.objects.get(uuid=aip_uuid)
    except SIP.DoesNotExist:
        logger.info("No record in database for transfer: %s", aip_uuid)
        raise
    fsentry_tree = FSEntriesTree(
        objects_directory_path, base_directory_path_string, aip
    )
    fsentry_tree.scan()
    return fsentry_tree


def create_agent_premis_obj(job, file_objs, opts, state):
    """Returns a set of PREMIS agent objects wrapped in an amdSec to be
    appended to the tree which will link the other PREMIS object
    properties to their agent information.
    """

    # Retrieve all unique agents associated with every file object in
    # the transfer.
    all_agents = set()
    for file_obj in file_objs:
        agents = Agent.objects.filter(event__file_uuid_id=file_obj.uuid).distinct()
        for agent in agents:
            all_agents.add(agent)
    state.globalAmdSecCounter += 1
    amd_id = "{}_{}".format(AMDSEC_NAME, state.globalAmdSecCounter)
    amd_sec = etree.Element(AMDSEC_ATTR, ID=amd_id)
    for agent_record in all_agents:
        agent = agents_to_premis(agent_record)
        state.globalDigiprovMDCounter += 1
        digiprov_md = etree.Element(
            ns.metsBNS + DIGIPROV_NAME,
            ID="{}_{}".format(DIGIPROV_NAME, state.globalDigiprovMDCounter),
        )
        amd_sec.append(digiprov_md)
        md_wrap = etree.SubElement(digiprov_md, MDWRAP_ATTR, MDTYPE=PREMIS_AGENT)
        xml_data = etree.SubElement(md_wrap, XMLDATA_ATTR)
        xml_data.append(agent)
    return amd_sec


def generate_id_and_repr(
    representation_id, fsentry_tree, sip_dir_name, struct_map_div, opts, state
):
    """Generate an intellectual entity object and representation for
    the AIP.
    """

    file_group_identifier = opts.fileGroupIdentifier

    # Return the SIP model for the AIP.
    sip_mdl = SIP.objects.filter(uuid=file_group_identifier).first()

    if not sip_mdl:
        raise GenerateIEAndRepresentationErr("Cannot find the SIP model we're after...")

    file_objs = fsentry_tree.retrieve_file_objs()

    aip_dmd_sec = create_aip_ie(sip_mdl, sip_dir_name)
    state.globalDmdSecCounter += 1
    state.dmdSecs.append(aip_dmd_sec)

    aip_dmd_id = "{}_{}".format(DMDSEC_NAME, state.globalDmdSecCounter)
    aip_dmd_sec.set(ID_ATTR, aip_dmd_id)

    struct_map_div.set(DMDID_NAME, aip_dmd_id)

    repr_amd_sec = create_repr_amd_sec()

    state.globalAmdSecCounter += 1
    state.dmdSecs.append(repr_amd_sec)

    repr_amd_id = "{}_{}".format(AMDSEC_NAME, state.globalAmdSecCounter)
    repr_amd_sec.set(ID_ATTR, repr_amd_id)

    aip_repr_tech_md = create_aip_representation(
        sip_mdl, sip_dir_name, representation_id, state
    )
    repr_amd_sec.append(aip_repr_tech_md)

    aggregate_ingestion_event = create_aggregate_ingestion_event(file_objs, state)
    repr_amd_sec.append(aggregate_ingestion_event)


# WELLCOME TODO: Rewrite to use metsrw tuple syntax.
def create_repr_relationship(representation_id):
    """Create an element for a representation relationship"""
    relationship = etree.Element(ns.premisBNS + "relationship")
    etree.SubElement(
        relationship, ns.premisBNS + "relationshipType"
    ).text = "structural"
    etree.SubElement(
        relationship, ns.premisBNS + "relationshipSubType"
    ).text = "included in"

    relatedObjectIdentifier = etree.SubElement(
        relationship, ns.premisBNS + "relatedObjectIdentifier"
    )
    etree.SubElement(
        relatedObjectIdentifier, ns.premisBNS + "relatedObjectIdentifierType"
    ).text = "UUID"
    etree.SubElement(
        relatedObjectIdentifier, ns.premisBNS + "relatedObjectIdentifierValue"
    ).text = representation_id
    return relationship


def create_premis_object_characteristics_extensions(file_uuid):
    """Create PREMIS object characteristics extension

    Return true if we need to generate tool output, false if not.
    """
    return FPCommandOutput.objects.filter(
        file_id=file_uuid,
        rule__purpose__in=["characterization", "default_characterization"],
    ).values_list("content")


# OLD CODE AFTER HERE...................................................
# OLD CODE AFTER HERE...................................................
# OLD CODE AFTER HERE...................................................


def getDublinCore(unit, id_):
    db_field_mapping = collections.OrderedDict(
        [
            ("title", "title"),
            ("creator", "creator"),
            ("subject", "subject"),
            ("description", "description"),
            ("publisher", "publisher"),
            ("contributor", "contributor"),
            ("date", "date"),
            ("type", "type"),
            ("format", "format"),
            ("identifier", "identifier"),
            ("source", "source"),
            ("relation", "relation"),
            ("language", "language"),
            ("coverage", "coverage"),
            ("rights", "rights"),
            ("is_part_of", "isPartOf"),
        ]
    )

    try:
        dc = DublinCore.objects.get(
            metadataappliestotype_id=unit, metadataappliestoidentifier=id_
        )
    except DublinCore.DoesNotExist:
        return

    ret = etree.Element(
        ns.dctermsBNS + "dublincore", nsmap={"dcterms": ns.dctermsNS, "dc": ns.dcNS}
    )
    ret.set(
        ns.xsiBNS + "schemaLocation",
        ns.dctermsNS
        + " https://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd",
    )

    for dbname, term in db_field_mapping.items():
        txt = getattr(dc, dbname)
        elem_ns = ""
        # See http://dublincore.org/documents/2012/06/14/dcmi-terms/?v=elements for which elements are which namespace
        if term in (
            "contributor",
            "coverage",
            "creator",
            "date",
            "description",
            "format",
            "identifier",
            "language",
            "publisher",
            "relation",
            "rights",
            "source",
            "subject",
            "title",
            "type",
        ):
            elem_ns = ns.dcBNS
        elif term in ("isPartOf",):
            elem_ns = ns.dctermsBNS
        if txt:
            newChild(ret, elem_ns + term, text=txt)
    return ret


def _get_mdl_identifiers(mdl):
    """Get identifiers of a model as a type-value 2-tuple."""
    if isinstance(mdl, FakeDirMdl):
        return []
    return [(idfr.type, idfr.value) for idfr in mdl.identifiers.all()]


def _add_identifier(object_elem, identifier, bns=ns.premisBNS):
    """Add an identifier to a <premis:object>."""
    idfr_type, idfr_val = identifier
    objectIdentifier = etree.SubElement(object_elem, bns + "objectIdentifier")
    etree.SubElement(objectIdentifier, bns + "objectIdentifierType").text = idfr_type
    etree.SubElement(objectIdentifier, bns + "objectIdentifierValue").text = idfr_val
    return object_elem


def getDirDmdSec(dir_mdl, relativeDirectoryPath, representation_id):
    """Return an lxml ``Element`` representing a <mets:dmdSec> for a directory.
    It describes the directory as a PREMIS:OBJECT of type
    premis:intellectualEntity and lists the directory's original name (i.e.,
    relative path within the transfer) as well as the UUID assigned to it during
    transfer (or arrange), and any other identifiers, as
    premis:objectIdentifiers. Cf. https://projects.artefactual.com/issues/11192.
    """
    dir_uuid = dir_mdl.uuid
    ret = etree.Element(ns.metsBNS + "dmdSec")
    mdWrap = etree.SubElement(ret, ns.metsBNS + "mdWrap")
    mdWrap.set("MDTYPE", "PREMIS:OBJECT")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")

    # WELLCOME TODO: This needs replacing...
    object_elem = etree.SubElement(
        xmlData, ns.premisBNS + "object", nsmap={"premis": ns.premisNS}
    )
    object_elem.set(ns.xsiBNS + "type", "premis:intellectualEntity")
    object_elem.set(
        ns.xsiBNS + "schemaLocation",
        ns.premisNS + " http://www.loc.gov/standards/premis/v3/premis.xsd",
    )
    object_elem.set("version", "3.0")
    # Add the directory's UUID and any other identifiers as
    # <premis:objectIdentifier> children of <premis:object>.
    for identifier in chain((("UUID", dir_uuid),), _get_mdl_identifiers(dir_mdl)):
        object_elem = _add_identifier(object_elem, identifier, bns=ns.premisBNS)
    try:
        original_name = escape(dir_mdl.originallocation)
    except AttributeError:  # SIP model won't have originallocation
        original_name = escape(relativeDirectoryPath)
    etree.SubElement(object_elem, ns.premisBNS + "originalName").text = original_name

    # WELLCOME TODO: We need a relationship to a representation here?
    # ADD RELATIONSHIP 1

    # WELLCOME TODO: Let's leave this out until we get a better idea
    # from EM.

    # Example here: %transferDirectory%objects/artwork/ ...

    return ret


def createDMDIDsFromCSVMetadata(job, path, state):
    """
    Creates dmdSecs with metadata associated with path from the metadata.csv

    :param path: Path relative to the SIP to find CSV metadata on
    :return: Space-separated list of DMDIDs or empty string
    """
    metadata = state.CSV_METADATA.get(unicodeToStr(path), {})
    dmdsecs = createDmdSecsFromCSVParsedMetadata(job, metadata, state)
    return " ".join([d.get("ID") for d in dmdsecs])


def createDmdSecsFromCSVParsedMetadata(job, metadata, state):
    """
    Create dmdSec(s) from the provided metadata.

    :param metadata: OrderedDict with the metadata keys and a list of values
    :return: List of dmdSec Elements created
    """
    dc = None
    other = None
    ret = []

    # Archivematica does not support refined Dublin Core, e.g.
    # multitiered terms in the format dc.description.abstract
    # If these terms are encountered, an element with only the
    # last portion of the name will be added.
    # e.g., dc.description.abstract is mapped to <dc:abstract>
    refinement_regex = re.compile(r"\w+\.(.+)")

    for key, value in metadata.items():
        if key.startswith("dc.") or key.startswith("dcterms."):
            if dc is None:
                state.globalDmdSecCounter += 1
                ID = "dmdSec_" + state.globalDmdSecCounter.__str__()
                dmdSec = etree.Element(ns.metsBNS + "dmdSec", ID=ID)
                state.dmdSecs.append(dmdSec)
                ret.append(dmdSec)
                mdWrap = etree.SubElement(dmdSec, ns.metsBNS + "mdWrap")
                mdWrap.set("MDTYPE", "DC")
                xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
                dc = etree.Element(
                    ns.dctermsBNS + "dublincore",
                    nsmap={"dcterms": ns.dctermsNS, "dc": ns.dcNS},
                )
                dc.set(
                    ns.xsiBNS + "schemaLocation",
                    ns.dctermsNS
                    + " https://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd",
                )
                xmlData.append(dc)
            elem_namespace = ""
            if key.startswith("dc."):
                key = key.replace("dc.", "", 1)
                elem_namespace = ns.dcBNS
            elif key.startswith("dcterms."):
                key = key.replace("dcterms.", "", 1)
                elem_namespace = ns.dctermsBNS
            match = re.match(refinement_regex, key)
            if match:
                key, = match.groups()
            for v in value:
                try:
                    etree.SubElement(dc, elem_namespace + key).text = v.decode("utf-8")
                except UnicodeDecodeError:
                    job.pyprint(
                        "Skipping DC value; not valid UTF-8: {}".format(v),
                        file=sys.stderr,
                    )
        else:  # not a dublin core item
            if other is None:
                state.globalDmdSecCounter += 1
                ID = "dmdSec_" + state.globalDmdSecCounter.__str__()
                dmdSec = etree.Element(ns.metsBNS + "dmdSec", ID=ID)
                state.dmdSecs.append(dmdSec)
                ret.append(dmdSec)
                mdWrap = etree.SubElement(dmdSec, ns.metsBNS + "mdWrap")
                mdWrap.set("MDTYPE", "OTHER")
                mdWrap.set("OTHERMDTYPE", "CUSTOM")
                other = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
            for v in value:
                try:
                    etree.SubElement(
                        other, normalizeNonDcElementName(key)
                    ).text = v.decode("utf-8")
                except UnicodeDecodeError:
                    job.pyprint(
                        "Skipping DC value; not valid UTF-8: {}".format(v),
                        file=sys.stderr,
                    )
    return ret


def createDublincoreDMDSecFromDBData(
    job, unit_type, unit_uuid, baseDirectoryPath, state
):
    """
    Creates dmdSec containing DublinCore metadata for unit_uuid.

    If DC metadata exists in the DB, use that.
    If not, check the transfer metadata directory for a dublincore.xml file, and use that.

    :param str unit_type: Pk from MetadataAppliesToType
    :param str unit_uuid: SIP UUID
    :param str baseDirectoryPath: SIP path to check for transfer metadata
    :return: Tuple of (dmdSec Element, DMDID), or None
    """
    dc = getDublinCore(unit_type, unit_uuid)
    if dc is None:
        transfers = os.path.join(baseDirectoryPath, "objects/metadata/transfers/")
        if not os.path.isdir(transfers):
            return None
        for transfer in os.listdir(transfers):
            dcXMLFile = os.path.join(transfers, transfer, "dublincore.xml")
            if os.path.isfile(dcXMLFile):
                try:
                    parser = etree.XMLParser(remove_blank_text=True)
                    dtree = etree.parse(dcXMLFile, parser)
                    dc = dtree.getroot()
                    break
                except Exception as inst:
                    job.pyprint("error parsing file:", dcXMLFile, file=sys.stderr)
                    job.pyprint(type(inst), file=sys.stderr)  # the exception instance
                    job.pyprint(inst.args, file=sys.stderr)
                    job.print_output(traceback.format_exc())
                    state.error_accumulator.error_count += 1
        else:  # break not called, no DC successfully parsed
            return None
    state.globalDmdSecCounter += 1
    dmdSec = etree.Element(ns.metsBNS + "dmdSec")
    ID = "dmdSec_" + state.globalDmdSecCounter.__str__()
    dmdSec.set("ID", ID)
    mdWrap = etree.SubElement(dmdSec, ns.metsBNS + "mdWrap")
    mdWrap.set("MDTYPE", "DC")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
    xmlData.append(dc)
    return (dmdSec, ID)


def createDSpaceDMDSec(job, label, dspace_mets_path, directoryPathSTR, state):
    """
    Parse DSpace METS file and create a dmdSecs from the info.

    One dmdSec will contain a mdRef to the DSpace METS file. The other dmdSec
    will contain Dublin Core metadata with the identifier and parent collection
    identifier.

    :param str label: LABEL for the mdRef
    :param str dspace_mets_path: Path to the DSpace METS
    :param str directoryPathSTR: Relative path to the DSpace METS
    :return: dict of {<dmdSec ID>: <dmdSec Element>}
    """
    dmdsecs = collections.OrderedDict()
    root = etree.parse(dspace_mets_path)

    # Create mdRef to DSpace METS file
    state.globalDmdSecCounter += 1
    dmdid = "dmdSec_" + str(state.globalDmdSecCounter)
    dmdsec = etree.Element(ns.metsBNS + "dmdSec", ID=dmdid)
    dmdsecs[dmdid] = dmdsec
    xptr_dmdids = [
        i.get("ID") for i in root.findall("{http://www.loc.gov/METS/}dmdSec")
    ]
    try:
        xptr = "xpointer(id('{}'))".format(" ".join(xptr_dmdids))
    except TypeError:  # Trying to .join() on a list with None
        job.pyprint("dmdSec in", dspace_mets_path, "missing an ID", file=sys.stderr)
        raise
    newChild(
        dmdsec,
        ns.metsBNS + "mdRef",
        text=None,
        sets=[
            ("LABEL", label),
            (ns.xlinkBNS + "href", directoryPathSTR),
            ("MDTYPE", "OTHER"),
            ("LOCTYPE", "OTHER"),
            ("OTHERLOCTYPE", "SYSTEM"),
            ("XPTR", xptr),
        ],
    )

    # Create dmdSec with DC identifier and isPartOf
    identifier = root.findtext(
        'mets:amdSec/mets:sourceMD/mets:mdWrap/mets:xmlData/dim:dim/dim:field[@qualifier="uri"]',
        namespaces=ns.NSMAP,
    )
    part_of = root.findtext(
        'mets:amdSec/mets:sourceMD/mets:mdWrap/mets:xmlData/dim:dim/dim:field[@qualifier="isPartOf"]',
        namespaces=ns.NSMAP,
    )
    if identifier is None or part_of is None:
        job.pyprint(
            "Unable to parse identifer and isPartOf from",
            dspace_mets_path,
            file=sys.stderr,
        )
        return {}
    metadata = {"dc.identifier": [identifier], "dcterms.isPartOf": [part_of]}
    dc_dmdsecs = createDmdSecsFromCSVParsedMetadata(job, metadata, state)
    dmdsec = dc_dmdsecs[0]  # Should only be one dmdSec
    dmdid = dmdsec.get("ID")
    dmdsecs[dmdid] = dmdsec

    return dmdsecs


def createTechMD(fileUUID, state, representation_id):
    """
    Create a techMD containing a PREMIS:OBJECT for the file with fileUUID.

    :param str fileUUID: UUID of the File to create an object for
    :return: mets:techMD containing a premis:object
    """
    ret = etree.Element(ns.metsBNS + "techMD")
    techMD = ret

    state.globalTechMDCounter += 1
    techMD.set("ID", "techMD_" + str(state.globalTechMDCounter))

    mdWrap = etree.SubElement(techMD, ns.metsBNS + "mdWrap")
    mdWrap.set("MDTYPE", "PREMIS:OBJECT")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")

    premis_object = create_premis_object(fileUUID, representation_id)
    xmlData.append(premis_object)
    return ret


# WELLCOME TODO: Rewrite to use metsrw tuple syntax.
def create_premis_object(fileUUID, representation_id):
    """
    Create a PREMIS:OBJECT for fileUUID.

    Access the models for File, FileID, FPCommandOutput, Derivation

    :param str fileUUID: UUID of the File to create an object for
    :return: premis:object Element, suitable for inserting into mets:xmlData
    """
    f = File.objects.get(uuid=fileUUID)
    # PREMIS:OBJECT
    object_elem = etree.Element(ns.premisBNS + "object", nsmap={"premis": ns.premisNS})
    object_elem.set(ns.xsiBNS + "type", "premis:file")
    object_elem.set(
        ns.xsiBNS + "schemaLocation",
        ns.premisNS + " http://www.loc.gov/standards/premis/v3/premis.xsd",
    )
    object_elem.set("version", "3.0")

    # Add the UUID and any additional file identifiers, e.g., PIDs or
    # PURLs/URIs, to the XML.
    for identifier in chain((("UUID", fileUUID),), _get_mdl_identifiers(f)):
        object_elem = _add_identifier(object_elem, identifier)

    objectCharacteristics = etree.SubElement(
        object_elem, ns.premisBNS + "objectCharacteristics"
    )
    etree.SubElement(
        objectCharacteristics, ns.premisBNS + "compositionLevel"
    ).text = "0"

    fixity = etree.SubElement(objectCharacteristics, ns.premisBNS + "fixity")
    etree.SubElement(
        fixity, ns.premisBNS + "messageDigestAlgorithm"
    ).text = f.checksumtype
    etree.SubElement(fixity, ns.premisBNS + "messageDigest").text = f.checksum

    etree.SubElement(objectCharacteristics, ns.premisBNS + "size").text = str(f.size)

    for elem in create_premis_object_formats(fileUUID):
        objectCharacteristics.append(elem)

    creatingApplication = etree.Element(ns.premisBNS + "creatingApplication")
    etree.SubElement(
        creatingApplication, ns.premisBNS + "dateCreatedByApplication"
    ).text = f.modificationtime.strftime("%Y-%m-%d")
    objectCharacteristics.append(creatingApplication)
    etree.SubElement(object_elem, ns.premisBNS + "originalName").text = escape(
        f.originallocation
    )

    # WELLCOME TODO: We need a relationship to a representation here?
    # ADD RELATIONSHIP 2

    elems = create_premis_object_derivations(fileUUID, representation_id)
    if elems:
        for elem in elems:
            object_elem.append(elem)
    else:
        object_to_repr_rel = create_repr_relationship(representation_id)
        object_elem.append(object_to_repr_rel)

    return object_elem


def create_premis_object_formats(fileUUID):
    files = FileID.objects.filter(file_id=fileUUID)
    elements = []
    if not files.exists():
        fmt = etree.Element(ns.premisBNS + "format")
        formatDesignation = etree.SubElement(fmt, ns.premisBNS + "formatDesignation")
        etree.SubElement(
            formatDesignation, ns.premisBNS + "formatName"
        ).text = "Unknown"
        elements.append(fmt)
    for row in files.values_list(
        "format_name", "format_version", "format_registry_name", "format_registry_key"
    ):
        fmt = etree.Element(ns.premisBNS + "format")

        formatDesignation = etree.SubElement(fmt, ns.premisBNS + "formatDesignation")
        etree.SubElement(formatDesignation, ns.premisBNS + "formatName").text = row[0]
        etree.SubElement(formatDesignation, ns.premisBNS + "formatVersion").text = row[
            1
        ]

        formatRegistry = etree.SubElement(fmt, ns.premisBNS + "formatRegistry")
        etree.SubElement(
            formatRegistry, ns.premisBNS + "formatRegistryName"
        ).text = row[2]
        etree.SubElement(formatRegistry, ns.premisBNS + "formatRegistryKey").text = row[
            3
        ]
        elements.append(fmt)

    return elements


# WELLCOME TODO: Rewrite to use metsrw tuple syntax.
#
# ADDITIONAL: This function could do with a rewrite to remove its
# duplication anyway... Also, in practice, I'm not sure we ever need
# to loop through relationships. The relationships in an AIP are
# more simple.
def create_premis_object_derivations(fileUUID, representation_id):
    elements = []
    # Derivations
    derivations = Derivation.objects.filter(
        source_file_id=fileUUID, event__isnull=False
    )
    for derivation in derivations:
        relationship = etree.Element(ns.premisBNS + "relationship")
        etree.SubElement(
            relationship, ns.premisBNS + "relationshipType"
        ).text = "derivation"
        etree.SubElement(
            relationship, ns.premisBNS + "relationshipSubType"
        ).text = "is source of"

        relatedObjectIdentifier = etree.SubElement(
            relationship, ns.premisBNS + "relatedObjectIdentifier"
        )
        etree.SubElement(
            relatedObjectIdentifier, ns.premisBNS + "relatedObjectIdentifierType"
        ).text = "UUID"
        etree.SubElement(
            relatedObjectIdentifier, ns.premisBNS + "relatedObjectIdentifierValue"
        ).text = derivation.derived_file_id

        relatedEventIdentifier = etree.SubElement(
            relationship, ns.premisBNS + "relatedEventIdentifier"
        )
        etree.SubElement(
            relatedEventIdentifier, ns.premisBNS + "relatedEventIdentifierType"
        ).text = "UUID"
        etree.SubElement(
            relatedEventIdentifier, ns.premisBNS + "relatedEventIdentifierValue"
        ).text = str(derivation.event_id)

        # WELLCOME TODO: More unnecessary duplication.
        etree.SubElement(
            relationship, ns.premisBNS + "relationshipType"
        ).text = "structural"
        etree.SubElement(
            relationship, ns.premisBNS + "relationshipSubType"
        ).text = "included in"

        relatedObjectIdentifier = etree.SubElement(
            relationship, ns.premisBNS + "relatedObjectIdentifier"
        )
        etree.SubElement(
            relatedObjectIdentifier, ns.premisBNS + "relatedObjectIdentifierType"
        ).text = "UUID"
        etree.SubElement(
            relatedObjectIdentifier, ns.premisBNS + "relatedObjectIdentifierValue"
        ).text = representation_id

        elements.append(relationship)

    derivations = Derivation.objects.filter(
        derived_file_id=fileUUID, event__isnull=False
    )
    for derivation in derivations:
        relationship = etree.Element(ns.premisBNS + "relationship")
        etree.SubElement(
            relationship, ns.premisBNS + "relationshipType"
        ).text = "derivation"
        etree.SubElement(
            relationship, ns.premisBNS + "relationshipSubType"
        ).text = "has source"

        relatedObjectIdentifier = etree.SubElement(
            relationship, ns.premisBNS + "relatedObjectIdentifier"
        )
        etree.SubElement(
            relatedObjectIdentifier, ns.premisBNS + "relatedObjectIdentifierType"
        ).text = "UUID"
        etree.SubElement(
            relatedObjectIdentifier, ns.premisBNS + "relatedObjectIdentifierValue"
        ).text = derivation.source_file_id

        relatedEventIdentifier = etree.SubElement(
            relationship, ns.premisBNS + "relatedEventIdentifier"
        )
        etree.SubElement(
            relatedEventIdentifier, ns.premisBNS + "relatedEventIdentifierType"
        ).text = "UUID"
        etree.SubElement(
            relatedEventIdentifier, ns.premisBNS + "relatedEventIdentifierValue"
        ).text = str(derivation.event_id)

        # WELLCOME TODO: More unnecessary duplication.
        etree.SubElement(
            relationship, ns.premisBNS + "relationshipType"
        ).text = "structural"
        etree.SubElement(
            relationship, ns.premisBNS + "relationshipSubType"
        ).text = "included in"

        relatedObjectIdentifier = etree.SubElement(
            relationship, ns.premisBNS + "relatedObjectIdentifier"
        )
        etree.SubElement(
            relatedObjectIdentifier, ns.premisBNS + "relatedObjectIdentifierType"
        ).text = "UUID"
        etree.SubElement(
            relatedObjectIdentifier, ns.premisBNS + "relatedObjectIdentifierValue"
        ).text = representation_id

        elements.append(relationship)

    return elements


def getAMDSec(
    job,
    fileUUID,
    filePath,
    use,
    sip_uuid,
    transferUUID,
    itemdirectoryPath,
    typeOfTransfer,
    baseDirectoryPath,
    state,
    representation_id=None,
    tool_tech_mds=None,
):
    """
    Creates an amdSec.

    techMD contains a PREMIS:OBJECT, see createTechMD
    rightsMD contain PREMIS:RIGHTS, see archivematicaGetRights, archivematicaCreateMETSRightsDspaceMDRef or getTrimFileAmdSec
    digiprovMD contain PREMIS:EVENT and PREMIS:AGENT, see createDigiprovMD and createDigiprovMDAgents

    :param fileUUID: UUID of the file
    :param filePath: For archivematicaCreateMETSRightsDspaceMDRef
    :param use: If "original", look for rights metadata.
    :param sip_uuid: UUID of the SIP this file is in, to check for original file rights metadata.
    :param transferUUID: UUID of the Transfer this file was in, to check for original file rights metadata.
    :param itemdirectoryPath: For archivematicaCreateMETSRightsDspaceMDRef
    :param typeOfTransfer: Transfer type, used for checking for DSpace or TRIM rights metadata.
    :param baseDirectoryPath: For getTrimFileAmdSec
    """
    state.globalAmdSecCounter += 1
    AMDID = "amdSec_%s" % (state.globalAmdSecCounter.__str__())
    AMD = etree.Element(ns.metsBNS + "amdSec", ID=AMDID)
    ret = (AMD, AMDID)

    # tech MD
    AMD.append(createTechMD(fileUUID, state, representation_id))

    if use == "original":
        metadataAppliesToList = [
            (fileUUID, FileMetadataAppliesToType),
            (sip_uuid, SIPMetadataAppliesToType),
            (transferUUID, TransferMetadataAppliesToType),
        ]
        for a in archivematicaGetRights(job, metadataAppliesToList, fileUUID, state):
            state.globalRightsMDCounter += 1
            rightsMD = etree.SubElement(AMD, ns.metsBNS + "rightsMD")
            rightsMD.set("ID", "rightsMD_" + state.globalRightsMDCounter.__str__())
            mdWrap = newChild(rightsMD, ns.metsBNS + "mdWrap")
            mdWrap.set("MDTYPE", "PREMIS:RIGHTS")
            xmlData = newChild(mdWrap, ns.metsBNS + "xmlData")
            xmlData.append(a)

        if typeOfTransfer == "Dspace":
            for a in archivematicaCreateMETSRightsDspaceMDRef(
                job, fileUUID, filePath, transferUUID, itemdirectoryPath, state
            ):
                state.globalRightsMDCounter += 1
                rightsMD = etree.SubElement(AMD, ns.metsBNS + "rightsMD")
                rightsMD.set("ID", "rightsMD_" + state.globalRightsMDCounter.__str__())
                rightsMD.append(a)

        elif typeOfTransfer == "TRIM":
            digiprovMD = getTrimFileAmdSec(job, baseDirectoryPath, sip_uuid, fileUUID)
            state.globalDigiprovMDCounter += 1
            digiprovMD.set(
                "ID", "digiprovMD_" + state.globalDigiprovMDCounter.__str__()
            )
            AMD.append(digiprovMD)

    for a in createDigiprovMD(fileUUID, sip_uuid, state, tool_tech_mds):
        AMD.append(a)

    return ret


def _fixup_path_input_by_user(job, path):
    """Fix-up paths submitted by a user, e.g. in custom structmap examples so
    that they don't have to anticipate the Archivematica normalization process.
    """
    return os.path.join("", *[sanitize_name(name) for name in path.split(os.path.sep)])


def include_custom_structmap(
    job, baseDirectoryPath, state, custom_structmap="mets_structmap.xml"
):
    """Enable users in submitting a structmap with a transfer and have that
    included in the eventual AIP METS.
    """
    ret = []
    transferMetadata = os.path.join(
        baseDirectoryPath, os.path.join("objects", "metadata", "transfers")
    )
    if not os.path.isdir(transferMetadata):
        return ret
    baseLocations = os.listdir(transferMetadata)
    baseLocations.append(baseDirectoryPath)
    for dir_ in baseLocations:
        dirPath = os.path.join(transferMetadata, dir_)
        structMapXmlPath = os.path.join(dirPath, custom_structmap)
        if not os.path.isdir(dirPath):
            continue
        if os.path.isfile(structMapXmlPath):
            tree = etree.parse(structMapXmlPath)
            root = tree.getroot()
            structMap = root.find(ns.metsBNS + "structMap")
            id_ = structMap.get("ID")
            if not id_:
                state.globalStructMapCounter += 1
                structMap.set("ID", "structMap_{}".format(state.globalStructMapCounter))
            ret.append(structMap)
            # CONTENTIDS will map to fptrs and area elements where present.
            fptrs = root.xpath("//mets:fptr", namespaces={"mets": ns.metsNS})
            area_elements = root.xpath("//mets:area", namespaces={"mets": ns.metsNS})
            contentids = structMap.xpath(
                "//*[@CONTENTIDS]", namespaces={"mets:": ns.metsNS}
            )
            if not contentids:
                state.error_accumulator.error_count += 1
                logger.error(
                    "No CONTENTIDS found in custom structMap. AIP METS cannot be generated"
                )
                return []
            if len(contentids) < (len(fptrs) + len(area_elements)):
                logger.error(
                    "Mismatch of CONTENTID elements to elements we wish to replace. AIP METS cannot be generated"
                )
                state.error_accumulator.error_count += 1
                return []
            for item in contentids:
                file_path = item.get("CONTENTIDS")
                if not file_path:
                    logger.error(
                        "Empty file path in custom structMap. AIP METS cannot be generated"
                    )
                    state.error_accumulator.error_count += 1
                    return []
                normalized_path = _fixup_path_input_by_user(job, file_path)
                if normalized_path in state.fileNameToFileID:
                    item.set("FILEID", state.fileNameToFileID[normalized_path])
                else:
                    state.error_accumulator.error_count += 1
                    logger.error(
                        "No fileUUID for '%s'; original in custom structMap: %s",
                        normalized_path,
                        file_path,
                    )
                    return []
    if ret:
        job.pyprint("Custom structmap will be included in AIP METS")
    return ret


# DMDID="dmdSec_01" for an object goes in here
# <file ID="file1-UUID" GROUPID="G1" DMDID="dmdSec_02" ADMID="amdSec_01">

# WELLCOME TODO: WILL WE BE ABLE TO REMOVE THIS?
def createFileSec(
    job,
    directoryPath,
    parentDiv,
    baseDirectoryPath,
    baseDirectoryName,
    fileGroupIdentifier,
    fileGroupType,
    directories,
    state,
    includeAmdSec=True,
    representation_id=None,
    tool_tech_mds=None,
):

    """Creates fileSec and structMap entries for files on disk recursively.

    :param directoryPath: Path to recursively traverse and create METS entries for
    :param parentDiv: structMap div to attach created children to
    :param baseDirectoryPath: SIP path
    :param baseDirectoryName: Name of the %var% for the SIP path
    :param fileGroupIdentifier: SIP UUID
    :param fileGroupType: Name of the foreign key field linking to SIP UUID in files.
    :param includeAmdSec: If True, creates amdSecs for the files
    """
    filesInThisDirectory = []
    dspaceMetsDMDID = None
    try:
        directoryContents = sorted(os.listdir(directoryPath))
    except os.error:
        # Directory doesn't exist
        job.pyprint(directoryPath, "doesn't exist", file=sys.stderr)
        return

    # Create the <mets:div> element for the directory that this file is in.
    # If this directory has been assigned a UUID during transfer, retrieve that
    # UUID based on the directory's relative path and document it in its own
    # <mets:dmdSec> element.
    directoryName = os.path.basename(directoryPath)
    relativeDirectoryPath = "%SIPDirectory%" + os.path.join(
        directoryPath.replace(baseDirectoryPath, "", 1), ""
    )
    dir_mdl = directories.get(
        relativeDirectoryPath, directories.get(relativeDirectoryPath.rstrip("/"))
    )
    dir_dmd_id = None
    if dir_mdl:
        dirDmdSec = getDirDmdSec(dir_mdl, relativeDirectoryPath, representation_id)
        state.globalDmdSecCounter += 1
        state.dmdSecs.append(dirDmdSec)
        dir_dmd_id = "dmdSec_" + state.globalDmdSecCounter.__str__()
        dirDmdSec.set("ID", dir_dmd_id)
    structMapDiv = etree.SubElement(
        parentDiv, ns.metsBNS + "div", TYPE="Directory", LABEL=directoryName
    )

    DMDIDS = createDMDIDsFromCSVMetadata(
        job, directoryPath.replace(baseDirectoryPath, "", 1), state
    )
    if DMDIDS or dir_dmd_id:
        if DMDIDS and dir_dmd_id:
            structMapDiv.set("DMDID", dir_dmd_id + " " + DMDIDS)
        elif DMDIDS:
            structMapDiv.set("DMDID", DMDIDS)
        else:
            structMapDiv.set("DMDID", dir_dmd_id)

    for item in directoryContents:
        itemdirectoryPath = os.path.join(directoryPath, item)
        if os.path.isdir(itemdirectoryPath):
            # WELLCOME TODO: WILL WE BE ABLE TO REMOVE THIS?
            createFileSec(
                job,
                itemdirectoryPath,
                structMapDiv,
                baseDirectoryPath,
                baseDirectoryName,
                fileGroupIdentifier,
                fileGroupType,
                directories,
                state,
                includeAmdSec=includeAmdSec,
                representation_id=representation_id,
                tool_tech_mds=tool_tech_mds,
            )
        elif os.path.isfile(itemdirectoryPath):
            # Setup variables for creating file metadata
            DMDIDS = ""
            directoryPathSTR = itemdirectoryPath.replace(
                baseDirectoryPath, baseDirectoryName, 1
            )

            kwargs = {
                "removedtime__isnull": True,
                fileGroupType: fileGroupIdentifier,
                "currentlocation": directoryPathSTR,
            }
            try:
                f = File.objects.get(**kwargs)
            except File.DoesNotExist:
                job.pyprint(
                    'No uuid for file: "', directoryPathSTR, '"', file=sys.stderr
                )
                state.error_accumulator.error_count += 1
                continue

            use = f.filegrpuse
            label = f.label
            typeOfTransfer = f.transfer.type if f.transfer else None

            directoryPathSTR = itemdirectoryPath.replace(baseDirectoryPath, "", 1)

            # Special TRIM processing
            if typeOfTransfer == "TRIM" and state.trimStructMap is None:
                state.trimStructMap = etree.Element(
                    ns.metsBNS + "structMap",
                    attrib={
                        "TYPE": "logical",
                        "ID": "structMap_2",
                        "LABEL": "Hierarchical arrangement",
                    },
                )
                state.trimStructMapObjects = etree.SubElement(
                    state.trimStructMap,
                    ns.metsBNS + "div",
                    attrib={"TYPE": "File", "LABEL": "objects"},
                )

                trimDmdSec = getTrimDmdSec(job, baseDirectoryPath, fileGroupIdentifier)
                state.globalDmdSecCounter += 1
                state.dmdSecs.append(trimDmdSec)
                ID = "dmdSec_" + state.globalDmdSecCounter.__str__()
                trimDmdSec.set("ID", ID)
                state.trimStructMapObjects.set("DMDID", ID)

                trimAmdSec = etree.Element(ns.metsBNS + "amdSec")
                state.globalAmdSecCounter += 1
                state.amdSecs.append(trimAmdSec)
                ID = "amdSec_" + state.globalAmdSecCounter.__str__()
                trimAmdSec.set("ID", ID)

                digiprovMD = getTrimAmdSec(job, baseDirectoryPath, fileGroupIdentifier)
                state.globalDigiprovMDCounter += 1
                digiprovMD.set("ID", "digiprovMD_" + str(state.globalDigiprovMDCounter))

                trimAmdSec.append(digiprovMD)

                state.trimStructMapObjects.set("ADMID", ID)

            # Create <div TYPE="Item"> and child <fptr>
            # <fptr FILEID="file-<UUID>" LABEL="filename.ext">
            fileId = "file-{}".format(f.uuid)
            label = item if not label else label
            fileDiv = etree.SubElement(
                structMapDiv, ns.metsBNS + "div", LABEL=label, TYPE="Item"
            )
            etree.SubElement(fileDiv, ns.metsBNS + "fptr", FILEID=fileId)
            # Pair items listed in custom structmaps. Strip leading path
            # separator if it exists.
            state.fileNameToFileID[directoryPathSTR] = fileId

            # Determine fileGrp @GROUPID based on the file's fileGrpUse and transfer type
            GROUPID = ""
            if f.filegrpuuid:
                # GROUPID was determined elsewhere
                GROUPID = "Group-%s" % (f.filegrpuuid)
                if use == "TRIM file metadata":
                    use = "metadata"

            elif use in (
                "original",
                "submissionDocumentation",
                "metadata",
                "maildirFile",
            ):
                # These files are in a group defined by themselves
                GROUPID = "Group-%s" % (f.uuid)
                if use == "maildirFile":
                    use = "original"
                # Check for CSV-based Dublincore dmdSec
                if use == "original":
                    DMDIDS = createDMDIDsFromCSVMetadata(
                        job,
                        f.originallocation.replace("%transferDirectory%", "", 1),
                        state,
                    )
                    if DMDIDS:
                        fileDiv.set("DMDID", DMDIDS)
                    # More special TRIM processing
                    if typeOfTransfer == "TRIM":
                        trimFileDiv = etree.SubElement(
                            state.trimStructMapObjects,
                            ns.metsBNS + "div",
                            attrib={"TYPE": "Item"},
                        )

                        trimFileDmdSec = getTrimFileDmdSec(
                            job, baseDirectoryPath, fileGroupIdentifier, f.uuid
                        )
                        state.globalDmdSecCounter += 1
                        state.dmdSecs.append(trimFileDmdSec)
                        ID = "dmdSec_" + state.globalDmdSecCounter.__str__()
                        trimFileDmdSec.set("ID", ID)

                        trimFileDiv.set("DMDID", ID)

                        etree.SubElement(
                            trimFileDiv, ns.metsBNS + "fptr", FILEID=fileId
                        )

            elif typeOfTransfer == "Dspace" and (
                use in ("license", "text/ocr", "DSPACEMETS")
            ):
                # Dspace transfers are treated specially, but some of these fileGrpUses may be encountered in other types
                kwargs = {
                    "removedtime__isnull": True,
                    fileGroupType: fileGroupIdentifier,
                    "filegrpuse": "original",
                    "originallocation__startswith": os.path.dirname(f.originallocation),
                }
                original_file = File.objects.filter(**kwargs).first()
                if original_file is not None:
                    GROUPID = "Group-" + original_file.uuid

            elif use in ("preservation", "text/ocr", "derivative"):
                # Derived files should be in the original file's group
                try:
                    d = Derivation.objects.get(derived_file_id=f.uuid)
                except Derivation.DoesNotExist:
                    job.pyprint(
                        "Fatal error: unable to locate a Derivation object"
                        " where the derived file is {}".format(f.uuid)
                    )
                    raise
                GROUPID = "Group-" + d.source_file_id

            elif use == "service":
                # Service files are in the original file's group
                fileFileIDPath = itemdirectoryPath.replace(
                    baseDirectoryPath + "objects/service/",
                    baseDirectoryName + "objects/",
                )
                objectNameExtensionIndex = fileFileIDPath.rfind(".")
                fileFileIDPath = fileFileIDPath[: objectNameExtensionIndex + 1]

                kwargs = {
                    "removedtime__isnull": True,
                    fileGroupType: fileGroupIdentifier,
                    "filegrpuse": "original",
                    "currentlocation__startswith": fileFileIDPath,
                }
                original_file = File.objects.get(**kwargs)
                GROUPID = "Group-" + original_file.uuid

            elif use == "TRIM container metadata":
                GROUPID = "Group-%s" % (f.uuid)
                use = "metadata"

            # Special DSPACEMETS processing
            if f.transfer and f.transfer.type == "Dspace" and use == "DSPACEMETS":
                use = "submissionDocumentation"
                admidApplyTo = None
                if GROUPID == "":  # is an AIP identifier
                    GROUPID = f.uuid
                    admidApplyTo = structMapDiv.getparent()

                label = "mets.xml-%s" % (GROUPID)
                dspace_dmdsecs = createDSpaceDMDSec(
                    job, label, itemdirectoryPath, directoryPathSTR, state
                )
                if dspace_dmdsecs:
                    state.dmdSecs.extend(dspace_dmdsecs.values())
                    ids = " ".join(dspace_dmdsecs.keys())
                    if admidApplyTo is not None:
                        admidApplyTo.set("DMDID", ids)
                    else:
                        dspaceMetsDMDID = ids

            # Special Dataverse processing. If there's .tab file, check if
            # there's a Dataverse METS with additional metadata.
            if f.originallocation.endswith(".tab"):
                dv_metadata = create_dataverse_tabfile_dmdsec(
                    job, baseDirectoryPath, os.path.basename(f.originallocation)
                )
                state.dmdSecs.extend(dv_metadata)
                ids = " ".join([ds.get("ID") for ds in dv_metadata])
                if ids != "":
                    fileDiv.attrib["DMDID"] = fileDiv.attrib.get("DMDID", "") + ids

            if GROUPID == "":
                state.error_accumulator.error_count += 1
                job.pyprint(
                    'No groupID for file: "', directoryPathSTR, '"', file=sys.stderr
                )

            if use not in state.globalFileGrps:
                job.pyprint('Invalid use: "%s"' % (use), file=sys.stderr)
                state.error_accumulator.error_count += 1
            else:
                file_elem = etree.SubElement(
                    state.globalFileGrps[use],
                    ns.metsBNS + "file",
                    ID=fileId,
                    GROUPID=GROUPID,
                )
                if use == "original":
                    filesInThisDirectory.append(file_elem)
                # <Flocat xlink:href="objects/file1-UUID" locType="other" otherLocType="system"/>
                newChild(
                    file_elem,
                    ns.metsBNS + "FLocat",
                    sets=[
                        (ns.xlinkBNS + "href", directoryPathSTR),
                        ("LOCTYPE", "OTHER"),
                        ("OTHERLOCTYPE", "SYSTEM"),
                    ],
                )

                if includeAmdSec:
                    AMD, ADMID = getAMDSec(
                        job,
                        f.uuid,
                        directoryPathSTR,
                        use,
                        fileGroupIdentifier,
                        f.transfer_id,
                        itemdirectoryPath,
                        typeOfTransfer,
                        baseDirectoryPath,
                        state,
                        representation_id,
                        tool_tech_mds=tool_tech_mds,
                    )
                    state.amdSecs.append(AMD)
                    file_elem.set("ADMID", ADMID)

    if dspaceMetsDMDID is not None:
        for file_elem in filesInThisDirectory:
            file_elem.set("DMDID", dspaceMetsDMDID)

    return structMapDiv


def build_arranged_structmap(job, original_structmap, sip_uuid):
    """
    Given a structMap, builds a new copy of the structMap with file and directory labels assigned according to their intellectual arrangement.
    Logical arrangement is determined using the levels of description which were assigned to them during SIP arrange.

    :param etree.Element original_structmap: the structMap on which the arranged structMap should be based.
    :param str sip_uuid: the SIP's UUID
    """
    tag_dict = dict(
        SIPArrange.objects.filter(sip_id=sip_uuid).values_list(
            "arrange_path", "level_of_description"
        )
    )
    if not tag_dict:
        return

    structmap = copy.deepcopy(original_structmap)
    structmap.attrib["TYPE"] = "logical"
    structmap.attrib["LABEL"] = "Hierarchical"
    structmap.attrib["ID"] = "structMap_{}".format(uuid4())
    root_div = structmap.find("./mets:div", namespaces=ns.NSMAP)
    del root_div.attrib["TYPE"]
    objects = root_div.find('./mets:div[@LABEL="objects"]', namespaces=ns.NSMAP)

    # The contents of submissionDocumentation and metadata do
    # not have intellectual arrangement, so don't need to be
    # represented in this structMap.
    for label in ("submissionDocumentation", "metadata"):
        div = objects.find('.mets:div[@LABEL="{}"]'.format(label), namespaces=ns.NSMAP)
        if div is not None:
            objects.remove(div)

    # Handle objects level of description separately, since tag paths are relative to objects
    tag = tag_dict.get(".")
    if tag:
        job.pyprint("Adding TYPE=%s for logical structMap element objects" % tag)
        objects.attrib["TYPE"] = tag
    else:
        del objects.attrib["TYPE"]

    for element in objects.iterdescendants():
        if element.tag != ns.metsBNS + "div":
            continue

        # Build the full path relative to objects dir
        path = [element.attrib["LABEL"]]
        parent = element.getparent()
        while parent != objects:
            path.insert(0, parent.attrib["LABEL"])
            parent = parent.getparent()
        relative_location = os.path.join(*path)

        # Certain items won't have a level of description;
        # they should be retained in the tree, but have
        # no TYPE attribute.
        tag = tag_dict.get(relative_location)
        if tag:
            job.pyprint(
                "Adding TYPE=%s for logical structMap element %s"
                % (tag, relative_location)
            )
            element.attrib["TYPE"] = tag
        else:
            del element.attrib["TYPE"]

    return structmap


def find_source_metadata(path):
    """
    Returns lists of all metadata to be referenced in the final document.
    This includes transfer metadata (embedded), and any XML metadata contained
    in the `metadata/sourceMD` directory from the original transfer (mdRef).

    The first returned list is the set of transfer metadata; the second is
    all other metadata to reference.
    """
    transfer = []
    source = []
    for dirpath, subdirs, filenames in scandir.walk(path):
        if "transfer_metadata.xml" in filenames:
            transfer.append(os.path.join(dirpath, "transfer_metadata.xml"))

        if "sourceMD" in subdirs:
            pattern = os.path.join(dirpath, "sourceMD", "*.xml")
            source.extend(glob(pattern))

    return transfer, source


def find_bag_metadata(job, bag_logs_path):
    try:
        return Bag(bag_logs_path).info
    except BagError:
        job.pyprint(
            "Unable to locate or parse bag metadata at: {}".format(bag_logs_path),
            file=sys.stderr,
        )
        return {}


def create_object_metadata(job, struct_map, baseDirectoryPath, state):
    transfer_metadata_path = os.path.join(
        baseDirectoryPath, "objects/metadata/transfers"
    )
    transfer, source = find_source_metadata(transfer_metadata_path)

    paths = glob(
        os.path.join(baseDirectoryPath, "logs", "transfers", "**", "logs", "BagIt")
    )
    bag_info = [find_bag_metadata(job, path) for path in paths]

    if not transfer and not source and not bag_info:
        return

    state.globalAmdSecCounter += 1
    label = "amdSec_{}".format(state.globalAmdSecCounter)
    struct_map.set("ADMID", label)

    source_md_counter = 1

    el = etree.Element(ns.metsBNS + "amdSec", {"ID": label})

    for filename in transfer:
        sourcemd = etree.SubElement(
            el, ns.metsBNS + "sourceMD", {"ID": "sourceMD_{}".format(source_md_counter)}
        )
        mdwrap = etree.SubElement(sourcemd, ns.metsBNS + "mdWrap", {"MDTYPE": "OTHER"})
        xmldata = etree.SubElement(mdwrap, ns.metsBNS + "xmlData")
        source_md_counter += 1
        parser = etree.XMLParser(remove_blank_text=True)
        md = etree.parse(filename, parser)
        xmldata.append(md.getroot())

    for filename in source:
        sourcemd = etree.SubElement(
            el, ns.metsBNS + "sourceMD", {"ID": "sourceMD_{}".format(source_md_counter)}
        )
        source_md_counter += 1
        attributes = {
            ns.xlinkBNS + "href": os.path.relpath(filename, baseDirectoryPath),
            "MDTYPE": "OTHER",
            "LOCTYPE": "OTHER",
            "OTHERLOCTYPE": "SYSTEM",
        }
        etree.SubElement(sourcemd, ns.metsBNS + "mdRef", attributes)

    for bagdata in bag_info:
        # If there are no tags, skip creating an element
        if not bagdata:
            continue

        sourcemd = etree.SubElement(
            el, ns.metsBNS + "sourceMD", {"ID": "sourceMD_{}".format(source_md_counter)}
        )
        source_md_counter += 1
        mdwrap = etree.SubElement(
            sourcemd, ns.metsBNS + "mdWrap", {"MDTYPE": "OTHER", "OTHERMDTYPE": "BagIt"}
        )
        xmldata = etree.SubElement(mdwrap, ns.metsBNS + "xmlData")
        bag_metadata = etree.SubElement(xmldata, "transfer_metadata")
        for key, value in bagdata.items():
            if not isinstance(value, list):
                value = [value]
            for v in value:
                try:
                    bag_tag = etree.SubElement(bag_metadata, key)
                except ValueError:
                    job.pyprint(
                        "Skipping bag key {}; not a valid" " XML tag name".format(key),
                        file=sys.stderr,
                    )
                    continue
                bag_tag.text = v

    return el


# WELLCOME TODO: Note, we no longer output METS validation scripts here
# as PIM doesn't really work for us any-more.
def write_mets(tree, filename):
    """
    Write tree to filename, and a validate METS form.

    :param ElementTree tree: METS ElementTree
    :param str filename: Filename to write the METS to
    """

    tree.write(filename, pretty_print=True, xml_declaration=True, encoding="utf-8")


def get_paths_as_fsitems(baseDirectoryPath, objectsDirectoryPath):
    """Get all paths in the SIP as ``FSItem`` instances before deleting any
    empty directories. These filesystem items are crucially ordered so that
    directories always precede the paths of the items they contain.
    :param string baseDirectoryPath: path to the AIP with a trailing slash
    :param string objectsDirectoryPath: path to the AIP's object directory
    :returns: list of ``FSItem`` instances representing paths
    """
    all_fsitems = []
    for root, dirs, files in scandir.walk(objectsDirectoryPath):
        root = root.replace(baseDirectoryPath, "", 1)
        if files or dirs:
            all_fsitems.append(FSItem("dir", root, is_empty=False))
        else:
            all_fsitems.append(FSItem("dir", root, is_empty=True))
        for file_ in files:
            all_fsitems.append(
                FSItem("file", os.path.join(root, file_), is_empty=False)
            )
    return all_fsitems


# WELLCOME TODO: WILL WE BE ABLE TO REMOVE THIS?
def get_normative_structmap(
    baseDirectoryPath, objectsDirectoryPath, directories, state
):
    """Get a normative structMap representing the paths within a SIP.
    :param string baseDirectoryPath: path to the AIP with a trailing slash
    :param string objectsDirectoryPath: path to the AIP's object directory
    :param dict directories: maps directory model instance ``currentlocation``
    :returns: etree Element representing structMap XML
    """
    normativeStructMap = etree.Element(
        ns.metsBNS + "structMap",
        TYPE="logical",
        ID="structMap_{}".format(state.globalStructMapCounter),
        LABEL="Normative Directory Structure",
    )
    normativeStructMapDiv = etree.SubElement(
        normativeStructMap,
        ns.metsBNS + "div",
        TYPE="Directory",
        LABEL=os.path.basename(baseDirectoryPath.rstrip("/")),
    )
    all_fsitems = get_paths_as_fsitems(baseDirectoryPath, objectsDirectoryPath)
    add_normative_structmap_div(all_fsitems, normativeStructMapDiv, directories, state)
    return normativeStructMap


def add_normative_structmap_div(
    all_fsitems, root_el, directories, state, path_to_el=None, representation_id=None
):
    """Document all of the file/dir paths in ``all_fsitems`` in the
    lxml._Element instance ``root_el``. This constructs the <mets:div> element
    tree under the TYPE "logical" structMap with LABEL "Normative Directory
    Structure". Said structural map documents all files and directories,
    including empty directories, which latter are not documented in the
    physical structMap.
    :param list all_fsitems: contains ``FSItem`` instances crucially ordered so
        that parent directories always precede their children.
    :param lxml._Element root_el: root element for documenting the directory
        structure.
    :param dict directories: maps directory model instance ``currentlocation``
        values to directories for any and all directory model instances
        associated to the current SIP.
    :param dict path_to_el: maps paths from ``all_fsitems`` to the lxml elements
        that document them.
    :returns: None.
    """
    path_to_el = path_to_el or {"": root_el}
    for fsitem in all_fsitems:
        parent_path = os.path.dirname(fsitem.path)
        basename = os.path.basename(fsitem.path)
        try:
            parent_el = path_to_el[parent_path]
        except KeyError:
            logger.info(
                "Unable to find parent path {} of item {} in path_to_el\n{}".format(
                    parent_path, fsitem.path, pprint.pformat(path_to_el)
                )
            )
            raise
        el = etree.SubElement(
            parent_el,
            ns.metsBNS + "div",
            TYPE={"dir": "Directory"}.get(fsitem.type, "Item"),
            LABEL=basename,
        )
        if fsitem.is_empty:  # Create dmdSec for empty dirs
            if fsitem.path.startswith("objects/metadata/transfers/"):
                continue
            fsitem_path = "%SIPDirectory%" + fsitem.path
            dir_mdl = directories.get(
                fsitem_path,
                directories.get(fsitem_path.rstrip("/"), FakeDirMdl(uuid=str(uuid4()))),
            )
            dirDmdSec = getDirDmdSec(dir_mdl, fsitem_path, representation_id)
            state.globalDmdSecCounter += 1
            state.dmdSecs.append(dirDmdSec)
            dir_dmd_id = "dmdSec_" + str(state.globalDmdSecCounter)
            dirDmdSec.set("ID", dir_dmd_id)
            el.set("DMDID", dir_dmd_id)
        path_to_el[fsitem.path] = el


def create_mets(job, opts, tool_tech_mds=None):
    """Create METS

    Do all the things, and create the METS!

    Wellcome TODO: this is largely original code, and will need a
    refactor accordingly.
    """
    state = MetsState()
    SIP_TYPE = opts.sip_type
    baseDirectoryPath = opts.baseDirectoryPath

    XMLFile = opts.xmlFile
    XMLFile = XMLFile.replace("METS.", "METS-reduced.")

    baseDirectoryPath = opts.baseDirectoryPath
    baseDirectoryPathString = "%%%s%%" % (opts.baseDirectoryPathString)
    fileGroupIdentifier = opts.fileGroupIdentifier
    fileGroupType = opts.fileGroupType
    includeAmdSec = opts.amdSec
    createNormativeStructmap = opts.createNormativeStructmap
    keepNormativeStructmap = createNormativeStructmap

    # WELLCOME TODO: Do we want this UUID to come from anywhere else?
    # It's somewhat arbitrary when it is just a new UUID but maybe
    # that's okay. Do we need it to persist in the dashboard database
    # at all?
    representation_id = str(uuid.uuid4())

    # If reingesting, do not create a new METS, just modify existing one
    if "REIN" in SIP_TYPE:
        job.pyprint("Updating METS during reingest")
        # fileGroupIdentifier is SIPUUID, baseDirectoryPath is SIP dir,
        # don't keep existing normative structmap if creating one
        root = create_mets_reingest.archivematicaCreateMETSReingest.update_mets(
            job,
            baseDirectoryPath,
            fileGroupIdentifier,
            state,
            keep_normative_structmap=keepNormativeStructmap,
        )
        tree = etree.ElementTree(root)
        write_mets(tree, XMLFile)

        job.set_status(0)
        return
    # End reingest

    state.CSV_METADATA = parseMetadata(job, baseDirectoryPath, state)

    baseDirectoryPath = os.path.join(baseDirectoryPath, "")
    objectsDirectoryPath = os.path.join(baseDirectoryPath, "objects")

    # Fetch any ``Directory`` objects in the database that are contained within
    # this SIP and return them as a dict from relative paths to UUIDs. (See
    # createSIPfromTransferObjects.py for the association of ``Directory``
    # objects to a ``SIP``.
    directories = {
        d.currentlocation.rstrip("/"): d
        for d in Directory.objects.filter(sip_id=fileGroupIdentifier.encode()).all()
    }

    state.globalStructMapCounter += 1
    structMap = etree.Element(
        ns.metsBNS + "structMap",
        TYPE="physical",
        ID="structMap_{}".format(state.globalStructMapCounter),
        LABEL="Archivematica default",
    )
    sip_dir_name = os.path.basename(baseDirectoryPath.rstrip("/"))
    structMapDiv = etree.SubElement(
        structMap, ns.metsBNS + "div", TYPE="Directory", LABEL=sip_dir_name
    )

    if createNormativeStructmap:
        # Create the normative structmap.
        state.globalStructMapCounter += 1
        normativeStructMap = get_normative_structmap(
            baseDirectoryPath, objectsDirectoryPath, directories, state
        )
    else:
        job.pyprint("Skipping creation of normative structmap")
        normativeStructMap = None

    # Delete empty directories, see #8427
    for root, _, _ in scandir.walk(baseDirectoryPath, topdown=False):
        try:
            # os.rmdir(root)
            job.pyprint("Deleted empty directory", root)
        except OSError:
            pass

    # WELLCOME TODO: Replace other file object gathering code in this
    # module with this overall when there is a chance...
    #
    # Get the fsentry objects we want to work with in this AIP.
    fsentry_tree = _get_fsentry_tree(opts)

    # WELLCOME TODO: NEW CODE ENTRY POINT...
    generate_id_and_repr(
        representation_id, fsentry_tree, sip_dir_name, structMapDiv, opts, state
    )

    # WELLCOME TODO: WILL WE BE ABLE TO REMOVE THIS?
    structMapDivObjects = createFileSec(
        job,
        objectsDirectoryPath,
        structMapDiv,
        baseDirectoryPath,
        baseDirectoryPathString,
        fileGroupIdentifier,
        fileGroupType,
        directories,
        state,
        includeAmdSec=includeAmdSec,
        representation_id=representation_id,
        tool_tech_mds=tool_tech_mds,
    )

    el = create_object_metadata(job, structMapDivObjects, baseDirectoryPath, state)
    if el:
        state.amdSecs.append(el)

    # In an AIC, the metadata dir is not inside the objects dir
    metadataDirectoryPath = os.path.join(baseDirectoryPath, "metadata")
    # WELLCOME TODO: WILL WE BE ABLE TO REMOVE THIS?
    createFileSec(
        job,
        metadataDirectoryPath,
        structMapDiv,
        baseDirectoryPath,
        baseDirectoryPathString,
        fileGroupIdentifier,
        fileGroupType,
        directories,
        state,
        includeAmdSec=includeAmdSec,
        tool_tech_mds=tool_tech_mds,
    )

    fileSec = etree.Element(ns.metsBNS + "fileSec")
    for group in state.globalFileGrpsUses:  # state.globalFileGrps.itervalues():
        grp = state.globalFileGrps[group]
        if len(grp) > 0:
            fileSec.append(grp)

    rootNSMap = {"mets": ns.metsNS, "xsi": ns.xsiNS, "xlink": ns.xlinkNS}
    root = etree.Element(
        ns.metsBNS + "mets",
        nsmap=rootNSMap,
        attrib={
            "{"
            + ns.xsiNS
            + "}schemaLocation": "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version1121/mets.xsd"
        },
    )
    etree.SubElement(root, ns.metsBNS + "metsHdr").set(
        "CREATEDATE", timezone.now().strftime("%Y-%m-%dT%H:%M:%S")
    )

    dc = createDublincoreDMDSecFromDBData(
        job, SIPMetadataAppliesToType, fileGroupIdentifier, baseDirectoryPath, state
    )
    if dc is not None:
        (dmdSec, ID) = dc
        if structMapDivObjects is not None:
            structMapDivObjects.set("DMDID", ID)
        else:
            # AICs have no objects directory but do have DC metadata
            # Attach the DC metadata to the top level SIP div
            # See #9822 for details
            structMapDiv.set("DMDID", ID)
        root.append(dmdSec)

    # Look for Dataverse specific descriptive metatdata.
    dv = create_dataverse_sip_dmdsec(job, baseDirectoryPath)
    for dmdSec in dv:
        dmdid = dmdSec.attrib["ID"]
        dmdids = structMapDivObjects.get("DMDID", "") + " " + dmdid
        structMapDivObjects.set("DMDID", dmdids)
        root.append(dmdSec)

    for dmdSec in state.dmdSecs:
        root.append(dmdSec)

    for amdSec in state.amdSecs:
        root.append(amdSec)

    # The agent object is its own amdSec and appended to the others, and
    # before the fileSec in this case.
    file_objs = fsentry_tree.retrieve_file_objs()
    root.append(create_agent_premis_obj(job, file_objs, opts, state))

    # WELLCOME TODO: We replace the three sections below with the
    # three preceding lines. The file_sec, structmap, and normative
    # structmap are all created using an updated mechanism in this
    # work which can replace some of the legacy code if it proves
    # through testing to be valid/accurate/correct etc.
    #
    root.append(fileSec)
    root.append(structMap)
    if normativeStructMap is not None:
        root.append(normativeStructMap)
    #
    # WELLCOME TODO: There are still weaknesses with trying to use the
    # transfer METS mechanism to do what we want to do here. Largely
    # with the amdSec indices which are getting confused all over the
    # place. metsrw wants to know about the context of the document as
    # a whole. We're trying to swap pieces in and out until we've
    # refactored the piece.
    # file_sec, structmap, normative_structmap = create_mets_structure(job, opts)
    # root.append(file_sec)
    # root.append(structmap)
    # if createNormativeStructmap:
    #    root.append(normative_structmap)

    for custom_structmap in include_custom_structmap(job, baseDirectoryPath, state):
        root.append(custom_structmap)

    if state.trimStructMap is not None:
        root.append(state.trimStructMap)

    arranged_structmap = build_arranged_structmap(job, structMap, fileGroupIdentifier)
    if arranged_structmap is not None:
        root.append(arranged_structmap)

    printSectionCounters = True
    if printSectionCounters:
        job.pyprint("DmdSecs:", state.globalDmdSecCounter)
        job.pyprint("AmdSecs:", state.globalAmdSecCounter)
        job.pyprint("TechMDs:", state.globalTechMDCounter)
        job.pyprint("RightsMDs:", state.globalRightsMDCounter)
        job.pyprint("DigiprovMDs:", state.globalDigiprovMDCounter)

    tree = etree.ElementTree(root)
    write_mets(tree, XMLFile)

    job.pyprint(XMLFile, "exists", os.path.exists(XMLFile))
    job.set_status(state.error_accumulator.error_count)


# ----------------------------------------------------------------------
# METS STRUCTURE CODE BELOW
# ----------------------------------------------------------------------


def retrieve_file_sec(mets):
    """Retrieve file sec"""
    mets_root = mets.serialize()
    file_sec = mets_root.find(".//mets:fileSec", namespaces=ns.NSMAP)
    return file_sec


def retrieve_physical_structmap(mets):
    """Retrieve physical structmap"""
    mets_root = mets.serialize()
    struct_map = mets_root.find(
        ".//mets:structMap[@TYPE='physical']", namespaces=ns.NSMAP
    )
    return struct_map


def retrieve_logical_structmap(mets):
    """Retrieve logical structmap"""
    mets_root = mets.serialize()
    struct_map = mets_root.find(
        ".//mets:structMap[@TYPE='logical']", namespaces=ns.NSMAP
    )
    return struct_map


def create_mets_structure(job, opts):
    """Create tool mets

    Outputs a structmap, fileSec, and PREMIS objects containing largely
    just the PREMIS object characteristics extension which holds the
    tool output for objects from Archivematica's processing via the FPR.

    WELLCOME TODO:

        * How are amdSec counts guaranteed? (They are, but how was it
          achieved?)
        * This pattern is almost exactly the same as that for the tool
          output, so how do we use it across both scripts and save the
          duplication of effort. One option might be to output a chunk
          of it from the tool output, and then as we do here, strip
          out the duplicate segments relating to structure.
        * This work is also largely a cut-down duplication of Cole's
          work, how do we bring all three scripts together usefully? The
          transfer script is: https://git.io/JJK8a
        * There is so much camelCase in this original module, let's try
          and reduce that.
        * Other TODOs in-line.

    """
    aip_uuid = opts.fileGroupIdentifier

    fsentry_tree = _get_fsentry_tree(opts)
    fsentry_tree.scan()

    mets = metsrw.METSDocument()
    mets.objid = str(aip_uuid)
    mets.append_file(fsentry_tree.root_node)

    file_sec = retrieve_file_sec(mets)
    structmap = retrieve_physical_structmap(mets)
    normative_structmap = retrieve_logical_structmap(mets)

    return file_sec, structmap, normative_structmap
