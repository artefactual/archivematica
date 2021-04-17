#!/usr/bin/env python
from __future__ import unicode_literals

import os
import sys
import uuid

import pytest
from lxml import etree

import metsrw
from metsrw.plugins.premisrw import PREMIS_3_0_NAMESPACES

from fpr.models import Format, FormatGroup, FormatVersion, FPCommand, FPRule, FPTool
from main.models import (
    Agent,
    DashboardSetting,
    Directory,
    Event,
    File,
    FPCommandOutput,
    RightsStatement,
    Transfer,
)
from version import get_preservation_system_identifier

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
from create_transfer_mets import write_mets


PREMIS_NAMESPACES = PREMIS_3_0_NAMESPACES


@pytest.fixture()
def subdir_path(tmp_path):
    subdir = tmp_path / "subdir1"
    subdir.mkdir()

    return subdir


@pytest.fixture()
def empty_subdir_path(tmp_path):
    empty_subdir = tmp_path / "subdir2-empty"
    empty_subdir.mkdir()

    return empty_subdir


@pytest.fixture()
def file_path(subdir_path):
    file_path = subdir_path / "file1"
    file_path.write_text("Hello world")

    return file_path


@pytest.fixture()
def file_path2(subdir_path):
    file_path = subdir_path / "file2"
    file_path.write_text("Hello world")

    return file_path


@pytest.fixture()
def transfer(db):
    return Transfer.objects.create(
        uuid=uuid.uuid4(), currentlocation=r"%transferDirectory%"
    )


@pytest.fixture()
def file_obj(db, transfer, tmp_path, file_path):
    file_obj_path = "".join(
        [transfer.currentlocation, str(file_path.relative_to(tmp_path))]
    )
    file_obj = File.objects.create(
        uuid=uuid.uuid4(),
        transfer=transfer,
        originallocation=file_obj_path,
        currentlocation=file_obj_path,
        removedtime=None,
        size=113318,
        checksum="35e0cc683d75704fc5b04fc3633f6c654e10cd3af57471271f370309c7ff9dba",
        checksumtype="sha256",
    )
    file_obj.identifiers.create(type="TEST FILE", value="233456")

    return file_obj


@pytest.fixture()
def file_obj2(db, transfer, tmp_path, file_path2):
    file_obj_path = "".join(
        [transfer.currentlocation, str(file_path2.relative_to(tmp_path))]
    )
    return File.objects.create(
        uuid=uuid.uuid4(),
        transfer=transfer,
        originallocation=file_obj_path,
        currentlocation=file_obj_path,
        removedtime=None,
        size=113318,
        checksum="35e0cc683d75704fc5b04fc3633f6c654e10cd3af57471271f370309c7ff9dba",
        checksumtype="sha256",
    )


@pytest.fixture()
def dir_obj(db, transfer, tmp_path, subdir_path):
    dir_obj_path = "".join(
        [transfer.currentlocation, str(subdir_path.relative_to(tmp_path)), os.path.sep]
    )
    dir_obj = Directory.objects.create(
        uuid=uuid.uuid4(),
        transfer=transfer,
        originallocation=dir_obj_path,
        currentlocation=dir_obj_path,
    )
    dir_obj.identifiers.create(type="TEST ID", value="12345")

    return dir_obj


@pytest.fixture()
def event(request, db, file_obj):
    return Event.objects.create(
        event_id=uuid.uuid4(),
        file_uuid=file_obj,
        event_type="message digest calculation",
        event_detail='program="python"; module="hashlib.sha256()"',
        event_outcome_detail="d10bbb2cddc343cd50a304c21e67cb9d5937a93bcff5e717de2df65e0a6309d6",
    )


@pytest.fixture()
def fprule(db):
    format_group = FormatGroup.objects.create(description="group")
    format = Format.objects.create(description="format", group=format_group)
    format_version = FormatVersion.objects.create(
        format=format, version="1.0", description="Version 1.0"
    )
    tool = FPTool.objects.create(description="tool")
    command = FPCommand.objects.create(tool=tool, description="command")
    return FPRule.objects.create(
        purpose=FPRule.CHARACTERIZATION,
        command=command,
        format=format_version,
    )


@pytest.fixture()
def fpcommand_output(db, fprule, file_obj):
    return FPCommandOutput.objects.create(
        file=file_obj,
        rule=fprule,
        content='<?xml version="1.0" encoding="UTF-8"?><hello>World</hello>',
    )


@pytest.fixture()
def basic_rights_statement(db, file_obj):
    rights = RightsStatement.objects.create(
        metadataappliestotype_id="7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17",
        metadataappliestoidentifier=file_obj.uuid,
        rightsstatementidentifiertype="UUID",
        rightsstatementidentifiervalue=str(uuid.uuid4()),
    )
    rights_granted = rights.rightsstatementrightsgranted_set.create(
        act="Disseminate", startdate="2001-01-01", enddateopen=True
    )
    rights_granted.restrictions.create(restriction="Allow")
    rights_granted.notes.create(rightsgrantednote="A grant note")
    rights_granted.notes.create(rightsgrantednote="Another grant note")

    return rights


@pytest.fixture()
def copyright_rights(db, basic_rights_statement):
    basic_rights_statement.rightsbasis = "Copyright"
    basic_rights_statement.save()

    copyright_info = basic_rights_statement.rightsstatementcopyright_set.create(
        copyrightjurisdiction="CANADA",
        copyrightstatusdeterminationdate="2001-01-01",
        copyrightstatus="copyrighted",
        copyrightapplicablestartdate="2001-01-01",
        copyrightenddateopen=True,
    )
    copyright_info.rightsstatementcopyrightnote_set.create(
        copyrightnote="Here is a copyright note"
    )
    copyright_info.rightsstatementcopyrightnote_set.create(
        copyrightnote="Here is another copyright note"
    )
    copyright_info.rightsstatementcopyrightdocumentationidentifier_set.create(
        copyrightdocumentationidentifiertype="Tranfer form ID",
        copyrightdocumentationidentifiervalue="123-4",
        copyrightdocumentationidentifierrole="Transfer documentation",
    )

    return basic_rights_statement


@pytest.fixture()
def license_rights(db, basic_rights_statement):
    basic_rights_statement.rightsbasis = "License"
    basic_rights_statement.save()

    license_info = basic_rights_statement.rightsstatementlicense_set.create(
        licenseapplicablestartdate="2001-10-10",
        licenseenddateopen=True,
        licenseterms="Here are some license terms",
    )
    license_info.rightsstatementlicensedocumentationidentifier_set.create(
        licensedocumentationidentifiertype="Tranfer form ID",
        licensedocumentationidentifiervalue="123-4",
        licensedocumentationidentifierrole="Transfer documentation",
    )
    license_info.rightsstatementlicensenote_set.create(
        licensenote="Here is a license note"
    )

    return basic_rights_statement


@pytest.fixture()
def statute_rights(db, basic_rights_statement):
    basic_rights_statement.rightsbasis = "Statute"
    basic_rights_statement.save()

    statute_info = basic_rights_statement.rightsstatementstatuteinformation_set.create(
        statutejurisdiction="BC",
        statutecitation="A citation",
        statutedeterminationdate="2010-01-01",
        statuteapplicablestartdate="2001-10-10",
        statuteenddateopen=True,
    )
    statute_info.rightsstatementstatutedocumentationidentifier_set.create(
        statutedocumentationidentifiertype="Tranfer form ID",
        statutedocumentationidentifiervalue="123-4",
        statutedocumentationidentifierrole="Transfer documentation",
    )
    statute_info.rightsstatementstatuteinformationnote_set.create(
        statutenote="Here is a statute note"
    )

    return basic_rights_statement


@pytest.fixture()
def other_rights(db, basic_rights_statement):
    basic_rights_statement.rightsbasis = "Other"
    basic_rights_statement.save()

    other_info = (
        basic_rights_statement.rightsstatementotherrightsinformation_set.create(
            otherrightsbasis="A basis for rights",
            otherrightsapplicablestartdate="2001-10-10",
            otherrightsenddateopen=True,
        )
    )
    other_info.rightsstatementotherrightsdocumentationidentifier_set.create(
        otherrightsdocumentationidentifiertype="Tranfer form ID",
        otherrightsdocumentationidentifiervalue="123-4",
        otherrightsdocumentationidentifierrole="Transfer documentation",
    )
    other_info.rightsstatementotherrightsinformationnote_set.create(
        otherrightsnote="Here is an other rights note"
    )

    return basic_rights_statement


@pytest.fixture()
def dashboard_uuid(db):
    setting, _ = DashboardSetting.objects.get_or_create(
        name="dashboard_uuid", defaults={"value": str(uuid.uuid4())}
    )
    return setting.value


@pytest.mark.django_db
def test_transfer_mets_structmap_format(
    tmp_path, transfer, file_obj, subdir_path, empty_subdir_path, file_path
):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()
    structmap_types = mets_xml.xpath(
        ".//mets:structMap/@TYPE", namespaces=mets_xml.nsmap
    )
    root_div_labels = mets_xml.xpath(
        ".//mets:structMap/mets:div/@LABEL", namespaces=mets_xml.nsmap
    )
    subdir_div_labels = mets_xml.xpath(
        ".//mets:structMap/mets:div/mets:div/@LABEL", namespaces=mets_xml.nsmap
    )
    file_div_labels = mets_xml.xpath(
        ".//mets:structMap/mets:div/mets:div/mets:div/@LABEL", namespaces=mets_xml.nsmap
    )
    file_ids = mets_xml.xpath(
        ".//mets:structMap/mets:div/mets:div/mets:div/mets:fptr/@FILEID",
        namespaces=mets_xml.nsmap,
    )

    assert len(mets_doc.all_files()) == 4

    # Test that we have physical and logical structmaps
    assert len(structmap_types) == 2
    assert "physical" in structmap_types
    assert "logical" in structmap_types

    # Test that our physical structmap is labeled properly.
    assert root_div_labels[0] == tmp_path.name
    assert subdir_div_labels[0] == subdir_path.name
    assert file_div_labels[0] == file_path.name
    assert file_ids[0] == "file-{}".format(file_obj.uuid)

    # Test that both (empty and not empty) dirs show up in logical structmap
    assert subdir_div_labels[1] == subdir_path.name
    assert subdir_div_labels[2] == empty_subdir_path.name


@pytest.mark.django_db
def test_transfer_mets_filegrp_format(
    tmp_path, transfer, file_obj, subdir_path, empty_subdir_path, file_path
):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    file_entries = mets_xml.xpath(
        ".//mets:fileGrp/mets:file", namespaces=mets_xml.nsmap
    )
    expected_file_path = subdir_path.relative_to(tmp_path) / file_path.name

    assert file_entries[0].get("ID") == "file-{}".format(file_obj.uuid)
    assert file_entries[0][0].get("{http://www.w3.org/1999/xlink}href") == str(
        expected_file_path
    )


@pytest.mark.django_db
def test_transfer_mets_objid(tmp_path, transfer):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()
    objids = mets_xml.xpath("/*/@OBJID", namespaces=mets_xml.nsmap)

    assert len(objids) == 1
    assert objids[0] == str(transfer.uuid)


@pytest.mark.django_db
def test_transfer_mets_accession_id(tmp_path, transfer):
    transfer.accessionid = "12345"
    transfer.save()
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()
    alt_record_id = mets_xml.xpath(
        ".//mets:metsHdr/mets:altRecordID", namespaces=mets_xml.nsmap
    )[0]

    assert alt_record_id.get("TYPE") == "Accession ID"
    assert alt_record_id.text == "12345"


@pytest.mark.django_db
def test_transfer_mets_header(tmp_path, transfer, file_obj, dashboard_uuid):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    header = mets_xml.find(".//mets:metsHdr", namespaces=mets_xml.nsmap)
    agent = header.find("mets:agent", namespaces=mets_xml.nsmap)
    agent_name = agent.find("mets:name", namespaces=mets_xml.nsmap)
    agent_note = agent.find("mets:note", namespaces=mets_xml.nsmap)

    assert agent.get("ROLE") == "CREATOR"
    assert agent.get("TYPE") == "OTHER"
    assert agent.get("OTHERTYPE") == "SOFTWARE"
    assert agent_name.text == dashboard_uuid
    assert agent_note.text == "Archivematica dashboard UUID"


@pytest.mark.django_db
def test_transfer_mets_premis_object_includes_type(
    tmp_path, transfer, file_obj, fpcommand_output
):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()
    premis_objects = mets_xml.xpath(".//premis:object", namespaces=PREMIS_NAMESPACES)

    assert len(premis_objects) == 1

    attr = "{%s}type" % PREMIS_NAMESPACES["xsi"]
    assert premis_objects[0].get(attr) == "premis:file"


@pytest.mark.django_db
def test_transfer_mets_includes_fpcommand_output(
    tmp_path, transfer, file_obj, fpcommand_output
):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    expected_embed = etree.fromstring(fpcommand_output.content.encode("utf-8"))

    extensions = mets_xml.xpath(
        ".//premis:objectCharacteristicsExtension", namespaces=PREMIS_NAMESPACES
    )

    assert len(extensions) == 1

    assert extensions[0][0].tag == expected_embed.tag
    assert extensions[0][0].text == expected_embed.text


@pytest.mark.django_db
def test_transfer_mets_includes_events(tmp_path, transfer, event):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    premis_event = mets_xml.find(".//premis:event", namespaces=PREMIS_NAMESPACES)
    premis_event_id_type = premis_event.findtext(
        "premis:eventIdentifier/premis:eventIdentifierType",
        namespaces=PREMIS_NAMESPACES,
    )
    premis_event_id_value = premis_event.findtext(
        "premis:eventIdentifier/premis:eventIdentifierValue",
        namespaces=PREMIS_NAMESPACES,
    )
    premis_event_type = premis_event.findtext(
        "premis:eventType", namespaces=PREMIS_NAMESPACES
    )
    premis_event_date_time = premis_event.findtext(
        "premis:eventDateTime", namespaces=PREMIS_NAMESPACES
    )
    premis_event_detail = premis_event.findtext(
        "premis:eventDetailInformation/premis:eventDetail", namespaces=PREMIS_NAMESPACES
    )
    premis_event_outcome_note = premis_event.findtext(
        "premis:eventOutcomeInformation/premis:eventOutcomeDetail/premis:eventOutcomeDetailNote",
        namespaces=PREMIS_NAMESPACES,
    )
    premis_event_agent_id_type = premis_event.findtext(
        "premis:linkingAgentIdentifier/premis:linkingAgentIdentifierType",
        namespaces=PREMIS_NAMESPACES,
    )
    premis_event_agent_id_value = premis_event.findtext(
        "premis:linkingAgentIdentifier/premis:linkingAgentIdentifierValue",
        namespaces=PREMIS_NAMESPACES,
    )

    assert premis_event_id_type == "UUID"
    assert premis_event_id_value == str(event.event_id)
    assert premis_event_type == event.event_type
    assert premis_event_date_time == str(event.event_datetime)
    assert premis_event_detail == event.event_detail
    assert premis_event_outcome_note == event.event_outcome_detail
    assert (
        premis_event_agent_id_type
        == Agent.objects.get_preservation_system_agent().identifiertype
    )
    assert (
        premis_event_agent_id_value
        == Agent.objects.get_preservation_system_agent().identifiervalue
    )

    premis_agent_software = mets_xml.xpath(
        "//premis:agent/premis:agentType[text()='software']/..",
        namespaces=PREMIS_NAMESPACES,
    )[0]
    premis_agent_software_identifier_type = premis_agent_software.findtext(
        "premis:agentIdentifier/premis:agentIdentifierType",
        namespaces=PREMIS_NAMESPACES,
    )
    premis_agent_software_identifier_value = premis_agent_software.findtext(
        "premis:agentIdentifier/premis:agentIdentifierValue",
        namespaces=PREMIS_NAMESPACES,
    )
    premis_agent_software_name = premis_agent_software.findtext(
        "premis:agentName", namespaces=PREMIS_NAMESPACES
    )
    premis_agent_software_type = premis_agent_software.findtext(
        "premis:agentType", namespaces=PREMIS_NAMESPACES
    )

    assert premis_agent_software_identifier_type == "preservation system"
    assert (
        premis_agent_software_identifier_value == get_preservation_system_identifier()
    )
    assert premis_agent_software_name == "Archivematica"
    assert premis_agent_software_type == "software"


@pytest.mark.django_db
def test_transfer_mets_includes_basic_rights(
    tmp_path, transfer, file_obj, basic_rights_statement
):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    grant_db_obj = basic_rights_statement.rightsstatementrightsgranted_set.first()
    restriction_db_obj = grant_db_obj.restrictions.first()
    grant_notes = grant_db_obj.notes.order_by("id")

    rights_statement = mets_xml.find(
        ".//premis:rightsStatement", namespaces=PREMIS_NAMESPACES
    )
    rights_id = rights_statement.find(
        "premis:rightsStatementIdentifier/premis:rightsStatementIdentifierValue",
        namespaces=PREMIS_NAMESPACES,
    )
    rights_basis = rights_statement.find(
        "premis:rightsBasis", namespaces=PREMIS_NAMESPACES
    )
    rights_granted = rights_statement.find(
        "premis:rightsGranted", namespaces=PREMIS_NAMESPACES
    )
    rights_granted_act = rights_granted.find("premis:act", namespaces=PREMIS_NAMESPACES)
    rights_granted_restriction = rights_granted.find(
        "premis:restriction", namespaces=PREMIS_NAMESPACES
    )
    rights_term_of_grant = rights_granted.find(
        "premis:termOfGrant", namespaces=PREMIS_NAMESPACES
    )
    rights_term_of_grant_start = rights_term_of_grant.find(
        "premis:startDate", namespaces=PREMIS_NAMESPACES
    )
    rights_term_of_grant_end = rights_term_of_grant.find(
        "premis:endDate", namespaces=PREMIS_NAMESPACES
    )
    rights_granted_notes = rights_granted.findall(
        "premis:rightsGrantedNote", namespaces=PREMIS_NAMESPACES
    )
    linking_obj_id = rights_statement.find(
        "premis:linkingObjectIdentifier", namespaces=PREMIS_NAMESPACES
    )
    linking_obj_id_type = linking_obj_id.find(
        "premis:linkingObjectIdentifierType", namespaces=PREMIS_NAMESPACES
    )
    linking_obj_id_value = linking_obj_id.find(
        "premis:linkingObjectIdentifierValue", namespaces=PREMIS_NAMESPACES
    )

    assert rights_id.text == basic_rights_statement.rightsstatementidentifiervalue
    assert rights_basis.text == basic_rights_statement.rightsbasis

    assert rights_granted_act.text == grant_db_obj.act
    assert rights_granted_restriction.text == restriction_db_obj.restriction
    assert rights_term_of_grant_start.text == grant_db_obj.startdate
    assert rights_term_of_grant_end.text == "OPEN"

    assert linking_obj_id_type.text == "UUID"
    assert linking_obj_id_value.text == str(file_obj.uuid)

    for index, note in enumerate(grant_notes):
        assert rights_granted_notes[index].text == note.rightsgrantednote


@pytest.mark.django_db
def test_transfer_mets_includes_copyright_rights(
    tmp_path, transfer, file_obj, copyright_rights
):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    copyright_db_obj = copyright_rights.rightsstatementcopyright_set.first()
    copyright_note = copyright_db_obj.rightsstatementcopyrightnote_set.first()
    doc_identifier_db_obj = (
        copyright_db_obj.rightsstatementcopyrightdocumentationidentifier_set.first()
    )

    copyright_info = mets_xml.find(
        ".//premis:copyrightInformation", namespaces=PREMIS_NAMESPACES
    )
    rights_jurisdiction = copyright_info.find(
        "premis:copyrightJurisdiction", namespaces=PREMIS_NAMESPACES
    )
    rights_status_date = copyright_info.find(
        "premis:copyrightStatusDeterminationDate", namespaces=PREMIS_NAMESPACES
    )
    rights_note = copyright_info.find(
        "premis:copyrightNote", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier = copyright_info.find(
        "premis:copyrightDocumentationIdentifier", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_type = doc_identifier.find(
        "premis:copyrightDocumentationIdentifierType", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_value = doc_identifier.find(
        "premis:copyrightDocumentationIdentifierValue", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_role = doc_identifier.find(
        "premis:copyrightDocumentationRole", namespaces=PREMIS_NAMESPACES
    )
    applicable_dates = copyright_info.find(
        "premis:copyrightApplicableDates", namespaces=PREMIS_NAMESPACES
    )
    copyright_state_date = applicable_dates.find(
        "premis:startDate", namespaces=PREMIS_NAMESPACES
    )
    copyright_end_date = applicable_dates.find(
        "premis:endDate", namespaces=PREMIS_NAMESPACES
    )

    assert rights_jurisdiction.text == "CA"
    assert rights_status_date.text == copyright_db_obj.copyrightstatusdeterminationdate
    assert rights_note.text == copyright_note.copyrightnote
    assert (
        doc_identifier_type.text
        == doc_identifier_db_obj.copyrightdocumentationidentifiertype
    )
    assert (
        doc_identifier_value.text
        == doc_identifier_db_obj.copyrightdocumentationidentifiervalue
    )
    assert (
        doc_identifier_role.text
        == doc_identifier_db_obj.copyrightdocumentationidentifierrole
    )
    assert copyright_state_date.text == copyright_db_obj.copyrightapplicablestartdate
    assert copyright_end_date.text == "OPEN"


@pytest.mark.django_db
def test_transfer_mets_includes_license_rights(
    tmp_path, transfer, file_obj, license_rights
):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    license_db_obj = license_rights.rightsstatementlicense_set.first()
    license_note_db_obj = license_db_obj.rightsstatementlicensenote_set.first()
    doc_identifier_db_obj = (
        license_db_obj.rightsstatementlicensedocumentationidentifier_set.first()
    )

    license_info = mets_xml.find(
        ".//premis:licenseInformation", namespaces=PREMIS_NAMESPACES
    )
    license_terms = license_info.find(
        "premis:licenseTerms", namespaces=PREMIS_NAMESPACES
    )
    license_note = license_info.find("premis:licenseNote", namespaces=PREMIS_NAMESPACES)
    doc_identifier = license_info.find(
        "premis:licenseDocumentationIdentifier", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_type = doc_identifier.find(
        "premis:licenseDocumentationIdentifierType", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_value = doc_identifier.find(
        "premis:licenseDocumentationIdentifierValue", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_role = doc_identifier.find(
        "premis:licenseDocumentationRole", namespaces=PREMIS_NAMESPACES
    )
    applicable_dates = license_info.find(
        "premis:licenseApplicableDates", namespaces=PREMIS_NAMESPACES
    )
    state_date = applicable_dates.find("premis:startDate", namespaces=PREMIS_NAMESPACES)
    end_date = applicable_dates.find("premis:endDate", namespaces=PREMIS_NAMESPACES)

    assert license_note.text == license_note_db_obj.licensenote
    assert license_terms.text == license_db_obj.licenseterms
    assert (
        doc_identifier_type.text
        == doc_identifier_db_obj.licensedocumentationidentifiertype
    )
    assert (
        doc_identifier_value.text
        == doc_identifier_db_obj.licensedocumentationidentifiervalue
    )
    assert (
        doc_identifier_role.text
        == doc_identifier_db_obj.licensedocumentationidentifierrole
    )
    assert state_date.text == license_db_obj.licenseapplicablestartdate
    assert end_date.text == "OPEN"


@pytest.mark.django_db
def test_transfer_mets_includes_statute_rights(
    tmp_path, transfer, file_obj, statute_rights
):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    statute_db_obj = statute_rights.rightsstatementstatuteinformation_set.first()
    statute_note_db_obj = (
        statute_db_obj.rightsstatementstatuteinformationnote_set.first()
    )
    doc_identifier_db_obj = (
        statute_db_obj.rightsstatementstatutedocumentationidentifier_set.first()
    )

    statute_info = mets_xml.find(
        ".//premis:statuteInformation", namespaces=PREMIS_NAMESPACES
    )
    statute_jurisdiction = statute_info.find(
        "premis:statuteJurisdiction", namespaces=PREMIS_NAMESPACES
    )
    statute_determination_date = statute_info.find(
        "premis:statuteInformationDeterminationDate", namespaces=PREMIS_NAMESPACES
    )
    statute_citation = statute_info.find(
        "premis:statuteCitation", namespaces=PREMIS_NAMESPACES
    )
    statute_note = statute_info.find("premis:statuteNote", namespaces=PREMIS_NAMESPACES)
    doc_identifier = statute_info.find(
        "premis:statuteDocumentationIdentifier", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_type = doc_identifier.find(
        "premis:statuteDocumentationIdentifierType", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_value = doc_identifier.find(
        "premis:statuteDocumentationIdentifierValue", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_role = doc_identifier.find(
        "premis:statuteDocumentationRole", namespaces=PREMIS_NAMESPACES
    )
    applicable_dates = statute_info.find(
        "premis:statuteApplicableDates", namespaces=PREMIS_NAMESPACES
    )
    state_date = applicable_dates.find("premis:startDate", namespaces=PREMIS_NAMESPACES)
    end_date = applicable_dates.find("premis:endDate", namespaces=PREMIS_NAMESPACES)

    assert statute_jurisdiction.text == statute_db_obj.statutejurisdiction
    assert statute_citation.text == statute_db_obj.statutecitation
    assert statute_determination_date.text == statute_db_obj.statutedeterminationdate
    assert statute_note.text == statute_note_db_obj.statutenote
    assert (
        doc_identifier_type.text
        == doc_identifier_db_obj.statutedocumentationidentifiertype
    )
    assert (
        doc_identifier_value.text
        == doc_identifier_db_obj.statutedocumentationidentifiervalue
    )
    assert (
        doc_identifier_role.text
        == doc_identifier_db_obj.statutedocumentationidentifierrole
    )
    assert state_date.text == statute_db_obj.statuteapplicablestartdate
    assert end_date.text == "OPEN"


@pytest.mark.django_db
def test_transfer_mets_includes_other_rights(
    tmp_path, transfer, file_obj, other_rights
):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    other_rights_db_obj = other_rights.rightsstatementotherrightsinformation_set.first()
    other_rights_note_db_obj = (
        other_rights_db_obj.rightsstatementotherrightsinformationnote_set.first()
    )
    doc_identifier_db_obj = (
        other_rights_db_obj.rightsstatementotherrightsdocumentationidentifier_set.first()
    )

    other_rights_info = mets_xml.find(
        ".//premis:otherRightsInformation", namespaces=PREMIS_NAMESPACES
    )
    other_rights_basis = other_rights_info.find(
        "premis:otherRightsBasis", namespaces=PREMIS_NAMESPACES
    )
    other_rights_note = other_rights_info.find(
        "premis:otherRightsNote", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier = other_rights_info.find(
        "premis:otherRightsDocumentationIdentifier", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_type = doc_identifier.find(
        "premis:otherRightsDocumentationIdentifierType", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_value = doc_identifier.find(
        "premis:otherRightsDocumentationIdentifierValue", namespaces=PREMIS_NAMESPACES
    )
    doc_identifier_role = doc_identifier.find(
        "premis:otherRightsDocumentationRole", namespaces=PREMIS_NAMESPACES
    )
    applicable_dates = other_rights_info.find(
        "premis:otherRightsApplicableDates", namespaces=PREMIS_NAMESPACES
    )
    state_date = applicable_dates.find("premis:startDate", namespaces=PREMIS_NAMESPACES)
    end_date = applicable_dates.find("premis:endDate", namespaces=PREMIS_NAMESPACES)

    assert other_rights_basis.text == other_rights_db_obj.otherrightsbasis
    assert other_rights_note.text == other_rights_note_db_obj.otherrightsnote
    assert (
        doc_identifier_type.text
        == doc_identifier_db_obj.otherrightsdocumentationidentifiertype
    )
    assert (
        doc_identifier_value.text
        == doc_identifier_db_obj.otherrightsdocumentationidentifiervalue
    )
    assert (
        doc_identifier_role.text
        == doc_identifier_db_obj.otherrightsdocumentationidentifierrole
    )
    assert state_date.text == other_rights_db_obj.otherrightsapplicablestartdate
    assert end_date.text == "OPEN"


@pytest.mark.django_db
def test_transfer_mets_directory_identifiers(tmp_path, transfer, dir_obj):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    expected_identifier = dir_obj.identifiers.first()
    premis_ie = mets_xml.find(".//premis:object", namespaces=PREMIS_NAMESPACES)
    identifiers = premis_ie.findall(
        "premis:objectIdentifier", namespaces=PREMIS_NAMESPACES
    )

    namespaced_attr = "{%s}type" % PREMIS_NAMESPACES["xsi"]
    assert premis_ie.get(namespaced_attr) == "premis:intellectualEntity"

    assert identifiers[0][0].text == "UUID"
    assert identifiers[0][1].text == str(dir_obj.uuid)
    assert identifiers[1][0].text == expected_identifier.type
    assert identifiers[1][1].text == expected_identifier.value


@pytest.mark.django_db
def test_transfer_mets_file_identifiers(tmp_path, transfer, file_obj):
    mets_path = tmp_path / "METS.xml"
    write_mets(str(mets_path), str(tmp_path), "transferDirectory", transfer.uuid)
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()

    expected_identifier = file_obj.identifiers.first()
    premis_obj = mets_xml.find(".//premis:object", namespaces=PREMIS_NAMESPACES)
    identifiers = premis_obj.findall(
        "premis:objectIdentifier", namespaces=PREMIS_NAMESPACES
    )

    assert identifiers[0][0].text == "UUID"
    assert identifiers[0][1].text == str(file_obj.uuid)
    assert identifiers[1][0].text == expected_identifier.type
    assert identifiers[1][1].text == expected_identifier.value
