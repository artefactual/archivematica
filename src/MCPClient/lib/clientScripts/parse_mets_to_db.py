#!/usr/bin/env python2

import argparse
import datetime
from lxml import etree
import os
import uuid

import django
from django.db import transaction

django.setup()
# dashboard
from main import models
from fpr import models as fpr_models

# archivematicaCommon
import namespaces as ns
import fileOperations
import databaseFunctions

MD_TYPE_SIP_ID = "3e48343d-e2d2-4956-aaa3-b54d26eb9761"


def parse_format_version(job, element):
    """
    Parses the FPR FormatVersion for the file.

    Element can be the amdSec, or a PREMIS:OBJECT

    :param element: lxml Element that contains premis:format.
    :return: FormatVersion object or None
    """
    format_version = None
    try:
        # Looks for PRONOM ID first
        format_registry_name = ns.xml_findtext_premis(
            element, ".//premis:formatRegistryName"
        )
        if format_registry_name == "PRONOM":
            puid = ns.xml_findtext_premis(element, ".//premis:formatRegistryKey")
            job.pyprint("PUID", puid)
            format_version = fpr_models.FormatVersion.active.get(pronom_id=puid)
        elif format_registry_name == "Archivematica Format Policy Registry":
            key = ns.xml_findtext_premis(element, ".//premis:formatRegistryKey")
            job.pyprint("FPR key", key)
            format_version = fpr_models.IDRule.active.get(command_output=key).format
    except fpr_models.FormatVersion.DoesNotExist:
        pass
    return format_version


def parse_files(job, root):
    filesec = root.find(".//mets:fileSec", namespaces=ns.NSMAP)
    files = []

    for fe in filesec.findall(".//mets:file", namespaces=ns.NSMAP):
        filegrpuse = fe.getparent().get("USE")
        job.pyprint("filegrpuse", filegrpuse)

        amdid = fe.get("ADMID")
        job.pyprint("amdid", amdid)
        current_techmd = root.xpath(
            'mets:amdSec[@ID="' + amdid + '"]/mets:techMD[not(@STATUS="superseded")]',
            namespaces=ns.NSMAP,
        )[0]

        file_uuid = ns.xml_findtext_premis(
            current_techmd, ".//premis:objectIdentifierValue"
        )
        job.pyprint("file_uuid", file_uuid)

        original_path = ns.xml_findtext_premis(current_techmd, ".//premis:originalName")
        original_path = original_path.replace("%transferDirectory%", "%SIPDirectory%")
        job.pyprint("original_path", original_path)

        current_path = fe.find("mets:FLocat", namespaces=ns.NSMAP).get(
            ns.xlinkBNS + "href"
        )
        current_path = "%SIPDirectory%" + current_path
        job.pyprint("current_path", current_path)

        checksum = ns.xml_findtext_premis(current_techmd, ".//premis:messageDigest")
        job.pyprint("checksum", checksum)

        checksumtype = ns.xml_findtext_premis(
            current_techmd, ".//premis:messageDigestAlgorithm"
        )
        job.pyprint("checksumtype", checksumtype)

        size = ns.xml_findtext_premis(current_techmd, ".//premis:size")
        job.pyprint("size", size)

        # FormatVersion
        format_version = parse_format_version(job, current_techmd)
        job.pyprint("format_version", format_version)

        # Derivation
        derivation = derivation_event = None
        event = ns.xml_findtext_premis(
            current_techmd, ".//premis:relatedEventIdentifierValue"
        )
        job.pyprint("derivation event", event)
        related_uuid = ns.xml_findtext_premis(
            current_techmd, ".//premis:relatedObjectIdentifierValue"
        )
        job.pyprint("related_uuid", related_uuid)
        rel = ns.xml_findtext_premis(current_techmd, ".//premis:relationshipSubType")
        job.pyprint("relationship", rel)
        if rel == "is source of":
            derivation = related_uuid
            derivation_event = event

        file_info = {
            "uuid": file_uuid,
            "original_path": original_path,
            "current_path": current_path,
            "use": filegrpuse,
            "checksum": checksum,
            "checksumtype": checksumtype,
            "size": size,
            "format_version": format_version,
            "derivation": derivation,
            "derivation_event": derivation_event,
        }

        files.append(file_info)
        job.pyprint()

    return files


def update_files(sip_uuid, files):
    """
    Update file information to DB.

    :param sip_uuid: UUID of the SIP to parse the metadata for.
    :param files: List of dicts containing file info.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    # Add information to the DB
    for file_info in files:
        # Add file & reingest event
        event_id = str(uuid.uuid4())
        fileOperations.addFileToSIP(
            filePathRelativeToSIP=file_info["original_path"],
            fileUUID=file_info["uuid"],
            sipUUID=sip_uuid,
            taskUUID=event_id,
            date=now,
            sourceType="reingestion",
            use=file_info["use"],
        )
        # Update other file info
        # This doesn't use updateSizeAndChecksum because it also updates currentlocation
        models.File.objects.filter(uuid=file_info["uuid"]).update(
            checksum=file_info["checksum"],
            checksumtype=file_info["checksumtype"],
            size=file_info["size"],
            currentlocation=file_info["current_path"],
        )
        if file_info["format_version"]:
            # Add Format ID
            models.FileFormatVersion.objects.create(
                file_uuid_id=file_info["uuid"],
                format_version=file_info["format_version"],
            )

    # Derivation info
    # Has to be separate loop, as derived file may not be in DB otherwise
    # May not need to be parsed, if Derivation info can be roundtripped in METS Reader/Writer
    for file_info in files:
        if file_info["derivation"] is None:
            continue
        databaseFunctions.insertIntoDerivations(
            sourceFileUUID=file_info["uuid"], derivedFileUUID=file_info["derivation"]
        )


def parse_dc(job, sip_uuid, root):
    """
    Parse SIP-level DublinCore metadata into the DublinCore table.

    Deletes existing entries associated with this SIP.

    :param str sip_uuid: UUID of the SIP to parse the metadata for.
    :param root: root Element of the METS file.
    :return: DublinCore DB object, or None
    """
    # Delete existing DC
    models.DublinCore.objects.filter(
        metadataappliestoidentifier=sip_uuid, metadataappliestotype_id=MD_TYPE_SIP_ID
    ).delete()
    # Parse DC
    dmds = root.xpath(
        'mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]/parent::*', namespaces=ns.NSMAP
    )
    dc_model = None
    # Find which DC to parse into DB
    if len(dmds) > 0:
        DC_TERMS_MATCHING = {
            "title": "title",
            "creator": "creator",
            "subject": "subject",
            "description": "description",
            "publisher": "publisher",
            "contributor": "contributor",
            "date": "date",
            "type": "type",
            "format": "format",
            "identifier": "identifier",
            "source": "source",
            "relation": "relation",
            "language": "language",
            "coverage": "coverage",
            "rights": "rights",
            "isPartOf": "is_part_of",
        }
        # Want most recently updated
        dmds = sorted(
            dmds, key=lambda e: (e.get("CREATED") is not None, e.get("CREATED"))
        )
        # Only want SIP DC, not file DC
        div = root.find(
            'mets:structMap/mets:div/mets:div[@TYPE="Directory"][@LABEL="objects"]',
            namespaces=ns.NSMAP,
        )
        dmdids = div.get("DMDID")
        # No SIP DC
        if dmdids is None:
            return
        dmdids = dmdids.split()
        for dmd in dmds[::-1]:  # Reversed
            if dmd.get("ID") in dmdids:
                dc_xml = dmd.find(
                    "mets:mdWrap/mets:xmlData/dcterms:dublincore", namespaces=ns.NSMAP
                )
                break
        dc_model = models.DublinCore(
            metadataappliestoidentifier=sip_uuid,
            metadataappliestotype_id=MD_TYPE_SIP_ID,
            status=models.METADATA_STATUS_REINGEST,
        )
        job.pyprint("Dublin Core:")
        for elem in dc_xml:
            tag = elem.tag.replace(ns.dctermsBNS, "", 1).replace(ns.dcBNS, "", 1)
            job.pyprint(tag, elem.text)
            if elem.text is not None:
                setattr(dc_model, DC_TERMS_MATCHING[tag], elem.text)
        dc_model.save()
    return dc_model


def parse_rights(job, sip_uuid, root):
    """
    Parse PREMIS:RIGHTS metadata into the database.

    Deletes existing entries associated with this SIP.

    :param str sip_uuid: UUID of the SIP to parse the metadata for.
    :param root: root Element of the METS file.
    :return: List of RightsStatement objects for the parsed entries. Maybe be empty
    """
    # Delete existing PREMIS Rights
    del_rights = models.RightsStatement.objects.filter(
        metadataappliestoidentifier=sip_uuid, metadataappliestotype_id=MD_TYPE_SIP_ID
    )
    # TODO delete all the other rights things?
    models.RightsStatementCopyright.objects.filter(
        rightsstatement__in=del_rights
    ).delete()
    models.RightsStatementLicense.objects.filter(
        rightsstatement__in=del_rights
    ).delete()
    models.RightsStatementStatuteInformation.objects.filter(
        rightsstatement__in=del_rights
    ).delete()
    models.RightsStatementOtherRightsInformation.objects.filter(
        rightsstatement__in=del_rights
    ).delete()

    models.RightsStatementRightsGranted.objects.filter(
        rightsstatement__in=del_rights
    ).delete()
    del_rights.delete()

    parsed_rights = []
    amds = root.xpath("mets:amdSec/mets:rightsMD/parent::*", namespaces=ns.NSMAP)
    if amds:
        amd = amds[0]
        # Get rightsMDs
        # METS from original AIPs will not have @STATUS, and reingested AIPs will have only one @STATUS that is 'current'
        rights_stmts = ns.xml_xpath_premis(
            amd,
            'mets:rightsMD[not(@STATUS) or @STATUS="current"]/mets:mdWrap[@MDTYPE="PREMIS:RIGHTS"]/*/premis:rightsStatement',
        )

        # Parse to DB
        for statement in rights_stmts:
            rights_basis = ns.xml_findtext_premis(statement, "premis:rightsBasis")
            job.pyprint("rights_basis", rights_basis)
            # Don't parse identifier type/value so if it's modified the new one gets unique identifiers
            rights = models.RightsStatement.objects.create(
                metadataappliestotype_id=MD_TYPE_SIP_ID,
                metadataappliestoidentifier=sip_uuid,
                rightsstatementidentifiertype="",
                rightsstatementidentifiervalue="",
                rightsbasis=rights_basis,
                status=models.METADATA_STATUS_REINGEST,
            )
            if rights_basis == "Copyright":
                status = ns.xml_findtext_premis(statement, ".//premis:copyrightStatus")
                jurisdiction = ns.xml_findtext_premis(
                    statement, ".//premis:copyrightJurisdiction"
                )
                det_date = ns.xml_findtext_premis(
                    statement, ".//premis:copyrightStatusDeterminationDate"
                )
                start_date = ns.xml_findtext_premis(
                    statement, ".//premis:copyrightApplicableDates/premis:startDate"
                )
                end_date = ns.xml_findtext_premis(
                    statement, ".//premis:copyrightApplicableDates/premis:endDate"
                )
                end_open = False
                if end_date == "OPEN":
                    end_open = True
                    end_date = None
                cr = models.RightsStatementCopyright.objects.create(
                    rightsstatement=rights,
                    copyrightstatus=status,
                    copyrightjurisdiction=jurisdiction,
                    copyrightstatusdeterminationdate=det_date,
                    copyrightapplicablestartdate=start_date,
                    copyrightapplicableenddate=end_date,
                    copyrightenddateopen=end_open,
                )
                id_type = ns.xml_findtext_premis(
                    statement, ".//premis:copyrightDocumentationIdentifierType"
                )
                id_value = ns.xml_findtext_premis(
                    statement, ".//premis:copyrightDocumentationIdentifierValue"
                )
                id_role = ns.xml_findtext_premis(
                    statement, ".//premis:copyrightDocumentationRole"
                )
                models.RightsStatementCopyrightDocumentationIdentifier.objects.create(
                    rightscopyright=cr,
                    copyrightdocumentationidentifiertype=id_type,
                    copyrightdocumentationidentifiervalue=id_value,
                    copyrightdocumentationidentifierrole=id_role,
                )
                note = ns.xml_findtext_premis(statement, ".//premis:copyrightNote")
                models.RightsStatementCopyrightNote.objects.create(
                    rightscopyright=cr, copyrightnote=note
                )
            elif rights_basis == "License":
                terms = ns.xml_findtext_premis(statement, ".//premis:licenseTerms")
                start_date = ns.xml_findtext_premis(
                    statement, ".//premis:licenseApplicableDates/premis:startDate"
                )
                end_date = ns.xml_findtext_premis(
                    statement, ".//premis:licenseApplicableDates/premis:endDate"
                )
                end_open = False
                if end_date == "OPEN":
                    end_open = True
                    end_date = None
                li = models.RightsStatementLicense.objects.create(
                    rightsstatement=rights,
                    licenseterms=terms,
                    licenseapplicablestartdate=start_date,
                    licenseapplicableenddate=end_date,
                    licenseenddateopen=end_open,
                )
                id_type = ns.xml_findtext_premis(
                    statement, ".//premis:licenseDocumentationIdentifierType"
                )
                id_value = ns.xml_findtext_premis(
                    statement, ".//premis:licenseDocumentationIdentifierValue"
                )
                id_role = ns.xml_findtext_premis(
                    statement, ".//premis:licenseDocumentationRole"
                )
                models.RightsStatementLicenseDocumentationIdentifier.objects.create(
                    rightsstatementlicense=li,
                    licensedocumentationidentifiertype=id_type,
                    licensedocumentationidentifiervalue=id_value,
                    licensedocumentationidentifierrole=id_role,
                )
                note = (
                    statement.findtext(".//premis:licenseNote", namespaces=ns.NSMAP)
                    or ""
                )
                models.RightsStatementLicenseNote.objects.create(
                    rightsstatementlicense=li, licensenote=note
                )
            elif rights_basis == "Statute":
                jurisdiction = ns.xml_findtext_premis(
                    statement, ".//premis:statuteJurisdiction"
                )
                citation = ns.xml_findtext_premis(
                    statement, ".//premis:statuteCitation"
                )
                det_date = ns.xml_findtext_premis(
                    statement, ".//premis:statuteInformationDeterminationDate"
                )
                start_date = ns.xml_findtext_premis(
                    statement, ".//premis:statuteApplicableDates/premis:startDate"
                )
                end_date = ns.xml_findtext_premis(
                    statement, ".//premis:statuteApplicableDates/premis:endDate"
                )
                end_open = False
                if end_date == "OPEN":
                    end_open = True
                    end_date = None
                st = models.RightsStatementStatuteInformation.objects.create(
                    rightsstatement=rights,
                    statutejurisdiction=jurisdiction,
                    statutecitation=citation,
                    statutedeterminationdate=det_date,
                    statuteapplicablestartdate=start_date,
                    statuteapplicableenddate=end_date,
                    statuteenddateopen=end_open,
                )
                id_type = ns.xml_findtext_premis(
                    statement, ".//premis:statuteDocumentationIdentifierType"
                )
                id_value = ns.xml_findtext_premis(
                    statement, ".//premis:statuteDocumentationIdentifierValue"
                )
                id_role = ns.xml_findtext_premis(
                    statement, ".//premis:statuteDocumentationRole"
                )
                models.RightsStatementStatuteDocumentationIdentifier.objects.create(
                    rightsstatementstatute=st,
                    statutedocumentationidentifiertype=id_type,
                    statutedocumentationidentifiervalue=id_value,
                    statutedocumentationidentifierrole=id_role,
                )
                note = ns.xml_findtext_premis(statement, ".//premis:statuteNote")
                models.RightsStatementStatuteInformationNote.objects.create(
                    rightsstatementstatute=st, statutenote=note
                )
            elif rights_basis in ("Donor", "Policy", "Other"):
                other_basis = ns.xml_findtext_premis(
                    statement, ".//premis:otherRightsBasis", default="Other"
                )
                rights.rightsbasis = other_basis
                rights.save()
                start_date = ns.xml_findtext_premis(
                    statement, ".//premis:otherRightsApplicableDates/premis:startDate"
                )
                end_date = ns.xml_findtext_premis(
                    statement, ".//premis:otherRightsApplicableDates/premis:endDate"
                )
                end_open = False
                if end_date == "OPEN":
                    end_open = True
                    end_date = None
                ot = models.RightsStatementOtherRightsInformation.objects.create(
                    rightsstatement=rights,
                    otherrightsbasis=other_basis,
                    otherrightsapplicablestartdate=start_date,
                    otherrightsapplicableenddate=end_date,
                    otherrightsenddateopen=end_open,
                )
                id_type = ns.xml_findtext_premis(
                    statement, ".//premis:otherRightsDocumentationIdentifierType"
                )
                id_value = ns.xml_findtext_premis(
                    statement, ".//premis:otherRightsDocumentationIdentifierValue"
                )
                id_role = ns.xml_findtext_premis(
                    statement, ".//premis:otherRightsDocumentationRole"
                )
                models.RightsStatementOtherRightsDocumentationIdentifier.objects.create(
                    rightsstatementotherrights=ot,
                    otherrightsdocumentationidentifiertype=id_type,
                    otherrightsdocumentationidentifiervalue=id_value,
                    otherrightsdocumentationidentifierrole=id_role,
                )
                note = ns.xml_findtext_premis(statement, ".//premis:otherRightsNote")
                models.RightsStatementOtherRightsInformationNote.objects.create(
                    rightsstatementotherrights=ot, otherrightsnote=note
                )

            # Parse rightsGranted
            for rightsgranted_elem in ns.xml_findall_premis(
                statement, ".//premis:rightsGranted"
            ):
                rights_act = ns.xml_findtext_premis(rightsgranted_elem, "premis:act")
                rights_start_date = ns.xml_findtext_premis(
                    rightsgranted_elem, ".//premis:startDate"
                )
                rights_end_date = ns.xml_findtext_premis(
                    rightsgranted_elem, ".//premis:endDate"
                )
                rights_end_open = False
                if rights_end_date == "OPEN":
                    rights_end_date = None
                    rights_end_open = True
                job.pyprint("rights_act", rights_act)
                job.pyprint("rights_start_date", rights_start_date)
                job.pyprint("rights_end_date", rights_end_date)
                job.pyprint("rights_end_open", rights_end_open)
                rights_granted = models.RightsStatementRightsGranted.objects.create(
                    rightsstatement=rights,
                    act=rights_act,
                    startdate=rights_start_date,
                    enddate=rights_end_date,
                    enddateopen=rights_end_open,
                )

                rights_note = ns.xml_findtext_premis(
                    rightsgranted_elem, "premis:rightsGrantedNote"
                )
                job.pyprint("rights_note", rights_note)
                models.RightsStatementRightsGrantedNote.objects.create(
                    rightsgranted=rights_granted, rightsgrantednote=rights_note
                )

                rights_restriction = ns.xml_findtext_premis(
                    rightsgranted_elem, "premis:restriction"
                )
                job.pyprint("rights_restriction", rights_restriction)
                models.RightsStatementRightsGrantedRestriction.objects.create(
                    rightsgranted=rights_granted, restriction=rights_restriction
                )
            parsed_rights.append(rights)
    return parsed_rights


def main(job, sip_uuid, sip_path):
    # Set reingest type
    # TODO also support AIC-REIN
    sip = models.SIP.objects.filter(uuid=sip_uuid)
    sip.update(sip_type="AIP-REIN")

    # Parse METS to extract information needed by later microservices
    mets_path = os.path.join(
        sip_path, "metadata", "submissionDocumentation", "METS." + sip_uuid + ".xml"
    )
    root = etree.parse(mets_path)

    files = parse_files(job, root)
    update_files(sip_uuid, files)

    parse_dc(job, sip_uuid, root)

    parse_rights(job, sip_uuid, root)


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("sip_uuid", help="%SIPUUID%")
    parser.add_argument("sip_path", help="%SIPDirectory%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                job.pyprint("METS Reader")
                args = parser.parse_args(job.args[1:])

                job.set_status(main(job, args.sip_uuid, args.sip_path))
