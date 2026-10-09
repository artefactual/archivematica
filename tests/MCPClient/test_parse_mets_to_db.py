import os
import uuid
from typing import TypedDict
from unittest import mock

import pytest
from lxml import etree

from archivematica.dashboard.fpr import models as fprmodels
from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import parse_mets_to_db

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(THIS_DIR, "fixtures")


class FileInfo(TypedDict):
    """File information parsed from the METS file."""

    uuid: str
    original_path: str
    current_path: str
    use: str
    checksum: str
    checksumtype: str
    size: str
    format_version: fprmodels.FormatVersion | None
    derivation: str | None
    derivation_event: str | None


@pytest.fixture
def format_versions(db: None) -> dict[str, fprmodels.FormatVersion]:
    """The format versions of the files of the METS fixtures, by PRONOM identifier.

    Any other format version with the same PRONOM identifier is disabled so
    that the parser resolves the identifier to these.
    """
    result = {}
    for group, format_, description, version, pronom_id in [
        ("Image (Raster)", "JPEG", "JPEG 1.02", "1.02", "fmt/44"),
        ("Text (Markup)", "XML", "XML 1.0", "1.0", "fmt/101"),
        ("Text (Plain)", "Plain Text", "Generic TXT", "", "x-fmt/111"),
    ]:
        fprmodels.FormatVersion.objects.filter(pronom_id=pronom_id).update(
            enabled=False
        )
        result[pronom_id] = fprmodels.FormatVersion.objects.create(
            format=fprmodels.Format.objects.create(
                description=format_,
                group=fprmodels.FormatGroup.objects.create(description=group),
            ),
            description=description,
            version=version,
            pronom_id=pronom_id,
        )

    return result


@pytest.fixture
def orig_info(format_versions: dict[str, fprmodels.FormatVersion]) -> FileInfo:
    return {
        "uuid": "ae8d4290-fe52-4954-b72a-0f591bee2e2f",
        "original_path": "%SIPDirectory%objects/evelyn's photo.jpg",
        "current_path": "%SIPDirectory%objects/evelyn_s_photo.jpg",
        "use": "original",
        "checksum": "d2bed92b73c7090bb30a0b30016882e7069c437488e1513e9deaacbe29d38d92",
        "checksumtype": "sha256",
        "size": "158131",
        "format_version": format_versions["fmt/44"],
        "derivation": "8140ebe5-295c-490b-a34a-83955b7c844e",
        "derivation_event": "0ce13092-911f-4a89-b9e1-0e61921a03d4",
    }


@pytest.fixture
def pres_info() -> FileInfo:
    return {
        "uuid": "8140ebe5-295c-490b-a34a-83955b7c844e",
        "original_path": "%SIPDirectory%objects/evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif",
        "current_path": "%SIPDirectory%objects/evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif",
        "use": "preservation",
        "checksum": "d82448f154b9185bc777ecb0a3602760eb76ba85dd3098f073b2c91a03f571e9",
        "checksumtype": "sha256",
        "size": "1446772",
        "format_version": None,
        "derivation": None,
        "derivation_event": None,
    }


@pytest.fixture
def mets_info(format_versions: dict[str, fprmodels.FormatVersion]) -> FileInfo:
    return {
        "uuid": "590bd882-7521-498c-8f89-0958218f779d",
        "original_path": "%SIPDirectory%objects/submissionDocumentation/transfer-no-metadata-46260807-ece1-4a0e-b70a-9814c701146b/METS.xml",
        "current_path": "%SIPDirectory%objects/submissionDocumentation/transfer-no-metadata-46260807-ece1-4a0e-b70a-9814c701146b/METS.xml",
        "use": "submissionDocumentation",
        "checksum": "d41d8cd98f00b204e9800998ecf8427e",
        "checksumtype": "md5",
        "size": "12222",
        "format_version": format_versions["fmt/101"],
        "derivation": None,
        "derivation_event": None,
    }


@pytest.mark.django_db
def test_parse_dc_none_found(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should parse no DC if none is found."""
    sip_uuid = str(uuid.uuid4())
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_no_metadata.xml"))
    dc = parse_mets_to_db.parse_dc(mcp_job, sip_uuid, root)
    assert dc is None
    assert (
        models.DublinCore.objects.filter(metadataappliestoidentifier=sip_uuid).exists()
        is False
    )


@pytest.mark.django_db
def test_no_sip_dc(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should ignore file-level DC."""
    sip_uuid = "f35d2530-45eb-4eb1-aa09-fb30661e7dcd"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_only_file_dc.xml"))
    dc = parse_mets_to_db.parse_dc(mcp_job, sip_uuid, root)
    assert dc is None
    assert (
        models.DublinCore.objects.filter(metadataappliestoidentifier=sip_uuid).exists()
        is False
    )


@pytest.mark.django_db
def test_only_original(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should parse a SIP-level DC if found."""
    sip_uuid = "eacbf65f-2528-4be0-8cb3-532f45fcdff8"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_sip_dc.xml"))
    dc = parse_mets_to_db.parse_dc(mcp_job, sip_uuid, root)
    assert dc
    assert models.DublinCore.objects.filter(
        metadataappliestoidentifier=sip_uuid
    ).exists()
    assert dc.title == "Yamani Weapons"
    assert dc.creator == "Keladry of Mindelan"
    assert dc.subject == "Glaives"
    assert dc.description == "Glaives are cool"
    assert dc.publisher == "Tortall Press"
    assert dc.contributor == "Yuki"
    assert dc.date == "2014"
    assert dc.type == "Archival Information Package"
    assert dc.format == "parchement"
    assert dc.identifier == "42/1"
    assert dc.source == "Numair's library"
    assert dc.relation == "None"
    assert dc.language == "en"
    assert dc.rights == "Public Domain"
    assert dc.is_part_of == "AIC#43"


@pytest.mark.django_db
def test_dublin_core_non_core_properties(
    metadata_applies_to_types: dict[str, models.MetadataAppliesToType],
) -> None:
    """It should parse a SIP-level DC if contains non-core properties."""
    sip_uuid = "dbe62094-17af-427b-b6e7-0ac5799ee4e9"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_non_core_dc.xml"))
    job = mock.Mock(spec=Job)

    dc = parse_mets_to_db.parse_dc(job, sip_uuid, root)

    # Verify the Dublin Core core properties were populated.
    assert dc
    assert models.DublinCore.objects.filter(
        metadataappliestoidentifier=sip_uuid
    ).exists()
    assert dc.title == "Objects dir"

    # Verify the job prints the parsed Dublin Core core properties.
    assert job.pyprint.mock_calls == [
        mock.call("Dublin Core:"),
        mock.call("title", "Objects dir"),
    ]


@pytest.mark.django_db
def test_get_sip_dc_ignore_file_dc(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should parse a SIP-level DC even if file-level DC is also present."""
    sip_uuid = "55972e97-8d35-4b07-abaa-ae260c32d261"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_sip_and_file_dc.xml"))
    dc = parse_mets_to_db.parse_dc(mcp_job, sip_uuid, root)
    assert dc
    assert models.DublinCore.objects.filter(
        metadataappliestoidentifier=sip_uuid
    ).exists()
    assert dc.title == "Yamani Weapons"
    assert dc.creator == "Keladry of Mindelan"
    assert dc.subject == "Glaives"
    assert dc.description == "Glaives are cool"
    assert dc.publisher == "Tortall Press"
    assert dc.contributor == "Yuki"
    assert dc.date == "2014"
    assert dc.type == "Archival Information Package"
    assert dc.format == "parchement"
    assert dc.identifier == "42/1"
    assert dc.source == "Numair's library"
    assert dc.relation == "None"
    assert dc.language == "en"
    assert dc.rights == "Public Domain"
    assert dc.is_part_of == "AIC#43"


@pytest.mark.django_db
def test_multiple_sip_dc(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should parse the most recent SIP DC if multiple exist."""
    sip_uuid = "eacbf65f-2528-4be0-8cb3-532f45fcdff8"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_multiple_sip_dc.xml"))
    dc = parse_mets_to_db.parse_dc(mcp_job, sip_uuid, root)
    assert dc
    assert models.DublinCore.objects.filter(
        metadataappliestoidentifier=sip_uuid
    ).exists()
    assert dc.title == "Yamani Weapons"
    assert dc.creator == "Keladry of Mindelan"
    assert dc.subject == "Glaives"
    assert dc.description == "Glaives are awesome"
    assert dc.publisher == "Tortall Press"
    assert dc.contributor == "Yuki"
    assert dc.date == "2014"
    assert dc.type == "Archival Information Package"
    assert dc.format == "palimpsest"
    assert dc.identifier == "42/1"
    assert dc.source == ""
    assert dc.relation == "Everyone!"
    assert dc.language == "en"
    assert dc.rights == "Public Domain"
    assert dc.is_part_of == "AIC#43"


@pytest.mark.django_db
def test_parse_rights_none_found(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should parse no rights if none found."""
    sip_uuid = str(uuid.uuid4())
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_no_metadata.xml"))
    rights = parse_mets_to_db.parse_rights(mcp_job, sip_uuid, root)
    assert rights == []
    assert (
        models.RightsStatement.objects.filter(
            metadataappliestoidentifier=sip_uuid
        ).exists()
        is False
    )


@pytest.mark.django_db
def test_parse_copyright(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """
    It should parse copyright rights.
    It should parse multiple rightsGranted.
    """
    sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_all_rights.xml"))
    rights_list = parse_mets_to_db.parse_rights(mcp_job, sip_uuid, root)
    assert rights_list
    rights = models.RightsStatement.objects.get(
        metadataappliestoidentifier=sip_uuid, rightsbasis="Copyright"
    )
    assert rights.rightsstatementidentifiertype == ""
    assert rights.rightsstatementidentifiervalue == ""
    assert rights.rightsbasis == "Copyright"
    assert rights.status == "REINGEST"
    cr = models.RightsStatementCopyright.objects.get(rightsstatement=rights)
    assert cr.copyrightstatus == "Under copyright"
    assert cr.copyrightjurisdiction == "CA"
    assert cr.copyrightstatusdeterminationdate == "2015"
    assert cr.copyrightapplicablestartdate == "1990"
    assert cr.copyrightapplicableenddate is None
    assert cr.copyrightenddateopen is True
    di = models.RightsStatementCopyrightDocumentationIdentifier.objects.get(
        rightscopyright=cr
    )
    assert di.copyrightdocumentationidentifiertype == ""
    assert di.copyrightdocumentationidentifiervalue == ""
    assert di.copyrightdocumentationidentifierrole == ""
    note = models.RightsStatementCopyrightNote.objects.get(rightscopyright=cr)
    assert note.copyrightnote == "Copyright expires 2010"
    rg = models.RightsStatementRightsGranted.objects.filter(rightsstatement=rights)
    assert len(rg) == 2
    assert rg[0].act == "Disseminate"
    assert rg[0].startdate == "2000"
    assert rg[0].enddate is None
    assert rg[0].enddateopen is True
    rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg[0])
    assert rgnote.rightsgrantednote == "Attribution required"
    rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
        rightsgranted=rg[0]
    )
    assert rgrestriction.restriction == "Allow"
    assert rg[1].act == "Access"
    assert rg[1].startdate == "1999"
    assert rg[1].enddate is None
    assert rg[1].enddateopen is True
    rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg[1])
    assert rgnote.rightsgrantednote == "Access one year before dissemination"
    rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
        rightsgranted=rg[1]
    )
    assert rgrestriction.restriction == "Allow"


@pytest.mark.django_db
def test_parse_license(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should parse license rights."""
    sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_all_rights.xml"))
    rights_list = parse_mets_to_db.parse_rights(mcp_job, sip_uuid, root)
    assert rights_list
    rights = models.RightsStatement.objects.get(
        metadataappliestoidentifier=sip_uuid, rightsbasis="License"
    )
    assert rights.rightsstatementidentifiertype == ""
    assert rights.rightsstatementidentifiervalue == ""
    assert rights.rightsbasis == "License"
    assert rights.status == "REINGEST"
    li = models.RightsStatementLicense.objects.get(rightsstatement=rights)
    assert li.licenseterms == "CC-BY-SA"
    assert li.licenseapplicablestartdate == "2015"
    assert li.licenseapplicableenddate is None
    assert li.licenseenddateopen is True
    di = models.RightsStatementLicenseDocumentationIdentifier.objects.get(
        rightsstatementlicense=li
    )
    assert di.licensedocumentationidentifiertype == ""
    assert di.licensedocumentationidentifiervalue == ""
    assert di.licensedocumentationidentifierrole == ""
    note = models.RightsStatementLicenseNote.objects.get(rightsstatementlicense=li)
    assert note.licensenote == ""
    rg = models.RightsStatementRightsGranted.objects.get(rightsstatement=rights)
    assert rg.act == "Disseminate"
    assert rg.startdate == "2015"
    assert rg.enddate is None
    assert rg.enddateopen is True
    rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg)
    assert rgnote.rightsgrantednote == "Attribution required"
    rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
        rightsgranted=rg
    )
    assert rgrestriction.restriction == "Allow"


@pytest.mark.django_db
def test_parse_statute(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should parse statute rights."""
    sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_all_rights.xml"))
    rights_list = parse_mets_to_db.parse_rights(mcp_job, sip_uuid, root)
    assert rights_list
    rights = models.RightsStatement.objects.get(
        metadataappliestoidentifier=sip_uuid, rightsbasis="Statute"
    )
    assert rights.rightsstatementidentifiertype == ""
    assert rights.rightsstatementidentifiervalue == ""
    assert rights.rightsbasis == "Statute"
    assert rights.status == "REINGEST"
    st = models.RightsStatementStatuteInformation.objects.get(rightsstatement=rights)
    assert st.statutejurisdiction == "BC, Canada"
    assert st.statutecitation == "Freedom of Information Act"
    assert st.statutedeterminationdate == "2011"
    assert st.statuteapplicablestartdate == "1994"
    assert st.statuteapplicableenddate == "2094"
    assert st.statuteenddateopen is False
    di = models.RightsStatementStatuteDocumentationIdentifier.objects.get(
        rightsstatementstatute=st
    )
    assert di.statutedocumentationidentifiertype == ""
    assert di.statutedocumentationidentifiervalue == ""
    assert di.statutedocumentationidentifierrole == ""
    note = models.RightsStatementStatuteInformationNote.objects.get(
        rightsstatementstatute=st
    )
    assert note.statutenote == "SIN & health numbers"
    rg = models.RightsStatementRightsGranted.objects.get(rightsstatement=rights)
    assert rg.act == "Disseminate"
    assert rg.startdate == "1994"
    assert rg.enddate == "2094"
    assert rg.enddateopen is False
    rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg)
    assert rgnote.rightsgrantednote == ""
    rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
        rightsgranted=rg
    )
    assert rgrestriction.restriction == "Disallow"


@pytest.mark.django_db
def test_parse_policy(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should parse policy rights."""
    pass
    sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_all_rights.xml"))
    rights_list = parse_mets_to_db.parse_rights(mcp_job, sip_uuid, root)
    assert rights_list
    rights = models.RightsStatement.objects.get(
        metadataappliestoidentifier=sip_uuid, rightsbasis="Policy"
    )
    assert rights.rightsstatementidentifiertype == ""
    assert rights.rightsstatementidentifiervalue == ""
    assert rights.rightsbasis == "Policy"
    assert rights.status == "REINGEST"
    other = models.RightsStatementOtherRightsInformation.objects.get(
        rightsstatement=rights
    )
    assert other.otherrightsbasis == "Policy"
    assert other.otherrightsapplicablestartdate == "1989"
    assert other.otherrightsapplicableenddate is None
    assert other.otherrightsenddateopen is True
    di = models.RightsStatementOtherRightsDocumentationIdentifier.objects.get(
        rightsstatementotherrights=other
    )
    assert di.otherrightsdocumentationidentifiertype == ""
    assert di.otherrightsdocumentationidentifiervalue == ""
    assert di.otherrightsdocumentationidentifierrole == ""
    note = models.RightsStatementOtherRightsInformationNote.objects.get(
        rightsstatementotherrights=other
    )
    assert note.otherrightsnote == "Pubic relations office only"
    rg = models.RightsStatementRightsGranted.objects.get(rightsstatement=rights)
    assert rg.act == "Disseminate"
    assert rg.startdate == "1989-01-01"
    assert rg.enddate is None
    assert rg.enddateopen is True
    rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg)
    assert rgnote.rightsgrantednote == ""
    rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
        rightsgranted=rg
    )
    assert rgrestriction.restriction == "Conditional"


@pytest.mark.django_db
def test_parse_donor(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should parse donor rights."""
    pass
    sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_all_rights.xml"))
    rights_list = parse_mets_to_db.parse_rights(mcp_job, sip_uuid, root)
    assert rights_list
    rights = models.RightsStatement.objects.get(
        metadataappliestoidentifier=sip_uuid, rightsbasis="Donor"
    )
    assert rights.rightsstatementidentifiertype == ""
    assert rights.rightsstatementidentifiervalue == ""
    assert rights.rightsbasis == "Donor"
    assert rights.status == "REINGEST"
    other = models.RightsStatementOtherRightsInformation.objects.get(
        rightsstatement=rights
    )
    assert other.otherrightsbasis == "Donor"
    assert other.otherrightsapplicablestartdate == "2000-01-01"
    assert other.otherrightsapplicableenddate == "2020-01-01"
    assert other.otherrightsenddateopen is False
    di = models.RightsStatementOtherRightsDocumentationIdentifier.objects.get(
        rightsstatementotherrights=other
    )
    assert di.otherrightsdocumentationidentifiertype == "DID"
    assert di.otherrightsdocumentationidentifiervalue == "1"
    assert di.otherrightsdocumentationidentifierrole == "-"
    note = models.RightsStatementOtherRightsInformationNote.objects.get(
        rightsstatementotherrights=other
    )
    assert note.otherrightsnote == "Contact in 2010 for earlier"
    rg = models.RightsStatementRightsGranted.objects.get(rightsstatement=rights)
    assert rg.act == "Publish"
    assert rg.startdate == "2000-01-01"
    assert rg.enddate == "2020-01-01"
    assert rg.enddateopen is False
    rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg)
    assert rgnote.rightsgrantednote == ""
    rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
        rightsgranted=rg
    )
    assert rgrestriction.restriction == "Conditional"


@pytest.mark.django_db
def test_parse_multiple_rights(
    mcp_job: Job, metadata_applies_to_types: dict[str, models.MetadataAppliesToType]
) -> None:
    """It should only parse the most recent rights."""
    sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_updated_rights.xml"))
    rights_list = parse_mets_to_db.parse_rights(mcp_job, sip_uuid, root)
    assert rights_list
    rights = models.RightsStatement.objects.get(
        metadataappliestoidentifier=sip_uuid, rightsbasis="Statute"
    )
    assert rights.rightsstatementidentifiertype == ""
    assert rights.rightsstatementidentifiervalue == ""
    assert rights.rightsbasis == "Statute"
    assert rights.status == "REINGEST"
    st = models.RightsStatementStatuteInformation.objects.get(rightsstatement=rights)
    assert st.statutejurisdiction == "British Columbia, Canada"
    assert (
        st.statutecitation == "Freedom of Information Act and Protection of Privacy Act"
    )
    assert st.statutedeterminationdate == "2015"
    assert st.statuteapplicablestartdate == "2000"
    assert st.statuteapplicableenddate is None
    assert st.statuteenddateopen is True
    di = models.RightsStatementStatuteDocumentationIdentifier.objects.get(
        rightsstatementstatute=st
    )
    assert di.statutedocumentationidentifiertype == "Doc"
    assert di.statutedocumentationidentifiervalue == "1"
    assert di.statutedocumentationidentifierrole == "-"
    note = models.RightsStatementStatuteInformationNote.objects.get(
        rightsstatementstatute=st
    )
    assert note.statutenote == "SIN and health numbers"
    rg = models.RightsStatementRightsGranted.objects.get(rightsstatement=rights)
    assert rg.act == "Disseminate"
    assert rg.startdate == "2000"
    assert rg.enddate is None
    assert rg.enddateopen is True
    rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg)
    assert rgnote.rightsgrantednote == ""
    rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
        rightsgranted=rg
    )
    assert rgrestriction.restriction == "Disallow"


@pytest.mark.django_db
def test_parse_file_info(
    mcp_job: Job, orig_info: FileInfo, mets_info: FileInfo, pres_info: FileInfo
) -> None:
    """
    It should parse file info into a dict.
    It should attach derivation information to the original file.
    """
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_no_metadata.xml"))
    files = parse_mets_to_db.parse_files(mcp_job, root)
    assert files == [orig_info, mets_info, pres_info]


@pytest.mark.django_db
def test_parse_file_info_ignores_deleted_files_without_flocat(
    mcp_job: Job, format_versions: dict[str, fprmodels.FormatVersion]
) -> None:
    """It should ignore deleted file entries that have no physical location.

    Reingest retains deleted entries in the METS as provenance tombstones after
    their files have been removed from the AIP. They therefore have no FLocat
    and should not be loaded into the database as files to process again.
    """
    root = etree.parse(
        os.path.join(FIXTURES_DIR, "mets_deleted_file_without_flocat.xml")
    )

    files = parse_mets_to_db.parse_files(mcp_job, root)

    assert files == [
        {
            "uuid": "85aa559e-5a38-4be7-a814-708f738fd40c",
            "original_path": "%SIPDirectory%objects/preserved.txt",
            "current_path": "%SIPDirectory%objects/preserved.txt",
            "use": "preservation",
            "checksum": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
            "checksumtype": "sha256",
            "size": "11",
            "format_version": format_versions["x-fmt/111"],
            "derivation": None,
            "derivation_event": None,
        }
    ]


@pytest.mark.django_db
def test_parse_file_info_reingest(
    mcp_job: Job, orig_info: FileInfo, mets_info: FileInfo, pres_info: FileInfo
) -> None:
    """
    It should parse the correct techMD in the amdSec.
    """
    root = etree.parse(os.path.join(FIXTURES_DIR, "mets_superseded_techmd.xml"))
    files = parse_mets_to_db.parse_files(mcp_job, root)
    assert files == [orig_info, mets_info, pres_info]


@pytest.mark.django_db
def test_insert_file_info(
    sip: models.SIP, orig_info: FileInfo, mets_info: FileInfo, pres_info: FileInfo
) -> None:
    """It should insert file info into the DB."""
    files = [mets_info, pres_info, orig_info]
    parse_mets_to_db.update_files(str(sip.uuid), files)
    # Verify original file
    orig = models.File.objects.get(uuid=orig_info["uuid"])
    assert orig.sip_id == sip.uuid
    assert orig.transfer is None
    assert orig.originallocation.decode() == orig_info["original_path"]
    assert orig.currentlocation.decode() == orig_info["current_path"]
    assert orig.filegrpuse == orig_info["use"]
    assert orig.filegrpuuid == ""
    assert orig.checksum == orig_info["checksum"]
    assert orig.checksumtype == orig_info["checksumtype"]
    assert orig.size == int(orig_info["size"])
    assert models.Event.objects.get(
        file_uuid_id=orig_info["uuid"], event_type="reingestion"
    )
    assert models.FileFormatVersion.objects.get(
        file_uuid_id=orig_info["uuid"],
        format_version=orig_info["format_version"],
    )
    assert models.Derivation.objects.get(
        source_file_id=orig_info["uuid"], derived_file=pres_info["uuid"]
    )
    # Verify preservation file
    pres = models.File.objects.get(uuid=pres_info["uuid"])
    assert pres.sip_id == sip.uuid
    assert pres.transfer is None
    assert pres.originallocation.decode() == pres_info["original_path"]
    assert pres.currentlocation.decode() == pres_info["current_path"]
    assert pres.filegrpuse == pres_info["use"]
    assert pres.filegrpuuid == ""
    assert pres.checksum == pres_info["checksum"]
    assert pres.checksumtype == pres_info["checksumtype"]
    assert pres.size == int(pres_info["size"])
    assert models.Event.objects.get(
        file_uuid_id=pres_info["uuid"], event_type="reingestion"
    )
    assert (
        models.FileFormatVersion.objects.filter(file_uuid_id=pres_info["uuid"]).exists()
        is False
    )
    # Verify original file
    mets = models.File.objects.get(uuid=mets_info["uuid"])
    assert mets.sip_id == sip.uuid
    assert mets.transfer is None
    assert mets.originallocation.decode() == mets_info["original_path"]
    assert mets.currentlocation.decode() == mets_info["current_path"]
    assert mets.filegrpuse == mets_info["use"]
    assert mets.filegrpuuid == ""
    assert mets.checksum == mets_info["checksum"]
    assert mets.checksumtype == mets_info["checksumtype"]
    assert mets.size == int(mets_info["size"])
    assert models.Event.objects.get(
        file_uuid_id=mets_info["uuid"], event_type="reingestion"
    )
    assert models.FileFormatVersion.objects.get(
        file_uuid_id=mets_info["uuid"],
        format_version=mets_info["format_version"],
    )
    assert (
        models.Derivation.objects.filter(source_file_id=mets_info["uuid"]).exists()
        is False
    )
    assert (
        models.Derivation.objects.filter(derived_file=mets_info["uuid"]).exists()
        is False
    )


@pytest.mark.django_db
@mock.patch("archivematica.MCPClient.clientScripts.parse_mets_to_db.os")
@mock.patch("archivematica.MCPClient.clientScripts.parse_mets_to_db.etree")
def test_main_sets_aip_reingest_type(etree, os, sip):
    job = None
    assert not models.SIP.objects.filter(uuid=sip.uuid, sip_type="AIP-REIN").exists()

    parse_mets_to_db.main(job, str(sip.uuid), sip.currentpath)

    assert models.SIP.objects.filter(uuid=sip.uuid, sip_type="AIP-REIN").exists()


@pytest.mark.django_db
@mock.patch("archivematica.MCPClient.clientScripts.parse_mets_to_db.os")
@mock.patch("archivematica.MCPClient.clientScripts.parse_mets_to_db.etree")
def test_main_unsets_partial_reingest_flag(etree, os, sip):
    job = None
    sip.set_partial_reingest()
    assert sip.is_partial_reingest()

    parse_mets_to_db.main(job, str(sip.uuid), sip.currentpath)

    assert not sip.is_partial_reingest()
