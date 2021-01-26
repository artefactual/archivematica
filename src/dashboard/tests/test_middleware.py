# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from django.test.client import Client

from components import helpers
from installer.middleware import _load_exempt_urls


class ConfigurationCheckMiddlewareTestCase(TestCase):
    fixtures = ["test_user"]

    def setUp(self):
        self.client = Client()

    def test_user_is_sent_to_installer(self):
        response = self.client.get("/")

        self.assertRedirects(response, reverse("installer:welcome"))

    def test_installer(self):
        response = self.client.get(reverse("installer:welcome"))

        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_can_access_exempt_url(self):
        helpers.set_setting("dashboard_uuid", "test-uuid")

        with self.settings(LOGIN_EXEMPT_URLS=[r"^foobar"]):
            _load_exempt_urls()
            response = self.client.get("foobar")

        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_is_sent_to_login_page(self):
        helpers.set_setting("dashboard_uuid", "test-uuid")

        response = self.client.get(reverse("main:main_index"))

        if not settings.CAS_AUTHENTICATION:
            self.assertRedirects(response, settings.LOGIN_URL)

    def test_authenticated_user_passes(self):
        helpers.set_setting("dashboard_uuid", "test-uuid")
        self.client.login(username="test", password="test")

        response = self.client.get(reverse("transfer:transfer_index"))

        self.assertEqual(response.status_code, 200)


class AuditLogMiddlewareTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username="testclient", password="test")
        self.client.force_login(self.user)

    def test_audit_log_middleware_adds_username(self):
        """Test that X-Username is added for authenticated users."""
        with self.modify_settings(
            MIDDLEWARE={"append": "middleware.common.AuditLogMiddleware"}
        ):
            response = self.client.get("/transfer/", follow=True)
            self.assertTrue(response.has_header("X-Username"))
            self.assertEqual(response["X-Username"], self.user.username)

    def test_audit_log_middleware_unauthenticated(self):
        """Test absence of X-Username header for unauthenticated users.

        First we logout the authenticated user, and then we check that
        X-Username is not present in the response for a new request by
        an unauthenticated user.
        """
        with self.modify_settings(
            MIDDLEWARE={"append": "middleware.common.AuditLogMiddleware"}
        ):
            self.client.logout()

            response = self.client.get(settings.LOGIN_URL, follow=True)
            self.assertFalse(response.has_header("X-Username"))
