"""JSON-ready payload builders for FPR table views.

This module centralizes the Python-side formatting used by FPR list/detail views
before the payload is embedded in templates with Django's ``json_script`` and
hydrated by the Vue table components.

The helpers focus on digital preservation workflows (formats, format versions,
identification tools/commands/rules, and format policy tools/commands/rules)
while keeping the payload structure consistent across views.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from typing import TypedDict

from django.http import HttpRequest
from django.utils.text import Truncator

PayloadRow = dict[str, Any]


class ActionPayload(TypedDict):
    """UI action metadata rendered as a button/link in a table row."""

    key: str
    style: str


class CreatePayload(TypedDict, total=False):
    """Create-action metadata rendered as the toolbar button."""

    style: str
    parentUuid: str
    formatSlug: str


class ColumnPayload(TypedDict, total=False):
    """Column definition used by the frontend table component."""

    key: str
    # Optional per-view override. Generic labels come from Vue i18n.
    label: str
    sortable: bool


class TableUiPayload(TypedDict):
    """Action metadata used by the table UI shell."""

    create: CreatePayload | None


class TablePayload(TypedDict):
    """Top-level FPR table payload serialized into ``json_script``."""

    version: int
    kind: str
    columns: list[ColumnPayload]
    rows: list[PayloadRow]
    ui: TableUiPayload


def _action(key: str, style: str = "default") -> ActionPayload:
    """Build a row action descriptor for the FPR table UI."""

    return {"key": key, "style": style}


def _table_shell(
    kind: str,
    _request: HttpRequest,
    *,
    columns: list[ColumnPayload],
    rows: list[PayloadRow],
    create: CreatePayload | None = None,
) -> TablePayload:
    """Wrap FPR rows/columns in the shared table payload envelope."""

    return {
        "version": 1,
        "kind": kind,
        "columns": columns,
        "rows": rows,
        "ui": {
            "create": create,
        },
    }


def format_list_payload(request: HttpRequest, formats: Iterable[Any]) -> TablePayload:
    """Generate the formats list payload for browsing registered formats."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for format_obj in formats:
        row: PayloadRow = {
            "id": str(format_obj.uuid),
            "description": format_obj.description,
            "formatSlug": format_obj.slug,
            "groupName": format_obj.group_name or "",
            "groupSlug": (
                format_obj.group_slug
                if is_superuser and format_obj.group_slug
                else None
            ),
            "actions": [_action("view", "default")],
        }
        if is_superuser:
            row["actions"].append(_action("edit", "default"))
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
        }

    return _table_shell(
        "format-list",
        request,
        columns=[
            {"key": "description"},
            {"key": "groupName"},
            {"key": "actions", "sortable": False},
        ],
        rows=rows,
        create=create,
    )


def idcommand_list_payload(
    request: HttpRequest, idcommands: Iterable[Any]
) -> TablePayload:
    """Generate the list of identification commands used in format matching."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for command in idcommands:
        command_type = command.script_type
        if command.backend != command.Backend.LEGACY:
            command_type = command.get_script_type_display()
        row: PayloadRow = {
            "id": str(command.uuid),
            "command": command.description,
            "type": command_type,
            "tool": str(command.tool) if command.tool else "",
            "toolSlug": command.tool.slug if command.tool else None,
            "mode": command.config,
            "enabled": command.enabled,
            "actions": [_action("view", "default")],
        }
        if is_superuser:
            row["actions"].append(_action("replace", "default"))
            row["actions"].append(
                _action("disable" if command.enabled else "enable", "default")
            )
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
        }

    return _table_shell(
        "idcommand-list",
        request,
        columns=[
            {"key": "command"},
            {"key": "type"},
            {"key": "tool"},
            {"key": "mode"},
            {"key": "enabled"},
            {"key": "actions", "sortable": False},
        ],
        rows=rows,
        create=create,
    )


def fpcommand_list_payload(
    request: HttpRequest, fpcommands: Iterable[Any]
) -> TablePayload:
    """Generate the list of format policy commands used in preservation workflows."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for command in fpcommands:
        row: PayloadRow = {
            "id": str(command.uuid),
            "description": command.description,
            "usage": command.command_usage,
            "tool": command.tool.description if command.tool else "",
            "enabled": command.enabled,
            "actions": [_action("view", "default")],
        }
        if is_superuser:
            row["actions"].append(_action("replace", "default"))
            row["actions"].append(
                _action("disable" if command.enabled else "enable", "default")
            )
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
        }

    return _table_shell(
        "fpcommand-list",
        request,
        columns=[
            {"key": "description"},
            {"key": "usage"},
            {"key": "tool"},
            {"key": "enabled"},
            {"key": "actions", "sortable": False},
        ],
        rows=rows,
        create=create,
    )


def idtool_list_payload(request: HttpRequest, idtools: Iterable[Any]) -> TablePayload:
    """Generate the list of identification tools available in the registry."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for tool in idtools:
        row: PayloadRow = {
            "id": str(tool.uuid),
            "description": tool.description,
            "toolSlug": tool.slug,
            "version": tool.version or "",
            "actions": [_action("view")],
        }
        if is_superuser:
            row["actions"].append(_action("edit"))
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
        }

    return _table_shell(
        "idtool-list",
        request,
        columns=[
            {"key": "description"},
            {"key": "version"},
            {"key": "actions", "sortable": False},
        ],
        rows=rows,
        create=create,
    )


def fptool_list_payload(request: HttpRequest, fptools: Iterable[Any]) -> TablePayload:
    """Generate the list of format policy tools used for normalization tasks."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for tool in fptools:
        row: PayloadRow = {
            "id": str(tool.uuid),
            "description": tool.description,
            "toolSlug": tool.slug,
            "actions": [_action("view")],
        }
        if is_superuser:
            row["actions"].append(_action("edit"))
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
        }

    return _table_shell(
        "fptool-list",
        request,
        columns=[
            {"key": "description"},
            {"key": "actions", "sortable": False},
        ],
        rows=rows,
        create=create,
    )


def formatgroup_list_payload(
    request: HttpRequest, groups: Iterable[Any]
) -> TablePayload:
    """Generate the list of format groups used to classify preservation formats."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for group in groups:
        row: PayloadRow = {
            "id": str(group.uuid),
            "description": group.description,
            "groupSlug": group.slug if is_superuser else None,
            "actions": [],
        }
        if is_superuser:
            row["actions"] = [
                _action("edit"),
                _action("delete"),
            ]
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
        }

    columns: list[ColumnPayload] = [{"key": "description"}]
    if is_superuser:
        columns.append({"key": "actions", "sortable": False})

    return _table_shell(
        "formatgroup-list",
        request,
        columns=columns,
        rows=rows,
        create=create,
    )


def idrule_list_payload(request: HttpRequest, idrules: Iterable[Any]) -> TablePayload:
    """Generate the list of identification rules mapping outputs to formats."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for rule in idrules:
        command_tool = rule.command.tool
        row: PayloadRow = {
            "id": str(rule.uuid),
            "format": str(rule.format),
            "formatSlug": rule.format.format.slug,
            "command": rule.command.description,
            "commandUuid": str(rule.command.uuid),
            "output": rule.command_output,
            "tool": str(command_tool) if command_tool else "",
            "toolSlug": command_tool.slug if command_tool else None,
            "enabled": rule.enabled,
            "actions": [_action("view")],
        }
        if is_superuser:
            row["actions"].append(_action("replace"))
            row["actions"].append(_action("disable" if rule.enabled else "enable"))
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
        }

    return _table_shell(
        "idrule-list",
        request,
        columns=[
            {"key": "format"},
            {"key": "command"},
            {"key": "output"},
            {"key": "tool"},
            {"key": "enabled"},
            {"key": "actions", "sortable": False},
        ],
        rows=rows,
        create=create,
    )


def fprule_list_payload(request: HttpRequest, fprules: Iterable[Any]) -> TablePayload:
    """Generate the list of format policy rules for preservation actions."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for rule in fprules:
        row: PayloadRow = {
            "id": str(rule.uuid),
            "purpose": rule.purpose,
            "format": rule.format.description or "",
            "formatVersion": rule.format.version or "",
            "formatPronomId": rule.format.pronom_id or "",
            "formatSlug": rule.format.format.slug,
            "command": rule.command.description,
            "success": f"{rule.count_okay}/{rule.count_attempts}",
            "successOkay": rule.count_okay,
            "successAttempts": rule.count_attempts,
            "enabled": rule.enabled,
            "actions": [_action("view")],
        }
        if is_superuser:
            row["actions"].append(_action("replace"))
            row["actions"].append(_action("disable" if rule.enabled else "enable"))
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
        }

    return _table_shell(
        "fprule-list",
        request,
        columns=[
            {"key": "purpose"},
            {"key": "format"},
            {"key": "command"},
            {"key": "success"},
            {"key": "enabled"},
            {"key": "actions", "sortable": False},
        ],
        rows=rows,
        create=create,
    )


def format_detail_versions_payload(
    request: HttpRequest, format_obj: Any, format_versions: Iterable[Any]
) -> TablePayload:
    """Generate the format detail table listing known format versions."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for version in format_versions:
        row: PayloadRow = {
            "id": str(version.uuid),
            "description": version.description or "",
            "formatSlug": format_obj.slug,
            "versionSlug": version.slug,
            "version": version.version or "",
            "pronomId": version.pronom_id or "",
            "accessFormat": version.access_format,
            "preservationFormat": version.preservation_format,
            "enabled": version.enabled,
            "actions": [_action("view")],
        }
        if is_superuser:
            row["actions"].append(_action("replace"))
            row["actions"].append(_action("disable" if version.enabled else "enable"))
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
            "formatSlug": format_obj.slug,
        }

    return _table_shell(
        "format-detail-versions",
        request,
        columns=[
            {"key": "description"},
            {"key": "version"},
            {"key": "pronomId"},
            {"key": "accessFormat"},
            {"key": "preservationFormat"},
            {"key": "enabled"},
            {"key": "actions", "sortable": False},
        ],
        rows=rows,
        create=create,
    )


def idtool_detail_commands_payload(
    request: HttpRequest, idtool: Any, idcommands: Iterable[Any]
) -> TablePayload:
    """Generate the identification-command table shown on a tool detail page."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for command in idcommands:
        row: PayloadRow = {
            "id": str(command.uuid),
            "configuration": command.config,
            "identifier": command.description,
            "commandScript": Truncator(command.script).chars(100),
            "enabled": command.enabled,
            "actions": [_action("view")],
        }
        if is_superuser:
            row["actions"].append(_action("replace"))
            row["actions"].append(_action("disable"))
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
            "parentUuid": str(idtool.uuid),
        }

    return _table_shell(
        "idtool-detail-commands",
        request,
        columns=[
            {"key": "configuration"},
            {"key": "identifier"},
            {"key": "commandScript"},
            {"key": "enabled"},
            {"key": "actions", "sortable": False},
        ],
        rows=rows,
        create=create,
    )


def fptool_detail_commands_payload(
    request: HttpRequest, fptool: Any, fpcommands: Iterable[Any]
) -> TablePayload:
    """Generate the format policy command table shown on a tool detail page."""

    is_superuser = request.user.is_superuser
    rows: list[PayloadRow] = []
    for command in fpcommands:
        row: PayloadRow = {
            "id": str(command.uuid),
            "command": command.description,
            "uuid": str(command.uuid),
            "enabled": command.enabled,
            "actions": [],
        }
        if is_superuser:
            row["actions"] = [_action("replace")]
        rows.append(row)

    create: CreatePayload | None = None
    if is_superuser:
        create = {
            "style": "primary",
            "parentUuid": str(fptool.uuid),
        }

    columns: list[ColumnPayload] = [
        {"key": "command"},
        {"key": "uuid"},
        {"key": "enabled"},
    ]
    if is_superuser:
        columns.append({"key": "actions", "sortable": False})

    return _table_shell(
        "fptool-detail-commands",
        request,
        columns=columns,
        rows=rows,
        create=create,
    )


def formatgroup_form_formats_payload(
    request: HttpRequest, group_formats: Iterable[Any]
) -> TablePayload:
    """Generate the format membership table shown while editing a format group."""

    rows: list[PayloadRow] = []
    for format_obj in group_formats:
        rows.append(
            {
                "id": str(format_obj.uuid),
                "description": format_obj.description,
                "formatSlug": format_obj.slug,
                "actions": [_action("edit")],
            }
        )

    return _table_shell(
        "formatgroup-form-formats",
        request,
        columns=[
            {"key": "description"},
            {"key": "actions", "sortable": False},
        ],
        rows=rows,
        create={
            "style": "primary",
        },
    )
