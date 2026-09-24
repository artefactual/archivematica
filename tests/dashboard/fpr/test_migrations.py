import pytest

OLD_FIDO_COMMAND_UUID = "c5fa04a8-aae6-430e-bec6-8922341348ab"
NEW_FIDO_COMMAND_UUID = "595853b2-b4b4-4d30-b989-e1109732ed1c"

OLD_SIEGFRIED_COMMAND_UUID = "3634f5e1-65ba-423f-82c2-c0ec34560e9d"
NEW_SIEGFRIED_COMMAND_UUID = "4d3cacf4-e298-47cd-a1e4-460093f1c99a"

PYGFRIED_TOOL_UUID = "851bcb6d-0304-43b7-931f-774175ac6987"
CUSTOM_PYGFRIED_TOOL_UUID = "ed920e4f-f3b1-4f9f-b172-bfa1881966fa"
PYGFRIED_COMMAND_UUID = "de2759e9-31e1-48d6-810d-41b0cb77c27c"


@pytest.mark.django_db(transaction=True)
def test_0056_keeps_scripts_only_on_legacy_commands(migrate_apps) -> None:
    """Verify that batch commands do not copy their predecessors' scripts."""

    apps = migrate_apps(("fpr", "0055_update_idtools"))
    IDCommand = apps.get_model("fpr", "IDCommand")
    IDTool = apps.get_model("fpr", "IDTool")

    tool = IDTool(
        uuid="7a8d2dbb-440d-4a2a-a452-c85d5038f50d",
        description="Identifier",
        version="1.0",
        slug="identifier-10",
    )
    tool.save_base(raw=True)
    old_fido, _ = IDCommand.objects.update_or_create(
        uuid=OLD_FIDO_COMMAND_UUID,
        defaults={
            "description": "Fido command",
            "config": "PUID",
            "script": "identify with Fido",
            "script_type": "pythonScript",
            "tool": tool,
            "enabled": False,
        },
    )
    old_siegfried, _ = IDCommand.objects.update_or_create(
        uuid=OLD_SIEGFRIED_COMMAND_UUID,
        defaults={
            "description": "Siegfried command",
            "config": "PUID",
            "script": "identify with Siegfried",
            "script_type": "pythonScript",
            "tool": tool,
            "enabled": True,
        },
    )

    apps = migrate_apps(("fpr", "0056_add_batch_idcommands"))
    IDCommand = apps.get_model("fpr", "IDCommand")

    assert IDCommand.objects.get(uuid=OLD_FIDO_COMMAND_UUID).script == old_fido.script
    assert (
        IDCommand.objects.get(uuid=OLD_SIEGFRIED_COMMAND_UUID).script
        == old_siegfried.script
    )
    assert IDCommand.objects.get(uuid=NEW_FIDO_COMMAND_UUID).script == ""
    assert IDCommand.objects.get(uuid=NEW_SIEGFRIED_COMMAND_UUID).script == ""


@pytest.mark.django_db(transaction=True)
def test_0057_reuses_custom_pygfried_tool(migrate_apps) -> None:
    """Reuse matching custom tool data and preserve it during rollback."""

    apps = migrate_apps(("fpr", "0056_add_batch_idcommands"))
    IDTool = apps.get_model("fpr", "IDTool")
    custom_tool = IDTool(
        uuid=CUSTOM_PYGFRIED_TOOL_UUID,
        description="Pygfried",
        version="0.17.0",
        slug="pygfried-0170",
        enabled=True,
    )
    custom_tool.save_base(raw=True)

    apps = migrate_apps(("fpr", "0057_add_pygfried_backend"))
    IDCommand = apps.get_model("fpr", "IDCommand")
    IDTool = apps.get_model("fpr", "IDTool")

    command = IDCommand.objects.get(uuid=PYGFRIED_COMMAND_UUID)
    assert str(command.tool_id) == CUSTOM_PYGFRIED_TOOL_UUID
    assert not IDTool.objects.filter(uuid=PYGFRIED_TOOL_UUID).exists()

    apps = migrate_apps(("fpr", "0056_add_batch_idcommands"))
    IDCommand = apps.get_model("fpr", "IDCommand")
    IDTool = apps.get_model("fpr", "IDTool")

    assert IDTool.objects.filter(uuid=CUSTOM_PYGFRIED_TOOL_UUID).exists()
    assert not IDCommand.objects.filter(uuid=PYGFRIED_COMMAND_UUID).exists()
