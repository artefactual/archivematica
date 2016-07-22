# -*- coding: UTF-8 -*-
import os
import unittest

import identifier_functions

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(THIS_DIR, 'fixtures')

class TestIdentifierFunctions(unittest.TestCase):
    """Test extracting additional identifiers for indexing."""

    def test_mods(self):
        """It should return all identifiers."""
        path = os.path.join(FIXTURES_DIR, 'test-identifiers-MODS-METS.xml')
        identifiers = identifier_functions.extract_identifiers_from_mods(path)
        assert len(identifiers) == 4
        assert '28475' in identifiers
        assert 'Yamani' in identifiers
        assert 'Glaive 18' in identifiers
        assert 'http://archives.tortall.gov/yamani/permalink/28475' in identifiers
