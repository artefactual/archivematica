import uuid
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from archivematica.dashboard.fpr import models


def _assert_fpr_table_payload(response: Any, *, kind: str, script_id: str) -> None:
    payload = response.context["fpr_table_payload"]

    assert response.status_code == 200
    assert payload["version"] == 1
    assert payload["kind"] == kind
    assert "permissions" not in payload
    if payload["ui"]["create"] is not None:
        assert "url" not in payload["ui"]["create"]
    for row in payload["rows"]:
        for action in row.get("actions", []):
            assert "url" not in action
    assert f'id="{script_id}"' in response.content.decode()


def _create_format_version(
    *,
    group_description: str = "Group",
    format_description: str = "Format",
    version_description: str = "Format version",
) -> models.FormatVersion:
    return models.FormatVersion.objects.create(
        format=models.Format.objects.create(
            group=models.FormatGroup.objects.create(description=group_description),
            description=format_description,
        ),
        description=version_description,
    )


@pytest.mark.django_db
def test_idcommand_create(dashboard_uuid: uuid.UUID, admin_client: Client) -> None:
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

    resp = admin_client.get(url, {"parent": str(tool.uuid)})
    assert resp.context["form"].initial["tool"] == tool


@pytest.mark.django_db
def test_fpcommand_create(dashboard_uuid: uuid.UUID, admin_client: Client) -> None:
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

    resp = admin_client.get(url, {"parent": str(tool.uuid)})
    assert resp.context["form"].initial["tool"] == tool


@pytest.mark.django_db
def test_fpcommand_edit(dashboard_uuid: uuid.UUID, admin_client: Client) -> None:
    tool = models.FPTool.objects.create()
    verification_command = models.FPCommand.objects.create(
        command_usage="verification", tool=tool
    )
    format_version = models.FormatVersion.objects.create(
        format=models.Format.objects.create(group=models.FormatGroup.objects.create())
    )
    command = models.FPCommand.objects.create(
        description="Copying file to access directory",
        enabled=True,
        command_usage="normalization",
        tool=tool,
        output_format=format_version,
    )

    fpcommand_id = str(command.uuid)
    url = reverse("fpr:fpcommand_edit", args=[fpcommand_id])

    fpcommand = models.FPCommand.active.get(uuid=fpcommand_id)
    assert fpcommand.description == "Copying file to access directory"

    form_data = {
        "verification_command": [str(verification_command.uuid)],
        "description": ["new description"],
        "tool": [str(tool.uuid)],
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
        "output_format": [str(format_version.uuid)],
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
def test_fpcommand_delete(dashboard_uuid: uuid.UUID, admin_client: Client) -> None:
    command = models.FPCommand.objects.create(
        enabled=True,
        command_usage="normalization",
        tool=models.FPTool.objects.create(),
        output_format=models.FormatVersion.objects.create(
            format=models.Format.objects.create(
                group=models.FormatGroup.objects.create()
            )
        ),
    )

    fpcommand_id = str(command.uuid)
    url = reverse("fpr:fpcommand_delete", args=[fpcommand_id])

    assert models.FPCommand.active.filter(uuid=fpcommand_id).exists()

    resp = admin_client.post(url, follow=True, data={"disable": True})

    assert resp.status_code == 200
    assert not models.FPCommand.active.filter(uuid=fpcommand_id).exists()


@pytest.mark.django_db
def test_fpcommand_revisions(dashboard_uuid: uuid.UUID, admin_client: Client) -> None:
    initial_command = models.FPCommand.objects.create(
        description="initial command", tool=models.FPTool.objects.create()
    )
    new_command = models.FPCommand.objects.create(
        description="new command", replaces=initial_command, tool=initial_command.tool
    )

    fpcommand_id = str(new_command.uuid)
    url = reverse("fpr:revision_list", args=["fpcommand", fpcommand_id])
    fpcommand = models.FPCommand.active.get(uuid=fpcommand_id)

    resp = admin_client.get(url, follow=True)

    # Assert that the revision list shows multiple instances.
    content = resp.content.decode()
    assert str(fpcommand.uuid) in content
    assert str(fpcommand.replaces_id) in content


@pytest.mark.django_db
def test_format_create_creates_format(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    # Add a new format to the Unknown group.
    unknown_group, _ = models.FormatGroup.objects.get_or_create(description="Unknown")
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
def test_format_edit_updates_format(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    # Get details of the Matroska format from the Video group.
    video_group, _ = models.FormatGroup.objects.get_or_create(description="Video")
    format, _ = models.Format.objects.get_or_create(
        description="Matroska", group=video_group
    )
    format_uuid = format.uuid
    format_slug = format.slug

    # Update the group and description of the Matroska format.
    unknown_group, _ = models.FormatGroup.objects.get_or_create(description="Unknown")
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
def test_idrule_create(dashboard_uuid: uuid.UUID, admin_client: Client) -> None:
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
            format=format_version, command=command, command_output=command_output
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_fprule_create(dashboard_uuid: uuid.UUID, admin_client: Client) -> None:
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
            purpose=purpose, format=format_version, command=command
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_format_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    group = models.FormatGroup.objects.create(description="Text")
    models.Format.objects.create(description="Plain text", group=group)

    response = admin_client.get(reverse("fpr:format_list"))

    _assert_fpr_table_payload(
        response, kind="format-list", script_id="fpr-format-list-payload"
    )


@pytest.mark.django_db
def test_format_detail_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    format_obj = models.Format.objects.create(
        description="TIFF",
        group=models.FormatGroup.objects.create(description="Image"),
    )
    models.FormatVersion.objects.create(
        format=format_obj,
        description="TIFF 6.0",
        pronom_id="fmt/353",
    )

    response = admin_client.get(reverse("fpr:format_detail", args=[format_obj.slug]))

    _assert_fpr_table_payload(
        response,
        kind="format-detail-versions",
        script_id="fpr-format-detail-versions-payload",
    )


@pytest.mark.django_db
def test_formatgroup_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    models.FormatGroup.objects.create(description="Audio")

    response = admin_client.get(reverse("fpr:formatgroup_list"))

    _assert_fpr_table_payload(
        response, kind="formatgroup-list", script_id="fpr-formatgroup-list-payload"
    )


@pytest.mark.django_db
def test_formatgroup_edit_includes_fpr_table_payload_for_group_formats(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    group = models.FormatGroup.objects.create(description="Documents")
    models.Format.objects.create(description="PDF", group=group)

    response = admin_client.get(reverse("fpr:formatgroup_edit", args=[group.slug]))

    _assert_fpr_table_payload(
        response,
        kind="formatgroup-form-formats",
        script_id="fpr-formatgroup-form-formats-payload",
    )


@pytest.mark.django_db
def test_idtool_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    models.IDTool.objects.create(description="Siegfried", version="1.11.2")

    response = admin_client.get(reverse("fpr:idtool_list"))

    _assert_fpr_table_payload(
        response, kind="idtool-list", script_id="fpr-idtool-list-payload"
    )


@pytest.mark.django_db
def test_idtool_detail_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    idtool = models.IDTool.objects.create(description="DROID", version="6.7")
    models.IDCommand.objects.create(tool=idtool)

    response = admin_client.get(reverse("fpr:idtool_detail", args=[idtool.slug]))

    _assert_fpr_table_payload(
        response,
        kind="idtool-detail-commands",
        script_id="fpr-idtool-detail-commands-payload",
    )


@pytest.mark.django_db
def test_idrule_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    format_version = _create_format_version(
        group_description="Presentation",
        format_description="PowerPoint",
        version_description="PowerPoint 97-2003",
    )
    idtool = models.IDTool.objects.create(description="DROID", version="6.7")
    idcommand = models.IDCommand.objects.create(tool=idtool, description="DROID PUID")
    idrule = models.IDRule.objects.create(
        format=format_version,
        command=idcommand,
        command_output="fmt/126",
    )

    class _ReplacingRulesQuerySet:
        def values_list(self, *args: Any, **kwargs: Any) -> list[str]:
            return []

    observed_select_related_args: tuple[str, ...] | None = None

    class _IDRulesQuerySet(list[models.IDRule]):
        def select_related(self, *args: str) -> "_IDRulesQuerySet":
            nonlocal observed_select_related_args
            observed_select_related_args = args
            return self

    class _IDRuleManager:
        def filter(self, **kwargs: Any) -> _ReplacingRulesQuerySet:
            return _ReplacingRulesQuerySet()

        def exclude(self, **kwargs: Any) -> _IDRulesQuerySet:
            return _IDRulesQuerySet([idrule])

    monkeypatch.setattr(models.IDRule, "objects", _IDRuleManager())

    response = admin_client.get(reverse("fpr:idrule_list"))

    _assert_fpr_table_payload(
        response, kind="idrule-list", script_id="fpr-idrule-list-payload"
    )
    assert observed_select_related_args == ("format__format__group", "command__tool")


@pytest.mark.django_db
def test_idrule_list_handles_rules_without_tool(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    format_version = _create_format_version(
        group_description="Presentation",
        format_description="PowerPoint",
        version_description="PowerPoint 97-2003",
    )
    idcommand = models.IDCommand.objects.create(
        description="Rule command without tool",
        tool=None,
    )
    idrule = models.IDRule.objects.create(
        format=format_version,
        command=idcommand,
        command_output="fmt/126",
    )

    response = admin_client.get(reverse("fpr:idrule_list"))

    _assert_fpr_table_payload(
        response, kind="idrule-list", script_id="fpr-idrule-list-payload"
    )
    payload = response.context["fpr_table_payload"]
    row = next(row for row in payload["rows"] if row["id"] == str(idrule.uuid))
    assert row["tool"] == ""
    assert row["toolSlug"] is None


@pytest.mark.django_db
def test_idcommand_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    idtool = models.IDTool.objects.create(description="Siegfried", version="1.11.2")
    models.IDCommand.objects.create(tool=idtool, description="Siegfried command")

    response = admin_client.get(reverse("fpr:idcommand_list"))

    _assert_fpr_table_payload(
        response, kind="idcommand-list", script_id="fpr-idcommand-list-payload"
    )


@pytest.mark.django_db
def test_fprule_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    format_version = _create_format_version(
        group_description="Video",
        format_description="Matroska",
        version_description="Matroska v4",
    )
    fptool = models.FPTool.objects.create(description="FFmpeg", version="6.0")
    fpcommand = models.FPCommand.objects.create(
        tool=fptool,
        description="Transcode to access copy",
        command_usage="normalization",
    )
    models.FPRule.objects.create(
        purpose=models.FPRule.CHARACTERIZATION,
        format=format_version,
        command=fpcommand,
    )

    response = admin_client.get(reverse("fpr:fprule_list"))

    _assert_fpr_table_payload(
        response, kind="fprule-list", script_id="fpr-fprule-list-payload"
    )


@pytest.mark.django_db
def test_fptool_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    models.FPTool.objects.create(description="ImageMagick", version="7.1.1")

    response = admin_client.get(reverse("fpr:fptool_list"))

    _assert_fpr_table_payload(
        response, kind="fptool-list", script_id="fpr-fptool-list-payload"
    )


@pytest.mark.django_db
def test_fptool_detail_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    fptool = models.FPTool.objects.create(description="FFmpeg", version="6.0")
    models.FPCommand.objects.create(tool=fptool, command_usage="normalization")

    response = admin_client.get(reverse("fpr:fptool_detail", args=[fptool.slug]))

    _assert_fpr_table_payload(
        response,
        kind="fptool-detail-commands",
        script_id="fpr-fptool-detail-commands-payload",
    )


@pytest.mark.django_db
def test_fpcommand_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client
) -> None:
    fptool = models.FPTool.objects.create(description="FFmpeg", version="6.0")
    models.FPCommand.objects.create(
        tool=fptool,
        description="Normalize",
        command_usage="normalization",
    )

    response = admin_client.get(reverse("fpr:fpcommand_list"))

    _assert_fpr_table_payload(
        response, kind="fpcommand-list", script_id="fpr-fpcommand-list-payload"
    )
