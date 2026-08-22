import pytest

from archivematica.archivematicaCommon.namespaces import NSMAP
from archivematica.dashboard.main import models
from archivematica.MCPClient.clientScripts import archivematicaCreateMETSRights
from archivematica.MCPClient.clientScripts.create_mets_v2 import MetsState
from archivematica.MCPClient.clientScripts.create_mets_v2 import getAMDSec


@pytest.fixture()
def rights_statement(metadata_applies_to_types, sip_file):
    statement = models.RightsStatement.objects.create(
        metadataappliestotype=metadata_applies_to_types["file"],
        metadataappliestoidentifier=sip_file.uuid,
        rightsbasis="Copyright",
    )
    models.RightsStatementCopyright.objects.create(
        rightsstatement=statement,
        copyrightjurisdiction="Québec",
    )
    return statement


def test_archivematicaGetRights_with_non_ascii_copyright_jurisdiction(
    db,
    mcp_job,
    sip_file,
    rights_statement,
):
    metadataAppliesToList = [
        (sip_file.uuid, models.MetadataAppliesToType.FILE_TYPE),
    ]
    result = archivematicaCreateMETSRights.archivematicaGetRights(
        mcp_job, metadataAppliesToList, str(sip_file.uuid), MetsState()
    )
    assert len(result) == 1
    element = result[0]
    assert element.find("premis:rightsBasis", NSMAP).text == "Copyright"
    assert (
        element.find(
            "premis:copyrightInformation/premis:copyrightJurisdiction", NSMAP
        ).text
        == "Québec"
    )


def test_getAMDSec_combines_file_and_transfer_rights_for_original_file(
    db,
    mcp_job,
    metadata_applies_to_types,
    rights_statement,
    sip,
    sip_file,
    transfer,
):
    statement = models.RightsStatement.objects.create(
        metadataappliestotype=metadata_applies_to_types["transfer"],
        metadataappliestoidentifier=transfer.uuid,
        rightsbasis="License",
    )
    models.RightsStatementLicense.objects.create(
        rightsstatement=statement,
        licenseterms="CC-BY",
    )

    amdsec, _ = getAMDSec(
        mcp_job,
        str(sip_file.uuid),
        "objects/file.mp3",
        "original",
        str(sip.uuid),
        str(transfer.uuid),
        "",
        "standard",
        "",
        MetsState(),
    )

    rights_statements = amdsec.findall(".//premis:rightsStatement", NSMAP)
    assert len(rights_statements) == 2

    rights_by_basis = {
        item.findtext("premis:rightsBasis", namespaces=NSMAP): item
        for item in rights_statements
    }
    assert set(rights_by_basis) == {"Copyright", "License"}
    assert (
        rights_by_basis["License"].findtext(
            "premis:licenseInformation/premis:licenseTerms",
            namespaces=NSMAP,
        )
        == "CC-BY"
    )
    assert {
        item.findtext(
            "premis:linkingObjectIdentifier/premis:linkingObjectIdentifierValue",
            namespaces=NSMAP,
        )
        for item in rights_statements
    } == {str(sip_file.uuid)}
