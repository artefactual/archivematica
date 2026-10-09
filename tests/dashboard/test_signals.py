import uuid

import pytest

from archivematica.dashboard.main import models
from tests.factories import RightsStatementFactory


@pytest.fixture
def rights_statement(
    make_rights_statement: RightsStatementFactory,
) -> models.RightsStatement:
    """A copyright statement of a SIP with two rights granted."""
    result = make_rights_statement("sip", uuid.uuid4(), rightsbasis="Copyright")
    make_rights_statement.grant(
        result, "Disseminate", startdate="2000", enddateopen=True
    )
    make_rights_statement.grant(result, "Access", startdate="2016", enddate="")

    return result


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
    first, last = rights_statement.rightsstatementrightsgranted_set.order_by("pk")

    # Delete the first RightsGranted
    first.delete()

    # The statement still exists
    assert models.RightsStatement.objects.count() == 1
    assert models.RightsStatementRightsGranted.objects.count() == 1

    # Delete the last RightsGranted
    last.delete()

    # The statement is deleted too
    assert models.RightsStatement.objects.count() == 0
    assert models.RightsStatementRightsGranted.objects.count() == 0
