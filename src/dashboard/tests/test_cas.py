# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.urls import reverse
import pytest
import mock

from components import helpers
from components.accounts.backends import CustomCASBackend
from components.accounts.signals import _cas_user_is_administrator

TEST_CAS_USER = "casuser"
TEST_CAS_ADMIN_ATTRIBUTE = "usertype"
TEST_CAS_ADMIN_ATTRIBUTE_VALUE_POSITIVE = "admin"
TEST_CAS_ADMIN_ATTRIBUTE_VALUE_NEGATIVE = "regular"

TEST_CAS_ATTRIBUTES_STRING_POSITIVE = {
    TEST_CAS_ADMIN_ATTRIBUTE: TEST_CAS_ADMIN_ATTRIBUTE_VALUE_POSITIVE
}
TEST_CAS_ATTRIBUTES_STRING_NEGATIVE = {
    TEST_CAS_ADMIN_ATTRIBUTE: TEST_CAS_ADMIN_ATTRIBUTE_VALUE_NEGATIVE
}
TEST_CAS_ATTRIBUTES_LIST_POSITIVE = {
    TEST_CAS_ADMIN_ATTRIBUTE: [
        TEST_CAS_ADMIN_ATTRIBUTE_VALUE_POSITIVE,
        "attribute1",
        "attribute2",
    ]
}
TEST_CAS_ATTRIBUTES_LIST_NEGATIVE = {
    TEST_CAS_ADMIN_ATTRIBUTE: [
        TEST_CAS_ADMIN_ATTRIBUTE_VALUE_NEGATIVE,
        "attribute1",
        "attribute2",
    ]
}


def mock_verify(ticket, service):
    user = TEST_CAS_USER
    attributes = {
        "ticket": ticket,
        "service": service,
        TEST_CAS_ADMIN_ATTRIBUTE: TEST_CAS_ADMIN_ATTRIBUTE_VALUE_NEGATIVE,
    }
    pgtiou = None
    return user, attributes, pgtiou


def mock_verify_superuser(ticket, service):
    user = TEST_CAS_USER
    attributes = {
        "ticket": ticket,
        "service": service,
        TEST_CAS_ADMIN_ATTRIBUTE: TEST_CAS_ADMIN_ATTRIBUTE_VALUE_POSITIVE,
    }
    pgtiou = None
    return user, attributes, pgtiou


@pytest.mark.skipif(
    not settings.CAS_AUTHENTICATION, reason="tests will only pass if CAS is enabled"
)
class TestCAS(TestCase):
    def setUp(self):
        self.client = Client()

    def authenticate_user(self, request):
        """Helper function to authenticate a user using custom backend."""
        backend = CustomCASBackend()
        backend.authenticate(request, ticket="fake-ticket", service="fake-service")

    def create_request(self):
        """Helper function to create request that will redirect to CAS."""
        factory = RequestFactory()
        request = factory.get("/")
        request.session = {}
        return request

    def test_redirect_for_login(self):
        """Unauthenticated users should be redirected twice.

        After the initial redirect to LOGIN_URL, the user should be
        redirected again to the CAS server for authentication.
        """
        helpers.set_setting("dashboard_uuid", "test-uuid")

        response = self.client.get(reverse("main:main_index"))
        self.assertRedirects(
            response, settings.LOGIN_URL, status_code=302, target_status_code=302
        )

    @mock.patch("cas.CASClientV2.verify_ticket", mock_verify)
    def test_autoconfigure_email(self):
        """Test that email is autoconfigured from username and domain."""
        helpers.set_setting("dashboard_uuid", "test-uuid")

        with self.settings(
            CAS_AUTOCONFIGURE_EMAIL=True, CAS_EMAIL_DOMAIN="artefactual.com"
        ):
            request = self.create_request()

            # Check that user doesn't already exist.
            assert not User.objects.filter(username=TEST_CAS_USER).exists()

            # Create the user and check its properties.
            self.authenticate_user(request)
            user = User.objects.get(username=TEST_CAS_USER)
            assert user is not None
            assert user.username == TEST_CAS_USER
            assert user.email == "casuser@artefactual.com"

    @mock.patch("cas.CASClientV2.verify_ticket", mock_verify_superuser)
    def test_check_admin_attributes_superuser_new_user(self):
        """Test setting is_superuser for new users.

        If settings are properly configured and expected key-value is
        found in the CAS attributes, user.is_superuser should be True.
        """
        helpers.set_setting("dashboard_uuid", "test-uuid")

        # Check that user doesn't already exist.
        assert not User.objects.filter(username=TEST_CAS_USER).exists()

        with self.settings(
            CAS_CHECK_ADMIN_ATTRIBUTES=True,
            CAS_ADMIN_ATTRIBUTE=TEST_CAS_ADMIN_ATTRIBUTE,
            CAS_ADMIN_ATTRIBUTE_VALUE=TEST_CAS_ADMIN_ATTRIBUTE_VALUE_POSITIVE,
        ):
            request = self.create_request()
            self.authenticate_user(request)
            user = User.objects.get(username=TEST_CAS_USER)
            assert user is not None
            assert user.is_superuser is True

    @mock.patch("cas.CASClientV2.verify_ticket", mock_verify_superuser)
    def test_check_admin_attributes_superuser_existing_user(self):
        """Test setting is_superuser for existing users.

        If settings are properly configured and expected key-value is
        found in the CAS attributes, user.is_superuser for an existing
        non-administrative user should be updated to True.
        """
        helpers.set_setting("dashboard_uuid", "test-uuid")

        user = User.objects.create(username=TEST_CAS_USER)
        assert user is not None
        assert user.is_superuser is False

        # Authenticate again with CAS_CHECK_ADMIN_ATTRIBUTES enabled
        # and check that user.is_superuser has been updated to True.
        with self.settings(
            CAS_CHECK_ADMIN_ATTRIBUTES=True,
            CAS_ADMIN_ATTRIBUTE=TEST_CAS_ADMIN_ATTRIBUTE,
            CAS_ADMIN_ATTRIBUTE_VALUE=TEST_CAS_ADMIN_ATTRIBUTE_VALUE_POSITIVE,
        ):
            request = self.create_request()
            self.authenticate_user(request)
            user = User.objects.get(username=TEST_CAS_USER)
            assert user is not None
            assert user.is_superuser is True

    @mock.patch("cas.CASClientV2.verify_ticket", mock_verify)
    def test_check_admin_attributes_regular_new_user(self):
        """Test setting is_superuser for new users.

        If settings are properly configured and expected key-value is
        not found in the CAS attributes, user.is_superuser should be
        False.
        """
        helpers.set_setting("dashboard_uuid", "test-uuid")

        # Check that user doesn't already exist.
        assert not User.objects.filter(username=TEST_CAS_USER).exists()

        with self.settings(
            CAS_CHECK_ADMIN_ATTRIBUTES=True,
            CAS_ADMIN_ATTRIBUTE=TEST_CAS_ADMIN_ATTRIBUTE,
            CAS_ADMIN_ATTRIBUTE_VALUE=TEST_CAS_ADMIN_ATTRIBUTE_VALUE_POSITIVE,
        ):
            request = self.create_request()
            self.authenticate_user(request)
            user = User.objects.get(username=TEST_CAS_USER)
            assert user is not None
            assert user.is_superuser is False

    @mock.patch("cas.CASClientV2.verify_ticket", mock_verify_superuser)
    def test_check_admin_attributes_regular_existing_user(self):
        """Test setting is_superuser for existing users.

        If settings are properly configured and expected key-value is
        not found in the CAS attributes, user.is_superuser for an
        existing administrative user should be updated to False.
        """
        helpers.set_setting("dashboard_uuid", "test-uuid")

        # Create a new superuser.
        user = User.objects.create(username=TEST_CAS_USER, is_superuser=True)
        assert user is not None
        assert user.is_superuser is True

        # Authenticate with CAS_ADMIN_ATTRIBUTE_VALUE set to a value
        # not present in the CAS attributes and check that
        # user.is_superuser has been updated to False.
        with self.settings(
            CAS_CHECK_ADMIN_ATTRIBUTES=True,
            CAS_ADMIN_ATTRIBUTE=TEST_CAS_ADMIN_ATTRIBUTE,
            CAS_ADMIN_ATTRIBUTE_VALUE="something else",
        ):
            request = self.create_request()
            self.authenticate_user(request)
            user = User.objects.get(username=TEST_CAS_USER)
            assert user is not None
            assert user.is_superuser is False

    def test_cas_user_is_administrator(self):
        """Unit test for _cas_user_is_administrator helper."""
        # If settings are improperly configured, function should return
        # False.
        with self.settings(
            CAS_CHECK_ADMIN_ATTRIBUTES=True,
            CAS_ADMIN_ATTRIBUTE=TEST_CAS_ADMIN_ATTRIBUTE,
            CAS_ADMIN_ATTRIBUTE_VALUE=None,
        ):
            assert (
                _cas_user_is_administrator(TEST_CAS_ATTRIBUTES_STRING_POSITIVE) is False
            )

        # Ensure function returns expected values whether
        # CAS_ADMIN_ATTRIBUTE is a string or a list.
        with self.settings(
            CAS_CHECK_ADMIN_ATTRIBUTES=True,
            CAS_ADMIN_ATTRIBUTE=TEST_CAS_ADMIN_ATTRIBUTE,
            CAS_ADMIN_ATTRIBUTE_VALUE=TEST_CAS_ADMIN_ATTRIBUTE_VALUE_POSITIVE,
        ):
            assert (
                _cas_user_is_administrator(TEST_CAS_ATTRIBUTES_STRING_POSITIVE) is True
            )
            assert (
                _cas_user_is_administrator(TEST_CAS_ATTRIBUTES_STRING_NEGATIVE) is False
            )
            assert _cas_user_is_administrator(TEST_CAS_ATTRIBUTES_LIST_POSITIVE) is True
            assert (
                _cas_user_is_administrator(TEST_CAS_ATTRIBUTES_LIST_NEGATIVE) is False
            )
