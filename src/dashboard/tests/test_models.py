# -*- coding: utf-8 -*-

from django.test import TestCase
import mock

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
