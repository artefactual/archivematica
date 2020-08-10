# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from components import helpers
from fpr.models import FPTool, IDTool, FPCommand


class TestViews(TestCase):
    def setUp(self):
        user = User.objects.create_superuser("demo", "demo@example.com", "demo")
        self.client.login(username=user.username, password="demo")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_idcommand_create(self):
        url = reverse("fpr:idcommand_create")
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
        url = reverse("fpr:fpcommand_create")
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

    def test_fpcommand_delete(self):
        fpcommand_id = "0fd7935a-ed0d-4f67-aa25-1b44684f6aca"
        url = reverse("fpr:fpcommand_delete", args=[fpcommand_id])

        self.assertEqual(FPCommand.active.filter(uuid=fpcommand_id).exists(), True)

        resp = self.client.post(url, follow=True, data={"disable": True})

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(FPCommand.active.filter(uuid=fpcommand_id).exists(), False)
