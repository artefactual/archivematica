import pytest

from archivematica.archivematicaCommon.namespaces import NSMAP
from archivematica.dashboard.main import models
from archivematica.MCPClient.clientScripts import archivematicaCreateMETSRights
from archivematica.MCPClient.clientScripts.create_mets_v2 import MetsState


@pytest.fixture()
def rights_statement(db, sip_file):
    models.MetadataAppliesToType.objects.get_or_create(
        pk="7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17", description="File"
    )
    statement = models.RightsStatement.objects.create(
        metadataappliestotype=models.MetadataAppliesToType.objects.get(
            id=models.MetadataAppliesToType.FILE_TYPE
        ),
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
