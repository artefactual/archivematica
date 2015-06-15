#!/usr/bin/python2

from __future__ import print_function
import datetime
from lxml import etree
import sys
import os
import uuid

import archivematicaXMLNamesSpace as ns

# archivematicaCommon
import fileOperations
import databaseFunctions

# dashboard
from main import models
from fpr import models as fpr_models

MD_TYPE_SIP_ID = "3e48343d-e2d2-4956-aaa3-b54d26eb9761"

def parse_files(root):
    filesec = root.find('.//mets:fileSec', namespaces=ns.NSMAP)
    files = []

    for fe in filesec.findall('.//mets:file', namespaces=ns.NSMAP):
        filegrpuse = fe.getparent().get('USE')
        print('filegrpuse', filegrpuse)

        amdid = fe.get('ADMID')
        print('amdid', amdid)
        amdsec = root.find('.//mets:amdSec[@ID="'+amdid+'"]', namespaces=ns.NSMAP)

        file_uuid = amdsec.findtext('.//premis:objectIdentifierValue', namespaces=ns.NSMAP)
        print('file_uuid', file_uuid)

        original_path = amdsec.findtext('.//premis:originalName', namespaces=ns.NSMAP)
        original_path = original_path.replace('%transferDirectory%', '%SIPDirectory%')
        print('original_path', original_path)

        current_path = fe.find('mets:FLocat', namespaces=ns.NSMAP).get(ns.xlinkBNS+'href')
        current_path = '%SIPDirectory%' + current_path
        print('current_path', current_path)

        checksum = amdsec.findtext('.//premis:messageDigest', namespaces=ns.NSMAP)
        print('checksum', checksum)

        size = amdsec.findtext('.//premis:size', namespaces=ns.NSMAP)
        print('size', size)

        # FormatVersion
        format_version = None
        try:
            # Looks for PRONOM ID first
            if amdsec.findtext('.//premis:formatRegistryName', namespaces=ns.NSMAP) == 'PRONOM':
                puid = amdsec.findtext('.//premis:formatRegistryKey', namespaces=ns.NSMAP)
                print('PUID', puid)
                format_version = fpr_models.FormatVersion.active.get(pronom_id=puid)
            elif amdsec.findtext('.//premis:formatRegistryName', namespaces=ns.NSMAP) == 'Archivematica Format Policy Registry':
                key = amdsec.findtext('.//premis:formatRegistryKey', namespaces=ns.NSMAP)
                print('FPR key', key)
                format_version = fpr_models.IDRule.active.get(command_output=key).format
            # If not, look for formatName
            if not format_version:
                name = amdsec.findtext('.//premis:formatName', namespaces=ns.NSMAP)
                print('Format name', name)
                format_version = fpr_models.FormatVersion.active.get(description=name)
        except fpr_models.FormatVersion.DoesNotExist:
            pass
        print('format_version', format_version)

        # Derivation
        derivation = derivation_event = None
        event = amdsec.findtext('.//premis:relatedEventIdentifierValue', namespaces=ns.NSMAP)
        print('derivation event', event)
        related_uuid = amdsec.findtext('.//premis:relatedObjectIdentifierValue', namespaces=ns.NSMAP)
        print('related_uuid', related_uuid)
        rel = amdsec.findtext('.//premis:relationshipSubType', namespaces=ns.NSMAP)
        print('relationship', rel)
        if rel == 'is source of':
            derivation = related_uuid
            derivation_event = event

        file_info = {
            'uuid': file_uuid,
            'original_path': original_path,
            'current_path': current_path,
            'use': filegrpuse,
            'checksum': checksum,
            'size': size,
            'format_version': format_version,
            'derivation': derivation,
            'derivation_event': derivation_event,
        }

        files.append(file_info)
        print()

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
            filePathRelativeToSIP=file_info['original_path'],
            fileUUID=file_info['uuid'],
            sipUUID=sip_uuid,
            taskUUID=event_id,
            date=now,
            sourceType="reingestion",
            use=file_info['use'],
        )
        # Update other file info
        models.File.objects.filter(uuid=file_info['uuid']).update(
            checksum=file_info['checksum'],
            size=file_info['size'],
            currentlocation=file_info['current_path']
        )
        if file_info['format_version']:
            # Add Format ID
            models.FileFormatVersion.objects.create(
                file_uuid_id=file_info['uuid'],
                format_version=file_info['format_version']
            )

    # Derivation info
    # Has to be separate loop, as derived file may not be in DB otherwise
    # May not need to be parsed, if Derivation info can be roundtripped in METS Reader/Writer
    for file_info in files:
        if file_info['derivation'] is None:
            continue
        databaseFunctions.insertIntoDerivations(
            sourceFileUUID=file_info['uuid'],
            derivedFileUUID=file_info['derivation'],
            relatedEventUUID=file_info['derivation_event'],
        )

def parse_dc(sip_uuid, root):
    """
    Parse SIP-level DublinCore metadata into the DublinCore table.

    Deletes existing entries associated with this SIP.

    :param str sip_uuid: UUID of the SIP to parse the metadata for.
    :param root: root Element of the METS file.
    :return: DublinCore DB object, or None
    """
    # Delete existing DC
    models.DublinCore.objects.filter(metadataappliestoidentifier=sip_uuid, metadataappliestotype_id=MD_TYPE_SIP_ID).delete()
    # Parse DC
    dmds = root.xpath('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]/parent::*', namespaces=ns.NSMAP)
    dc_model = None
    # Find which DC to parse into DB
    if len(dmds) > 0:
        DC_TERMS_MATCHING = {
            'title': 'title',
            'creator': 'creator',
            'subject': 'subject',
            'description': 'description',
            'publisher': 'publisher',
            'contributor': 'contributor',
            'date': 'date',
            'type': 'type',
            'format': 'format',
            'identifier': 'identifier',
            'source': 'source',
            'relation': 'relation',
            'language': 'language',
            'coverage': 'coverage',
            'rights': 'rights',
            'isPartOf': 'is_part_of',
        }
        # Want most recently updated
        dmds = sorted(dmds, key=lambda e: e.get('CREATED'))
        # Only want SIP DC, not file DC
        div = root.find('mets:structMap/mets:div/mets:div[@TYPE="Directory"][@LABEL="objects"]', namespaces=ns.NSMAP)
        dmdids = div.get('DMDID')
        # No SIP DC
        if dmdids is None:
            return
        dmdids = dmdids.split()
        for dmd in dmds[::-1]:  # Reversed
            if dmd.get('ID') in dmdids:
                dc_xml = dmd.find('mets:mdWrap/mets:xmlData/dcterms:dublincore', namespaces=ns.NSMAP)
                break
        dc_model = models.DublinCore(
            metadataappliestoidentifier=sip_uuid,
            metadataappliestotype_id=MD_TYPE_SIP_ID,
            status=models.METADATA_STATUS_REINGEST,
        )
        print('Dublin Core:')
        for elem in dc_xml:
            tag = elem.tag.replace(ns.dctermsBNS, '', 1).replace(ns.dcBNS, '', 1)
            print(tag, elem.text)
            setattr(dc_model, DC_TERMS_MATCHING[tag], elem.text)
        dc_model.save()
    return dc_model

def parse_rights(sip_uuid, root):
    """
    Parse PREMIS:RIGHTS metadata into the database.

    Deletes existing entries associated with this SIP.

    :param str sip_uuid: UUID of the SIP to parse the metadata for.
    :param root: root Element of the METS file.
    :return: List of RightsStatement objects for the parsed entries. Maybe be empty
    """
    # Delete existing PREMIS Rights
    del_rights = models.RightsStatement.objects.filter(metadataappliestoidentifier=sip_uuid, metadataappliestotype_id=MD_TYPE_SIP_ID)
    # TODO delete all the other rights things?
    models.RightsStatementCopyright.objects.filter(rightsstatement__in=del_rights).delete()
    models.RightsStatementLicense.objects.filter(rightsstatement__in=del_rights).delete()
    models.RightsStatementStatuteInformation.objects.filter(rightsstatement__in=del_rights).delete()
    models.RightsStatementOtherRightsInformation.objects.filter(rightsstatement__in=del_rights).delete()

    models.RightsStatementRightsGranted.objects.filter(rightsstatement__in=del_rights).delete()
    del_rights.delete()

    parsed_rights = []
    amds = root.xpath('mets:amdSec/mets:rightsMD/parent::*', namespaces=ns.NSMAP)
    if amds:
        amd = amds[0]
        # Get rightsMDs
        # METS from original AIPs will not have @STATUS, and reingested AIPs will have only one @STATUS that is 'current'
        rights_stmts = amd.xpath('mets:rightsMD[not(@STATUS) or @STATUS="current"]/mets:mdWrap[@MDTYPE="PREMIS:RIGHTS"]/*/premis:rightsStatement', namespaces=ns.NSMAP)

        # Parse to DB
        for statement in rights_stmts:
            rights_basis = statement.findtext('premis:rightsBasis', namespaces=ns.NSMAP)
            print('rights_basis', rights_basis)
            # Don't parse identifier type/value so if it's modified the new one gets unique identifiers
            rights = models.RightsStatement.objects.create(
                metadataappliestotype_id=MD_TYPE_SIP_ID,
                metadataappliestoidentifier=sip_uuid,
                rightsstatementidentifiertype="",
                rightsstatementidentifiervalue="",
                rightsbasis=rights_basis,
                status=models.METADATA_STATUS_REINGEST,
            )
            if rights_basis == 'Copyright':
                status = statement.findtext('.//premis:copyrightStatus', namespaces=ns.NSMAP) or ""
                jurisdiction = statement.findtext('.//premis:copyrightJurisdiction', namespaces=ns.NSMAP) or ""
                det_date = statement.findtext('.//premis:copyrightStatusDeterminationDate', namespaces=ns.NSMAP) or ""
                start_date = statement.findtext('.//premis:copyrightApplicableDates/premis:startDate', namespaces=ns.NSMAP) or ""
                end_date = statement.findtext('.//premis:copyrightApplicableDates/premis:endDate', namespaces=ns.NSMAP) or ""
                end_open = False
                if end_date == 'OPEN':
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
                id_type = statement.findtext('.//premis:copyrightDocumentationIdentifierType', namespaces=ns.NSMAP) or ""
                id_value = statement.findtext('.//premis:copyrightDocumentationIdentifierValue', namespaces=ns.NSMAP) or ""
                id_role = statement.findtext('.//premis:copyrightDocumentationRole', namespaces=ns.NSMAP) or ""
                models.RightsStatementCopyrightDocumentationIdentifier.objects.create(
                    rightscopyright=cr,
                    copyrightdocumentationidentifiertype=id_type,
                    copyrightdocumentationidentifiervalue=id_value,
                    copyrightdocumentationidentifierrole=id_role,
                )
                note = statement.findtext('.//premis:copyrightNote', namespaces=ns.NSMAP) or ""
                models.RightsStatementCopyrightNote.objects.create(
                    rightscopyright=cr,
                    copyrightnote=note,
                )
            elif rights_basis == 'License':
                terms = statement.findtext('.//premis:licenseTerms', namespaces=ns.NSMAP) or ""
                start_date = statement.findtext('.//premis:licenseApplicableDates/premis:startDate', namespaces=ns.NSMAP) or ""
                end_date = statement.findtext('.//premis:licenseApplicableDates/premis:endDate', namespaces=ns.NSMAP) or ""
                end_open = False
                if end_date == 'OPEN':
                    end_open = True
                    end_date = None
                li = models.RightsStatementLicense.objects.create(
                    rightsstatement=rights,
                    licenseterms=terms,
                    licenseapplicablestartdate=start_date,
                    licenseapplicableenddate=end_date,
                    licenseenddateopen=end_open,
                )
                id_type = statement.findtext('.//premis:licenseDocumentationIdentifierType', namespaces=ns.NSMAP) or ""
                id_value = statement.findtext('.//premis:licenseDocumentationIdentifierValue', namespaces=ns.NSMAP) or ""
                id_role = statement.findtext('.//premis:licenseDocumentationRole', namespaces=ns.NSMAP) or ""
                models.RightsStatementLicenseDocumentationIdentifier.objects.create(
                    rightsstatementlicense=li,
                    licensedocumentationidentifiertype=id_type,
                    licensedocumentationidentifiervalue=id_value,
                    licensedocumentationidentifierrole=id_role,
                )
                note = statement.findtext('.//premis:licenseNote', namespaces=ns.NSMAP) or ""
                models.RightsStatementLicenseNote.objects.create(
                    rightsstatementlicense=li,
                    licensenote=note,
                )
            elif rights_basis == 'Statute':
                jurisdiction = statement.findtext('.//premis:statuteJurisdiction', namespaces=ns.NSMAP) or ""
                citation = statement.findtext('.//premis:statuteCitation', namespaces=ns.NSMAP) or ""
                det_date = statement.findtext('.//premis:statuteInformationDeterminationDate', namespaces=ns.NSMAP) or ""
                start_date = statement.findtext('.//premis:statuteApplicableDates/premis:startDate', namespaces=ns.NSMAP) or ""
                end_date = statement.findtext('.//premis:statuteApplicableDates/premis:endDate', namespaces=ns.NSMAP) or ""
                end_open = False
                if end_date == 'OPEN':
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
                id_type = statement.findtext('.//premis:statuteDocumentationIdentifierType', namespaces=ns.NSMAP) or ""
                id_value = statement.findtext('.//premis:statuteDocumentationIdentifierValue', namespaces=ns.NSMAP) or ""
                id_role = statement.findtext('.//premis:statuteDocumentationRole', namespaces=ns.NSMAP) or ""
                models.RightsStatementStatuteDocumentationIdentifier.objects.create(
                    rightsstatementstatute=st,
                    statutedocumentationidentifiertype=id_type,
                    statutedocumentationidentifiervalue=id_value,
                    statutedocumentationidentifierrole=id_role,
                )
                note = statement.findtext('.//premis:statuteNote', namespaces=ns.NSMAP) or ""
                models.RightsStatementStatuteInformationNote.objects.create(
                    rightsstatementstatute=st,
                    statutenote=note,
                )
            elif rights_basis in ('Donor', 'Policy', 'Other'):
                other_basis = statement.findtext('.//premis:otherRightsBasis', namespaces=ns.NSMAP) or "Other"
                rights.rightsbasis = other_basis
                rights.save()
                start_date = statement.findtext('.//premis:otherRightsApplicableDates/premis:startDate', namespaces=ns.NSMAP) or ""
                end_date = statement.findtext('.//premis:otherRightsApplicableDates/premis:endDate', namespaces=ns.NSMAP) or ""
                end_open = False
                if end_date == 'OPEN':
                    end_open = True
                    end_date = None
                ot = models.RightsStatementOtherRightsInformation.objects.create(
                    rightsstatement=rights,
                    otherrightsbasis=other_basis,
                    otherrightsapplicablestartdate=start_date,
                    otherrightsapplicableenddate=end_date,
                    otherrightsenddateopen=end_open,
                )
                id_type = statement.findtext('.//premis:otherRightsDocumentationIdentifierType', namespaces=ns.NSMAP) or ""
                id_value = statement.findtext('.//premis:otherRightsDocumentationIdentifierValue', namespaces=ns.NSMAP) or ""
                id_role = statement.findtext('.//premis:otherRightsDocumentationRole', namespaces=ns.NSMAP) or ""
                models.RightsStatementOtherRightsDocumentationIdentifier.objects.create(
                    rightsstatementotherrights=ot,
                    otherrightsdocumentationidentifiertype=id_type,
                    otherrightsdocumentationidentifiervalue=id_value,
                    otherrightsdocumentationidentifierrole=id_role,
                )
                note = statement.findtext('.//premis:otherRightsNote', namespaces=ns.NSMAP) or ""
                models.RightsStatementOtherRightsInformationNote.objects.create(
                    rightsstatementotherrights=ot,
                    otherrightsnote=note,
                )

            # Parse rightsGranted
            rights_act = statement.findtext('.//premis:rightsGranted/premis:act', namespaces=ns.NSMAP) or ""
            rights_start_date = statement.findtext('.//premis:rightsGranted/*/premis:startDate', namespaces=ns.NSMAP) or ""
            rights_end_date = statement.findtext('.//premis:rightsGranted/*/premis:endDate', namespaces=ns.NSMAP) or ""
            rights_end_open = False
            if rights_end_date == 'OPEN':
                rights_end_date = None
                rights_end_open = True
            print('rights_act', rights_act)
            print('rights_start_date', rights_start_date)
            print('rights_end_date', rights_end_date)
            print('rights_end_open', rights_end_open)
            rights_granted = models.RightsStatementRightsGranted.objects.create(
                rightsstatement=rights,
                act=rights_act,
                startdate=rights_start_date,
                enddate=rights_end_date,
                enddateopen=rights_end_open,
            )

            rights_note = statement.findtext('.//premis:rightsGranted/premis:rightsGrantedNote', namespaces=ns.NSMAP) or ""
            print('rights_note', rights_note)
            models.RightsStatementRightsGrantedNote.objects.create(
                rightsgranted=rights_granted,
                rightsgrantednote=rights_note,
            )

            rights_restriction = statement.findtext('.//premis:rightsGranted/premis:restriction', namespaces=ns.NSMAP) or ""
            print('rights_restriction', rights_restriction)
            models.RightsStatementRightsGrantedRestriction.objects.create(
                rightsgranted=rights_granted,
                restriction=rights_restriction,
            )
            parsed_rights.append(rights)
    return parsed_rights

def update_default_config(processing_path):
    root = etree.parse(processing_path)

    # Do not run file ID in ingest
    ingest_id_mscl = '7a024896-c4f7-4808-a240-44c87c762bc5'
    use_existing_choice = models.MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=ingest_id_mscl).get(description='Use existing data')
    try:
        applies_to = root.xpath('//appliesTo[text()="%s"]' % ingest_id_mscl)[0]
    except IndexError:
        # Entry did not existing in preconfigured choices, so create
        choices = root.find('preconfiguredChoices')
        choice = etree.SubElement(choices, 'preconfiguredChoice')
        applies_to = etree.SubElement(choice, 'appliesTo').text = ingest_id_mscl
        go_to_chain = etree.SubElement(choice, 'goToChain')
    else:
        # Update existing entry
        go_to_chain = applies_to.getnext()
    go_to_chain.text = use_existing_choice.id

    # If normalize option has 'preservation', remove
    normalize_mscl = 'cb8e5706-e73f-472f-ad9b-d1236af8095f'
    try:
        applies_to = root.xpath('//appliesTo[text()="%s"]' % normalize_mscl)[0]
    except IndexError:
        # Entry did not existing in preconfigured choices
        pass
    else:
        # Update existing entry
        go_to_chain = applies_to.getnext()
        chain = models.MicroServiceChain.objects.get(pk=go_to_chain.text)
        if 'preservation' in chain.description:
            # Remove from processing MCP
            choice = go_to_chain.getparent()
            choice.getparent().remove(choice)

    # Write out processingMCP
    with open(processing_path, 'w') as f:
        f.write(etree.tostring(root, pretty_print=True))


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
    mets_path = os.path.join(sip_path, 'metadata', 'submissionDocumentation', 'METS.' + sip_uuid + '.xml')
    root = etree.parse(mets_path)

    files = parse_files(root)
    update_files(sip_uuid, files)

    parse_dc(sip_uuid, root)

    parse_rights(sip_uuid, root)

    # Update processingMCP
    processing_path = os.path.join(sip_path, 'processingMCP.xml')
    update_default_config(processing_path)


if __name__ == '__main__':
    print('METS Reader')
    sys.exit(main())
