# -*- coding: utf-8 -*-
"""Migration to replace magic links with unit variables."""
from __future__ import absolute_import, unicode_literals

from collections import namedtuple

from django.db import migrations

# Can't use apps.get_model for this model as we need to access class attributes.
from main.models import Job


def data_migration(apps, schema_editor):
    """Replace magic links with unit variables.

    TaskConfigSetUnitVariable and TaskConfigUnitVariableLinkPull superseded
    magic links but we still have data in the workflow using the old system.
    """
    ###########################################################################
    # Model Classes
    ###########################################################################

    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    TaskConfig = apps.get_model("main", "TaskConfig")
    TaskType = apps.get_model("main", "TaskType")
    TaskConfigSetUnitVariable = apps.get_model("main", "TaskConfigSetUnitVariable")
    TaskConfigUnitVariableLinkPull = apps.get_model(
        "main", "TaskConfigUnitVariableLinkPull"
    )

    ###########################################################################
    # Remove Orphans
    ###########################################################################

    TaskConfig.objects.filter(
        pk__in=(
            "c6f9f99a-0b60-438f-9a8d-35d4989db2bb",  # TaskType "assign magic link"
            "38324d67-8358-4679-902d-c20dcdfd548b",  # TaskType "goto magic link"
        )
    ).delete()

    ###########################################################################
    # Useful Task Types
    ###########################################################################

    set_unit_variable_link_type_pk = TaskType.objects.get(
        description="linkTaskManagerSetUnitVariable"
    ).pk
    get_unit_variable_link_type_pk = TaskType.objects.get(
        description="linkTaskManagerUnitVariableLinkPull"
    ).pk

    ###########################################################################
    # Replace "assign magic link" objects
    ###########################################################################

    assign_magic_link = namedtuple(
        "AssignMagicLink", "mscl_pk tc_pk tcmagic_pk goto_mscl_pk " "new_uuid new_var"
    )
    assign_magic_links = [
        # These two determine the path after the package is moved to quarantine.
        # The goto_magic_link that looks it up is
        # 55de1490-f3a0-4e1e-a25b-38b75f4f05e3 with description "Find type to
        # process as".
        assign_magic_link(
            # Description: "Designate to process as a standard transfer".
            mscl_pk="9071c352-aed5-444c-ac3f-b6c52dfb65ac",
            tc_pk="a2e93146-a3ff-4e6c-ae3d-76ce49ca5e1b",
            tcmagic_pk="5dffcd9c-472d-44e0-ae4d-a30705cf80cd",
            goto_mscl_pk="755b4177-c587-41a7-8c52-015277568302",
            new_uuid="677dd361-53a1-4780-9105-5a4ead821adb",
            new_var="linkAfterMovedToQuarantine",
        ),
        assign_magic_link(
            # Description: "Designate to process as a DSpace transfer".
            mscl_pk="a6e97805-a420-41af-b708-2a56de5b47a6",
            tc_pk="7872599e-ebfc-472b-bb11-524ff728679f",
            tcmagic_pk="f1357379-0118-4f51-aa49-37aeb702b760",
            goto_mscl_pk="05f99ffd-abf2-4f5a-9ec8-f80a59967b89",
            new_uuid="e2d0b0c9-869c-4e1d-ae5c-b420c829f7f1",
            new_var="linkAfterMovedToQuarantine",
        ),
        # These two determine the path after the package is removed from
        # quarantine. The goto_magic_link that looks it up is
        # fbc3857b-bb02-425b-89ce-2d6a39eaa542 with description: "Find type to
        # remove from quarantine as".
        assign_magic_link(
            # Description: "Designate to process as a standard transfer when
            # unquarantined".
            mscl_pk="cf71e6ff-7740-4bdb-a6a9-f392d678c6e1",
            tc_pk="851d679e-44db-485a-9b0e-2dfbdf80c791",
            tcmagic_pk="1c460578-e696-4378-a5d1-63ee77dd18bc",
            goto_mscl_pk="f3a58cbb-20a8-4c6d-9ae4-1a5f02c1a28e",
            new_uuid="f4b7f902-c1e1-47cc-a2ef-e71d1c7c6c39",
            new_var="linkAfterMovedFromQuarantine",
        ),
        assign_magic_link(
            # Description: "Designate to process as a DSpace transfer when
            # unquarantined".
            mscl_pk="7e65c627-c11d-4aad-beed-65ceb7053fe8",
            tc_pk="f5ca3e51-35ba-4cdd-acf5-7d4fec955e76",
            tcmagic_pk="5975a5df-41af-4e3e-8e4e-ec7aff3ae085",
            goto_mscl_pk="19adb668-b19a-4fcb-8938-f49d7485eaf3",
            new_uuid="3edcaf2b-72ce-4d42-8185-c2e582cebccc",
            new_var="linkAfterMovedFromQuarantine",
        ),
        # In a standard transfer, if "Verify transfer compliance" or "Verify
        # mets_structmap.xml compliance" fail the workflow does the following:
        #
        # 1. Execute the following assign_magic_link to associate the magic
        #    link.
        # 2. Execute "Failed compliance" which moves the package to the watched
        #    directory: "system/autoRestructureForCompliance".
        # 3. That triggers a new chain that starts with the goto_magic_link
        #    "Find branch to continue processing".
        #
        # This is the only use case of "system/autoRestructureForCompliance" and
        # there are no other assign_magic_links used to determine different
        # paths so we could probably simplify the workflow although I prefer to
        # do that after this migration.
        assign_magic_link(
            # Description: "Designate to process as a standard transfer".
            mscl_pk="2e7f83f9-495a-44b3-b0cf-bff66f021a4d",
            tc_pk="3875546f-9137-4c8f-9fcc-ed112eaa6414",
            tcmagic_pk="c691548f-0131-4bd5-864c-364b1f7feb7f",
            goto_mscl_pk="5c459c1a-f998-404d-a0dd-808709510b72",
            new_uuid="0ec83b1a-8f41-4731-8ac7-2159c1afdce9",
            new_var="linkAfterAutoRestructureForCompliance",
        ),
    ]

    for item in assign_magic_links:
        # Create TaskConfigSetUnitVariable.
        TaskConfigSetUnitVariable.objects.create(
            pk=item.new_uuid,
            variable=item.new_var,
            variablevalue=None,
            microservicechainlink_id=item.goto_mscl_pk,
        )
        # Update TaskConfig.
        TaskConfig.objects.filter(pk=item.tc_pk).update(
            tasktype_id=set_unit_variable_link_type_pk,
            tasktypepkreference=item.new_uuid,
        )

    ###########################################################################
    # Replace "goto magic link" objects
    ###########################################################################

    goto_magic_link = namedtuple("GotoMagicLink", "mscl_pk tc_pk new_uuid new_var")
    goto_magic_links = [
        goto_magic_link(
            # Description: "Find type to process as".
            mscl_pk="55de1490-f3a0-4e1e-a25b-38b75f4f05e3",
            tc_pk="07f6f419-d51f-4c69-bca6-a395adecbee0",
            new_uuid="59c4831d-687a-49ec-903c-e581fafc488e",
            new_var="linkAfterMovedToQuarantine",
        ),
        goto_magic_link(
            # Description: "Find type to remove from quarantine as".
            mscl_pk="fbc3857b-bb02-425b-89ce-2d6a39eaa542",
            tc_pk="93e01ed2-8d69-4a56-b686-3cf507931885",
            new_uuid="39c26a2f-f0c6-438e-bd37-3fdd1f235b65",
            new_var="linkAfterMovedFromQuarantine",
        ),
        goto_magic_link(
            # Description: "Find branch to continue processing".
            mscl_pk="a98ba456-3dcd-4f45-804c-a40220ddc6cb",
            tc_pk="8fa944df-1baf-4f89-8106-af013b5078f4",
            new_uuid="f7cd409f-909e-4df2-8179-18d9bf4ba890",
            new_var="linkAfterAutoRestructureForCompliance",
        ),
    ]

    for item in goto_magic_links:
        # Create TaskConfigUnitVariableLinkPull.
        TaskConfigUnitVariableLinkPull.objects.create(
            pk=item.new_uuid,
            variable=item.new_var,
            variablevalue=None,
            defaultmicroservicechainlink=None,
        )
        # Update TaskConfig.
        TaskConfig.objects.filter(pk=item.tc_pk).update(
            tasktype_id=get_unit_variable_link_type_pk,
            tasktypepkreference=item.new_uuid,
        )
        # Update defaultexitmessage so the job isn't marked as failed.
        MicroServiceChainLink.objects.filter(pk=item.mscl_pk).update(
            defaultexitmessage=Job.STATUS_COMPLETED_SUCCESSFULLY
        )

    ###########################################################################
    # Remove types that we don't need anymore
    ###########################################################################

    TaskType.objects.filter(
        description__in=("assign magic link", "goto magic link")
    ).delete()


class Migration(migrations.Migration):
    """Migration generated by Django. `data_migration` added by us."""

    dependencies = [("main", "0049_change_pointer_file_filegrpuse")]

    operations = [
        migrations.RemoveField(model_name="taskconfigassignmagiclink", name="execute"),
        migrations.RemoveField(model_name="taskconfigassignmagiclink", name="replaces"),
        migrations.RemoveField(model_name="sip", name="magiclink"),
        migrations.RemoveField(model_name="sip", name="magiclinkexitmessage"),
        migrations.RemoveField(model_name="transfer", name="magiclink"),
        migrations.RemoveField(model_name="transfer", name="magiclinkexitmessage"),
        migrations.DeleteModel(name="TaskConfigAssignMagicLink"),
        migrations.RunPython(data_migration),
    ]
