import os

import pytest
from pytest_bdd import scenarios
from steps_black_box import *  # noqa: F403
from steps_core import *  # noqa: F403

if "RUN_AMAUATS" not in os.environ:
    pytest.skip("Skipping AMAUAT tests", allow_module_level=True)


scenarios(
    "features/core/manual_normalization.feature",
    "features/core/transfer_mkv_conformance.feature",
    "features/core/uuids_for_directories.feature",
)
