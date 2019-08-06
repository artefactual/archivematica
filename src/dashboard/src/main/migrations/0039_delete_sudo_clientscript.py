# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """Delete "Set file permissions" chain links."""

    TaskConfig = apps.get_model("main", "TaskConfig")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )

    tc = TaskConfig.objects.get(id="ad38cdea-d1da-4d06-a7e5-6f75da85a718")
    stc = StandardTaskConfig.objects.get(
        id="6157fe87-26ff-49da-9899-d9036b21c4b0",
        execute="setDirectoryPermissionsForAppraisal_v0.0",
    )

    for mscl in MicroServiceChainLink.objects.filter(currenttask=tc):

        # Find the next chain link
        next_mscl = MicroServiceChainLinkExitCode.objects.get(
            microservicechainlink=mscl, exitcode=0
        ).nextmicroservicechainlink

        # Update affected chain links
        MicroServiceChainLinkExitCode.objects.filter(
            nextmicroservicechainlink=mscl
        ).update(nextmicroservicechainlink=next_mscl)
        MicroServiceChainLink.objects.filter(defaultnextchainlink=mscl).update(
            defaultnextchainlink=next_mscl
        )

        # Update affected chains
        MicroServiceChain.objects.filter(startinglink=mscl).update(
            startinglink=next_mscl
        )

        # Delete old exit codes
        MicroServiceChainLinkExitCode.objects.filter(
            microservicechainlink=mscl
        ).delete()

        mscl.delete()

    tc.delete()
    stc.delete()


class Migration(migrations.Migration):

    dependencies = [("main", "0038_fix_workflow_store_dip")]

    operations = [migrations.RunPython(data_migration)]
