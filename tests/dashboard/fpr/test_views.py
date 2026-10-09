import uuid
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from archivematica.dashboard.fpr import models


def _assert_fpr_table_payload(
    response: Any, *, kind: str, script_id: str, row: dict[str, object]
) -> None:
    """Check the table payload of the response, including the row of the
    fixture, whose expected values are compared all at once.
    """
    payload = response.context["fpr_table_payload"]

    assert response.status_code == 200
    assert payload["version"] == 1
    assert payload["kind"] == kind
    assert "permissions" not in payload
    if payload["ui"]["create"] is not None:
        assert "url" not in payload["ui"]["create"]
    for actual in payload["rows"]:
        for action in actual.get("actions", []):
            assert "url" not in action
    assert f'id="{script_id}"' in response.content.decode()
    (actual,) = [actual for actual in payload["rows"] if actual["id"] == row["id"]]
    assert {key: actual[key] for key in row} == row


@pytest.fixture
def format_group(format_group: models.FormatGroup) -> models.FormatGroup:
    format_group.description = "Video"
    format_group.save()

    return format_group


@pytest.fixture
def format(format: models.Format) -> models.Format:
    format.description = "Matroska"
    format.save()

    return format


@pytest.fixture
def format_version(format_version: models.FormatVersion) -> models.FormatVersion:
    format_version.description = "Matroska v4"
    format_version.version = "4"
    format_version.pronom_id = "fmt/569"
    format_version.save()

    return format_version


@pytest.fixture
def fptool(fptool: models.FPTool) -> models.FPTool:
    fptool.description = "FFmpeg"
    fptool.version = "6.0"
    fptool.save()

    return fptool


@pytest.fixture
def fpcommand(fpcommand: models.FPCommand) -> models.FPCommand:
    fpcommand.description = "Transcode to access copy"
    fpcommand.command_usage = "normalization"
    fpcommand.save()

    return fpcommand


@pytest.fixture
def idtool(idtool: models.IDTool) -> models.IDTool:
    idtool.description = "Siegfried"
    idtool.version = "1.11.2"
    idtool.save()

    return idtool


@pytest.fixture
def idcommand(idcommand: models.IDCommand) -> models.IDCommand:
    idcommand.description = "Siegfried command"
    idcommand.save()

    return idcommand


@pytest.fixture
def idrule(idrule: models.IDRule) -> models.IDRule:
    idrule.command_output = "fmt/569"
    idrule.save()

    return idrule


@pytest.mark.django_db
def test_idcommand_create(
    dashboard_uuid: uuid.UUID, admin_client: Client, idtool: models.IDTool
) -> None:
    url = reverse("fpr:idcommand_create")

    resp = admin_client.get(url)
    assert resp.context["form"].initial["tool"] is None

    resp = admin_client.get(url, {"parent": str(uuid.uuid4())})
    assert resp.context["form"].initial["tool"] is None

    resp = admin_client.get(url, {"parent": str(idtool.uuid)})
    assert resp.context["form"].initial["tool"] == idtool


@pytest.mark.django_db
def test_fpcommand_create(
    dashboard_uuid: uuid.UUID, admin_client: Client, fptool: models.FPTool
) -> None:
    url = reverse("fpr:fpcommand_create")

    resp = admin_client.get(url)
    assert resp.context["form"].initial["tool"] is None

    resp = admin_client.get(url, {"parent": str(uuid.uuid4())})
    assert resp.context["form"].initial["tool"] is None

    resp = admin_client.get(url, {"parent": str(fptool.uuid)})
    assert resp.context["form"].initial["tool"] == fptool


@pytest.mark.django_db
def test_fpcommand_edit(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    fptool: models.FPTool,
    format_version: models.FormatVersion,
) -> None:
    verification_command = models.FPCommand.objects.create(
        command_usage="verification", tool=fptool
    )
    command = models.FPCommand.objects.create(
        description="Copying file to access directory",
        enabled=True,
        command_usage="normalization",
        tool=fptool,
        output_format=format_version,
    )

    fpcommand_id = str(command.uuid)
    url = reverse("fpr:fpcommand_edit", args=[fpcommand_id])

    fpcommand = models.FPCommand.active.get(uuid=fpcommand_id)
    assert fpcommand.description == "Copying file to access directory"

    form_data = {
        "verification_command": [str(verification_command.uuid)],
        "description": ["new description"],
        "tool": [str(fptool.uuid)],
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
    fpcommand = models.FPCommand.active.get(replaces=fpcommand)
    assert fpcommand.description == "new description"


@pytest.mark.django_db
def test_fpcommand_delete(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    fptool: models.FPTool,
    format_version: models.FormatVersion,
) -> None:
    command = models.FPCommand.objects.create(
        enabled=True,
        command_usage="normalization",
        tool=fptool,
        output_format=format_version,
    )

    fpcommand_id = str(command.uuid)
    url = reverse("fpr:fpcommand_delete", args=[fpcommand_id])

    assert models.FPCommand.active.filter(uuid=fpcommand_id).exists()

    resp = admin_client.post(url, follow=True, data={"disable": True})

    assert resp.status_code == 200
    assert not models.FPCommand.active.filter(uuid=fpcommand_id).exists()


@pytest.mark.django_db
def test_fpcommand_revisions(
    dashboard_uuid: uuid.UUID, admin_client: Client, fpcommand: models.FPCommand
) -> None:
    new_command = models.FPCommand.objects.create(
        description="new command", replaces=fpcommand, tool=fpcommand.tool
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
def test_idrule_create(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    format_version: models.FormatVersion,
    idcommand: models.IDCommand,
) -> None:
    url = reverse("fpr:idrule_create")

    resp = admin_client.get(url)

    assert resp.context["form"].initial == {}
    assert "Create identification rule" in resp.content.decode()

    command_output = ".ppt"

    resp = admin_client.post(
        url,
        {
            "format": format_version.uuid,
            "command": idcommand.uuid,
            "command_output": command_output,
        },
        follow=True,
    )

    assert "Saved." in resp.content.decode()
    assert (
        models.IDRule.objects.filter(
            format=format_version, command=idcommand, command_output=command_output
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_fprule_create(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    format_version: models.FormatVersion,
    fpcommand: models.FPCommand,
) -> None:
    url = reverse("fpr:fprule_create")

    resp = admin_client.get(url)

    assert resp.context["form"].initial == {}
    assert "Create format policy rule" in resp.content.decode()

    purpose = models.FPRule.CHARACTERIZATION

    resp = admin_client.post(
        url,
        {
            "f-purpose": purpose,
            "f-format": format_version.uuid,
            "f-command": fpcommand.uuid,
        },
        follow=True,
    )

    assert "Saved." in resp.content.decode()
    assert (
        models.FPRule.objects.filter(
            purpose=purpose, format=format_version, command=fpcommand
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_format_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client, format: models.Format
) -> None:
    response = admin_client.get(reverse("fpr:format_list"))

    _assert_fpr_table_payload(
        response,
        kind="format-list",
        script_id="fpr-format-list-payload",
        row={
            "id": str(format.uuid),
            "description": "Matroska",
            "formatSlug": format.slug,
            "groupName": "Video",
        },
    )


@pytest.mark.django_db
def test_format_detail_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    format: models.Format,
    format_version: models.FormatVersion,
) -> None:
    response = admin_client.get(reverse("fpr:format_detail", args=[format.slug]))

    _assert_fpr_table_payload(
        response,
        kind="format-detail-versions",
        script_id="fpr-format-detail-versions-payload",
        row={
            "id": str(format_version.uuid),
            "description": "Matroska v4",
            "version": "4",
            "pronomId": "fmt/569",
            "enabled": True,
        },
    )


@pytest.mark.django_db
def test_formatgroup_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client, format_group: models.FormatGroup
) -> None:
    response = admin_client.get(reverse("fpr:formatgroup_list"))

    _assert_fpr_table_payload(
        response,
        kind="formatgroup-list",
        script_id="fpr-formatgroup-list-payload",
        row={"id": str(format_group.uuid), "description": "Video"},
    )


@pytest.mark.django_db
def test_formatgroup_edit_includes_fpr_table_payload_for_group_formats(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    format_group: models.FormatGroup,
    format: models.Format,
) -> None:
    response = admin_client.get(
        reverse("fpr:formatgroup_edit", args=[format_group.slug])
    )

    _assert_fpr_table_payload(
        response,
        kind="formatgroup-form-formats",
        script_id="fpr-formatgroup-form-formats-payload",
        row={
            "id": str(format.uuid),
            "description": "Matroska",
            "formatSlug": format.slug,
        },
    )


@pytest.mark.django_db
def test_idtool_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client, idtool: models.IDTool
) -> None:
    response = admin_client.get(reverse("fpr:idtool_list"))

    _assert_fpr_table_payload(
        response,
        kind="idtool-list",
        script_id="fpr-idtool-list-payload",
        row={
            "id": str(idtool.uuid),
            "description": "Siegfried",
            "version": "1.11.2",
            "toolSlug": idtool.slug,
        },
    )


@pytest.mark.django_db
def test_idtool_detail_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    idtool: models.IDTool,
    idcommand: models.IDCommand,
) -> None:
    response = admin_client.get(reverse("fpr:idtool_detail", args=[idtool.slug]))

    _assert_fpr_table_payload(
        response,
        kind="idtool-detail-commands",
        script_id="fpr-idtool-detail-commands-payload",
        row={
            "id": str(idcommand.uuid),
            "identifier": "Siegfried command",
            "configuration": "PUID",
            "enabled": True,
        },
    )


@pytest.mark.django_db
def test_idrule_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    monkeypatch: pytest.MonkeyPatch,
    idtool: models.IDTool,
    idrule: models.IDRule,
) -> None:
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
        response,
        kind="idrule-list",
        script_id="fpr-idrule-list-payload",
        row={
            "id": str(idrule.uuid),
            "command": "Siegfried command",
            "output": "fmt/569",
            "toolSlug": idtool.slug,
            "enabled": True,
        },
    )
    assert observed_select_related_args == ("format__format__group", "command__tool")


@pytest.mark.django_db
def test_idrule_list_handles_rules_without_tool(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    format_version: models.FormatVersion,
) -> None:
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
        response,
        kind="idrule-list",
        script_id="fpr-idrule-list-payload",
        row={
            "id": str(idrule.uuid),
            "command": "Rule command without tool",
            "output": "fmt/126",
            "tool": "",
            "toolSlug": None,
        },
    )


@pytest.mark.django_db
def test_idcommand_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    idtool: models.IDTool,
    idcommand: models.IDCommand,
) -> None:
    response = admin_client.get(reverse("fpr:idcommand_list"))

    _assert_fpr_table_payload(
        response,
        kind="idcommand-list",
        script_id="fpr-idcommand-list-payload",
        row={
            "id": str(idcommand.uuid),
            "command": "Siegfried command",
            "mode": "PUID",
            "toolSlug": idtool.slug,
            "enabled": True,
        },
    )


@pytest.mark.django_db
def test_fprule_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    fprule_characterization: models.FPRule,
) -> None:
    response = admin_client.get(reverse("fpr:fprule_list"))

    _assert_fpr_table_payload(
        response,
        kind="fprule-list",
        script_id="fpr-fprule-list-payload",
        row={
            "id": str(fprule_characterization.uuid),
            "purpose": "characterization",
            "format": "Matroska v4",
            "formatVersion": "4",
            "formatPronomId": "fmt/569",
            "command": "Transcode to access copy",
            "success": "0/0",
            "enabled": True,
        },
    )


@pytest.mark.django_db
def test_fptool_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client, fptool: models.FPTool
) -> None:
    response = admin_client.get(reverse("fpr:fptool_list"))

    _assert_fpr_table_payload(
        response,
        kind="fptool-list",
        script_id="fpr-fptool-list-payload",
        row={"id": str(fptool.uuid), "description": "FFmpeg", "toolSlug": fptool.slug},
    )


@pytest.mark.django_db
def test_fptool_detail_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    fptool: models.FPTool,
    fpcommand: models.FPCommand,
) -> None:
    response = admin_client.get(reverse("fpr:fptool_detail", args=[fptool.slug]))

    _assert_fpr_table_payload(
        response,
        kind="fptool-detail-commands",
        script_id="fpr-fptool-detail-commands-payload",
        row={
            "id": str(fpcommand.uuid),
            "command": "Transcode to access copy",
            "enabled": True,
        },
    )


@pytest.mark.django_db
def test_fpcommand_list_includes_fpr_table_payload(
    dashboard_uuid: uuid.UUID, admin_client: Client, fpcommand: models.FPCommand
) -> None:
    response = admin_client.get(reverse("fpr:fpcommand_list"))

    _assert_fpr_table_payload(
        response,
        kind="fpcommand-list",
        script_id="fpr-fpcommand-list-payload",
        row={
            "id": str(fpcommand.uuid),
            "description": "Transcode to access copy",
            "usage": "normalization",
            "tool": "FFmpeg",
            "enabled": True,
        },
    )
