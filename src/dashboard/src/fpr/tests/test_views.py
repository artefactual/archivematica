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

    def test_fpcommand_edit(self):
        fpcommand_id = "41112047-7ddf-4bf0-9156-39fe96b32d53"
        url = reverse("fpr:fpcommand_edit", args=[fpcommand_id])

        fpcommand = FPCommand.active.get(uuid=fpcommand_id)
        self.assertEqual(fpcommand.description, "Copying file to access directory")

        form_data = {
            u"verification_command": [u"ef3ea000-0c3c-4cae-adc2-aa2a6ccbffce"],
            u"description": [u"new description"],
            u"tool": [u"0efc346e-6373-4799-819d-17cc0f21f827"],
            u"event_detail_command": [u""],
            u"output_location": [
                u"%outputDirectory%%prefix%%fileName%%postfix%%fileExtensionWithDot%"
            ],
            u"command_usage": [u"normalization"],
            u"command": [
                u'cp -R "%inputFile%" "%outputDirectory%%prefix%%fileName%%postfix%%fileExtensionWithDot%"'
            ],
            u"csrfmiddlewaretoken": [
                u"k5UUufiJuSOLNOGJYlU2ODow5iKPhOuLc9Q0EmUoIXsQLZ7r5Ede7Pf0pSQEm0lP"
            ],
            u"output_format": [u"0ab4cd40-90e7-4d75-b294-498177b3897d"],
            u"script_type": [u"command"],
        }
        resp = self.client.post(url, follow=True, data=form_data)
        self.assertEqual(resp.status_code, 200)

        # Our fpcommand is now expected to be disabled.
        fpcommand = FPCommand.objects.get(uuid=fpcommand_id)
        self.assertEqual(fpcommand.enabled, False)

        # And replaced by a new fpcommand.
        fpcommand = FPCommand.active.get(replaces_id=fpcommand_id)
        self.assertEqual(fpcommand.description, "new description")

    def test_fpcommand_delete(self):
        fpcommand_id = "0fd7935a-ed0d-4f67-aa25-1b44684f6aca"
        url = reverse("fpr:fpcommand_delete", args=[fpcommand_id])

        self.assertEqual(FPCommand.active.filter(uuid=fpcommand_id).exists(), True)

        resp = self.client.post(url, follow=True, data={"disable": True})

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(FPCommand.active.filter(uuid=fpcommand_id).exists(), False)

    def test_fpcommand_revisions(self):
        fpcommand_id = "11036e14-78d9-4449-8360-e2da394279ad"
        url = reverse("fpr:revision_list", args=["fpcommand", fpcommand_id])
        fpcommand = FPCommand.active.get(uuid=fpcommand_id)

        resp = self.client.get(url, follow=True)

        # Assert that the revision list shows multiple instances.
        self.assertContains(resp, fpcommand.uuid)
        self.assertContains(resp, fpcommand.replaces_id)
