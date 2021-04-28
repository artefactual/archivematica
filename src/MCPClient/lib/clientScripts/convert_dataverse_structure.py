#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Convert Dataverse Structure

Given a transfer type Dataverse, read the metadata submission object
``dataset.json`` to generate a Dataverse METS.xml file. This METS file will
then later be used to create a Transfer METS.xml document as part of the
Archivematica submission information package (SIP).

The METS.xml will reflect various properties of the ``dataset.json`` file. An
example of a specific feature of Dataverse is the existence of Bundle objects
for Tabular data. Bundles contain derivatives of a tabular data file that are
created by Dataverse to enable the data to be interacted with using as wide a
range of tools as possible. These Derivatives are transcribed to the Dataverse
METS.xml.

The module will also extract a minimal Data Documentation Initiative (DDI) XML
structure from the dataset metadata.

More information about Dataverse in Archivematica can be found in the
Archivematica documentation:

https://wiki.archivematica.org/Dataverse
"""

import json
import os
import sys
import uuid

from lxml import etree

# Database functions requires Django to be set up.
import django
import six

django.setup()

from custom_handlers import get_script_logger
import metsrw


logger = get_script_logger("archivematica.mcp.client.convert_dataverse_struct")


class ConvertDataverseError(Exception):
    """Exception class for failures that might occur during the execution of
    this script.
    """


# Mapping from originalFormatLabel in dataset.json to file extension. The
# values here are associated with Dataverse Bundles, created when Tabular data
# is ingested, see: http://guides.dataverse.org/en/latest/user/dataset-management.html?highlight=bundle
# The formats supported for tabluar data ingests are here:
# http://guides.dataverse.org/en/latest/user/tabulardataingest/supportedformats.html
EXTENSION_MAPPING = {
    "Comma Separated Values": ".csv",
    "MS Excel (XLSX)": ".xlsx",
    "R Data": ".RData",
    "SPSS Portable": ".por",
    "SPSS SAV": ".sav",
    "Stata Binary": ".dta",
    "Stata 13 Binary": ".dta",
    "UNKNOWN": "UNKNOWN",
}


def output_ddi_elems_info(job, ddi_elems):
    """Cycle through the DDI elements retrieved from the dataset.json file.
    Output information about the dataset to the user.
    """
    draft = False
    job.pyprint("Fields retrieved from Dataverse:")
    for ddi_k, ddi_v in six.iteritems(ddi_elems):
        if ddi_k == "Version Type" and ddi_v == "DRAFT":
            draft = True
        job.pyprint("{}: {}".format(ddi_k, ddi_v))
    # Provide information to the user where data in the Dataverse may cause the
    # transfer to fail, e.g. when transferred in a DRAFT state.
    if draft:
        job.pyprint(
            "Dataset is in a DRAFT state and may not transfer correctly",
            file=sys.stderr,
        )


def get_ddi_title(dataset_md_latest):
    """Retrieve the title of the dataset for the DDI XML snippet."""
    citation = dataset_md_latest.get("metadataBlocks", {}).get("citation")
    fields = citation.get("fields", None)
    if fields:
        for field in fields:
            if field.get("typeName") == "title":
                return field.get("value", "").strip()
    raise ConvertDataverseError(
        "Unable to retrieve DDI metadata fields from dataset.json"
    )


def get_ddi_author(dataset_md_latest):
    """Retrieve the authors of the the dataset for the DDI XML snippet.
    Importantly for the reader, the information is captured in an array of
    dictionaries. The array preserves order which is important in academic
    publishing.
    """
    authors = []
    citation = dataset_md_latest.get("metadataBlocks", {}).get("citation")
    fields = citation.get("fields", None)
    if fields:
        for field in fields:
            if field.get("typeName") == "author":
                author_list = field.get("value")
                for author in author_list:
                    entry = {}
                    entry["affiliation"] = (
                        author.get("authorAffiliation", {}).get("value", "").strip()
                    )
                    entry["name"] = (
                        author.get("authorName", {}).get("value", "").strip()
                    )
                    authors.append(entry)
        return authors
    raise ConvertDataverseError(
        "Unable to retrieve DDI metadata fields from dataset.json"
    )


def create_ddi(job, json_metadata, dataset_md_latest):
    """Create the DDI dmdSec from the JSON metadata."""
    ddi_elems = {}
    try:
        ddi_elems["Title"] = get_ddi_title(dataset_md_latest)
        ddi_elems["Author"] = get_ddi_author(dataset_md_latest)
    except ConvertDataverseError as err:
        logger.error(err)
        raise
    ddi_elems["PID Type"] = json_metadata.get("protocol", "")
    ddi_elems["IDNO"] = json_metadata.get("persistentUrl", "")
    ddi_elems["Version Date"] = dataset_md_latest.get("releaseTime", "")
    ddi_elems["Version Type"] = dataset_md_latest.get("versionState", "")
    ddi_elems["Version Number"] = "{}.{}".format(
        dataset_md_latest.get("versionNumber", ""),
        dataset_md_latest.get("versionMinorNumber", ""),
    )
    ddi_elems["Restriction Text"] = dataset_md_latest.get("termsOfUse", "")
    ddi_elems["Distributor Text"] = json_metadata.get("publisher", "")

    # Provide some log information to the user.
    output_ddi_elems_info(job, ddi_elems)

    # Create XML.
    nsmap = {"ddi": "http://www.icpsr.umich.edu/DDI"}
    ddins = "{" + nsmap["ddi"] + "}"
    ddi_root = etree.Element(ddins + "codebook", nsmap=nsmap)
    ddi_root.attrib["version"] = "2.5"

    root_ns = "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
    dv_ns = (
        "http://www.ddi:codebook:2_5 "
        "http://www.ddialliance.org/Specification/DDI-Codebook/2.5/"
        "XMLSchema/codebook.xsd"
    )
    ddi_root.attrib[root_ns] = dv_ns

    stdydscr = etree.SubElement(ddi_root, ddins + "stdyDscr", nsmap=nsmap)
    citation = etree.SubElement(stdydscr, ddins + "citation", nsmap=nsmap)

    titlstmt = etree.SubElement(citation, ddins + "titlStmt", nsmap=nsmap)
    etree.SubElement(titlstmt, ddins + "titl", nsmap=nsmap).text = ddi_elems["Title"]

    etree.SubElement(
        titlstmt, ddins + "IDNo", agency=ddi_elems["PID Type"]
    ).text = ddi_elems["IDNO"]

    rspstmt = etree.SubElement(citation, ddins + "rspStmt")

    for auth in ddi_elems["Author"]:
        etree.SubElement(
            rspstmt, ddins + "AuthEnty", affiliation=auth.get("affiliation", "")
        ).text = auth.get("name", "")

    diststmt = etree.SubElement(citation, ddins + "distStmt")
    etree.SubElement(diststmt, ddins + "distrbtr").text = ddi_elems["Distributor Text"]

    verstmt = etree.SubElement(citation, ddins + "verStmt")
    etree.SubElement(
        verstmt,
        ddins + "version",
        date=ddi_elems["Version Date"],
        type=ddi_elems["Version Type"],
    ).text = ddi_elems["Version Number"]

    dataaccs = etree.SubElement(stdydscr, ddins + "dataAccs")
    usestmt = etree.SubElement(dataaccs, ddins + "useStmt")
    etree.SubElement(usestmt, ddins + "restrctn").text = ddi_elems["Restriction Text"]

    return ddi_root


def display_checksum_for_user(job, fname, checksum_value, checksum_type="MD5"):
    """Provide some feedback to the user that enables them to understand what
    this script is doing in the Dataverse workflow.
    """
    job.pyprint(
        "Checksum for '{}' retrieved from dataset.json: {} ({})".format(
            fname, checksum_value, checksum_type
        )
    )


def create_bundle(job, tabfile_json):
    """Create the FSEntry objects for the various files in a Dataverse bundle
    identified initially by a ```.tab``` file being requested from the
    Dataverse API.

    A bundle is a collection of multiple representations of a tabular data
    file. Bundles are created by Dataverse to allow interaction with as wide a
    range of tools as possible.

    Documentation on Bundles can be found on the Dataverse pages:

       * http://guides.dataverse.org/en/latest/user/dataset-management.html?highlight=bundle
    """
    # Base name is .tab with suffix stripped
    tabfile_name = tabfile_json.get("label")
    if tabfile_name is None:
        return None

    # Else, continue processing.
    job.pyprint("Creating entries for tabfile bundle {}".format(tabfile_name))
    base_name = tabfile_name[:-4]
    bundle = metsrw.FSEntry(path=base_name, type="Directory")
    # Find the original file and add it to the METS FS Entries.
    tabfile_datafile = tabfile_json.get("dataFile")
    fname = None
    ext = EXTENSION_MAPPING.get(
        tabfile_datafile.get("originalFormatLabel", ""), "UNKNOWN"
    )
    logger.info("Retrieved extension mapping value: %s", ext)
    logger.info(
        "Original file format listed as %s",
        tabfile_datafile.get("originalFileFormat", "None"),
    )
    if ext == "UNKNOWN":
        fname = tabfile_datafile.get("filename")
        logger.info("Original Format Label is UNKNOWN, using filename: %s", fname)
    if fname is None:
        fname = "{}{}".format(base_name, ext)
    checksum_value = tabfile_datafile.get("md5")
    if checksum_value is None:
        return None
    display_checksum_for_user(job, fname, checksum_value)
    original_file = metsrw.FSEntry(
        path="{}/{}".format(base_name, fname),
        use="original",
        file_uuid=str(uuid.uuid4()),
        checksumtype="MD5",
        checksum=checksum_value,
    )
    bundle.add_child(original_file)
    if tabfile_datafile.get("originalFormatLabel") != "R Data":
        # RData derivative
        fsentry = metsrw.FSEntry(
            path="{}/{}.RData".format(base_name, base_name),
            use="derivative",
            derived_from=original_file,
            file_uuid=str(uuid.uuid4()),
        )
        bundle.add_child(fsentry)

    # Bundle contents described earlier in this module are expected to remain
    # consistent. Among the additional data files in support of a table-based
    # dataset there are supposed to be three citation files. These are added
    # as FSEntry objects below.

    # Tabfile
    fsentry = metsrw.FSEntry(
        path="{}/{}".format(base_name, tabfile_datafile.get("filename")),
        use="derivative",
        derived_from=original_file,
        file_uuid=str(uuid.uuid4()),
    )
    fsentry.add_dmdsec(
        md="{}/{}-ddi.xml".format(base_name, base_name),
        mdtype="DDI",
        mode="mdref",
        label="{}-ddi.xml".format(base_name),
        loctype="OTHER",
        otherloctype="SYSTEM",
    )
    bundle.add_child(fsentry)
    # -ddi.xml
    fsentry = metsrw.FSEntry(
        path="{}/{}-ddi.xml".format(base_name, base_name),
        use="metadata",
        derived_from=original_file,
        file_uuid=str(uuid.uuid4()),
    )
    bundle.add_child(fsentry)
    # citation - endnote
    fsentry = metsrw.FSEntry(
        path="{}/{}citation-endnote.xml".format(base_name, base_name),
        use="metadata",
        derived_from=original_file,
        file_uuid=str(uuid.uuid4()),
    )
    bundle.add_child(fsentry)
    # citation - ris
    fsentry = metsrw.FSEntry(
        path="{}/{}citation-ris.ris".format(base_name, base_name),
        use="metadata",
        derived_from=original_file,
        file_uuid=str(uuid.uuid4()),
    )
    bundle.add_child(fsentry)
    # citation - bib
    fsentry = metsrw.FSEntry(
        path="{}/{}citation-bib.bib".format(base_name, base_name),
        use="metadata",
        derived_from=original_file,
        file_uuid=str(uuid.uuid4()),
    )
    bundle.add_child(fsentry)
    return bundle


def retrieve_terms_of_access(dataset_md_latest):
    """Return a tuple that can be used to direct users to information about a
    dataset if it is restricted.
    """
    return dataset_md_latest.get("termsOfAccess")


def test_if_zip_in_name(fname):
    """Check if a file-path ends in a .zip extension. If so, return true. This
    helps us to log some information about the characteristics of the package
    as we go.
    """
    ext_ = os.path.splitext(fname)[1]
    if ext_.lower() == ".zip":
        return True
    return False


def add_ddi_xml(job, sip, json_metadata, dataset_md_latest):
    """Create a DDI XML data block and add this to the METS."""
    ddi_root = create_ddi(job, json_metadata, dataset_md_latest)
    if ddi_root is None:
        return None
    sip.add_dmdsec(md=ddi_root, mdtype="DDI")
    return sip


def add_metadata_ref(sip, md_name, md_loc):
    """Add a single mdref to the METS file."""
    sip.add_dmdsec(
        md=md_loc,
        mdtype="OTHER",
        mode="mdref",
        label=md_name,
        loctype="OTHER",
        otherloctype="SYSTEM",
    )
    return sip


def add_md_dir_to_structmap(sip):
    """Add the metadata directory to the structmap."""
    md_dir = metsrw.FSEntry(path="metadata", use=None, type="Directory")
    sip.add_child(md_dir)
    # Add dataset.json to the fileSec output.
    fsentry = metsrw.FSEntry(
        path="metadata/dataset.json", use="metadata", file_uuid=str(uuid.uuid4())
    )
    # Add dataset.json to the metadata fileSec group.
    md_dir.add_child(fsentry)
    return sip


def add_dataset_files_to_md(job, sip, dataset_md_latest, contact_information):
    """Add file entries to the Dataverse METS document."""

    # Add original files to the METS document.
    files = dataset_md_latest.get("files")
    if not files:
        return None

    # Signal to users the existence of zip files in this transfer.
    zipped_file = False

    # Signal to users that this transfer might consist of metadata only.
    if len(files) == 0:
        logger.info(
            "Metadata only transfer? There are no file entries in this "
            "transfer's metadata."
        )

    for file_json in files:
        is_restricted = file_json.get("restricted")
        if is_restricted is True and contact_information:
            logger.error(
                "Restricted dataset files may not have transferred " "correctly: %s",
                contact_information,
            )

        data_file = file_json.get("dataFile", {})
        if data_file.get("filename", "").endswith(".tab"):
            # A Tabular Data File from Dataverse will consist of an original
            # tabular format submitted by the researcher plus multiple
            # different representations. We need to map that here.
            bundle = create_bundle(job, file_json)
            if bundle:
                sip.add_child(bundle)
            else:
                logger.error(
                    "Create Dataverse transfer METS failed. " "Bundle returned: %s",
                    bundle,
                )
                return None
        else:
            path_ = None
            if data_file:
                path_ = data_file.get("filename")
            if path_:
                if test_if_zip_in_name(path_):
                    # provide some additional logging around the contents of the
                    # dataset we're processing.
                    if not zipped_file:
                        zipped_file = True
                        logger.info("Non-bundle .zip file found in the dataset.")
                checksum_value = data_file.get("md5")
                if checksum_value is None:
                    return None
                display_checksum_for_user(job, path_, checksum_value)
                f = metsrw.FSEntry(
                    path=path_,
                    use="original",
                    file_uuid=str(uuid.uuid4()),
                    checksumtype="MD5",
                    checksum=checksum_value,
                )
                sip.add_child(f)
            else:
                logger.error(
                    "Problem retrieving filename from metadata, returned "
                    "datafile: %s, path: %s",
                    data_file,
                    path_,
                )
                return None
    return sip


def write_mets_to_file(sip, unit_path, output_md_path, output_md_name):
    """Write METS to file."""
    metadata_path = output_md_path
    if metadata_path is None:
        metadata_path = os.path.join(unit_path, "metadata")
    if not os.path.exists(metadata_path):
        os.makedirs(metadata_path)

    metadata_name = output_md_name
    if metadata_name is None:
        metadata_name = "METS.xml"
    mets_path = os.path.join(metadata_path, metadata_name)

    # Write the data structure out to a file and ensure that the encoding is
    # purposely set to UTF-8. This pattern is used in ```create_mets_v2.py```.
    # Given the opportunity we should add an encoding feature to the metsrw
    # package.
    mets_f = metsrw.METSDocument()
    mets_f.append_file(sip)
    with open(mets_path, "wb") as xml_file:
        xml_file.write(
            etree.tostring(
                mets_f.serialize(),
                pretty_print=True,
                encoding="utf-8",
                xml_declaration=True,
            )
        )


def load_md_and_return_json(unit_path, dataset_md_name):
    """Load and parse Dataverse metadata from disk. Return JSON to calling
    function.
    """
    json_path = os.path.join(unit_path, "metadata", dataset_md_name)
    logger.info("Metadata directory exists %s", os.path.exists(json_path))
    try:
        with open(json_path, "r") as md_file:
            return json.load(md_file)
    except IOError as err:
        logger.error("Error opening dataset metadata: %s", err)
        return None


def convert_dataverse_to_mets(
    job,
    unit_path,
    dataset_md_name="dataset.json",
    output_md_path=None,
    output_md_name=None,
):
    """Create a transfer METS file from a Dataverse's dataset.json file"""
    logger.info(
        "Convert Dataverse structure called with '%s' unit directory", unit_path
    )

    json_metadata = load_md_and_return_json(unit_path, dataset_md_name)
    if json_metadata is None:
        raise ConvertDataverseError("Unable to the load Dataverse metadata file")
    dataset_md_latest = get_latest_version_metadata(json_metadata)
    if dataset_md_latest is None:
        raise ConvertDataverseError(
            "Unable to find the dataset metadata section from dataset.json"
        )

    # If a dataset is restricted we may not have access to all the files. We
    # may also want to flag this dataset to the users of this service. We
    # can do this here and below. We do not yet know whether this microservice
    # should fail because we don't know how all datasets behave when some
    # restrictions are placed on them.
    contact_information = retrieve_terms_of_access(dataset_md_latest)

    # Create METS
    try:
        sip = metsrw.FSEntry(
            path="None",
            label=get_ddi_title(dataset_md_latest),
            use=None,
            type="Directory",
        )
    except TypeError as err:
        citation_msg = ("Unable to gather citation data from dataset.json: %s", err)
        logger.error(citation_msg)
        raise ConvertDataverseError(citation_msg)

    sip = add_ddi_xml(job, sip, json_metadata, dataset_md_latest)
    if sip is None:
        raise ConvertDataverseError("Error creating SIP from Dataverse DDI")

    sip = add_metadata_ref(sip, dataset_md_name, "metadata/{}".format(dataset_md_name))

    sip = add_dataset_files_to_md(job, sip, dataset_md_latest, contact_information)
    if sip is None:
        raise ConvertDataverseError("Error adding Dataset files to METS")

    # On success of the following two functions, the module will return None
    # to JobContext which expects non-zero as a failure code only.
    sip = add_md_dir_to_structmap(sip)
    write_mets_to_file(sip, unit_path, output_md_path, output_md_name)


def get_latest_version_metadata(json_metadata):
    """If the datatset has been downloaded from the Dataverse web ui then there
    is a slightly different structure. While the structure is different, the
    majority of fields should remain the same and work with Archivematica. Just
    in case, we log the version here and inform the user of potential
    compatibility issues.

    Ref: https://github.com/IQSS/dataverse/issues/4715
    """
    dataset_version = json_metadata.get("datasetVersion")
    if dataset_version:
        logger.info(
            "Dataset seems to have been downloaded from the Dataverse Web UI."
            "Some features of this method may be incompatible with "
            "Archivematica at present."
        )
        return dataset_version
    return json_metadata.get("latestVersion")


def init_convert_dataverse(job):
    """Extract the arguments provided to the script and call the primary
    function concerned with converting the Dataverse metadata JSON.
    """
    try:
        transfer_dir = job.args[1]
        logger.info("Convert Dataverse Structure with dir: '%s'", transfer_dir)
        return convert_dataverse_to_mets(job, unit_path=transfer_dir)
    except IndexError:
        convert_dv_msg = (
            "Problem with the supplied arguments to the function len: {}".format(
                len(job.args)
            )
        )
        logger.error(convert_dv_msg)
        raise ConvertDataverseError(convert_dv_msg)


def call(jobs):
    """Primary entry point for MCP Client script."""
    for job in jobs:
        with job.JobContext(logger=logger):
            job.set_status(init_convert_dataverse(job))
