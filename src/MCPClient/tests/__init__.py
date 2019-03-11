import shutil
import tempfile
import unittest

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


class TempDirMixin(unittest.TestCase):
    """A test case mixin that creates a temporary directory.

    It sets ``tmpdir`` as an instance of ``pathlib.Path``.
    """

    def setUp(self):
        super(TempDirMixin, self).setUp()
        self.tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        shutil.rmtree(str(self.tmpdir))
