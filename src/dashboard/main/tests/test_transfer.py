import uuid

import pytest
from main import models


@pytest.mark.parametrize(
    "in_transfer, transfer_type, in_sip, expected_output",
    [
        # File in transfer of type Transfer.ARCHIVEMATICA_AIP returns
        # True.
        (True, models.Transfer.ARCHIVEMATICA_AIP, False, True),
        # File in transfer of another type returns False.
        (True, "", False, False),
        (True, "Not an Archivematica AIP", False, False),
        # File in SIP returns False.
        (False, None, True, False),
        # File in both Transfer and SIP (shouldn't happen) returns False.
        (True, None, True, False),
    ],
)
def test_file_in_reingested_aip(
    transfer, sip, in_transfer, transfer_type, in_sip, expected_output
):
    """Test File.in_reingested_aip property."""
    file_ = models.File.objects.create(uuid=uuid.uuid4())
    if in_transfer:
        file_.transfer = transfer
        file_.save()
    if transfer_type:
        file_.transfer.type = transfer_type
        file_.transfer.save()
    if in_sip:
        file_.sip = sip
        file_.save()
    assert file_.in_reingested_aip == expected_output
