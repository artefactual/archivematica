import pytest
from components import helpers
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from fpr.models import Format
from fpr.models import FormatGroup
from fpr.models import FPCommand
from fpr.models import FPTool
from fpr.models import IDTool


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

        resp = self.client.get(url, {"parent": "c80458d9-2b62-40f4-b61c-936bfb72901d"})
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

        resp = self.client.get(url, {"parent": "d993bdcf-a944-4df8-b960-1b20c14ffe68"})
        self.assertEqual(resp.context["form"].initial["tool"], None)

        resp = self.client.get(url, {"parent": tool.uuid})
        self.assertEqual(resp.context["form"].initial["tool"], tool)

    def test_fpcommand_edit(self):
        fpcommand_id = "41112047-7ddf-4bf0-9156-39fe96b32d53"
        url = reverse("fpr:fpcommand_edit", args=[fpcommand_id])

        fpcommand = FPCommand.active.get(uuid=fpcommand_id)
        self.assertEqual(fpcommand.description, "Copying file to access directory")

        form_data = {
            "verification_command": ["ef3ea000-0c3c-4cae-adc2-aa2a6ccbffce"],
            "description": ["new description"],
            "tool": ["0efc346e-6373-4799-819d-17cc0f21f827"],
            "event_detail_command": [""],
            "output_location": [
                "%outputDirectory%%prefix%%fileName%%postfix%%fileExtensionWithDot%"
            ],
            "command_usage": ["normalization"],
            "command": [
                'cp -R "%inputFile%" "%outputDirectory%%prefix%%fileName%%postfix%%fileExtensionWithDot%"'
            ],
            "csrfmiddlewaretoken": [
                "k5UUufiJuSOLNOGJYlU2ODow5iKPhOuLc9Q0EmUoIXsQLZ7r5Ede7Pf0pSQEm0lP"
            ],
            "output_format": ["0ab4cd40-90e7-4d75-b294-498177b3897d"],
            "script_type": ["command"],
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
        fpcommand_id = "cb335c49-e6ce-445f-a774-494a6f2300c6"
        url = reverse("fpr:revision_list", args=["fpcommand", fpcommand_id])
        fpcommand = FPCommand.active.get(uuid=fpcommand_id)

        resp = self.client.get(url, follow=True)

        # Assert that the revision list shows multiple instances.
        self.assertContains(resp, fpcommand.uuid)
        self.assertContains(resp, fpcommand.replaces_id)


@pytest.mark.django_db
def test_format_create_creates_format(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")
    # Add a new format to the Unknown group.
    unknown_group = FormatGroup.objects.get(description="Unknown")
    format_description = "My test format"

    assert Format.objects.filter(description=format_description).count() == 0

    response = admin_client.post(
        reverse("fpr:format_create"),
        data={"f-group": unknown_group.uuid, "f-description": format_description},
        follow=True,
    )
    assert response.status_code == 200

    content = response.content.decode()
    assert "Saved" in content
    assert "Format My test format" in content
    assert (
        Format.objects.filter(
            description=format_description, group=unknown_group
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_format_edit_updates_format(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")
    # Get details of the Matroska format from the Video group.
    video_group = FormatGroup.objects.get(description="Video")
    format = Format.objects.get(description="Matroska", group=video_group)
    format_uuid = format.uuid
    format_slug = format.slug

    # Update the group and description of the Matroska format.
    unknown_group = FormatGroup.objects.get(description="Unknown")
    new_format_description = "My matroska format"

    assert (
        Format.objects.filter(
            description=new_format_description, group=unknown_group
        ).count()
        == 0
    )

    response = admin_client.post(
        reverse("fpr:format_edit", kwargs={"slug": format_slug}),
        data={"f-group": unknown_group.uuid, "f-description": new_format_description},
        follow=True,
    )
    assert response.status_code == 200

    content = response.content.decode()
    assert "Saved" in content
    assert "Format My matroska format" in content
    assert (
        Format.objects.filter(
            uuid=format_uuid,
            slug=format_slug,
            description=new_format_description,
            group=unknown_group,
        ).count()
        == 1
    )
