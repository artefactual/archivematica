import uuid
from unittest import mock

import pytest
from django.contrib.auth.models import User

from archivematica.dashboard.main import models
from tests.factories import TransferFactory


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


@pytest.mark.parametrize(
    "sip_uuid, input_path, expected_package_name",
    [
        # No directory - returns UUID.
        (
            "11111111-1111-1111-1111-111111111111",
            "",
            "11111111-1111-1111-1111-111111111111",
        ),
        # First pattern - simulates the directory of a transfer
        # in-progress with no trailing slash.
        (
            "22222222-2222-2222-2222-222222222222",
            "/directory-1/directory-1/transfer-name-22222222-2222-2222-2222-222222222222",
            "transfer-name",
        ),
        # Second pattern - simulates the directory of a transfer
        # in-progress with trailing slash.
        (
            "33333333-3333-3333-3333-333333333333",
            "/directory-1/directory-1/transfer-name-33333333-3333-3333-3333-333333333333/",
            "transfer-name",
        ),
        # Third pattern - simulates a new transfer with arbitrary
        # path with no trailing slash.
        (
            "44444444-4444-4444-4444-444444444444",
            "%sharedPath%currentlyProcessing/path-1",
            "path-1",
        ),
        # Fourth pattern - simulates a new transfer with arbitrary
        # path with trailing slash.
        (
            "55555555-5555-5555-5555-555555555555",
            "%sharedPath%currentlyProcessing/path-2/",
            "path-2",
        ),
        # Fifth pattern - will fail all conditions but we ensure the
        # Job doesn't return None and we retrieve the UUID at least.
        (
            "66666666-6666-6666-6666-666666666666",
            "%sharedPath%currentlyProcessingpath-2",
            "66666666-6666-6666-6666-666666666666",
        ),
        # Sixth pattern - should not happen within the Archivematica
        # workflow as the slashes would be terminated or single, but
        # will simulate all group matching failing.
        (
            "77777777-7777-7777-7777-777777777777",
            "/directory-1/directory-1/transfer-name-77777777-7777-7777-7777-777777777777//",
            "77777777-7777-7777-7777-777777777777",
        ),
        # Seventh pattern - should not happen within the
        # Archivematica workflow as the slashes would be terminated
        # or single, but will simulate all group matching failing.
        (
            "88888888-8888-8888-8888-888888888888",
            "%sharedPath%currentlyProcessing/path-2//",
            "88888888-8888-8888-8888-888888888888",
        ),
    ],
)
def test_job_get_directory_name(sip_uuid, input_path, expected_package_name):
    job = models.Job()
    job.sipuuid = sip_uuid
    job.directory = input_path
    assert job.get_directory_name() == expected_package_name
