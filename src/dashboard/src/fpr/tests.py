from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from fpr.forms import FPRuleForm, IDToolForm
from fpr.models import (
    Format,
    FormatGroup,
    FormatVersion,
    FPCommand,
    FPRule,
    FPTool,
    IDCommand,
    IDTool,
)
from fpr.utils import get_revision_descendants


class TestUtils(TestCase):
    def test_get_revision_descendants(self):
        cmd1 = IDCommand.objects.create(uuid="37f3bd7c-bb24-4899-b7c4-785ff1c764ac")
        cmd2 = IDCommand(description="Foobar")
        cmd2.save(replacing=cmd1)

        descendants = get_revision_descendants(IDCommand, cmd1.uuid, [123])
        self.assertEqual(descendants, [123, cmd2])

        with self.assertRaises(IDCommand.DoesNotExist):
            descendants = get_revision_descendants(IDCommand, "12345", [])


class TestViews(TestCase):
    def setUp(self):
        user = User.objects.create_superuser("demo", "demo@example.com", "demo")
        self.client.login(username=user.username, password="demo")

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


class TestForms(TestCase):
    def test_IDToolForm(self):
        data = {"description": "Foobar", "version": "v1.2.3"}

        form = IDToolForm(data)
        self.assertTrue(form.is_valid())
        form.save()

        # Our second attempt should not validate.
        form = IDToolForm(data)
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.non_field_errors(),
            ["An ID tool with this description and version already exists"],
        )

    def test_FPRuleForm(self):
        fprule = self.create_fprule()
        form = FPRuleForm(
            {
                "purpose": fprule.purpose,
                "format": fprule.format.uuid,
                "command": fprule.command.uuid,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.non_field_errors(),
            [
                "An identical FP rule already exists."
                " See rule {}.".format(fprule.uuid)
            ],
        )

    @staticmethod
    def create_fprule():
        fmt_group = FormatGroup.objects.create(description="My group")
        fmt = Format.objects.create(
            uuid="b99dcf12-f28a-4aa3-8fc7-8a6fc2c67b61",
            description="My format",
            group=fmt_group,
        )
        fmt_version = FormatVersion.objects.create(
            uuid="1f628739-d670-487e-9658-8229837e4d2b",
            format=fmt,
            version="v1.2.3",
            description="My format version",
        )
        cmd = FPCommand.objects.create(uuid="223a24cd-6697-4361-b8e7-72d081319a84")
        return FPRule.objects.create(
            uuid="37f3bd7c-bb24-4899-b7c4-785ff1c764ac",
            purpose="validation",
            format=fmt_version,
            command=cmd,
        )
