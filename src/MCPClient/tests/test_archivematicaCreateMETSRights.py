import uuid

import archivematicaCreateMETSRights
import pytest
from client.job import Job
from create_mets_v2 import MetsState
from main import models
from namespaces import NSMAP


@pytest.fixture()
def job():
    return Job("stub", "stub", [])


@pytest.fixture()
def file_(db):
    return models.File.objects.create(
        uuid=uuid.uuid4(),
    )


@pytest.fixture()
def rights_statement(db, file_):
    statement = models.RightsStatement.objects.create(
        metadataappliestotype=models.MetadataAppliesToType.objects.get(
            id=models.MetadataAppliesToType.FILE_TYPE
        ),
        metadataappliestoidentifier=file_.uuid,
        rightsbasis="Copyright",
    )
    models.RightsStatementCopyright.objects.create(
        rightsstatement=statement,
        copyrightjurisdiction="Québec",
    )
    return statement


def test_archivematicaGetRights_with_non_ascii_copyright_jurisdiction(
    db,
    job,
    file_,
    rights_statement,
):
    metadataAppliesToList = [
        (file_.uuid, models.MetadataAppliesToType.FILE_TYPE),
    ]
    result = archivematicaCreateMETSRights.archivematicaGetRights(
        job, metadataAppliesToList, str(file_.uuid), MetsState()
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
