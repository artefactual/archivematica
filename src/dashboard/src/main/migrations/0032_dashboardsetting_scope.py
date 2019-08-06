# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import ast

from django.db import migrations, models

from main.models import DashboardSetting, DashboardSettingManager, Job


def data_migration_atom_to_dict(apps, schema_editor):
    """
    Convert old settings into a new DashboardSetting dict, e.g. in the
    scenario where the user had the following settings in the previous form:

        +--------------------------+-----------------------+
        | name                     | value                 |
        +--------------------------+-----------------------+
        | dip_upload_atom_url      | http://localhost/atom |
        | dip_upload_atom_email    | demo@example.com      |
        | dip_upload_atom_password | demo                  |
        | dip_upload_atom_version  | 2                     |
        +--------------------------+-----------------------+

    We're going to convert them into:

        +---------------+-----------------------+-------------------+
        | name          | value                 | scope             |
        +---------------+-----------------------+-------------------+
        | url           | http://localhost/atom | upload-qubit_v0.0 |
        | version       | 2                     | upload-qubit_v0.0 |
        | password      | demo                  | upload-qubit_v0.0 |
        | email         | demo@example.com      | upload-qubit_v0.0 |
        | debug         |                       | upload-qubit_v0.0 |
        | rsync_target  |                       | upload-qubit_v0.0 |
        | rsync_command |                       | upload-qubit_v0.0 |
        | key           |                       | upload-qubit_v0.0 |
        +---------------+-----------------------+-------------------+
                                        * Blank means empty string.

    """

    old_prefix = "dip_upload_atom_"
    fields = (
        "url",
        "email",
        "password",
        "rsync_target",
        "rsync_command",
        "version",
        "debug",
        "key",
    )

    qs = apps.get_model("main", "DashboardSetting").objects.filter(
        name__in=["{}{}".format(old_prefix, field) for field in fields]
    )
    old_dict = dict(qs.values_list("name", "value"))
    new_dict = {
        field: old_dict.get("{}{}".format(old_prefix, field)) for field in fields
    }

    # Set new dict and delete previous tuples. Reminder: migrations run inside
    # a transaction.
    DashboardSetting.objects.set_dict("upload-qubit_v0.0", new_dict)
    qs.delete()


def data_migration_atom_restore_std(apps, schema_editor):
    """
    Restore StandardTaskConfig arguments (we were ovewriting) and update the
    "Upload DIP to AtoM" chains to make use of MicroServiceChoiceReplacementDic
    as we do in AS/ATK uploads.
    """
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    std = StandardTaskConfig.objects.get(execute="upload-qubit_v0.0")
    std.arguments = '--url="%url%"  --email="%email%" --password="%password%" --uuid="%SIPUUID%" --debug="%debug%" --version="%version%" --rsync-command="%rsync_command%" --rsync-target="%rsync_target%"'
    std.save()

    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    TaskConfig = apps.get_model("main", "TaskConfig")

    # New UUIDs for a new MSCL, its TaskConfig, and its exit code
    uuids = (
        "7f975ba6-2185-434c-b507-2911f3c77213",
        "a987e8d6-e633-4551-a082-2334a300fa72",
        "c9e90d83-533f-44c3-8220-083a6eb91751",
    )

    # Create new MSCL
    new_mscl = MicroServiceChainLink.objects.create(
        id=uuids[0],
        microservicegroup="Upload DIP",
        defaultexitmessage=Job.STATUS_FAILED,
        defaultnextchainlink_id="651236d2-d77f-4ca7-bfe9-6332e96608ff",
        currenttask=TaskConfig.objects.create(
            id=uuids[1],
            tasktypepkreference="",
            description="Choose config for AtoM DIP upload",
            tasktype_id="9c84b047-9a6d-463f-9836-eafa49743b84",
        ),  # linkTaskManagerReplacementDicFromChoice
    )

    # Create new exit code
    MicroServiceChainLinkExitCode.objects.create(
        id=uuids[2],
        microservicechainlink=new_mscl,
        nextmicroservicechainlink_id="651236d2-d77f-4ca7-bfe9-6332e96608ff",
    )

    # Update MSC
    MicroServiceChain.objects.filter(
        pk="0fe9842f-9519-4067-a691-8a363132ae24", description="Upload DIP to Atom"
    ).update(
        description="Upload DIP to AtoM",  # Cosmetic change (s/Atom/AtoM)
        startinglink=new_mscl,
    )


def data_migration_as_to_dict(apps, schema_editor):
    """
    Move config attributes from ArchivesSpaceConfig and
    MicroServiceChoiceReplacementDic to joint DashboardSetting dict.
    """
    ArchivesSpaceConfig = apps.get_model("administration", "ArchivesSpaceConfig")
    MicroServiceChoiceReplacementDic = apps.get_model(
        "main", "MicroServiceChoiceReplacementDic"
    )

    # List of arguments
    cmd_args = (
        "host",
        "port",
        "user",
        "passwd",
        "dip_location",
        "dip_name",
        "dip_uuid",
        "restrictions",
        "object_type",
        "xlink_actuate",
        "xlink_show",
        "use_statement",
        "uri_prefix",
        "access_conditions",
        "use_conditions",
        "inherit_notes",
        "repository",
    )

    # Default to empty string for every argument
    config_dict = {arg_name: "" for arg_name in cmd_args}

    # Attempt to read defaults from MicroServiceChoiceReplacementDic
    try:
        mscrd = MicroServiceChoiceReplacementDic.objects.get(
            pk="f8749dd2-0923-4b57-a074-45cd92ace56f",
            description="ArchivesSpace Config",
        )
    except MicroServiceChoiceReplacementDic.DoesNotExist:
        pass
    else:
        try:
            replacementdic = ast.literal_eval(mscrd.replacementdic)
        except (SyntaxError, ValueError):
            # This is likely going to happen (SyntaxError) because the value was
            # mailformed, not a valid literal.
            pass
        else:
            for arg_name in cmd_args:
                attr_name = str("%{}%".format(arg_name))
                if attr_name in replacementdic:
                    config_dict[arg_name] = replacementdic[attr_name]
        mscrd.delete()  # As LinkTaskManagerReplacementDicFromChoice will look up DashboardSetting

    # Attempt to read current config from ArchivesSpaceConfig
    config = ArchivesSpaceConfig.objects.first()
    if config is not None:
        for arg_name in cmd_args:
            attr = getattr(config, arg_name, "")
            if attr:
                config_dict[arg_name] = attr

    DashboardSetting.objects.set_dict("upload-archivesspace_v0.0", config_dict)


def data_migration_atk_to_dict(apps, schema_editor):
    """
    Move config attributes from ArchivistsToolkitConfig and
    MicroServiceChoiceReplacementDic to joint DashboardSetting dict.
    """
    ArchivistsToolkitConfig = apps.get_model(
        "administration", "ArchivistsToolkitConfig"
    )
    MicroServiceChoiceReplacementDic = apps.get_model(
        "main", "MicroServiceChoiceReplacementDic"
    )

    # List of arguments
    cmd_args = (
        "host",
        "port",
        "dbname",
        "dbuser",
        "dbpass",
        "dip_location",
        "dip_name",
        "dip_uuid",
        "atuser",
        "restrictions",
        "object_type",
        "ead_actuate",
        "ead_show",
        "use_statement",
        "uri_prefix",
        "access_conditions",
        "use_conditions",
    )

    # Default to empty string for every argument
    config_dict = {arg_name: "" for arg_name in cmd_args}

    # Attempt to read defaults from MicroServiceChoiceReplacementDic
    try:
        mscrd = MicroServiceChoiceReplacementDic.objects.get(
            pk="5395d1ea-a892-4029-b5a8-5264a17bbade",
            description="Archivists Toolkit Config",
        )
    except MicroServiceChoiceReplacementDic.DoesNotExist:
        pass
    else:
        try:
            replacementdic = ast.literal_eval(mscrd.replacementdic)
        except (SyntaxError, ValueError):
            # This is likely going to happen (SyntaxError) because the value was
            # mailformed, not a valid literal.
            pass
        else:
            for arg_name in cmd_args:
                attr_name = str("%{}%".format(arg_name))
                if attr_name in replacementdic:
                    config_dict[arg_name] = replacementdic[attr_name]
        mscrd.delete()  # As LinkTaskManagerReplacementDicFromChoice will look up DashboardSetting

    # Attempt to read current config from ArchivistsToolkitConfig
    config = ArchivistsToolkitConfig.objects.first()
    if config is not None:
        for arg_name in cmd_args:
            attr = getattr(config, arg_name, "")
            if attr:
                config_dict[arg_name] = attr

    DashboardSetting.objects.set_dict("upload-archivistsToolkit_v0.0", config_dict)


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0031_job_currentstep_choices"),
        ("administration", "0006_use_statement_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="dashboardsetting",
            name="scope",
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterModelManagers(
            name="dashboardsetting", managers=[("objects", DashboardSettingManager())]
        ),
        migrations.RunPython(data_migration_atom_to_dict),
        migrations.RunPython(data_migration_atom_restore_std),
        migrations.RunPython(data_migration_as_to_dict),
        migrations.RunPython(data_migration_atk_to_dict),
    ]
