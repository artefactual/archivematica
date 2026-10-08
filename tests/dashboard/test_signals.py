import pytest

from archivematica.dashboard.main import models


@pytest.fixture
def rights_statement(
    metadata_applies_to_types: dict[str, models.MetadataAppliesToType],
) -> models.RightsStatement:
    """A copyright statement of a SIP with two rights granted."""
    result = models.RightsStatement.objects.create(
        metadataappliestotype=metadata_applies_to_types["sip"],
        metadataappliestoidentifier="d64b0f43-f6d3-42ac-9821-c559dca13786",
        rightsbasis="Copyright",
        status="ORIGINAL",
    )
    models.RightsStatementRightsGranted.objects.create(
        rightsstatement=result, act="Disseminate", startdate="2000", enddateopen=True
    )
    models.RightsStatementRightsGranted.objects.create(
        rightsstatement=result, act="Access", startdate="2016", enddate=""
    )

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
