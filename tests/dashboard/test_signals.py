import pathlib

import pytest
from django.core.management import call_command

from archivematica.dashboard.main import models

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def rights_statement(db: None) -> models.RightsStatement:
    """The rights statement with two rights granted of the rights.json fixture."""
    call_command(
        "loaddata",
        FIXTURES_DIR / "metadata_type.json",
        FIXTURES_DIR / "rights.json",
        verbosity=0,
    )

    return models.RightsStatement.objects.get(pk=1)


def test_delete_rights_statement(rights_statement: models.RightsStatement) -> None:
    """It should delete all children."""
    assert models.RightsStatement.objects.count() == 1
    assert models.RightsStatementRightsGranted.objects.count() == 2

    models.RightsStatement.objects.filter(pk=rights_statement.pk).delete()

    assert models.RightsStatement.objects.count() == 0
    assert models.RightsStatementRightsGranted.objects.count() == 0


def test_delete_rights_granted(rights_statement: models.RightsStatement) -> None:
    """It should delete RightsStatements with no RightsGranted."""
    assert models.RightsStatement.objects.count() == 1
    assert models.RightsStatementRightsGranted.objects.count() == 2

    # Delete the first RightsGranted
    models.RightsStatementRightsGranted.objects.filter(pk=1).delete()

    # The statement still exists
    assert models.RightsStatement.objects.count() == 1
    assert models.RightsStatementRightsGranted.objects.count() == 1

    # Delete the last RightsGranted
    models.RightsStatementRightsGranted.objects.filter(pk=2).delete()

    # The statement is deleted too
    assert models.RightsStatement.objects.count() == 0
    assert models.RightsStatementRightsGranted.objects.count() == 0
