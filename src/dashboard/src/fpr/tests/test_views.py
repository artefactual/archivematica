# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from components import helpers
from fpr.models import FPTool, IDTool


class TestViews(TestCase):
    def setUp(self):
        user = User.objects.create_superuser("demo", "demo@example.com", "demo")
        self.client.login(username=user.username, password="demo")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_idcommand_create(self):
        url = reverse("idcommand_create")
        tool = IDTool.objects.create(
            uuid="37f3bd7c-bb24-4899-b7c4-785ff1c764ac",
            description="Foobar",
            version="v1.2.3",
        )

        resp = self.client.get(url)
        self.assertEqual(resp.context["form"].initial["tool"], None)

        resp = self.client.get(url, {"parent": 12345})
        self.assertEqual(resp.context["form"].initial["tool"], None)

        resp = self.client.get(url, {"parent": tool.uuid})
        self.assertEqual(resp.context["form"].initial["tool"], tool)

    def test_fpcommand_create(self):
        url = reverse("fpcommand_create")
        tool = FPTool.objects.create(
            uuid="37f3bd7c-bb24-4899-b7c4-785ff1c764ac",
            description="Foobar",
            version="v1.2.3",
        )

        resp = self.client.get(url)
        self.assertEqual(resp.context["form"].initial["tool"], None)

        resp = self.client.get(url, {"parent": 12345})
        self.assertEqual(resp.context["form"].initial["tool"], None)

        resp = self.client.get(url, {"parent": tool.uuid})
        self.assertEqual(resp.context["form"].initial["tool"], tool)
