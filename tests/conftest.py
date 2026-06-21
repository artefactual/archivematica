import uuid

import pytest

from archivematica.dashboard.main.models import DashboardSetting


@pytest.fixture
def dashboard_uuid(db: None) -> uuid.UUID:
    """Set the dashboard UUID without importing Tastypie-dependent helpers."""
    result = uuid.uuid4()
    DashboardSetting.objects.filter(name="dashboard_uuid").delete()
    DashboardSetting.objects.create(name="dashboard_uuid", value=str(result))

    return result
