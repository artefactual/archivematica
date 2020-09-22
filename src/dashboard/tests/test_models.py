# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.db import IntegrityError
from django.test import TestCase
import mock

import pytest

from main import models


class TestActiveAgent(TestCase):
    fixtures = ["test_user"]

    def test_transfer_update_active_agent(self):
        user = models.User.objects.get(id=1)
        transfer = models.Transfer.objects.create()
        transfer.update_active_agent(user.id)
        assert models.UnitVariable.objects.get(
            unittype="Transfer",
            unituuid=transfer.uuid,
            variable="activeAgent",
            variablevalue=user.userprofile.agent_id,
        )

    def test_sip_update_active_agent(self):
        user = models.User.objects.get(id=1)
        sip = models.SIP.objects.create()
        sip.update_active_agent(user.id)
        assert models.UnitVariable.objects.get(
            unittype="SIP",
            unituuid=sip.uuid,
            variable="activeAgent",
            variablevalue=user.userprofile.agent_id,
        )

    def test_unitvariable_update_variable(self):
        obj, created = models.UnitVariable.objects.update_variable(
            "UNIT_TYPE", "UNIT_ID", "VARIABLE", "VALUE", "LINK_ID"
        )
        assert created is True
        assert isinstance(obj, models.UnitVariable)
        models.UnitVariable.objects.get(
            unittype="UNIT_TYPE",
            unituuid="UNIT_ID",
            variable="VARIABLE",
            variablevalue="VALUE",
            microservicechainlink="LINK_ID",
        )

        obj, created = models.UnitVariable.objects.update_variable(
            "UNIT_TYPE", "UNIT_ID", "VARIABLE", "NEW_VALUE", "NEW_LINK_ID"
        )
        assert created is False
        assert isinstance(obj, models.UnitVariable)
        models.UnitVariable.objects.get(
            unittype="UNIT_TYPE",
            unituuid="UNIT_ID",
            variable="VARIABLE",
            variablevalue="NEW_VALUE",
            microservicechainlink="NEW_LINK_ID",
        )


@mock.patch("main.models.Agent")
def test_create_user_agent(agent_mock):
    agent_mock.objects.update_or_create.return_value = (None, False)
    user_mock = mock.Mock(
        id=1234, username=u"maría", first_name=u"María", last_name=u"Martínez"
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


def test_sip_arrange_create_many(db):
    arranges = [
        models.SIPArrange(original_path=None, arrange_path="a.txt", file_uuid=None),
        models.SIPArrange(original_path=None, arrange_path="b.txt", file_uuid=None),
    ]
    assert not models.SIPArrange.objects.count()
    models.SIPArrange.create_many(arranges)
    assert models.SIPArrange.objects.count() == 2


def test_sip_arrange_create_many_with_integrity_error(mocker):
    mocker.patch(
        "main.models.SIPArrange.objects.bulk_create", side_effect=IntegrityError()
    )
    arrange1_mock = mocker.Mock()
    arrange2_mock = mocker.Mock()
    models.SIPArrange.create_many([arrange1_mock, arrange2_mock])
    # If bulk creation fails each SIPArrange is saved individually
    assert arrange1_mock.save.called_once()
    assert arrange2_mock.save.called_once()


class TestJobModel(object):
    """Tests for the Job model."""

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
    def test_get_directory_name(self, sip_uuid, input_path, expected_package_name):
        job = models.Job()
        job.sipuuid = sip_uuid
        job.directory = input_path
        assert job.get_directory_name() == expected_package_name
