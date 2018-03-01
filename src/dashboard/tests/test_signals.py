import os

from django.test import TestCase

from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestSignals(TestCase):
    fixture_files = ['metadata_type.json', 'rights.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

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
