import uuid
from unittest import mock

import pytest
from django.contrib.auth.models import User

from archivematica.dashboard.main import models
from tests.factories import TransferFactory


@pytest.mark.django_db
def test_transfer_update_active_agent(
    admin_user: User, make_transfer: TransferFactory
) -> None:
    transfer = make_transfer()

    transfer.update_active_agent(admin_user.id)

    assert (
        models.UnitVariable.objects.filter(
            unittype="Transfer",
            unituuid=transfer.uuid,
            variable="activeAgent",
            variablevalue=admin_user.userprofile.agent_id,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_sip_update_active_agent(admin_user: User, sip: models.SIP) -> None:
    sip.update_active_agent(admin_user.id)

    assert (
        models.UnitVariable.objects.filter(
            unittype="SIP",
            unituuid=sip.uuid,
            variable="activeAgent",
            variablevalue=admin_user.userprofile.agent_id,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_unitvariable_update_variable() -> None:
    unit_uuid = uuid.uuid4()
    link_id = uuid.uuid4()

    obj, created = models.UnitVariable.objects.update_variable(
        "UNIT_TYPE", unit_uuid, "VARIABLE", "VALUE", link_id
    )

    assert created is True
    assert isinstance(obj, models.UnitVariable)
    assert (
        models.UnitVariable.objects.filter(
            unittype="UNIT_TYPE",
            unituuid=unit_uuid,
            variable="VARIABLE",
            variablevalue="VALUE",
            microservicechainlink=link_id,
        ).count()
        == 1
    )

    new_link_id = uuid.uuid4()
    obj, created = models.UnitVariable.objects.update_variable(
        "UNIT_TYPE", unit_uuid, "VARIABLE", "NEW_VALUE", new_link_id
    )

    assert created is False
    assert isinstance(obj, models.UnitVariable)
    assert (
        models.UnitVariable.objects.filter(
            unittype="UNIT_TYPE",
            unituuid=unit_uuid,
            variable="VARIABLE",
            variablevalue="NEW_VALUE",
            microservicechainlink=new_link_id,
        ).count()
        == 1
    )


@mock.patch("archivematica.dashboard.main.models.Agent")
def test_create_user_agent(agent_mock):
    agent_mock.objects.update_or_create.return_value = (None, False)
    user_mock = mock.Mock(
        id=1234, username="maría", first_name="María", last_name="Martínez"
    )
    models.create_user_agent(None, user_mock)
    agent_mock.objects.update_or_create.assert_called_once_with(
        userprofile__user=user_mock,
        defaults={
            "identifiertype": "Archivematica user pk",
            "identifiervalue": "1234",
            "name": 'username="maría", first_name="María", last_name="Martínez"',
            "agenttype": "Archivematica user",
        },
    )


# UUID of the unit of the job whose directory name is parsed.
SIP_UUID = uuid.uuid4()


@pytest.mark.parametrize(
    "input_path, expected_package_name",
    [
        # No directory - returns UUID.
        ("", SIP_UUID),
        # First pattern - simulates the directory of a transfer
        # in-progress with no trailing slash.
        (f"/directory-1/directory-1/transfer-name-{SIP_UUID}", "transfer-name"),
        # Second pattern - simulates the directory of a transfer
        # in-progress with trailing slash.
        (f"/directory-1/directory-1/transfer-name-{SIP_UUID}/", "transfer-name"),
        # Third pattern - simulates a new transfer with arbitrary
        # path with no trailing slash.
        ("%sharedPath%currentlyProcessing/path-1", "path-1"),
        # Fourth pattern - simulates a new transfer with arbitrary
        # path with trailing slash.
        ("%sharedPath%currentlyProcessing/path-2/", "path-2"),
        # Fifth pattern - will fail all conditions but we ensure the
        # Job doesn't return None and we retrieve the UUID at least.
        ("%sharedPath%currentlyProcessingpath-2", SIP_UUID),
        # Sixth pattern - should not happen within the Archivematica
        # workflow as the slashes would be terminated or single, but
        # will simulate all group matching failing.
        (f"/directory-1/directory-1/transfer-name-{SIP_UUID}//", SIP_UUID),
        # Seventh pattern - should not happen within the
        # Archivematica workflow as the slashes would be terminated
        # or single, but will simulate all group matching failing.
        ("%sharedPath%currentlyProcessing/path-2//", SIP_UUID),
    ],
    ids=[
        "no_directory",
        "transfer_without_slash",
        "transfer_with_slash",
        "path_without_slash",
        "path_with_slash",
        "no_match",
        "transfer_double_slash",
        "path_double_slash",
    ],
)
def test_job_get_directory_name(
    input_path: str, expected_package_name: str | uuid.UUID
) -> None:
    job = models.Job()
    job.sipuuid = SIP_UUID
    job.directory = input_path
    assert job.get_directory_name() == expected_package_name
