import pathlib

from django.test import TestCase
from main import models

METADATA_TYPE_FIXTURE = (
    pathlib.Path(__file__).parent / "fixtures" / "metadata_type.json"
)
RIGHTS_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "rights.json"


class TestSignals(TestCase):
    fixtures = [METADATA_TYPE_FIXTURE, RIGHTS_FIXTURE]

    def test_delete_rights_statement(self):
        """It should delete all children."""
        # Verify exist
        assert models.RightsStatement.objects.count() == 1
        assert models.RightsStatementRightsGranted.objects.count() == 2
        # Delete
        models.RightsStatement.objects.filter(pk=1).delete()
        # Verify children deleted
        assert models.RightsStatement.objects.count() == 0
        assert models.RightsStatementRightsGranted.objects.count() == 0

    def test_delete_rights_granted(self):
        """It should delete RightsStatements with no RightsGranted."""
        # Verify exist
        assert models.RightsStatement.objects.count() == 1
        assert models.RightsStatementRightsGranted.objects.count() == 2
        # Delete RightsGranted
        models.RightsStatementRightsGranted.objects.filter(pk=1).delete()
        # Verify Statement still exists
        assert models.RightsStatement.objects.count() == 1
        assert models.RightsStatementRightsGranted.objects.count() == 1
        # Delete last RightsGranted
        models.RightsStatementRightsGranted.objects.filter(pk=2).delete()
        # Verify statement deleted
        assert models.RightsStatement.objects.count() == 0
        assert models.RightsStatementRightsGranted.objects.count() == 0
