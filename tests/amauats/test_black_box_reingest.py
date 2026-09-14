import os

import pytest
from pytest_bdd import scenarios
from steps_black_box import *  # noqa: F403

if "RUN_AMAUATS" not in os.environ:
    pytest.skip("Skipping AMAUAT tests", allow_module_level=True)


scenarios(
    "features/black_box/reingest_aip.feature",
    "features/black_box/metadata_xml.feature",
)
