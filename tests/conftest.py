import uuid

import pytest

from archivematica.dashboard.components import helpers


@pytest.fixture
def dashboard_uuid(db: None) -> uuid.UUID:
    result = uuid.uuid4()
    helpers.set_setting("dashboard_uuid", str(result))

    return result
