# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import uuid

from create_mets_v2 import MetsState
from client.job import Job
from main import models
from namespaces import NSMAP
import pytest

import archivematicaCreateMETSRights


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
