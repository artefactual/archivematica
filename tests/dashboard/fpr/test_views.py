import uuid

import pytest
from components import helpers
from django.test import Client
from django.urls import reverse
from fpr import models


@pytest.fixture
def dashboard_uuid() -> None:
    helpers.set_setting("dashboard_uuid", str(uuid.uuid4()))


@pytest.mark.django_db
def test_idcommand_create(dashboard_uuid: None, admin_client: Client) -> None:
    url = reverse("fpr:idcommand_create")
    tool = models.IDTool.objects.create(
        uuid="37f3bd7c-bb24-4899-b7c4-785ff1c764ac",
        description="Foobar",
        version="v1.2.3",
    )

    resp = admin_client.get(url)
    assert resp.context["form"].initial["tool"] is None

    resp = admin_client.get(url, {"parent": str(uuid.uuid4())})
    assert resp.context["form"].initial["tool"] is None

    resp = admin_client.get(url, {"parent": tool.uuid})
    assert resp.context["form"].initial["tool"] == tool


@pytest.mark.django_db
def test_fpcommand_create(dashboard_uuid: None, admin_client: Client) -> None:
    url = reverse("fpr:fpcommand_create")
    tool = models.FPTool.objects.create(
        uuid="37f3bd7c-bb24-4899-b7c4-785ff1c764ac",
        description="Foobar",
        version="v1.2.3",
    )

    resp = admin_client.get(url)
    assert resp.context["form"].initial["tool"] is None

    resp = admin_client.get(url, {"parent": str(uuid.uuid4())})
    assert resp.context["form"].initial["tool"] is None

    resp = admin_client.get(url, {"parent": tool.uuid})
    assert resp.context["form"].initial["tool"] == tool


@pytest.mark.django_db
def test_fpcommand_edit(dashboard_uuid: None, admin_client: Client) -> None:
    fpcommand_id = "41112047-7ddf-4bf0-9156-39fe96b32d53"
    url = reverse("fpr:fpcommand_edit", args=[fpcommand_id])

    fpcommand = models.FPCommand.active.get(uuid=fpcommand_id)
    assert fpcommand.description == "Copying file to access directory"

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
    resp = admin_client.post(url, follow=True, data=form_data)
    assert resp.status_code == 200

    # Our fpcommand is now expected to be disabled.
    fpcommand = models.FPCommand.objects.get(uuid=fpcommand_id)
    assert not fpcommand.enabled

    # And replaced by a new fpcommand.
    fpcommand = models.FPCommand.active.get(replaces_id=fpcommand_id)
    assert fpcommand.description == "new description"


@pytest.mark.django_db
def test_fpcommand_delete(dashboard_uuid: None, admin_client: Client) -> None:
    fpcommand_id = "0fd7935a-ed0d-4f67-aa25-1b44684f6aca"
    url = reverse("fpr:fpcommand_delete", args=[fpcommand_id])

    assert models.FPCommand.active.filter(uuid=fpcommand_id).exists()

    resp = admin_client.post(url, follow=True, data={"disable": True})

    assert resp.status_code == 200
    assert not models.FPCommand.active.filter(uuid=fpcommand_id).exists()


@pytest.mark.django_db
def test_fpcommand_revisions(dashboard_uuid: None, admin_client: Client) -> None:
    fpcommand_id = "cb335c49-e6ce-445f-a774-494a6f2300c6"
    url = reverse("fpr:revision_list", args=["fpcommand", fpcommand_id])
    fpcommand = models.FPCommand.active.get(uuid=fpcommand_id)

    resp = admin_client.get(url, follow=True)

    # Assert that the revision list shows multiple instances.
    content = resp.content.decode()
    assert str(fpcommand.uuid) in content
    assert str(fpcommand.replaces_id) in content


@pytest.mark.django_db
def test_format_create_creates_format(
    dashboard_uuid: None, admin_client: Client
) -> None:
    # Add a new format to the Unknown group.
    unknown_group = models.FormatGroup.objects.get(description="Unknown")
    format_description = "My test format"

    assert models.Format.objects.filter(description=format_description).count() == 0

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
        models.Format.objects.filter(
            description=format_description, group=unknown_group
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_format_edit_updates_format(dashboard_uuid: None, admin_client: Client) -> None:
    # Get details of the Matroska format from the Video group.
    video_group = models.FormatGroup.objects.get(description="Video")
    format = models.Format.objects.get(description="Matroska", group=video_group)
    format_uuid = format.uuid
    format_slug = format.slug

    # Update the group and description of the Matroska format.
    unknown_group = models.FormatGroup.objects.get(description="Unknown")
    new_format_description = "My matroska format"

    assert (
        models.Format.objects.filter(
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
        models.Format.objects.filter(
            uuid=format_uuid,
            slug=format_slug,
            description=new_format_description,
            group=unknown_group,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_idrule_create(dashboard_uuid: None, admin_client: Client) -> None:
    url = reverse("fpr:idrule_create")

    resp = admin_client.get(url)

    assert resp.context["form"].initial == {}
    assert "Create identification rule" in resp.content.decode()

    format_version = models.FormatVersion.objects.create(
        format=models.Format.objects.create(
            group=models.FormatGroup.objects.create(description="Group"),
            description="Format",
        ),
        description="Format version",
    )
    command = models.IDCommand.objects.create(
        tool=models.IDTool.objects.create(description="Tool")
    )
    command_output = ".ppt"

    resp = admin_client.post(
        url,
        {
            "format": format_version.uuid,
            "command": command.uuid,
            "command_output": command_output,
        },
        follow=True,
    )

    assert "Saved." in resp.content.decode()
    assert (
        models.IDRule.objects.filter(
            format=format_version.uuid,
            command=command.uuid,
            command_output=command_output,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_fprule_create(dashboard_uuid: None, admin_client: Client) -> None:
    url = reverse("fpr:fprule_create")

    resp = admin_client.get(url)

    assert resp.context["form"].initial == {}
    assert "Create format policy rule" in resp.content.decode()

    purpose = models.FPRule.CHARACTERIZATION
    format_version = models.FormatVersion.objects.create(
        format=models.Format.objects.create(
            group=models.FormatGroup.objects.create(description="Group"),
            description="Format",
        ),
        description="Format version",
    )
    command = models.FPCommand.objects.create(
        tool=models.FPTool.objects.create(description="Tool")
    )

    resp = admin_client.post(
        url,
        {
            "f-purpose": purpose,
            "f-format": format_version.uuid,
            "f-command": command.uuid,
        },
        follow=True,
    )

    assert "Saved." in resp.content.decode()
    assert (
        models.FPRule.objects.filter(
            purpose=purpose,
            format=format_version.uuid,
            command=command.uuid,
        ).count()
        == 1
    )
