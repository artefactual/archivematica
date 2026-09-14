import os

import pytest
from pytest_bdd import scenarios
from steps_black_box import *  # noqa: F403

if "RUN_AMAUATS" not in os.environ:
    pytest.skip("Skipping AMAUAT tests", allow_module_level=True)


scenarios(
    "features/black_box/checksum.feature",
    "features/black_box/description_rights.feature",
    "features/black_box/extract_package.feature",
    "features/black_box/transfer_microservices.feature",
    "features/black_box/validation.feature",
    "features/black_box/virus.feature",
)
