# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
import pytest

from mockldap import MockLdap


@pytest.mark.skipif(
    not settings.LDAP_AUTHENTICATION, reason="tests will only pass if LDAP is enabled"
)
class TestLDAP(TestCase):
    # See settings.test for LDAP settings configuration
    top = ("o=test", {"o": ["test"]})
    example = ("ou=example,o=test", {"ou": ["example"]})
    alice = (
        "cn=alice_ldap,ou=example,o=test",
        {
            "cn": ["alice_ldap"],
            "givenName": ["Alice"],
            "sn": ["Example"],
            "mail": ["alice@example.com"],
            "userPassword": ["alicepw"],
        },
    )

    directory = dict([top, example, alice])

    @classmethod
    def setUpClass(cls):
        cls.mock_ldap = MockLdap(cls.directory)

    @classmethod
    def tearDownClass(cls):
        del cls.mock_ldap

    def setUp(self):
        self.mock_ldap = MockLdap(self.directory)
        self.mock_ldap.start()
        self.ldapobj = self.mock_ldap["ldap://localhost/"]

    def tearDown(self):
        self.mock_ldap.stop()
        del self.ldapobj
        del self.mock_ldap

    def test_login_with_ldap_details(self):
        assert self.client.login(username="alice_ldap", password="alicepw")
        alice = User.objects.get(username="alice")
        assert alice.first_name == "Alice"
        assert alice.last_name == "Example"
        assert alice.email == "alice@example.com"
        assert alice.api_key
