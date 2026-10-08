import os
import pathlib
import shutil
import uuid

import metsrw
import pytest
from lxml import etree

from archivematica.archivematicaCommon.namespaces import NSMAP
from archivematica.archivematicaCommon.namespaces import nsmap_for_premis2
from archivematica.archivematicaCommon.version import get_preservation_system_identifier
from archivematica.dashboard.fpr import models as fprmodels
from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import archivematicaCreateMETSReingest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(THIS_DIR, "fixtures")

REMOVE_BLANK_PARSER = etree.XMLParser(remove_blank_text=True)

# UUID of the AIP of the aip fixture, described by the METS fixtures.
SIP_UUID = "4060ee97-9c3f-4822-afaf-ebdf838284c3"

# UUID of a SIP that has no metadata in the database.
SIP_UUID_NONE = "dnedne7c-5bd2-4249-84a1-2f00f725b981"

# UUIDs of the SIPs with Dublin Core metadata of the dublincore fixture.
DC_SIP_UUID_ORIGINAL = "8b891d7c-5bd2-4249-84a1-2f00f725b981"
DC_SIP_UUID_REINGEST = "87d30df4-63f5-434b-9da6-25aa995de6fe"
DC_SIP_UUID_UPDATED = "5d78a2a5-57a6-430f-87b2-b89fb3ccb050"

# UUIDs of the SIPs with rights statements of the rights_statements fixture.
RIGHTS_SIP_UUID_ORIGINAL = "a4a5480c-9f51-4119-8dcb-d3f12e647c14"
RIGHTS_SIP_UUID_REINGEST = "10d57d98-29e5-4b2c-9f9f-d163e632eb31"
RIGHTS_SIP_UUID_UPDATED = "2941f14c-bd57-4f4a-a514-a3bf6ac5adf0"

METADATA_CSV_SIP_DIR = os.path.join(FIXTURES_DIR, "metadata_csv_sip", "")


@pytest.fixture
def aip(db: None) -> models.SIP:
    """The reingested AIP described by the METS fixtures."""
    return models.SIP.objects.create(
        uuid=uuid.UUID(SIP_UUID),
        sip_type="AIP-REIN",
        currentpath=(
            "%sharedPath%watchedDirectories/workFlowDecisions/metadataReminder/"
            f"no-metadata-{SIP_UUID}/"
        ),
    )


@pytest.fixture
def original_file(aip: models.SIP) -> models.File:
    """The original JPEG of the AIP, renamed during its transfer."""
    return models.File.objects.create(
        uuid=uuid.UUID("ae8d4290-fe52-4954-b72a-0f591bee2e2f"),
        sip=aip,
        filegrpuse="original",
        originallocation=b"%SIPDirectory%objects/evelyn's photo.jpg",
        currentlocation=b"%SIPDirectory%objects/evelyn_s_photo.jpg",
        checksum="d2bed92b73c7090bb30a0b30016882e7069c437488e1513e9deaacbe29d38d92",
        size=158131,
    )


@pytest.fixture
def preservation_derivative(aip: models.SIP) -> models.File:
    """The TIFF derivative of the original JPEG."""
    location = (
        b"%SIPDirectory%objects/evelyn_s_photo-8140ebe5-295c-490b-a34a-83955b7c844e.tif"
    )
    return models.File.objects.create(
        uuid=uuid.UUID("8140ebe5-295c-490b-a34a-83955b7c844e"),
        sip=aip,
        filegrpuse="preservation",
        originallocation=location,
        currentlocation=location,
        checksum="d82448f154b9185bc777ecb0a3602760eb76ba85dd3098f073b2c91a03f571e9",
        size=1446772,
    )


@pytest.fixture
def transfer_mets_file(aip: models.SIP) -> models.File:
    """The METS file of the transfer, kept as submission documentation."""
    location = (
        b"%SIPDirectory%objects/submissionDocumentation/"
        b"transfer-no-metadata-46260807-ece1-4a0e-b70a-9814c701146b/METS.xml"
    )
    return models.File.objects.create(
        uuid=uuid.UUID("590bd882-7521-498c-8f89-0958218f779d"),
        sip=aip,
        filegrpuse="submissionDocumentation",
        originallocation=location,
        currentlocation=location,
        checksum="51132e5ce1b5d2c2c363f05495f447ea924ab29c2cda2c11037b5fca2119e45a",
        size=12222,
    )


@pytest.fixture
def metadata_csv_file(aip: models.SIP) -> models.File:
    """The metadata.csv file added to the AIP during the reingest."""
    return models.File.objects.create(
        uuid=uuid.UUID("66370f14-2f64-4750-9d50-547614be40e8"),
        sip=aip,
        filegrpuse="metadata",
        originallocation=b"%SIPDirectory%metadata/metadata.csv",
        currentlocation=b"%SIPDirectory%objects/metadata/metadata.csv",
        checksum="e8121d8a660e2992872f0b67923d2d08dde9a1ba72dfd58e5a31e68fbac3633c",
        size=154,
    )


@pytest.fixture
def metadata_text_file(aip: models.SIP) -> models.File:
    """A metadata file in a subdirectory, added to the AIP during the reingest."""
    return models.File.objects.create(
        uuid=uuid.UUID("950253b2-e5b1-4222-bb86-4eb436af5713"),
        sip=aip,
        filegrpuse="metadata",
        originallocation=b"%SIPDirectory%metadata/foo/foo.txt",
        currentlocation=b"%SIPDirectory%objects/metadata/foo/foo.txt",
        size=154,
    )


@pytest.fixture
def aip_files(
    original_file: models.File,
    preservation_derivative: models.File,
    transfer_mets_file: models.File,
    metadata_csv_file: models.File,
    metadata_text_file: models.File,
) -> list[models.File]:
    """All the files of the AIP."""
    return [
        original_file,
        preservation_derivative,
        transfer_mets_file,
        metadata_csv_file,
        metadata_text_file,
    ]


@pytest.fixture
def unrelated_agent(db: None) -> models.Agent:
    """An organization agent that is not linked to any event."""
    return models.Agent.objects.create(
        agenttype="organization",
        identifiertype="repository code",
        identifiervalue="Unrelated Agent",
        name="Unrelated Agent",
    )


@pytest.fixture
def reingest_events(
    original_file: models.File,
    preservation_derivative: models.File,
    transfer_mets_file: models.File,
    demo_organization_agent: models.Agent,
    user_agent: models.Agent,
) -> list[models.Event]:
    """The events of the reingest: the files of the METS are reingested, the
    preservation derivative is deleted and the fixity of the original is checked.
    """
    result = []
    for file_, event_type, event_detail, event_outcome, event_outcome_detail in [
        (original_file, "reingestion", "", "", ""),
        (transfer_mets_file, "reingestion", "", "", ""),
        (preservation_derivative, "reingestion", "", "", ""),
        (preservation_derivative, "deletion", "", "", ""),
        (
            original_file,
            "fixity check",
            'program="python"; module="hashlib.sha256()"',
            "Pass",
            "91a5ddca3637590c2ddb50da5feb73ff0b8a98cd09a98afb79adc2cf70bc6220 verified",
        ),
    ]:
        event = models.Event.objects.create(
            file_uuid=file_,
            event_type=event_type,
            event_detail=event_detail,
            event_outcome=event_outcome,
            event_outcome_detail=event_outcome_detail,
        )
        event.agents.add(demo_organization_agent, user_agent)
        result.append(event)

    return result


@pytest.fixture
def recalculated_checksum(
    original_file: models.File,
    demo_organization_agent: models.Agent,
    user_agent: models.Agent,
) -> models.Event:
    """The MD5 checksum of the original file, calculated during the reingest."""
    original_file.checksum = "ac63a92ba5a94c337e740d6f189200d0"
    original_file.checksumtype = "md5"
    original_file.save()
    result = models.Event.objects.create(
        file_uuid=original_file,
        event_type="message digest calculation",
        event_detail='program="python"; module="hashlib.md5()"',
        event_outcome_detail="ac63a92ba5a94c337e740d6f189200d0",
    )
    result.agents.add(demo_organization_agent, user_agent)

    return result


@pytest.fixture
def new_file_id(
    original_file: models.File,
    demo_organization_agent: models.Agent,
    user_agent: models.Agent,
) -> models.FileID:
    """The format of the original file, identified again during the reingest."""
    event = models.Event.objects.create(
        file_uuid=original_file,
        event_type="format identification",
        event_detail='program="Fido"; version="1.2"',
        event_outcome="Positive",
        event_outcome_detail="fmt/9000",
    )
    event.agents.add(demo_organization_agent, user_agent)

    return models.FileID.objects.create(
        file=original_file,
        format_name="Newer fancier JPEG",
        format_version="9001",
        format_registry_name="PRONOM",
        format_registry_key="fmt/9000",
    )


@pytest.fixture
def new_characterization(
    original_file: models.File, format_version: fprmodels.FormatVersion
) -> list[models.FPCommandOutput]:
    """The output of the characterization commands run during the reingest."""
    result = []
    for tool, version, command, content in [
        (
            "FFprobe",
            "2.2.0",
            'ffprobe -i "%fileFullName%" -show_data -show_format -show_error -show_streams -show_chapters -show_private_data -show_versions -print_format xml',
            '<?xml version="1.0" encoding="UTF-8"?>\n<ffprobe>Stub ffprobe output</ffprobe>\n',
        ),
        (
            "MediaInfo",
            "0.7.52",
            'mediainfo --Language=Raw -f --Output=XML "%fileFullName%"',
            '<?xml version="1.0" encoding="UTF-8"?>\n<Mediainfo version="0.7.67">Stub MediaInfo output</Mediainfo>\n',
        ),
    ]:
        rule = fprmodels.FPRule.objects.create(
            purpose=fprmodels.FPRule.CHARACTERIZATION,
            format=format_version,
            command=fprmodels.FPCommand.objects.create(
                tool=fprmodels.FPTool.objects.create(description=tool, version=version),
                description=tool,
                command=command,
                script_type="bashScript",
                command_usage="characterization",
            ),
        )
        result.append(
            models.FPCommandOutput.objects.create(
                file=original_file, rule=rule, content=content
            )
        )

    return result


@pytest.fixture
def new_preservation_derivative(
    aip: models.SIP,
    original_file: models.File,
    demo_organization_agent: models.Agent,
    user_agent: models.Agent,
) -> models.File:
    """A TIFF derivative of the original JPEG, normalized during the reingest."""
    location = (
        b"%SIPDirectory%objects/evelyn_s_photo-d8cc7af7-284a-42f5-b7f4-e181a0efc35f.tif"
    )
    result = models.File.objects.create(
        uuid=uuid.UUID("d8cc7af7-284a-42f5-b7f4-e181a0efc35f"),
        sip=aip,
        filegrpuse="preservation",
        originallocation=location,
        currentlocation=location,
        checksum="d82448f154b9185bc777ecb0a3602760eb76ba85dd3098f073b2c91a03f571e9",
        checksumtype="sha256",
        size=1446772,
    )
    models.FileID.objects.create(file=result, format_name="TIFF")
    normalization = models.Event.objects.create(
        file_uuid=original_file,
        event_id=uuid.UUID("291f9be4-d19a-4bcc-8e1c-d3f01e4a48b1"),
        event_type="normalization",
        event_detail=(
            'ArchivematicaFPRCommandID="a34ddc9b-c922-4bb6-8037-bbe713332175"; '
            'program="convert"; version="Version: ImageMagick 6.7.7-10 2014-03-06 '
            'Q16 http://www.imagemagick.org"\n'
        ),
        event_outcome_detail=location.decode(),
    )
    models.Derivation.objects.create(
        source_file=original_file, derived_file=result, event=normalization
    )
    events = [normalization]
    for event_type, event_detail, event_outcome, event_outcome_detail in [
        ("creation", "", "", ""),
        (
            "message digest calculation",
            'program="python"; module="hashlib.sha256()"',
            "",
            "d82448f154b9185bc777ecb0a3602760eb76ba85dd3098f073b2c91a03f571e9",
        ),
        (
            "fixity check",
            'program="python"; module="hashlib.sha256()"',
            "Pass",
            "d82448f154b9185bc777ecb0a3602760eb76ba85dd3098f073b2c91a03f571e9 verified",
        ),
    ]:
        events.append(
            models.Event.objects.create(
                file_uuid=result,
                event_type=event_type,
                event_detail=event_detail,
                event_outcome=event_outcome,
                event_outcome_detail=event_outcome_detail,
            )
        )
    for event in events:
        event.agents.add(demo_organization_agent, user_agent)

    return result


@pytest.fixture
def dublincore(
    metadata_applies_to_types: dict[str, models.MetadataAppliesToType],
) -> list[models.DublinCore]:
    """The Dublin Core metadata of three SIPs: as ingested, as reingested without
    changes and as updated during the reingest.
    """
    result = []
    for sip_uuid, status in [
        (DC_SIP_UUID_ORIGINAL, "ORIGINAL"),
        (DC_SIP_UUID_REINGEST, "REINGEST"),
    ]:
        result.append(
            models.DublinCore.objects.create(
                metadataappliestotype=metadata_applies_to_types["sip"],
                metadataappliestoidentifier=sip_uuid,
                status=status,
                title="Yamani Weapons",
                creator="Keladry of Mindelan",
                subject="Glaives",
                description="Glaives are cool",
                publisher="Tortall Press",
                contributor="Yuki",
                date="2015",
                type="Archival Information Package",
                format="parchement",
                identifier="42/1",
                source="Numair's library",
                relation="None",
                language="en",
                rights="Public Domain",
                is_part_of="AIC#42",
            )
        )
    result.append(
        models.DublinCore.objects.create(
            metadataappliestotype=metadata_applies_to_types["sip"],
            metadataappliestoidentifier=DC_SIP_UUID_UPDATED,
            status="UPDATED",
            title="Yamani Weapons",
            creator="Keladry of Mindelan",
            subject="Glaives",
            description="Glaives are awesome",
            publisher="Tortall Press",
            contributor="Yuki, Neal",
            type="Archival Information Package",
            format="palimpsest",
            identifier="42/1",
            language="en",
            coverage="Partial",
            rights="Public Domain",
        )
    )

    return result


def grant_rights(
    statement: models.RightsStatement,
    act: str,
    startdate: str,
    enddate: str,
    enddateopen: bool,
    restriction: str,
    note: str | None = None,
) -> models.RightsStatementRightsGranted:
    """Add a rights granted with a restriction and an optional note to a statement."""
    result = models.RightsStatementRightsGranted.objects.create(
        rightsstatement=statement,
        act=act,
        startdate=startdate,
        enddate=enddate,
        enddateopen=enddateopen,
    )
    models.RightsStatementRightsGrantedRestriction.objects.create(
        rightsgranted=result, restriction=restriction
    )
    if note is not None:
        models.RightsStatementRightsGrantedNote.objects.create(
            rightsgranted=result, rightsgrantednote=note
        )

    return result


def add_copyright_information(statement: models.RightsStatement) -> None:
    """Describe an open-ended Canadian copyright in a statement."""
    copyright_information = models.RightsStatementCopyright.objects.create(
        rightsstatement=statement,
        copyrightstatus="Under copyright",
        copyrightjurisdiction="Canada",
        copyrightstatusdeterminationdate="2015",
        copyrightapplicablestartdate="1990",
        copyrightapplicableenddate="",
        copyrightenddateopen=True,
    )
    models.RightsStatementCopyrightNote.objects.create(
        rightscopyright=copyright_information, copyrightnote="Copyright expires 2010"
    )


def add_statute_information(
    statement: models.RightsStatement, enddate: str, note: str
) -> None:
    """Describe the Freedom of Information Act statute in a statement."""
    statute_information = models.RightsStatementStatuteInformation.objects.create(
        rightsstatement=statement,
        statutejurisdiction="BC, Canada",
        statutecitation="Freedom of Information Act",
        statutedeterminationdate="2011",
        statuteapplicablestartdate="1994",
        statuteapplicableenddate=enddate,
        statuteenddateopen=False,
    )
    models.RightsStatementStatuteInformationNote.objects.create(
        rightsstatementstatute=statute_information, statutenote=note
    )


@pytest.fixture
def rights_statements(
    metadata_applies_to_types: dict[str, models.MetadataAppliesToType],
) -> list[models.RightsStatement]:
    """The rights statements of three SIPs: as ingested, as reingested without
    changes and as updated during the reingest.
    """

    def create_statement(
        sip_uuid: str, rightsbasis: str, status: str
    ) -> models.RightsStatement:
        return models.RightsStatement.objects.create(
            metadataappliestotype=metadata_applies_to_types["sip"],
            metadataappliestoidentifier=sip_uuid,
            rightsbasis=rightsbasis,
            status=status,
        )

    copyright_statement = create_statement(
        RIGHTS_SIP_UUID_ORIGINAL, "Copyright", "ORIGINAL"
    )
    add_copyright_information(copyright_statement)
    grant_rights(
        copyright_statement,
        "Disseminate",
        "2000",
        "",
        True,
        "Allow",
        "Attribution required",
    )

    statute_statement = create_statement(
        RIGHTS_SIP_UUID_ORIGINAL, "Statute", "ORIGINAL"
    )
    add_statute_information(statute_statement, "2094", "SIN & health numbers")
    grant_rights(statute_statement, "Disseminate", "1994", "2094", False, "Disallow")

    license_statement = create_statement(
        RIGHTS_SIP_UUID_ORIGINAL, "License", "ORIGINAL"
    )
    license_information = models.RightsStatementLicense.objects.create(
        rightsstatement=license_statement,
        licenseterms="CC-BY-SA",
        licenseapplicablestartdate="2015",
        licenseapplicableenddate="",
        licenseenddateopen=True,
    )
    models.RightsStatementLicenseNote.objects.create(
        rightsstatementlicense=license_information,
        licensenote="Creative Commons Attribution Share Alike",
    )
    grant_rights(
        license_statement,
        "Disseminate",
        "2015",
        "",
        True,
        "Allow",
        "Attribution Required",
    )

    donor_statement = create_statement(RIGHTS_SIP_UUID_ORIGINAL, "Donor", "ORIGINAL")
    other_rights_information = (
        models.RightsStatementOtherRightsInformation.objects.create(
            rightsstatement=donor_statement,
            otherrightsbasis="Other",
            otherrightsapplicablestartdate="2000-01-01",
            otherrightsapplicableenddate="2100-01-01",
            otherrightsenddateopen=False,
        )
    )
    models.RightsStatementOtherRightsDocumentationIdentifier.objects.create(
        rightsstatementotherrights=other_rights_information,
        otherrightsdocumentationidentifiertype="DID",
        otherrightsdocumentationidentifiervalue="1",
        otherrightsdocumentationidentifierrole="-",
    )
    models.RightsStatementOtherRightsInformationNote.objects.create(
        rightsstatementotherrights=other_rights_information,
        otherrightsnote="Contact in 2010 for earlier release.",
    )
    grant_rights(
        donor_statement, "Publish", "2000-01-01", "2100-01-01", False, "Conditional"
    )

    reingested_copyright_statement = create_statement(
        RIGHTS_SIP_UUID_REINGEST, "Copyright", "REINGEST"
    )
    add_copyright_information(reingested_copyright_statement)
    grant_rights(
        reingested_copyright_statement,
        "Disseminate",
        "2000",
        "",
        True,
        "Allow",
        "Attribution required",
    )

    updated_statute_statement = create_statement(
        RIGHTS_SIP_UUID_UPDATED, "Statute", "UPDATED"
    )
    add_statute_information(updated_statute_statement, "2054", "SIN")
    grant_rights(
        updated_statute_statement, "Disseminate", "1994", "2054", False, "Disallow"
    )

    return [
        copyright_statement,
        statute_statement,
        license_statement,
        donor_statement,
        reingested_copyright_statement,
        updated_statute_statement,
        *(
            create_statement(RIGHTS_SIP_UUID_UPDATED, rightsbasis, "REINGEST")
            for rightsbasis in ["Copyright", "License", "Donor", "Policy"]
        ),
    ]


@pytest.mark.django_db
def test_object_not_updated(mcp_job: Job, reingest_events: list[models.Event]) -> None:
    """It should do nothing if the object has not been updated."""
    # Verify METS state
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert (
        len(
            mets.tree.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 1
    )
    # Run test
    mets = archivematicaCreateMETSReingest.update_object(mcp_job, mets)
    root = mets.serialize()
    # Verify no change
    assert (
        len(
            root.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 1
    )


@pytest.mark.django_db
def test_update_checksum_type(
    mcp_job: Job,
    reingest_events: list[models.Event],
    recalculated_checksum: models.Event,
) -> None:
    """It should add a new techMD with the new checksum & checksumtype."""
    # Verify METS state
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert (
        len(
            mets.tree.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 1
    )
    # Run test
    mets = archivematicaCreateMETSReingest.update_object(mcp_job, mets)
    root = mets.serialize()
    assert (
        len(
            root.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 2
    )
    # Verify old techMD
    old_techmd = root.find('.//mets:techMD[@ID="techMD_2"]', namespaces=NSMAP)
    old_techmd = root.xpath(
        'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID="techMD_2"]', namespaces=NSMAP
    )[0]
    assert old_techmd.attrib["STATUS"] == "superseded"
    namespaces = nsmap_for_premis2()
    assert (
        old_techmd.findtext(".//premis:messageDigestAlgorithm", namespaces=namespaces)
        == "sha256"
    )
    assert (
        old_techmd.findtext(".//premis:messageDigest", namespaces=namespaces)
        == "d2bed92b73c7090bb30a0b30016882e7069c437488e1513e9deaacbe29d38d92"
    )
    # Verify new techMD
    new_techmd = root.xpath(
        'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID!="techMD_2"]', namespaces=NSMAP
    )[0]
    assert new_techmd.attrib["STATUS"] == "current"
    assert (
        new_techmd.findtext(".//premis:messageDigestAlgorithm", namespaces=NSMAP)
        == "md5"
    )
    assert (
        new_techmd.findtext(".//premis:messageDigest", namespaces=NSMAP)
        == "ac63a92ba5a94c337e740d6f189200d0"
    )
    # Verify rest of new techMD was created
    assert new_techmd.find(".//premis:formatName", namespaces=NSMAP) is not None
    assert (
        new_techmd.find(".//premis:relatedObjectIdentifierType", namespaces=NSMAP)
        is not None
    )
    assert (
        len(
            new_techmd.find(
                ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
            )
        )
        > 0
    )


@pytest.mark.django_db
def test_update_file_id(
    mcp_job: Job, reingest_events: list[models.Event], new_file_id: models.FileID
) -> None:
    """It should add a new techMD with the new file ID."""
    # Verify METS state
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert (
        len(
            mets.tree.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 1
    )
    # Run test
    mets = archivematicaCreateMETSReingest.update_object(mcp_job, mets)
    root = mets.serialize()
    assert (
        len(
            root.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 2
    )
    # Verify old techMD
    old_techmd = root.find('.//mets:techMD[@ID="techMD_2"]', namespaces=NSMAP)
    old_techmd = root.xpath(
        'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID="techMD_2"]', namespaces=NSMAP
    )[0]
    assert old_techmd.attrib["STATUS"] == "superseded"
    namespaces = nsmap_for_premis2()
    assert (
        old_techmd.findtext(".//premis:formatName", namespaces=namespaces)
        == "JPEG 1.02"
    )
    assert (
        old_techmd.findtext(".//premis:formatVersion", namespaces=namespaces) == "1.02"
    )
    assert (
        old_techmd.findtext(".//premis:formatRegistryKey", namespaces=namespaces)
        == "fmt/44"
    )
    # Verify new techMD
    new_techmd = root.xpath(
        'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID!="techMD_2"]', namespaces=NSMAP
    )[0]
    assert new_techmd.attrib["STATUS"] == "current"
    assert (
        new_techmd.findtext(".//premis:formatName", namespaces=NSMAP)
        == "Newer fancier JPEG"
    )
    assert new_techmd.findtext(".//premis:formatVersion", namespaces=NSMAP) == "9001"
    assert (
        new_techmd.findtext(".//premis:formatRegistryKey", namespaces=NSMAP)
        == "fmt/9000"
    )
    # Verify rest of new techMD was created
    assert (
        new_techmd.find(".//premis:relatedObjectIdentifierType", namespaces=NSMAP)
        is not None
    )
    assert (
        len(
            new_techmd.find(
                ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
            )
        )
        > 0
    )


@pytest.mark.django_db
def test_update_characterization(
    mcp_job: Job,
    reingest_events: list[models.Event],
    new_characterization: list[models.FPCommandOutput],
) -> None:
    """It should add a new techMD with the new characterization."""
    # Verify METS state
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert (
        len(
            mets.tree.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 1
    )
    # Run test
    mets = archivematicaCreateMETSReingest.update_object(mcp_job, mets)
    root = mets.serialize()
    assert (
        len(
            root.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 2
    )
    # Verify old techMD - fall back to PREMIS 2
    old_techmd = root.find('.//mets:techMD[@ID="techMD_2"]', namespaces=NSMAP)
    old_techmd = root.xpath(
        'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID="techMD_2"]', namespaces=NSMAP
    )[0]
    assert old_techmd.attrib["STATUS"] == "superseded"
    namespaces = nsmap_for_premis2()
    assert (
        len(
            old_techmd.find(
                ".//premis:objectCharacteristicsExtension", namespaces=namespaces
            )
        )
        == 3
    )
    # Verify new techMD
    new_techmd = root.xpath(
        'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID!="techMD_2"]', namespaces=NSMAP
    )[0]
    assert new_techmd.attrib["STATUS"] == "current"
    assert (
        len(
            new_techmd.find(
                ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
            )
        )
        == 2
    )
    assert (
        new_techmd.find(".//premis:objectCharacteristicsExtension", namespaces=NSMAP)[
            0
        ].text
        == "Stub ffprobe output"
    )
    assert (
        new_techmd.find(".//premis:objectCharacteristicsExtension", namespaces=NSMAP)[
            1
        ].text
        == "Stub MediaInfo output"
    )
    # Verify rest of new techMD was created
    assert new_techmd.find(".//premis:formatName", namespaces=NSMAP) is not None
    assert (
        new_techmd.find(".//premis:relatedObjectIdentifierType", namespaces=NSMAP)
        is not None
    )


@pytest.mark.django_db
def test_update_preservation_derivative(
    mcp_job: Job,
    reingest_events: list[models.Event],
    new_preservation_derivative: models.File,
) -> None:
    """It should add a new techMD with the new relationship."""
    # Verify METS state
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert (
        len(
            mets.tree.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 1
    )
    # Run test
    mets = archivematicaCreateMETSReingest.update_object(mcp_job, mets)
    root = mets.serialize()
    assert (
        len(
            root.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 2
    )
    # Verify old techMD
    old_techmd = root.find('.//mets:techMD[@ID="techMD_2"]', namespaces=NSMAP)
    old_techmd = root.xpath(
        'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID="techMD_2"]', namespaces=NSMAP
    )[0]
    assert old_techmd.attrib["STATUS"] == "superseded"
    namespaces = nsmap_for_premis2()
    assert (
        old_techmd.findtext(
            ".//premis:relatedObjectIdentifierValue", namespaces=namespaces
        )
        == "8140ebe5-295c-490b-a34a-83955b7c844e"
    )
    assert (
        old_techmd.findtext(
            ".//premis:relatedEventIdentifierValue", namespaces=namespaces
        )
        == "0ce13092-911f-4a89-b9e1-0e61921a03d4"
    )
    # Verify new techMD
    new_techmd = root.xpath(
        'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID!="techMD_2"]', namespaces=NSMAP
    )[0]
    assert new_techmd.attrib["STATUS"] == "current"
    assert (
        new_techmd.findtext(".//premis:relatedObjectIdentifierValue", namespaces=NSMAP)
        == "d8cc7af7-284a-42f5-b7f4-e181a0efc35f"
    )
    assert (
        new_techmd.findtext(".//premis:relatedEventIdentifierValue", namespaces=NSMAP)
        == "291f9be4-d19a-4bcc-8e1c-d3f01e4a48b1"
    )
    # Verify rest of new techMD was created
    assert new_techmd.find(".//premis:formatName", namespaces=NSMAP) is not None
    assert (
        new_techmd.find(".//premis:relatedObjectIdentifierType", namespaces=NSMAP)
        is not None
    )
    assert (
        len(
            new_techmd.find(
                ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
            )
        )
        > 0
    )


@pytest.mark.django_db
def test_update_all(
    mcp_job: Job,
    reingest_events: list[models.Event],
    recalculated_checksum: models.Event,
    new_file_id: models.FileID,
    new_characterization: list[models.FPCommandOutput],
    new_preservation_derivative: models.File,
) -> None:
    """
    It should add new updated object and mark the old one as superseded.
    It should add after the last techMD.
    It should not modify other objects.
    It should have a new format identification event.
    """
    # Verify METS state
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert (
        len(
            mets.tree.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 1
    )
    # Run test
    mets = archivematicaCreateMETSReingest.update_object(mcp_job, mets)
    root = mets.serialize()
    assert (
        len(
            root.findall(
                'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                namespaces=NSMAP,
            )
        )
        == 2
    )
    # Verify old techMD
    old_techmd = root.find('.//mets:techMD[@ID="techMD_2"]', namespaces=NSMAP)
    old_techmd = root.xpath(
        'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID="techMD_2"]', namespaces=NSMAP
    )[0]
    assert old_techmd.attrib["STATUS"] == "superseded"
    # Verify new techMD
    new_techmd = root.xpath(
        'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID!="techMD_2"]', namespaces=NSMAP
    )[0]
    assert new_techmd.attrib["STATUS"] == "current"
    # Checksums
    assert (
        new_techmd.findtext(".//premis:messageDigestAlgorithm", namespaces=NSMAP)
        == "md5"
    )
    assert (
        new_techmd.findtext(".//premis:messageDigest", namespaces=NSMAP)
        == "ac63a92ba5a94c337e740d6f189200d0"
    )
    # File ID
    assert (
        new_techmd.findtext(".//premis:formatName", namespaces=NSMAP)
        == "Newer fancier JPEG"
    )
    assert new_techmd.findtext(".//premis:formatVersion", namespaces=NSMAP) == "9001"
    assert (
        new_techmd.findtext(".//premis:formatRegistryKey", namespaces=NSMAP)
        == "fmt/9000"
    )
    # Characterize
    assert (
        len(
            new_techmd.find(
                ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
            )
        )
        == 2
    )
    assert (
        new_techmd.find(".//premis:objectCharacteristicsExtension", namespaces=NSMAP)[
            0
        ].text
        == "Stub ffprobe output"
    )
    assert (
        new_techmd.find(".//premis:objectCharacteristicsExtension", namespaces=NSMAP)[
            1
        ].text
        == "Stub MediaInfo output"
    )
    # Preservation
    assert (
        new_techmd.findtext(".//premis:relatedObjectIdentifierValue", namespaces=NSMAP)
        == "d8cc7af7-284a-42f5-b7f4-e181a0efc35f"
    )
    assert (
        new_techmd.findtext(".//premis:relatedEventIdentifierValue", namespaces=NSMAP)
        == "291f9be4-d19a-4bcc-8e1c-d3f01e4a48b1"
    )


@pytest.mark.xfail(raises=NotImplementedError, reason="not implemented", strict=True)
def test_update_reingest_object() -> None:
    """
    It should add new updated object and mark all the old ones as superseded.
    It should add after the last techMD.
    """
    raise NotImplementedError()


@pytest.mark.parametrize("techmd_id", ["techMD_1", "techMD_2", "techMD_3"])
def test__update_premis_object(techmd_id: str) -> None:
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_namespaces.xml")
    )
    root = mets.serialize()

    path = f'.//mets:techMD[@ID="{techmd_id}"]/mets:mdWrap/mets:xmlData/premis:object'
    premis_object = root.find(path, namespaces=nsmap_for_premis2())
    # This is what we're trying to avoid: PREMIS as the default ns.
    assert premis_object.nsmap[None] == "info:lc/xmlns/premis-v2"
    new = archivematicaCreateMETSReingest._update_premis_object(premis_object, "file")
    # Previous element has been emptied.
    assert len(premis_object.getchildren()) == 0
    # It should not have a default namespace anymore.
    assert None not in new.nsmap
    # PREMIS should be using the ``premis`` prefix.
    assert new.nsmap["premis"] == "http://www.loc.gov/premis/v3"
    # Children have been incorporated into the new object.
    assert len(new.getchildren())
    # Subelements are prefixed too.
    assert len(new.find(".//premis:fixity", namespaces=NSMAP)) == 2


@pytest.mark.django_db
def test_no_dc(mcp_job: Job, dublincore: list[models.DublinCore]) -> None:
    """It should do nothing if there is no DC entry."""
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert (
        mets.tree.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
        is None
    )
    mets = archivematicaCreateMETSReingest.update_dublincore(
        mcp_job, mets, SIP_UUID_NONE
    )
    assert (
        mets.serialize().find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
        is None
    )


@pytest.mark.django_db
def test_dc_not_updated(mcp_job: Job, dublincore: list[models.DublinCore]) -> None:
    """It should do nothing if the DC has not been modified."""
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert (
        mets.tree.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
        is None
    )
    mets = archivematicaCreateMETSReingest.update_dublincore(
        mcp_job, mets, DC_SIP_UUID_REINGEST
    )
    assert (
        mets.serialize().find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
        is None
    )


@pytest.mark.django_db
def test_new_dc(mcp_job: Job, dublincore: list[models.DublinCore]) -> None:
    """
    It should add a new DC if there was none before.
    It should add after the metsHdr if no dmdSecs exist.
    """
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert (
        mets.tree.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
        is None
    )
    mets = archivematicaCreateMETSReingest.update_dublincore(
        mcp_job, mets, DC_SIP_UUID_ORIGINAL
    )
    root = mets.serialize()
    assert (
        root.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP) is not None
    )
    dmdsec = root.find("mets:dmdSec", namespaces=NSMAP)
    assert dmdsec.attrib["CREATED"]
    # Verify fileSec div updated
    assert (
        root.find(
            'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
            namespaces=NSMAP,
        ).attrib["DMDID"]
        == dmdsec.attrib["ID"]
    )
    # Verify DC correct
    dc_elem = root.find(
        'mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]/mets:xmlData/dcterms:dublincore',
        namespaces=NSMAP,
    )
    assert len(dc_elem) == 15
    assert dc_elem[0].tag == "{http://purl.org/dc/elements/1.1/}title"
    assert dc_elem[0].text == "Yamani Weapons"
    assert dc_elem[1].tag == "{http://purl.org/dc/elements/1.1/}creator"
    assert dc_elem[1].text == "Keladry of Mindelan"
    assert dc_elem[2].tag == "{http://purl.org/dc/elements/1.1/}subject"
    assert dc_elem[2].text == "Glaives"
    assert dc_elem[3].tag == "{http://purl.org/dc/elements/1.1/}description"
    assert dc_elem[3].text == "Glaives are cool"
    assert dc_elem[4].tag == "{http://purl.org/dc/elements/1.1/}publisher"
    assert dc_elem[4].text == "Tortall Press"
    assert dc_elem[5].tag == "{http://purl.org/dc/elements/1.1/}contributor"
    assert dc_elem[5].text == "Yuki"
    assert dc_elem[6].tag == "{http://purl.org/dc/elements/1.1/}date"
    assert dc_elem[6].text == "2015"
    assert dc_elem[7].tag == "{http://purl.org/dc/elements/1.1/}type"
    assert dc_elem[7].text == "Archival Information Package"
    assert dc_elem[8].tag == "{http://purl.org/dc/elements/1.1/}format"
    assert dc_elem[8].text == "parchement"
    assert dc_elem[9].tag == "{http://purl.org/dc/elements/1.1/}identifier"
    assert dc_elem[9].text == "42/1"
    assert dc_elem[10].tag == "{http://purl.org/dc/elements/1.1/}source"
    assert dc_elem[10].text == "Numair's library"
    assert dc_elem[11].tag == "{http://purl.org/dc/elements/1.1/}relation"
    assert dc_elem[11].text == "None"
    assert dc_elem[12].tag == "{http://purl.org/dc/elements/1.1/}language"
    assert dc_elem[12].text == "en"
    assert dc_elem[13].tag == "{http://purl.org/dc/elements/1.1/}rights"
    assert dc_elem[13].text == "Public Domain"
    assert dc_elem[14].tag == "{http://purl.org/dc/terms/}isPartOf"
    assert dc_elem[14].text == "AIC#42"


@pytest.mark.django_db
def test_update_existing_dc(mcp_job: Job, dublincore: list[models.DublinCore]) -> None:
    """
    It should add a new updated DC and mark the old one as original.
    It should ignore file-level DC.
    It should add after the last dmdSec.
    """
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_sip_and_file_dc.xml")
    )
    assert (
        len(
            mets.tree.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
        )
        == 4
    )
    mets = archivematicaCreateMETSReingest.update_dublincore(
        mcp_job, mets, DC_SIP_UUID_UPDATED
    )
    root = mets.serialize()
    assert (
        len(root.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP))
        == 5
    )
    # Verify file-level DC not updated
    assert (
        root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP).get("STATUS") is None
    )
    assert (
        root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP).get("STATUS") is None
    )
    assert (
        root.find('mets:dmdSec[@ID="dmdSec_3"]', namespaces=NSMAP).get("STATUS") is None
    )
    # Verify original SIP-level marked as original-superseded
    assert (
        root.find('mets:dmdSec[@ID="dmdSec_4"]', namespaces=NSMAP).attrib["STATUS"]
        == "original-superseded"
    )
    # Verify dmdSec created
    dmdsec = root.xpath(
        'mets:dmdSec[not(@ID="dmdSec_1" or @ID="dmdSec_2" or @ID="dmdSec_3" or @ID="dmdSec_4")]',
        namespaces=NSMAP,
    )[0]
    assert dmdsec.attrib["STATUS"] == "update"
    assert dmdsec.attrib["CREATED"]
    # Verify fileSec div updated
    assert (
        dmdsec.attrib["ID"]
        in root.find(
            'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
            namespaces=NSMAP,
        ).attrib["DMDID"]
    )
    assert (
        "dmdSec_4"
        in root.find(
            'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
            namespaces=NSMAP,
        ).attrib["DMDID"]
    )
    # Verify new DC
    dc_elem = dmdsec.find(".//dcterms:dublincore", namespaces=NSMAP)
    assert len(dc_elem) == 12
    assert dc_elem[0].tag == "{http://purl.org/dc/elements/1.1/}title"
    assert dc_elem[0].text == "Yamani Weapons"
    assert dc_elem[1].tag == "{http://purl.org/dc/elements/1.1/}creator"
    assert dc_elem[1].text == "Keladry of Mindelan"
    assert dc_elem[2].tag == "{http://purl.org/dc/elements/1.1/}subject"
    assert dc_elem[2].text == "Glaives"
    assert dc_elem[3].tag == "{http://purl.org/dc/elements/1.1/}description"
    assert dc_elem[3].text == "Glaives are awesome"
    assert dc_elem[4].tag == "{http://purl.org/dc/elements/1.1/}publisher"
    assert dc_elem[4].text == "Tortall Press"
    assert dc_elem[5].tag == "{http://purl.org/dc/elements/1.1/}contributor"
    assert dc_elem[5].text == "Yuki, Neal"
    assert dc_elem[6].tag == "{http://purl.org/dc/elements/1.1/}type"
    assert dc_elem[6].text == "Archival Information Package"
    assert dc_elem[7].tag == "{http://purl.org/dc/elements/1.1/}format"
    assert dc_elem[7].text == "palimpsest"
    assert dc_elem[8].tag == "{http://purl.org/dc/elements/1.1/}identifier"
    assert dc_elem[8].text == "42/1"
    assert dc_elem[9].tag == "{http://purl.org/dc/elements/1.1/}language"
    assert dc_elem[9].text == "en"
    assert dc_elem[10].tag == "{http://purl.org/dc/elements/1.1/}coverage"
    assert dc_elem[10].text == "Partial"
    assert dc_elem[11].tag == "{http://purl.org/dc/elements/1.1/}rights"
    assert dc_elem[11].text == "Public Domain"


@pytest.mark.django_db
def test_update_reingested_dc(
    mcp_job: Job, dublincore: list[models.DublinCore]
) -> None:
    """
    It should add a new DC if old ones exist.
    It should not mark other reingested DC as original.
    """
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_multiple_sip_dc.xml")
    )
    assert (
        len(
            mets.tree.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
        )
        == 2
    )
    mets = archivematicaCreateMETSReingest.update_dublincore(
        mcp_job, mets, DC_SIP_UUID_UPDATED
    )
    root = mets.serialize()
    assert (
        len(root.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP))
        == 3
    )
    # Verify existing DC marked as original-superseded
    assert (
        root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP).get("STATUS")
        == "original-superseded"
    )
    assert (
        root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP).get("STATUS")
        == "update-superseded"
    )
    # Verify dmdSec created
    dmdsec = root.xpath(
        'mets:dmdSec[not(@ID="dmdSec_1" or @ID="dmdSec_2")]', namespaces=NSMAP
    )[0]
    assert dmdsec.attrib["STATUS"] == "update"
    assert dmdsec.attrib["CREATED"]
    # Verify fileSec div updated
    assert (
        dmdsec.attrib["ID"]
        in root.find(
            'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
            namespaces=NSMAP,
        ).attrib["DMDID"]
    )
    assert (
        "dmdSec_1"
        in root.find(
            'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
            namespaces=NSMAP,
        ).attrib["DMDID"]
    )
    assert (
        "dmdSec_2"
        in root.find(
            'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
            namespaces=NSMAP,
        ).attrib["DMDID"]
    )
    # Verify new DC
    dc_elem = dmdsec.find(".//dcterms:dublincore", namespaces=NSMAP)
    assert len(dc_elem) == 12
    assert dc_elem[0].tag == "{http://purl.org/dc/elements/1.1/}title"
    assert dc_elem[0].text == "Yamani Weapons"
    assert dc_elem[1].tag == "{http://purl.org/dc/elements/1.1/}creator"
    assert dc_elem[1].text == "Keladry of Mindelan"
    assert dc_elem[2].tag == "{http://purl.org/dc/elements/1.1/}subject"
    assert dc_elem[2].text == "Glaives"
    assert dc_elem[3].tag == "{http://purl.org/dc/elements/1.1/}description"
    assert dc_elem[3].text == "Glaives are awesome"
    assert dc_elem[4].tag == "{http://purl.org/dc/elements/1.1/}publisher"
    assert dc_elem[4].text == "Tortall Press"
    assert dc_elem[5].tag == "{http://purl.org/dc/elements/1.1/}contributor"
    assert dc_elem[5].text == "Yuki, Neal"
    assert dc_elem[6].tag == "{http://purl.org/dc/elements/1.1/}type"
    assert dc_elem[6].text == "Archival Information Package"
    assert dc_elem[7].tag == "{http://purl.org/dc/elements/1.1/}format"
    assert dc_elem[7].text == "palimpsest"
    assert dc_elem[8].tag == "{http://purl.org/dc/elements/1.1/}identifier"
    assert dc_elem[8].text == "42/1"
    assert dc_elem[9].tag == "{http://purl.org/dc/elements/1.1/}language"
    assert dc_elem[9].text == "en"
    assert dc_elem[10].tag == "{http://purl.org/dc/elements/1.1/}coverage"
    assert dc_elem[10].text == "Partial"
    assert dc_elem[11].tag == "{http://purl.org/dc/elements/1.1/}rights"
    assert dc_elem[11].text == "Public Domain"


@pytest.mark.django_db
def test_delete_dc(mcp_job: Job, dublincore: list[models.DublinCore]) -> None:
    """It should create a new dmdSec with no values."""
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_multiple_sip_dc.xml")
    )
    assert (
        len(
            mets.tree.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
        )
        == 2
    )

    mets = archivematicaCreateMETSReingest.update_dublincore(
        mcp_job, mets, SIP_UUID_NONE
    )
    root = mets.serialize()

    assert (
        len(root.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP))
        == 2
    )
    # Verify existing DC marked as original-superseded and deleted
    assert (
        root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP).get("STATUS")
        == "original-superseded"
    )
    assert (
        root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP).get("STATUS")
        == "deleted"
    )


@pytest.mark.django_db
def test_no_rights(
    mcp_job: Job, rights_statements: list[models.RightsStatement]
) -> None:
    """It should do nothing if there are no rights entries."""
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert mets.tree.find("mets:amdSec/mets:rightsMD", namespaces=NSMAP) is None
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    mets = archivematicaCreateMETSReingest.update_rights(
        mcp_job, mets, SIP_UUID_NONE, state
    )
    root = mets.serialize()
    assert root.find("mets:amdSec/mets:rightsMD", namespaces=NSMAP) is None


@pytest.mark.django_db
def test_rights_not_updated(
    mcp_job: Job, rights_statements: list[models.RightsStatement]
) -> None:
    """It should do nothing if the rights have not been modified."""
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert mets.tree.find("mets:amdSec/mets:rightsMD", namespaces=NSMAP) is None
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    mets = archivematicaCreateMETSReingest.update_rights(
        mcp_job, mets, RIGHTS_SIP_UUID_REINGEST, state
    )
    root = mets.serialize()
    assert root.find("mets:amdSec/mets:rightsMD", namespaces=NSMAP) is None


@pytest.mark.django_db
def test_new_rights(
    mcp_job: Job, rights_statements: list[models.RightsStatement]
) -> None:
    """
    It should add a new rights if there were none before.
    It should add after the last techMD.
    It should add rights to all original files.
    It should not add rights to the METS file amdSec.
    """
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert mets.tree.find("mets:amdSec/mets:rightsMD", namespaces=NSMAP) is None
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    mets = archivematicaCreateMETSReingest.update_rights(
        mcp_job, mets, RIGHTS_SIP_UUID_ORIGINAL, state
    )
    root = mets.serialize()

    # Verify new rightsMD for all rightsstatements
    assert len(root.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 4
    # Verify all associated with the original file
    assert (
        len(root.findall('mets:amdSec[@ID="amdSec_2"]/mets:rightsMD', namespaces=NSMAP))
        == 4
    )
    # Verify rightsMDs exist with correct basis
    assert (
        root.xpath('.//premis:rightsBasis[text()="Copyright"]', namespaces=NSMAP)[0]
        is not None
    )
    assert (
        root.xpath('.//premis:rightsBasis[text()="Statute"]', namespaces=NSMAP)[0]
        is not None
    )
    assert (
        root.xpath('.//premis:rightsBasis[text()="License"]', namespaces=NSMAP)[0]
        is not None
    )
    assert (
        root.xpath('.//premis:rightsBasis[text()="Other"]', namespaces=NSMAP)[0]
        is not None
    )


@pytest.mark.django_db
def test_update_existing_rights(
    mcp_job: Job, rights_statements: list[models.RightsStatement]
) -> None:
    """
    It should add new updated rights and mark the old ones as superseded.
    It should add after the last rightsMD.
    It should add rights to all files.
    It should not add rights to the METS file.
    """
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_all_rights.xml")
    )
    assert len(mets.tree.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 5
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    mets = archivematicaCreateMETSReingest.update_rights(
        mcp_job, mets, RIGHTS_SIP_UUID_UPDATED, state
    )
    root = mets.serialize()

    # Verify new rightsMD for all rightsstatements
    assert len(root.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 6
    # Verify all associated with the original file
    assert (
        len(root.findall('mets:amdSec[@ID="amdSec_1"]/mets:rightsMD', namespaces=NSMAP))
        == 6
    )
    assert (
        root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_1"]', namespaces=NSMAP).get(
            "STATUS"
        )
        is None
    )
    assert (
        root.find(
            'mets:amdSec/mets:rightsMD[@ID="rightsMD_2"]', namespaces=NSMAP
        ).attrib["STATUS"]
        == "superseded"
    )
    assert (
        root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_3"]', namespaces=NSMAP).get(
            "STATUS"
        )
        is None
    )
    assert (
        root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_4"]', namespaces=NSMAP).get(
            "STATUS"
        )
        is None
    )
    assert (
        root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_5"]', namespaces=NSMAP).get(
            "STATUS"
        )
        is None
    )
    new_rights = root.find('mets:amdSec[@ID="amdSec_1"]', namespaces=NSMAP)[6]
    assert new_rights is not None
    assert new_rights.attrib["STATUS"] == "current"
    assert new_rights.attrib["CREATED"]
    assert new_rights.findtext(".//premis:rightsBasis", namespaces=NSMAP) == "Statute"
    assert (
        new_rights.findtext(
            ".//premis:statuteApplicableDates/premis:endDate", namespaces=NSMAP
        )
        == "2054"
    )
    assert (
        new_rights.findtext(
            ".//premis:termOfRestriction/premis:endDate", namespaces=NSMAP
        )
        == "2054"
    )
    assert new_rights.findtext(".//premis:statuteNote", namespaces=NSMAP) == "SIN"


@pytest.mark.django_db
def test_update_reingested_rights(
    mcp_job: Job, rights_statements: list[models.RightsStatement]
) -> None:
    """
    It should add new updated rights and mark all the old ones as superseded.
    It should add after the last rightsMD.
    It should add rights to all files.
    It should not add rights to the METS file.
    """
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_updated_rights.xml")
    )
    assert len(mets.tree.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 2
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    mets = archivematicaCreateMETSReingest.update_rights(
        mcp_job, mets, RIGHTS_SIP_UUID_UPDATED, state
    )
    root = mets.serialize()

    # Verify new rightsMD for all rightsstatements
    assert len(root.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 3
    # Verify all associated with the original file
    assert (
        len(root.findall('mets:amdSec[@ID="amdSec_1"]/mets:rightsMD', namespaces=NSMAP))
        == 3
    )
    assert (
        root.find(
            'mets:amdSec/mets:rightsMD[@ID="rightsMD_1"]', namespaces=NSMAP
        ).attrib["STATUS"]
        == "superseded"
    )
    assert (
        root.find(
            'mets:amdSec/mets:rightsMD[@ID="rightsMD_2"]', namespaces=NSMAP
        ).attrib["STATUS"]
        == "superseded"
    )
    new_rights = root.find('mets:amdSec[@ID="amdSec_1"]', namespaces=NSMAP)[3]
    assert new_rights is not None
    assert new_rights.attrib["STATUS"] == "current"
    assert new_rights.attrib["CREATED"]
    assert (
        new_rights.find(
            ".//premis:statuteApplicableDates/premis:endDate", namespaces=NSMAP
        ).text
        == "2054"
    )
    assert (
        new_rights.find(
            ".//premis:termOfRestriction/premis:endDate", namespaces=NSMAP
        ).text
        == "2054"
    )
    assert new_rights.find(".//premis:statuteNote", namespaces=NSMAP).text == "SIN"


@pytest.mark.django_db
def test_delete_rights(
    mcp_job: Job, rights_statements: list[models.RightsStatement]
) -> None:
    """It should mark the original rightsMD as obsolete."""
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_all_rights.xml")
    )
    assert len(mets.tree.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 5
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    mets = archivematicaCreateMETSReingest.update_rights(
        mcp_job, mets, SIP_UUID_NONE, state
    )
    root = mets.serialize()

    assert len(root.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 5
    assert (
        len(
            root.findall(
                'mets:amdSec/mets:rightsMD[@STATUS="superseded"]', namespaces=NSMAP
            )
        )
        == 5
    )


@pytest.mark.django_db
def test_delete_and_add(
    mcp_job: Job, rights_statements: list[models.RightsStatement]
) -> None:
    """
    Use case: Entire rights basis deleted, new one added
    Solution: Mark original rightsMD as superseded. New rightsMD marked as current.
    It should mark the original rightsMD as obsolete.
    """
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_updated_rights.xml")
    )
    assert len(mets.tree.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 2
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    mets = archivematicaCreateMETSReingest.update_rights(
        mcp_job, mets, RIGHTS_SIP_UUID_ORIGINAL, state
    )
    root = mets.serialize()

    assert len(root.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 6
    assert (
        len(
            root.findall(
                'mets:amdSec/mets:rightsMD[@STATUS="superseded"]', namespaces=NSMAP
            )
        )
        == 2
    )
    assert (
        root.find(
            'mets:amdSec/mets:rightsMD[@ID="rightsMD_1"]', namespaces=NSMAP
        ).attrib["STATUS"]
        == "superseded"
    )
    assert (
        root.find(
            'mets:amdSec/mets:rightsMD[@ID="rightsMD_2"]', namespaces=NSMAP
        ).attrib["STATUS"]
        == "superseded"
    )
    assert (
        len(
            root.findall(
                'mets:amdSec/mets:rightsMD[@STATUS="current"]', namespaces=NSMAP
            )
        )
        == 4
    )
    assert (
        root.xpath(
            'mets:amdSec/mets:rightsMD[@STATUS="current"]//premis:rightsBasis[text()="Statute"]',
            namespaces=NSMAP,
        )
        != []
    )


@pytest.mark.django_db
def test_all_files_get_events(
    mcp_job: Job, reingest_events: list[models.Event]
) -> None:
    """
    It should add reingestion events to all files.
    It should add deletion events only to deleted files.
    It should add new format identification, normalization, fixity check events to the original object.
    It should not change Agent information.
    """
    models.Agent.objects.all().delete()
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    num_events = models.Event.objects.count()
    assert (
        len(
            mets.tree.findall(
                './/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP
            )
        )
        == 16
    )
    assert (
        len(
            mets.tree.findall(
                './/mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP
            )
        )
        == 9
    )
    mets = archivematicaCreateMETSReingest.add_events(mcp_job, mets, SIP_UUID)
    root = mets.serialize()
    assert (
        len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP))
        == 16 + num_events
    )
    # Preservation
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_1"]//premis:eventType[text()="reingestion"]',
            namespaces=NSMAP,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_1"]//premis:eventType[text()="deletion"]',
            namespaces=NSMAP,
        )
        != []
    )
    # Original object
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="reingestion"]',
            namespaces=NSMAP,
        )
        != []
    )
    namespaces = nsmap_for_premis2()
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="format identification"]',
            namespaces=namespaces,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="normalization"]',
            namespaces=namespaces,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="fixity check"]',
            namespaces=namespaces,
        )
        != []
    )
    # Transfer METS
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_3"]//premis:eventType[text()="reingestion"]',
            namespaces=NSMAP,
        )
        != []
    )
    # Agents
    assert (
        len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP))
        == 12
    )


@pytest.mark.django_db
def test_agent_not_in_mets(
    mcp_job: Job, reingest_events: list[models.Event], unrelated_agent: models.Agent
) -> None:
    """
    It should add a new Agent if it doesn't already exist.
    It should only add one new Agent even if multiple Events are added.
    """
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    num_events = models.Event.objects.count()
    assert (
        len(
            mets.tree.findall(
                './/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP
            )
        )
        == 16
    )
    assert (
        len(
            mets.tree.findall(
                './/mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP
            )
        )
        == 9
    )
    models.Agent.objects.filter(
        identifiertype="repository code", agenttype="organization"
    ).update(identifiervalue="new-repo-code")
    nsmap_v2 = nsmap_for_premis2()
    mets = archivematicaCreateMETSReingest.add_events(mcp_job, mets, SIP_UUID)
    root = mets.serialize()
    assert (
        len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP))
        == 16 + num_events
    )
    assert (
        len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP))
        == 15
    )
    # Preservation
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_1"]//premis:eventType[text()="reingestion"]',
            namespaces=NSMAP,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_1"]//premis:eventType[text()="deletion"]',
            namespaces=NSMAP,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_1"]//premis:agentIdentifierValue[text()="%s"]'
            % get_preservation_system_identifier(),
            namespaces=NSMAP,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_1"]//premis:agentIdentifierValue[text()="demo"]',
            namespaces=nsmap_v2,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_1"]//premis:agentIdentifierValue[text()="new-repo-code"]',
            namespaces=NSMAP,
        )
        != []
    )
    # Original
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="reingestion"]',
            namespaces=NSMAP,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="format identification"]',
            namespaces=nsmap_v2,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="normalization"]',
            namespaces=nsmap_v2,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="fixity check"]',
            namespaces=nsmap_v2,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:agentIdentifierValue[text()="%s"]'
            % get_preservation_system_identifier(),
            namespaces=NSMAP,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:agentIdentifierValue[text()="demo"]',
            namespaces=nsmap_v2,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_2"]//premis:agentIdentifierValue[text()="new-repo-code"]',
            namespaces=NSMAP,
        )
        != []
    )
    # Transfer METS
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_3"]//premis:eventType[text()="reingestion"]',
            namespaces=NSMAP,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_3"]//premis:agentIdentifierValue[text()="%s"]'
            % get_preservation_system_identifier(),
            namespaces=NSMAP,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_3"]//premis:agentIdentifierValue[text()="demo"]',
            namespaces=nsmap_v2,
        )
        != []
    )
    assert (
        root.xpath(
            'mets:amdSec[@ID="amdSec_3"]//premis:agentIdentifierValue[text()="new-repo-code"]',
            namespaces=NSMAP,
        )
        != []
    )


@pytest.mark.django_db
def test_no_new_files(
    mcp_job: Job,
    tmp_path: pathlib.Path,
    aip_files: list[models.File],
    new_preservation_derivative: models.File,
) -> None:
    """It should not modify the fileSec or structMap if there are no new files."""
    sip_dir = tmp_path / "emptysip"
    shutil.copytree(os.path.join(FIXTURES_DIR, "emptysip"), str(sip_dir))
    # Make sure directory is empty
    (sip_dir / "objects/metadata/transfers/.gitignore").unlink()

    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert len(mets.tree.findall("mets:amdSec", namespaces=NSMAP)) == 3
    assert len(mets.tree.findall("mets:fileSec//mets:file", namespaces=NSMAP)) == 3
    assert (
        mets.tree.find('mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP)
        is None
    )
    assert (
        len(
            mets.tree.findall(
                'mets:structMap[@TYPE="physical"]//mets:div', namespaces=NSMAP
            )
        )
        == 10
    )

    mets = archivematicaCreateMETSReingest.add_new_files(
        mcp_job, mets, SIP_UUID, str(sip_dir)
    )
    root = mets.serialize()
    assert len(root.findall("mets:amdSec", namespaces=NSMAP)) == 3
    assert len(root.findall("mets:fileSec//mets:file", namespaces=NSMAP)) == 3
    assert (
        root.find('mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP)
        is None
    )

    # There used to be 10 <mets:div> elements under the physical structMap.
    # However, now metsrw does not list empty directories (or directories
    # that only contain empty directories) in the physical structMap.
    # Therefore, the directories in the following path will not be
    # documented after metsrw has re-serialized:
    # metadata/transfers/no-metadata-46260807-ece1-4a0e-b70a-9814c701146b/
    assert (
        len(
            root.findall('mets:structMap[@TYPE="physical"]//mets:div', namespaces=NSMAP)
        )
        == 7
    )


@pytest.mark.django_db
def test_add_metadata_csv(
    mcp_job: Job,
    aip_files: list[models.File],
    new_preservation_derivative: models.File,
) -> None:
    """
    It should add a metadata file to the fileSec, structMap & amdSec.
    It should add a dmdSec, whose contents the metadata CSV tests cover.
    """
    sip_dir = os.path.join(FIXTURES_DIR, "metadata_csv_sip", "")
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert len(mets.tree.findall("mets:amdSec", namespaces=NSMAP)) == 3
    assert len(mets.tree.findall("mets:fileSec//mets:file", namespaces=NSMAP)) == 3
    assert (
        mets.tree.find('mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP)
        is None
    )
    assert (
        len(
            mets.tree.findall(
                'mets:structMap[@TYPE="physical"]//mets:div', namespaces=NSMAP
            )
        )
        == 10
    )

    mets = archivematicaCreateMETSReingest.add_new_files(
        mcp_job, mets, SIP_UUID, sip_dir
    )

    file_uuid = "66370f14-2f64-4750-9d50-547614be40e8"
    root = mets.serialize()
    # Check structMap
    div = root.find(
        'mets:structMap/mets:div/mets:div[@LABEL="objects"]/mets:div[@LABEL="metadata"]/mets:div[@TYPE="Item"]',
        namespaces=NSMAP,
    )
    assert div is not None
    assert div.attrib["LABEL"] == "metadata.csv"
    assert len(div) == 1
    assert div[0].tag == "{http://www.loc.gov/METS/}fptr"
    assert div[0].attrib["FILEID"] == "file-" + file_uuid
    # Check fileSec
    mets_grp = root.find('mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP)
    assert mets_grp is not None
    assert len(mets_grp) == 1
    assert mets_grp[0].tag == "{http://www.loc.gov/METS/}file"
    assert mets_grp[0].attrib["ID"] == "file-" + file_uuid
    assert mets_grp[0].attrib["GROUPID"] == "Group-" + file_uuid
    adm_id = mets_grp[0].attrib["ADMID"]
    assert adm_id
    assert len(mets_grp[0]) == 1
    assert mets_grp[0][0].tag == "{http://www.loc.gov/METS/}FLocat"
    assert mets_grp[0][0].attrib["LOCTYPE"] == "OTHER"
    assert mets_grp[0][0].attrib["OTHERLOCTYPE"] == "SYSTEM"
    assert (
        mets_grp[0][0].attrib["{http://www.w3.org/1999/xlink}href"]
        == "objects/metadata/metadata.csv"
    )
    # Check amdSec
    amdsec = root.find('mets:amdSec[@ID="' + adm_id + '"]', namespaces=NSMAP)
    assert amdsec is not None
    assert (
        amdsec.findtext(".//premis:objectIdentifierValue", namespaces=NSMAP)
        == file_uuid
    )
    assert (
        amdsec.findtext(".//premis:messageDigest", namespaces=NSMAP)
        == "e8121d8a660e2992872f0b67923d2d08dde9a1ba72dfd58e5a31e68fbac3633c"
    )
    assert amdsec.findtext(".//premis:size", namespaces=NSMAP) == "154"
    assert (
        amdsec.findtext(".//premis:originalName", namespaces=NSMAP)
        == "%SIPDirectory%metadata/metadata.csv"
    )


@pytest.mark.django_db
def test_new_metadata_file_in_subdir(
    mcp_job: Job,
    aip_files: list[models.File],
    new_preservation_derivative: models.File,
) -> None:
    """It should add the new subdirs to the structMap."""
    sip_dir = os.path.join(FIXTURES_DIR, "metadata_file_in_subdir_sip", "")
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert len(mets.tree.findall("mets:amdSec", namespaces=NSMAP)) == 3
    assert len(mets.tree.findall("mets:fileSec//mets:file", namespaces=NSMAP)) == 3
    assert (
        mets.tree.find('mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP)
        is None
    )
    assert (
        len(
            mets.tree.findall(
                'mets:structMap[@TYPE="physical"]//mets:div', namespaces=NSMAP
            )
        )
        == 10
    )

    mets = archivematicaCreateMETSReingest.add_new_files(
        mcp_job, mets, SIP_UUID, sip_dir
    )

    file_uuid = "950253b2-e5b1-4222-bb86-4eb436af5713"
    root = mets.serialize()
    # Check structMap
    # Dir
    div = root.find(
        'mets:structMap/mets:div/mets:div[@LABEL="objects"]/mets:div[@LABEL="metadata"]/mets:div[@LABEL="foo"]',
        namespaces=NSMAP,
    )
    assert div is not None
    assert len(div) == 1
    # File
    div = root.find(
        'mets:structMap/mets:div/mets:div[@LABEL="objects"]/mets:div[@LABEL="metadata"]/mets:div/mets:div[@TYPE="Item"]',
        namespaces=NSMAP,
    )
    assert div is not None
    assert div.attrib["LABEL"] == "foo.txt"
    assert len(div) == 1
    assert div[0].tag == "{http://www.loc.gov/METS/}fptr"
    assert div[0].attrib["FILEID"] == "file-" + file_uuid
    # Check fileSec
    mets_grp = root.find('mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP)
    assert mets_grp is not None
    assert len(mets_grp) == 1
    assert mets_grp[0].tag == "{http://www.loc.gov/METS/}file"
    assert mets_grp[0].attrib["ID"] == "file-" + file_uuid
    assert mets_grp[0].attrib["GROUPID"] == "Group-" + file_uuid
    adm_id = mets_grp[0].attrib["ADMID"]
    assert adm_id
    assert len(mets_grp[0]) == 1
    assert mets_grp[0][0].tag == "{http://www.loc.gov/METS/}FLocat"
    assert mets_grp[0][0].attrib["LOCTYPE"] == "OTHER"
    assert mets_grp[0][0].attrib["OTHERLOCTYPE"] == "SYSTEM"
    assert (
        mets_grp[0][0].attrib["{http://www.w3.org/1999/xlink}href"]
        == "objects/metadata/foo/foo.txt"
    )
    # Check amdSec
    amdsec = root.find('mets:amdSec[@ID="' + adm_id + '"]', namespaces=NSMAP)
    assert amdsec is not None
    assert (
        amdsec.findtext(".//premis:objectIdentifierValue", namespaces=NSMAP)
        == file_uuid
    )


@pytest.mark.django_db
def test_new_preservation_file(
    mcp_job: Job,
    aip_files: list[models.File],
    new_preservation_derivative: models.File,
) -> None:
    """
    It should add an amdSec for the new file.
    It should not have a reingestion event.
    It should add the new file to the fileSec under 'preservation'.
    It should add the new file to the structMap.
    Done elsewhere:
    update_object creates a new relationship in the original object.
    add_events adds a new normalization event to the original object.
    delete_files moves the old preservation object to 'deleted' fileGrp
    """
    # Verify existing
    file_uuid = "d8cc7af7-284a-42f5-b7f4-e181a0efc35f"
    original_file_uuid = "ae8d4290-fe52-4954-b72a-0f591bee2e2f"
    file_path = "evelyn_s_photo-d8cc7af7-284a-42f5-b7f4-e181a0efc35f.tif"
    sip_dir = os.path.join(FIXTURES_DIR, "new_preservation_file", "")
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert len(mets.tree.findall("mets:amdSec", namespaces=NSMAP)) == 3
    assert len(mets.tree.findall("mets:fileSec//mets:file", namespaces=NSMAP)) == 3
    assert (
        len(
            mets.tree.find(
                'mets:fileSec/mets:fileGrp[@USE="preservation"]', namespaces=NSMAP
            )
        )
        == 1
    )
    assert (
        len(
            mets.tree.findall(
                'mets:structMap[@TYPE="physical"]//mets:div', namespaces=NSMAP
            )
        )
        == 10
    )
    # Run test
    mets = archivematicaCreateMETSReingest.add_new_files(
        mcp_job, mets, SIP_UUID, sip_dir
    )
    root = mets.serialize()
    # Check fileSec
    mets_grp = root.find(
        'mets:fileSec/mets:fileGrp[@USE="preservation"]', namespaces=NSMAP
    )
    assert len(mets_grp) == 2
    file_ = mets_grp.find('mets:file[@ID="file-' + file_uuid + '"]', namespaces=NSMAP)
    assert file_.attrib["GROUPID"] == "Group-" + original_file_uuid
    adm_id = file_.attrib["ADMID"]
    assert adm_id
    assert len(file_) == 1
    assert file_[0].tag == "{http://www.loc.gov/METS/}FLocat"
    assert file_[0].attrib["LOCTYPE"] == "OTHER"
    assert file_[0].attrib["OTHERLOCTYPE"] == "SYSTEM"
    assert (
        file_[0].attrib["{http://www.w3.org/1999/xlink}href"]
        == "objects/evelyn_s_photo-d8cc7af7-284a-42f5-b7f4-e181a0efc35f.tif"
    )
    # Check structMap
    div = root.find(
        'mets:structMap/mets:div/mets:div[@LABEL="objects"]/mets:div[@LABEL="'
        + file_path
        + '"]',
        namespaces=NSMAP,
    )
    assert div is not None
    assert div.attrib["TYPE"] == "Item"
    assert len(div) == 1
    assert div[0].tag == "{http://www.loc.gov/METS/}fptr"
    assert div[0].attrib["FILEID"] == "file-" + file_uuid
    # Check amdSec
    assert len(root.findall("mets:amdSec", namespaces=NSMAP)) == 4
    amdsec = root.find('mets:amdSec[@ID="' + adm_id + '"]', namespaces=NSMAP)
    assert amdsec is not None
    # Check techMD
    premis_object = amdsec.find(".//premis:object", namespaces=NSMAP)
    assert premis_object is not None
    assert (
        premis_object.findtext(".//premis:objectIdentifierValue", namespaces=NSMAP)
        == file_uuid
    )
    assert (
        premis_object.findtext(".//premis:messageDigestAlgorithm", namespaces=NSMAP)
        == "sha256"
    )
    assert (
        premis_object.findtext(".//premis:messageDigest", namespaces=NSMAP)
        == "d82448f154b9185bc777ecb0a3602760eb76ba85dd3098f073b2c91a03f571e9"
    )
    assert premis_object.findtext(".//premis:size", namespaces=NSMAP) == "1446772"
    assert premis_object.findtext(".//premis:formatName", namespaces=NSMAP) == "TIFF"
    assert (
        premis_object.findtext(".//premis:originalName", namespaces=NSMAP)
        == "%SIPDirectory%objects/evelyn_s_photo-d8cc7af7-284a-42f5-b7f4-e181a0efc35f.tif"
    )
    assert (
        premis_object.findtext(".//premis:relationshipType", namespaces=NSMAP)
        == "derivation"
    )
    assert (
        premis_object.findtext(".//premis:relationshipSubType", namespaces=NSMAP)
        == "has source"
    )
    assert (
        premis_object.findtext(
            ".//premis:relatedObjectIdentifierValue", namespaces=NSMAP
        )
        == original_file_uuid
    )
    assert (
        premis_object.findtext(
            ".//premis:relatedEventIdentifierValue", namespaces=NSMAP
        )
        == "291f9be4-d19a-4bcc-8e1c-d3f01e4a48b1"
    )
    # Events: creation, message digest calculation, fixity check
    assert (
        amdsec.xpath('.//premis:eventType[text()="creation"]', namespaces=NSMAP) != []
    )
    assert (
        amdsec.xpath(
            './/premis:eventType[text()="message digest calculation"]',
            namespaces=NSMAP,
        )
        != []
    )
    assert (
        amdsec.xpath('.//premis:eventType[text()="fixity check"]', namespaces=NSMAP)
        != []
    )
    # Agents
    assert (
        amdsec.xpath(
            './/premis:agentIdentifierValue[text()="%s"]'
            % get_preservation_system_identifier(),
            namespaces=NSMAP,
        )
        != []
    )
    assert (
        amdsec.xpath('.//premis:agentIdentifierValue[text()="demo"]', namespaces=NSMAP)
        != []
    )
    assert (
        amdsec.xpath(
            """.//premis:agentName[text()='username="kmindelan", first_name="Keladry", last_name="Mindelan"']""",
            namespaces=NSMAP,
        )
        != []
    )


@pytest.mark.django_db
def test_delete_file(reingest_events: list[models.Event]) -> None:
    """
    It should change the fileGrp USE to deleted.
    It should remove the FLocat from the fileSec.
    It should remove the div from the structMap.
    It should add a deletion event (covered by add_events).
    """
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert (
        mets.tree.find('.//mets:fileGrp[@USE="preservation"]', namespaces=NSMAP)
        is not None
    )
    assert mets.tree.find('.//mets:fileGrp[@USE="deleted"]', namespaces=NSMAP) is None
    assert (
        mets.tree.find(
            './/mets:file[@ID="file-8140ebe5-295c-490b-a34a-83955b7c844e"]',
            namespaces=NSMAP,
        )
        is not None
    )
    assert (
        mets.tree.find(
            './/mets:FLocat[@xlink:href="objects/evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif"]',
            namespaces=NSMAP,
        )
        is not None
    )
    assert (
        mets.tree.find(
            './/mets:div[@LABEL="evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif"]',
            namespaces=NSMAP,
        )
        is not None
    )

    mets = archivematicaCreateMETSReingest.delete_files(mets, SIP_UUID)
    root = mets.serialize()

    assert root.find('.//mets:fileGrp[@USE="preservation"]', namespaces=NSMAP) is None
    deletedgrp = root.find('.//mets:fileGrp[@USE="deleted"]', namespaces=NSMAP)
    assert deletedgrp is not None
    assert len(deletedgrp) == 1
    assert deletedgrp[0].tag == "{http://www.loc.gov/METS/}file"
    assert deletedgrp[0].attrib["ID"] == "file-8140ebe5-295c-490b-a34a-83955b7c844e"
    assert (
        deletedgrp[0].attrib["GROUPID"] == "Group-ae8d4290-fe52-4954-b72a-0f591bee2e2f"
    )
    assert deletedgrp[0].attrib["ADMID"] == "amdSec_1"
    assert len(deletedgrp[0].attrib) == 3
    assert len(deletedgrp[0]) == 0
    assert (
        root.find(
            './/mets:div[@LABEL="evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif"]',
            namespaces=NSMAP,
        )
        is None
    )


@pytest.mark.django_db
def test_new_dmdsecs(
    mcp_job: Job, aip_files: list[models.File], metadata_csv_file: models.File
) -> None:
    """It should add file-level dmdSecs."""
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert len(mets.tree.findall("mets:dmdSec", namespaces=NSMAP)) == 0
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    mets = archivematicaCreateMETSReingest.update_metadata_csv(
        mcp_job,
        mets,
        metadata_csv_file,
        SIP_UUID,
        METADATA_CSV_SIP_DIR,
        state,
    )
    root = mets.serialize()
    assert len(root.findall("mets:dmdSec", namespaces=NSMAP)) == 1
    dmdsec = root.find("mets:dmdSec", namespaces=NSMAP)
    assert dmdsec.attrib["ID"]
    assert dmdsec.attrib["CREATED"]
    assert dmdsec.attrib["STATUS"] == "update"
    assert dmdsec.findtext(".//dc:title", namespaces=NSMAP) == "Mountain Tents"
    assert (
        dmdsec.findtext(".//dc:description", namespaces=NSMAP) == "Tents on a mountain"
    )


@pytest.mark.django_db
def test_new_dmdsecs_for_directories(
    mcp_job: Job, aip_files: list[models.File], metadata_csv_file: models.File
) -> None:
    """It should add directory-level dmdSecs."""
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_sip_and_file_dc.xml")
    )
    assert not mets.get_file(label="Landing_zone", type="Directory").dmdsecs
    # Import metadata for the objects/Landing_zone directory
    # from fixtures/metadata_csv_directories/objects/metadata/metadata.csv
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    sip_dir = os.path.join(FIXTURES_DIR, "metadata_csv_directories", "")
    mets = archivematicaCreateMETSReingest.update_metadata_csv(
        mcp_job, mets, metadata_csv_file, SIP_UUID, sip_dir, state
    )
    # Verify the new dmdSec for the Landing_zone directory
    assert len(mets.get_file(label="Landing_zone", type="Directory").dmdsecs) == 1
    dmdsec = (
        mets.get_file(label="Landing_zone", type="Directory").dmdsecs[0].serialize()
    )
    assert dmdsec.findtext(".//dc:title", namespaces=NSMAP) == "The landing zone"
    assert (
        dmdsec.findtext(".//dc:description", namespaces=NSMAP) == "A zone for landing"
    )


@pytest.mark.django_db
def test_update_existing(
    mcp_job: Job, aip_files: list[models.File], metadata_csv_file: models.File
) -> None:
    """
    It should add new dmdSecs.
    It should updated the existing dmdSec as original.
    """
    mets = metsrw.METSDocument.fromfile(os.path.join(FIXTURES_DIR, "mets_file_dc.xml"))
    assert len(mets.tree.findall("mets:dmdSec", namespaces=NSMAP)) == 1
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    mets = archivematicaCreateMETSReingest.update_metadata_csv(
        mcp_job,
        mets,
        metadata_csv_file,
        SIP_UUID,
        METADATA_CSV_SIP_DIR,
        state,
    )
    root = mets.serialize()
    assert len(root.findall("mets:dmdSec", namespaces=NSMAP)) == 2
    orig = root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP)
    assert orig.attrib["STATUS"] == "original-superseded"
    div = root.xpath('.//mets:div[contains(@DMDID,"dmdSec_1")]', namespaces=NSMAP)[0]
    assert div.attrib["DMDID"]
    dmdid = div.attrib["DMDID"].split()[1]
    new = root.find('mets:dmdSec[@ID="' + dmdid + '"]', namespaces=NSMAP)
    assert new.attrib["CREATED"]
    assert new.attrib["STATUS"] == "update"
    assert new.findtext(".//dc:title", namespaces=NSMAP) == "Mountain Tents"
    assert new.findtext(".//dc:description", namespaces=NSMAP) == "Tents on a mountain"


@pytest.mark.django_db
def test_update_reingest(
    mcp_job: Job, aip_files: list[models.File], metadata_csv_file: models.File
) -> None:
    """
    It should add new dmdSecs.
    It should not updated the already updated dmdSecs.
    """
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_file_dc_updated.xml")
    )
    assert len(mets.tree.findall("mets:dmdSec", namespaces=NSMAP)) == 2
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    mets = archivematicaCreateMETSReingest.update_metadata_csv(
        mcp_job,
        mets,
        metadata_csv_file,
        SIP_UUID,
        METADATA_CSV_SIP_DIR,
        state,
    )
    root = mets.serialize()
    assert len(root.findall("mets:dmdSec", namespaces=NSMAP)) == 3
    orig = root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP)
    assert orig.attrib["STATUS"] == "original-superseded"
    updated = root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP)
    assert updated.attrib["STATUS"] == "update-superseded"
    div = root.xpath('.//mets:div[contains(@DMDID,"dmdSec_1")]', namespaces=NSMAP)[0]
    assert div.attrib["DMDID"]
    dmdid = div.attrib["DMDID"].split()[2]
    new = root.find('mets:dmdSec[@ID="' + dmdid + '"]', namespaces=NSMAP)
    assert new.attrib["CREATED"]
    assert new.attrib["STATUS"] == "update"
    assert new.findtext(".//dc:title", namespaces=NSMAP) == "Mountain Tents"
    assert new.findtext(".//dc:description", namespaces=NSMAP) == "Tents on a mountain"


@pytest.mark.django_db
def test_non_dublincore_dmdsecs(
    mcp_job: Job, aip_files: list[models.File], metadata_csv_file: models.File
) -> None:
    """It should add file-level dmdSecs for non DC metadata."""
    mets = metsrw.METSDocument.fromfile(
        os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
    )
    assert not mets.get_file(path="objects/evelyn_s_photo.jpg", type="Item").dmdsecs
    # Import DC and non DC metadata for the objects/evelyn_s_photo.jpg file
    # from fixtures/metadata_csv_nondc/objects/metadata/metadata.csv
    state = archivematicaCreateMETSReingest.createmets2.MetsState()
    sip_dir = os.path.join(FIXTURES_DIR, "metadata_csv_nondc", "")
    mets = archivematicaCreateMETSReingest.update_metadata_csv(
        mcp_job, mets, metadata_csv_file, SIP_UUID, sip_dir, state
    )
    # Verify the new dmdSecs for the objects/evelyn_s_photo.jpg file
    assert (
        len(mets.get_file(path="objects/evelyn_s_photo.jpg", type="Item").dmdsecs) == 2
    )
    dmdsecs = [
        dmdsec.serialize()
        for dmdsec in mets.get_file(
            path="objects/evelyn_s_photo.jpg", type="Item"
        ).dmdsecs
    ]
    # There should be one DC dmdsec
    dc_dmdsecs = [
        dmdsec
        for dmdsec in dmdsecs
        if dmdsec.find(".//dcterms:dublincore", namespaces=NSMAP) is not None
    ]
    assert len(dc_dmdsecs) == 1
    assert dc_dmdsecs[0].findtext(".//dc:title", namespaces=NSMAP) == "Mountain Tents"
    assert (
        dc_dmdsecs[0].findtext(".//dc:description", namespaces=NSMAP)
        == "Tents on a mountain"
    )
    # And one non DC dmdsec
    nondc_dmdsecs = [
        dmdsec
        for dmdsec in dmdsecs
        if dmdsec.find(
            './/mets:mdWrap[@MDTYPE="OTHER"][@OTHERMDTYPE="CUSTOM"]/mets:xmlData',
            namespaces=NSMAP,
        )
        is not None
    ]
    assert len(nondc_dmdsecs) == 1
    assert nondc_dmdsecs[0].findtext(".//nondc", namespaces=NSMAP) == "Non DC metadata"
    assert (
        nondc_dmdsecs[0].findtext(".//custom_field", namespaces=NSMAP)
        == "A custom field"
    )
