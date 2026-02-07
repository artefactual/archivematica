import pytest

from archivematica.dashboard.main.models import MetadataAppliesToType


@pytest.fixture
def metadata_applies_to_types(db):
    sip_type, _ = MetadataAppliesToType.objects.get_or_create(description="SIP")
    transfer_type, _ = MetadataAppliesToType.objects.get_or_create(
        description="Transfer"
    )
    file_type, _ = MetadataAppliesToType.objects.get_or_create(description="File")
    return {"sip": sip_type, "transfer": transfer_type, "file": file_type}
