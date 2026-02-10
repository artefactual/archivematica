import pytest

from archivematica.archivematicaCommon.namespaces import NSMAP
from archivematica.dashboard.main import models
from archivematica.MCPClient.clientScripts import archivematicaCreateMETSRights
from archivematica.MCPClient.clientScripts.create_mets_v2 import MetsState


@pytest.fixture()
def rights_statement(db, sip_file):
    statement = models.RightsStatement.objects.create(
        metadata_applies_to=models.MetadataAppliesTo.FILE,
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
        (sip_file.uuid, models.MetadataAppliesTo.FILE),
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
