import shutil
import tempfile
import unittest
from pathlib import Path


class TempDirMixin(unittest.TestCase):
    """A test case mixin that creates a temporary directory.

    It sets ``tmpdir`` as an instance of ``pathlib.Path``.
    """

    def setUp(self):
        super().setUp()
        self.tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        shutil.rmtree(str(self.tmpdir))
