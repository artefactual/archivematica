import json

from components import helpers
from components.helpers import generate_api_key
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from tastypie.models import ApiKey


class TestAuth(TestCase):
    """Authentication sanity checks."""

    fixtures = ["test_user"]

    API_URLS = (
        reverse("api:completed_transfers"),
        reverse("api:completed_ingests"),
        reverse("api:get_levels_of_description"),
    )

    def setUp(self):
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def authenticate(self):
        self.client = Client()
        self.client.login(username="test", password="test")

    def test_site_requires_auth(self):
        for url in [
            reverse("transfer:transfer_index"),
            reverse("ingest:ingest_index"),
            reverse("administration:api"),
            reverse("administration:general"),
            reverse("administration:premis_agent"),
            # Verify that exempted URLs cannot be used to access other areas
            # that are restricted.
            "{}/{}".format(settings.LOGIN_URL.rstrip("/"), "transfer/"),
            "{}/{}".format(settings.LOGIN_URL.rstrip("/"), "abcdefgh/api/"),
            "{}/{}".format(settings.LOGIN_URL.rstrip("/"), "version"),
        ]:
            response = self.client.get(url)

            self.assertRedirects(response, settings.LOGIN_URL)

    def test_site_performs_session_auth(self):
        self.authenticate()

        for url in [
            reverse("transfer:transfer_index"),
            reverse("ingest:ingest_index"),
            reverse("administration:api"),
        ]:
            response = self.client.get(url, follow=False)

            self.assertEqual(response.status_code, 200)

    def test_api_requires_auth(self):
        for url in self.API_URLS:
            response = self.client.get(url)

            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                response.content.decode("utf8"),
                json.dumps({"message": "API key not valid.", "error": True}),
            )

    def test_api_authenticates_via_key(self):
        user = get_user_model().objects.get(pk=1)
        generate_api_key(user)
        key = ApiKey.objects.get(user=user).key

        for url in self.API_URLS:
            response = self.client.get(
                url, headers={"authorization": f"ApiKey test:{key}"}, follow=False
            )

            self.assertEqual(response.status_code, 200)

    def test_api_authenticates_via_session(self):
        self.authenticate()

        for url in self.API_URLS:
            response = self.client.get(url, follow=False)

            self.assertEqual(response.status_code, 200)
