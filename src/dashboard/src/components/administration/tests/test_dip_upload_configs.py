# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.urls import reverse
from django.test import TestCase

from components import helpers
from components.administration.views_dip_upload import _AS_DICTNAME, _ATOM_DICTNAME
from main.models import DashboardSetting


class TestDipUploadAsConfig(TestCase):
    fixtures = ["test_user"]

    def setUp(self):
        self.client.login(username="test", password="test")
        self.url = reverse("administration:dips_as")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.request.get("PATH_INFO"), "/administration/dips/as/")
        self.assertTemplateUsed(response, "administration/dips_as_edit.html")
        self.assertFalse(response.context["form"].is_valid())

    def test_post_minimum_required(self):
        response = self.client.post(
            self.url,
            {
                "base_url": "http://aspace.test.org:8089",
                "user": "admin",
                "xlink_show": "embed",
                "xlink_actuate": "none",
                "uri_prefix": "http://example.com",
                "repository": 2,
                "restrictions": "yes",
            },
        )
        form = response.context["form"]
        messages = list(response.context["messages"])
        config = DashboardSetting.objects.get_dict(_AS_DICTNAME)

        self.assertTrue(form.is_valid())
        self.assertFalse(form.errors)

        self.assertTrue(messages)
        self.assertEqual(messages[0].message, "Saved.")
        self.assertEqual(messages[0].tags, "info")

        self.assertIsInstance(config, dict)
        self.assertEqual(config["base_url"], "http://aspace.test.org:8089")
        self.assertEqual(config["repository"], "2")
        self.assertEqual(len(list(config.keys())), len(form.fields))

    def test_post_missing_fields(self):
        response = self.client.post(
            self.url, {"base_url": "http://aspace.test.org:8089"}
        )
        form = response.context["form"]
        config = DashboardSetting.objects.get_dict(_AS_DICTNAME)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)

        self.assertFormError(response, "form", "user", "This field is required.")
        self.assertFormError(response, "form", "xlink_show", "This field is required.")
        self.assertFormError(
            response, "form", "xlink_actuate", "This field is required."
        )
        self.assertFormError(response, "form", "uri_prefix", "This field is required.")
        self.assertFormError(response, "form", "repository", "This field is required.")
        self.assertFormError(
            response, "form", "restrictions", "This field is required."
        )

        self.assertIsInstance(config, dict)


class TestDipUploadAtomConfig(TestCase):
    fixtures = ["test_user"]

    def setUp(self):
        self.client.login(username="test", password="test")
        self.url = reverse("administration:dips_atom_index")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_get(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.request.get("PATH_INFO"), "/administration/dips/atom/"
        )
        self.assertTemplateUsed(response, "administration/dips_atom_edit.html")
        self.assertFalse(response.context["form"].is_valid())

    def test_post_minimum_required(self):
        response = self.client.post(
            self.url,
            {
                "url": "https://search.efimm.org",
                "email": "demo@example.com",
                "password": "demo",
                "version": 2,
            },
        )
        form = response.context["form"]
        messages = list(response.context["messages"])
        config = DashboardSetting.objects.get_dict(_ATOM_DICTNAME)

        self.assertTrue(form.is_valid())
        self.assertFalse(form.errors)

        self.assertTrue(messages)
        self.assertEqual(messages[0].message, "Saved.")
        self.assertEqual(messages[0].tags, "info")

        self.assertIsInstance(config, dict)
        self.assertEqual(config["url"], "https://search.efimm.org")
        self.assertEqual(config["email"], "demo@example.com")
        self.assertEqual(config["password"], "demo")
        self.assertEqual(config["version"], "2")
        self.assertEqual(config["key"], "")
        self.assertEqual(len(list(config.keys())), len(form.fields))

    def test_post_missing_fields(self):
        response = self.client.post(self.url, {"url": "https://search.efimm.org"})
        form = response.context["form"]
        config = DashboardSetting.objects.get_dict(_ATOM_DICTNAME)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)

        self.assertFormError(response, "form", "email", "This field is required.")
        self.assertFormError(response, "form", "password", "This field is required.")
        self.assertFormError(response, "form", "version", "This field is required.")

        self.assertIsInstance(config, dict)
