# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import lxml.etree as etree
import os

import metsrw

from .fs_entries_tree import FSEntriesTree
from main.models import File, SIP

import namespaces as ns

# from custom_handlers import get_script_logger
import logging

logger = logging


def remove_logical_structmap(mets):
    """Remove the logical structmap

    Remove logical structmap is output by default from mets-reader-
    writer, but it isn't a default argument in Archivematica.
    """
    mets_root = mets.serialize()
    struct_map = mets_root.find(
        ".//mets:structMap[@TYPE='logical']", namespaces=ns.NSMAP
    )
    mets_root.remove(struct_map)
    mets = etree.ElementTree(mets_root)
    return mets_root


def find_tool_tech_mds(mets, aip_uuid):
    """Find tech mds

    Retrieve all of the tech_mds from the tools document and return
    them for use in the primary mets via a lookup table.
    """
    tech_md_arr = {}
    mets_root = mets.serialize()
    tech_mds = mets_root.findall(".//mets:techMD", namespaces=ns.NSMAP)
    for tech_md in tech_mds:
        file_name = tech_md.find(".//premis:originalName", namespaces=ns.NSMAP).text
        try:
            file_obj = File.objects.get(sip_id=aip_uuid, originallocation=file_name)
            premis_id = file_obj.uuid
        except File.DoesNotExist:
            continue
        if premis_id in tech_md_arr:
            # WELLCOME TODO; when cleaning up, let's challenge the assumption
            # of one tech_md per file id here. What happens if there are
            # multiple tools per output for example.
            raise ValueError("Value already seen...")
        tech_md_arr[premis_id] = tech_md.get("ID")
    return tech_md_arr


def create_tool_mets(job, opts):
    """Create tool mets

    Outputs a structmap, fileSec, and PREMIS objects containing largely
    just the PREMIS object characteristics extension which holds the
    tool output for objects from Archivematica's processing via the FPR.
    """

    # Based entirely on create_transfer_METS from Cole...
    # https://git.io/JJK8a

    XMLFile = opts.xmlFile
    XMLFile = XMLFile.replace("METS.", "METS-tools.")

    # WELLCOME TODO: We can convert these variables to camel_case which
    # would be a start towards refactoring this legacy piece.

    base_directory_path = opts.baseDirectoryPath
    base_directory_path_string = "%%%s%%" % (opts.baseDirectoryPathString)
    aip_uuid = opts.fileGroupIdentifier
    file_group_type = opts.fileGroupType
    include_amd_sec = opts.amdSec
    create_normative_structmap = opts.createNormativeStructmap

    # WELLCOME TODO: Delete this stuff... it's just garnish to help
    # refactoring, i.e. what is it all??
    job.pyprint("____________")
    job.pyprint("")
    job.pyprint("1. dir path", base_directory_path)
    job.pyprint("2. path string", base_directory_path_string)
    job.pyprint("3. aip uuid", aip_uuid)
    job.pyprint("4. file grp type", file_group_type)
    job.pyprint("5. inc amdsec", include_amd_sec)
    job.pyprint("6. norm structmap", create_normative_structmap)
    job.pyprint("")
    job.pyprint("‾‾‾‾‾‾‾‾‾‾‾‾")

    # Wellcome TODO: this is way too finicky...
    base_directory_path = os.path.join(base_directory_path, "")
    objects_directory_path = os.path.join(base_directory_path, "objects")

    objects_directory_path = base_directory_path

    mets = metsrw.METSDocument()
    mets.objid = str(aip_uuid)

    try:
        aip = SIP.objects.get(uuid=aip_uuid)
    except SIP.DoesNotExist:
        logger.info("No record in database for transfer: %s", aip_uuid)
        raise

    fsentry_tree = FSEntriesTree(
        objects_directory_path, base_directory_path_string, aip
    )
    fsentry_tree.scan()

    mets.append_file(fsentry_tree.root_node)

    # WELLCOME TODO; We might attempt to perform validation differently
    # i.e. via a microservice:
    #
    # https://github.com/artefactual/archivematica/pull/1590
    #
    # NB. Also, getting intermittent xlink issues... LoC problems?
    #
    # is_valid, _ = metsrw.xsd_validate(mets.serialize())
    # if not is_valid:
    #    raise ValueError("METS doesn't validate")

    # The primary METS needs a mapping to the new tech MD values to
    # create a mapping that can be useful to the reader.
    tool_tech_mds = find_tool_tech_mds(mets, aip_uuid=aip_uuid)

    # WELLCOME TODO: This is very much a hack until we can solve:
    # https://github.com/archivematica/Issues/issues/1272
    mets = remove_logical_structmap(mets)

    mets = etree.ElementTree(mets)
    mets.write(XMLFile, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    return tool_tech_mds
