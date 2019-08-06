from __future__ import absolute_import
from django.test import TestCase

from main.models import SIP, Transfer, UnitVariable, User


class TestActiveAgent(TestCase):
    fixtures = ["test_user"]

    def test_transfer_update_active_agent(self):
        user = User.objects.get(id=1)
        transfer = Transfer.objects.create()
        transfer.update_active_agent(user.id)
        assert UnitVariable.objects.get(
            unittype="Transfer",
            unituuid=transfer.uuid,
            variable="activeAgent",
            variablevalue=user.userprofile.agent_id,
        )

    def test_sip_update_active_agent(self):
        user = User.objects.get(id=1)
        sip = SIP.objects.create()
        sip.update_active_agent(user.id)
        assert UnitVariable.objects.get(
            unittype="SIP",
            unituuid=sip.uuid,
            variable="activeAgent",
            variablevalue=user.userprofile.agent_id,
        )

    def test_unitvariable_update_variable(self):
        obj, created = UnitVariable.objects.update_variable(
            "UNIT_TYPE", "UNIT_ID", "VARIABLE", "VALUE", "LINK_ID"
        )
        assert created is True
        assert isinstance(obj, UnitVariable)
        UnitVariable.objects.get(
            unittype="UNIT_TYPE",
            unituuid="UNIT_ID",
            variable="VARIABLE",
            variablevalue="VALUE",
            microservicechainlink="LINK_ID",
        )

        obj, created = UnitVariable.objects.update_variable(
            "UNIT_TYPE", "UNIT_ID", "VARIABLE", "NEW_VALUE", "NEW_LINK_ID"
        )
        assert created is False
        assert isinstance(obj, UnitVariable)
        UnitVariable.objects.get(
            unittype="UNIT_TYPE",
            unituuid="UNIT_ID",
            variable="VARIABLE",
            variablevalue="NEW_VALUE",
            microservicechainlink="NEW_LINK_ID",
        )
