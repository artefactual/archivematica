import archivematicaCreateMETSRights
import pytest
from create_mets_v2 import MetsState
from main import models
from namespaces import NSMAP


@pytest.fixture()
def rights_statement(db, sip_file):
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
